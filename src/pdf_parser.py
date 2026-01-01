"""PDF parsing module - extracts text, images, and layout information"""
import fitz  # PyMuPDF
from pathlib import Path
from PIL import Image
from tqdm import tqdm
import json
import io
from statistics import mean
from config import OUTPUT_DIR, IMG_DIR, IMAGE_QUALITY, DPI


def save_pixmap(pix, fname_base):
    """Save pixmap as JPEG image"""
    out = IMG_DIR / f"{fname_base}.jpg"
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    img.save(out, format="JPEG", quality=IMAGE_QUALITY, optimize=True)
    return str(out)


def _bbox_overlap(bbox1, bbox2, threshold=0.5):
    """
    Check if two bounding boxes overlap significantly
    
    Args:
        bbox1, bbox2: Bounding boxes as [x0, y0, x1, y1]
        threshold: Minimum overlap ratio to consider as overlapping
        
    Returns:
        bool: True if boxes overlap significantly
    """
    x1_min, y1_min, x1_max, y1_max = bbox1
    x2_min, y2_min, x2_max, y2_max = bbox2
    
    # Calculate intersection area
    x_overlap = max(0, min(x1_max, x2_max) - max(x1_min, x2_min))
    y_overlap = max(0, min(y1_max, y2_max) - max(y1_min, y2_min))
    intersection = x_overlap * y_overlap
    
    if intersection == 0:
        return False
    
    # Calculate union area
    area1 = (x1_max - x1_min) * (y1_max - y1_min)
    area2 = (x2_max - x2_min) * (y2_max - y2_min)
    
    # Check if intersection is significant relative to smaller box
    smaller_area = min(area1, area2)
    overlap_ratio = intersection / smaller_area if smaller_area > 0 else 0
    
    return overlap_ratio > threshold


def parse_pdf(pdf_path):
    """
    Parse PDF and extract text, images, and layout information
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        list: List of page dictionaries with blocks
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    doc = fitz.open(str(pdf_path))
    all_pages = []

    for p in tqdm(range(len(doc)), desc="Parsing PDF"):
        page = doc[p]
        page_json = {
            "page_number": p + 1,
            "width": page.rect.width,
            "height": page.rect.height,
            "blocks": []
        }

        # ---------- 1) Tables (NEW - detect tables first) ----------
        table_bboxes = []
        try:
            tables = page.find_tables()
            for table in tables:
                table_bbox = table.bbox
                table_bboxes.append(table_bbox)
                
                # Extract table as pandas dataframe
                df = table.to_pandas()
                
                # Convert table to structured text with clear column headers
                table_text_parts = []
                
                # Add header row with clear separators
                if not df.empty:
                    headers = [str(h) for h in df.columns]
                    table_text_parts.append(" | ".join(headers))
                    table_text_parts.append("-" * 50)
                    
                    # Add data rows
                    for idx, row in df.iterrows():
                        row_values = [str(v) if str(v) != 'nan' else '' for v in row]
                        table_text_parts.append(" | ".join(row_values))
                
                table_text = "\n".join(table_text_parts)
                
                if table_text.strip():
                    page_json["blocks"].append({
                        "type": "table",
                        "text": table_text,
                        "bbox": list(table_bbox),
                        "rows": len(df),
                        "cols": len(df.columns)
                    })
        except Exception as e:
            # If table detection fails, continue with regular text extraction
            pass

        # ---------- 2) Text blocks (skip areas covered by tables) ----------
        td = page.get_text("dict")
        for b in td.get("blocks", []):
            if b.get("type", 0) == 0 and "lines" in b:
                # Check if this block overlaps with any table
                block_bbox = b["bbox"]
                overlaps_table = False
                for table_bbox in table_bboxes:
                    if _bbox_overlap(block_bbox, table_bbox):
                        overlaps_table = True
                        break
                
                if overlaps_table:
                    continue  # Skip text blocks that are part of tables
                
                texts, sizes = [], []
                for ln in b["lines"]:
                    for sp in ln.get("spans", []):
                        texts.append(sp.get("text", ""))
                        if "size" in sp:
                            sizes.append(sp["size"])
                text = " ".join(t.strip() for t in texts).strip()
                if text:
                    page_json["blocks"].append({
                        "type": "text",
                        "text": text,
                        "bbox": b["bbox"],
                        "font_size": round(mean(sizes), 2) if sizes else None
                    })

        # ---------- 3) Images ----------
        rd = page.get_text("rawdict")
        raw_image_blocks = []
        for b in rd.get("blocks", []):
            if b.get("type", 0) == 1:
                raw_image_blocks.append(b)

        xref_tuples = page.get_images(full=True)
        xrefs = {t[0] for t in xref_tuples}

        img_counter = 0
        for b in raw_image_blocks:
            bbox = b.get("bbox")
            xref = b.get("xref")
            fname_base = f"p{p+1:03d}_{img_counter:04d}"
            saved_path = None
            method = None

            if xref in xrefs:
                try:
                    info = doc.extract_image(xref)
                    img_bytes = info["image"]
                    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                    out_path = IMG_DIR / f"{fname_base}.jpg"
                    img.save(out_path, format="JPEG", quality=IMAGE_QUALITY, optimize=True)
                    saved_path = str(out_path)
                    method = "extract_image"
                except Exception:
                    pass

            # Fallback: clip and rasterize
            if saved_path is None and bbox:
                try:
                    pix = page.get_pixmap(clip=fitz.Rect(bbox), dpi=DPI, alpha=False)
                    saved_path = save_pixmap(pix, fname_base)
                    method = "clip_rasterize"
                except Exception:
                    method = "failed"

            page_json["blocks"].append({
                "type": "image",
                "bbox": bbox,
                "path": saved_path,
                "extract_method": method
            })
            img_counter += 1

        # ---------- 4) Vector drawings ----------
        try:
            drawings = page.get_drawings()
            for d in drawings:
                page_json["blocks"].append({
                    "type": "vector",
                    "bbox": list(d.get("rect", fitz.Rect()).irect),
                    "items": len(d.get("items", []))
                })
        except Exception:
            pass

        # ---------- 5) Sort blocks (top to bottom, left to right) ----------
        page_json["blocks"].sort(
            key=lambda x: (
                round(x["bbox"][1], 1) if x.get("bbox") else 0,
                round(x["bbox"][0], 1) if x.get("bbox") else 0
            )
        )
        all_pages.append(page_json)

    doc.close()
    
    # Save layout JSON
    output_path = OUTPUT_DIR / "layout.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_pages, f, ensure_ascii=False, indent=2)

    print(f"✅ Done. JSON: {output_path}")
    print(f"🖼️ Images saved under: {IMG_DIR}")
    
    return all_pages


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python pdf_parser.py <pdf_file_path>")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    parse_pdf(pdf_file)
