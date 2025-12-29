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

        # ---------- 1) Text blocks ----------
        td = page.get_text("dict")
        for b in td.get("blocks", []):
            if b.get("type", 0) == 0 and "lines" in b:
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

        # ---------- 2) Images ----------
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

        # ---------- 3) Vector drawings ----------
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

        # ---------- 4) Sort blocks (top to bottom, left to right) ----------
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
