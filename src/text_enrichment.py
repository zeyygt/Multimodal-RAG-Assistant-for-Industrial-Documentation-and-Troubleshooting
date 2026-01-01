"""Text enrichment module - adds semantic annotations to text blocks"""
import json
import re
from statistics import mean, median
from pathlib import Path
from ocr_utils import normalize_bbox, run_ocr_for_image
from config import OUTPUT_DIR


def split_numbered_items(text):
    """
    Split a single text block containing multiple numbered items
    into separate blocks - but ONLY if they are actual list items,
    not section headings like "2.4 Power on"
    """
    # Don't split if text is short and looks like a heading
    if len(text) < 120 and not text.endswith(('.', '?', '!')):
        # Check if it's a section heading pattern (e.g., "2.4 Something")
        if re.match(r'^\d+(\.\d+)*\s+\w+', text) and len(text.split()) < 10:
            return [text]  # Keep as is, it's a heading
    
    # Pattern: ①, ②, ③ or 1., 1), •, -, etc. (but not section numbers like "2.4")
    # Only split on patterns that look like list items within longer text
    pattern = r'(?:\n|^)\s*([①②③④⑤⑥⑦⑧⑨⑩]|\d+\.\s|\d+\)\s|[-•]\s)'
    parts = re.split(pattern, text)

    # If only 1-2 parts, it's probably not a list
    if len(parts) <= 3:
        return [text]
    
    results = []
    i = 1
    while i < len(parts):
        marker = parts[i].strip()
        if i + 1 < len(parts):
            content = parts[i + 1].strip()
            if content:  # Only add non-empty content
                results.append(f"{marker} {content}")
        i += 2

    return results if len(results) > 1 else [text]


def enrich_text_blocks(page, size_factor=1.15):
    """
    Enrich text blocks with semantic information:
    - Detect headings
    - Identify list items
    - Mark captions
    - Detect headers/footers
    
    Args:
        page (dict): Page dictionary with blocks
        size_factor (float): Font size multiplier for heading detection
        
    Returns:
        list: Enriched blocks
    """
    blocks = page["blocks"]
    page_h = page.get("height", None)

    # Calculate median font size
    font_sizes = [
        b["font_size"]
        for b in blocks
        if b.get("font_size") and b.get("type") == "text"
    ]
    med_font = median(font_sizes) if font_sizes else 10

    for b in blocks:
        # Skip non-text/non-table blocks
        if b.get("type") not in ("text", "table"):
            continue
        
        # Tables don't need role enrichment, just mark them
        if b.get("type") == "table":
            b["role"] = "table"
            b["clean_text"] = b.get("text", "")
            continue

        clean = re.sub(r"\s+", " ", b["text"]).strip()
        b["clean_text"] = clean
        char_len = len(clean)
        size = b.get("font_size", 0) or 0.0

        # List item detection - CHECK THIS FIRST
        has_unicode = bool(re.search(r"[①②③④⑤⑥⑦⑧⑨⑩]", clean))
        has_bullet = bool(re.match(r"^(\d+[\.\)]\s+|[-•*]\s+)", clean))
        b["is_list_item"] = has_unicode or has_bullet

        # Heading detection (but exclude list items like "3. Insert a blank...")
        # Section headings: "2.4 Power on" (has dot in middle)
        # NOT list items: "3. Insert card" (ends with dot or parenthesis)
        numbered = bool(re.match(r"^\d+(\.\d+)+\s+", clean))  # Must have at least 2 levels (e.g., 2.4)
        all_caps = clean.isupper() and char_len <= 80 and any(c.isalpha() for c in clean)
        not_sentence = not clean.endswith((".", "?", "!", ":", ","))
        short_text = char_len < 120

        maybe_heading = (
            not b["is_list_item"] and  # CRITICAL: Don't make list items headings
            short_text and (
                size >= med_font * size_factor or
                numbered or
                all_caps
            ) and not_sentence
        )

        heading_level = None
        if maybe_heading:
            if numbered:
                # Count dots to determine depth (2.4 = level 2, 2.4.1 = level 3)
                parts = clean.split()[0] if clean.split() else ""
                depth = parts.count(".") 
                heading_level = min(depth, 3)  # Cap at level 3
            elif size >= med_font * 1.5:
                heading_level = 1
            elif size >= med_font * 1.25:
                heading_level = 2
            else:
                heading_level = 3

        b["is_heading"] = maybe_heading
        b["heading_level"] = heading_level

        # Caption detection
        b["is_caption"] = bool(re.match(r"^(Figure|Fig\.|Table)\s+\d+", clean, re.I))

        # Header / Footer detection
        bbox = b.get("bbox") or [0, 0, 0, 0]
        y0, y1 = bbox[1], bbox[3]

        is_footer = page_h and y0 > page_h * 0.85 and char_len > 10
        is_header = page_h and y1 < page_h * 0.15 and char_len < 80

        # Role assignment
        if b["is_caption"]:
            b["role"] = "caption"
        elif b["is_heading"]:
            b["role"] = "section_heading" if heading_level == 1 else "subsection_heading"
        elif b["is_list_item"]:
            b["role"] = "list_item"
        elif is_footer:
            b["role"] = "footer"
        elif is_header:
            b["role"] = "header"
        else:
            b["role"] = "body"

    return blocks


def enrich_layout(input_path=None):
    """
    Main function to enrich layout with text annotations and OCR
    
    Args:
        input_path (str): Path to layout.json file
    """
    if input_path is None:
        input_path = OUTPUT_DIR / "layout.json"
    else:
        input_path = Path(input_path)

    with open(input_path, "r", encoding="utf-8") as f:
        pages = json.load(f)

    for page in pages:
        page_w = page["width"]
        page_h = page["height"]

        new_blocks = []
        for b in page["blocks"]:
            if b["type"] == "text":
                # Split numbered items
                splitted = split_numbered_items(b["text"])

                if len(splitted) == 1:
                    b["text"] = splitted[0]
                    new_blocks.append(b)
                else:
                    for part in splitted:
                        new_b = b.copy()
                        new_b["text"] = part
                        new_blocks.append(new_b)
            else:
                new_blocks.append(b)

        page["blocks"] = new_blocks

        # Enrich text blocks
        page["blocks"] = enrich_text_blocks(page)

        # Normalize bboxes and run OCR on images
        for b in page["blocks"]:
            if "bbox" in b:
                b["bbox_norm"] = normalize_bbox(b["bbox"], page_w, page_h)

            if b["type"] == "image":
                path = b.get("path")
                b["ocr_text"] = run_ocr_for_image(path)

    # Save enriched layout
    out_path = OUTPUT_DIR / "layout_text_enriched.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(pages, f, ensure_ascii=False, indent=2)

    print(f"✅ Text enrichment completed: {out_path}")
    return pages


if __name__ == "__main__":
    enrich_layout()
