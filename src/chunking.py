"""Chunking module - creates semantic chunks from parsed PDF"""
import json
from pathlib import Path
from config import OUTPUT_DIR


def normalize_text(t):
    """Normalize whitespace in text"""
    return " ".join(t.split()).strip() if t else ""


def union_bbox_norm(blocks):
    """Calculate union of normalized bounding boxes"""
    xs0, ys0, xs1, ys1 = [], [], [], []
    for b in blocks:
        bb = b.get("bbox_norm")
        if bb:
            x0, y0, x1, y1 = bb
            xs0.append(x0)
            ys0.append(y0)
            xs1.append(x1)
            ys1.append(y1)
    if not xs0:
        return None
    return [min(xs0), min(ys0), max(xs1), max(ys1)]


def create_chunks(input_path=None):
    """
    Create multimodal chunks from semantically linked layout
    
    Chunks are created based on:
    - Section headings (create new chunks)
    - Body text and list items (added to current chunk)
    - Images (added to current chunk with metadata)
    
    Args:
        input_path (str): Path to layout_semantic_links.json
        
    Returns:
        list: List of chunk dictionaries
    """
    if input_path is None:
        input_path = OUTPUT_DIR / "layout_semantic_links.json"
    else:
        input_path = Path(input_path)

    with open(input_path, "r", encoding="utf-8") as f:
        pages = json.load(f)

    chunks = []
    chunk_id = 0
    current_chunk = None
    last_heading = None

    for page in pages:
        page_num = page["page_number"]
        blocks = page["blocks"]

        for idx, b in enumerate(blocks):

            # ------------------------------------------------
            # 1) HEADING: Create new chunk OR continue existing
            # ------------------------------------------------
            if b.get("type") == "text" and b.get("role") in ("section_heading", "subsection_heading"):

                heading = normalize_text(b.get("clean_text") or b.get("text"))
                level = b.get("heading_level", 2) or 2

                # If it's the SAME heading as before, continue the chunk (multi-page section)
                if current_chunk and heading == last_heading:
                    # Just skip this duplicate heading, keep building same chunk
                    continue
                
                # Different heading - finalize previous chunk and start new
                if current_chunk:
                    chunks.append(current_chunk)
                    chunk_id += 1

                last_heading = heading
                current_chunk = {
                    "id": f"chunk_{chunk_id:06d}",
                    "page_number": page_num,
                    "section_heading": heading,
                    "section_level": int(level),
                    "text": heading + "\n",
                    "text_blocks": [(page_num, idx)],
                    "image_blocks": [],
                    "images": [],
                    "ocr_snippets": "",
                    "bbox_union_norm": None,
                    "modality": "text"
                }
                continue

            # ------------------------------------------------
            # 2) BODY / LIST ITEM / CAPTION
            # ------------------------------------------------
            if current_chunk and b.get("type") == "text" and b.get("role") in ("body", "list_item", "caption"):

                current_chunk["text_blocks"].append((page_num, idx))
                txt = normalize_text(b.get("clean_text") or b.get("text"))

                if b["role"] == "list_item":
                    current_chunk["text"] += f"- {txt}\n"
                elif b["role"] == "caption":
                    current_chunk["text"] += f"[Caption] {txt}\n"
                else:
                    current_chunk["text"] += txt + "\n"
                continue

            # ------------------------------------------------
            # 3) Orphan body text (before first heading)
            # ------------------------------------------------
            if not current_chunk and b.get("type") == "text" and b.get("role") in ("body", "list_item"):
                heading = f"Page {page_num} – Unnamed Section"
                last_heading = heading

                current_chunk = {
                    "id": f"chunk_{chunk_id:06d}",
                    "page_number": page_num,
                    "section_heading": heading,
                    "section_level": 3,
                    "text": heading + "\n",
                    "text_blocks": [],
                    "image_blocks": [],
                    "images": [],
                    "ocr_snippets": "",
                    "bbox_union_norm": None,
                    "modality": "text"
                }

                current_chunk["text_blocks"].append((page_num, idx))
                txt = normalize_text(b.get("clean_text") or b.get("text"))
                current_chunk["text"] += txt + "\n"
                continue

            # ------------------------------------------------
            # 4) IMAGE BLOCK
            # ------------------------------------------------
            if b.get("type") == "image":

                img_obj = {
                    "path": b.get("path"),
                    "bbox_norm": b.get("bbox_norm"),
                    "ocr_text": b.get("ocr_text"),
                    "linked_text": b.get("linked_text"),
                    "similarity_score": b.get("similarity_score")
                }

                if current_chunk:
                    current_chunk["image_blocks"].append((page_num, idx))
                    current_chunk["images"].append(img_obj)

                    if b.get("ocr_text"):
                        current_chunk["ocr_snippets"] += " " + b["ocr_text"]

                    current_chunk["modality"] = "multimodal"
                else:
                    # Orphan image chunk
                    orphan_chunk = {
                        "id": f"chunk_{chunk_id:06d}",
                        "page_number": page_num,
                        "section_heading": f"Image on page {page_num}",
                        "section_level": 3,
                        "text": "",
                        "text_blocks": [],
                        "image_blocks": [(page_num, idx)],
                        "images": [img_obj],
                        "ocr_snippets": b.get("ocr_text") or "",
                        "bbox_union_norm": b.get("bbox_norm"),
                        "modality": "image"
                    }
                    chunks.append(orphan_chunk)
                    chunk_id += 1

                continue

    # Finalize last chunk
    if current_chunk:
        chunks.append(current_chunk)

    # Save chunks
    output_path = OUTPUT_DIR / "chunks_final.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"🔥 Multimodal chunking completed.")
    print(f"📦 Total chunks: {len(chunks)}")
    print(f"📁 Output: {output_path}")

    return chunks


if __name__ == "__main__":
    create_chunks()
