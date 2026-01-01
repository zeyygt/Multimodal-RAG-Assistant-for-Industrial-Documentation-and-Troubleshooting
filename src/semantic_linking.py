"""Semantic linking module - links images to related text using CLIP"""
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
import torch
from PIL import Image
from tqdm import tqdm
from config import OUTPUT_DIR, CLIP_MODEL, SIMILARITY_THRESHOLD, DEVICE


def semantic_link_images_to_text(blocks, img_dir=None):
    """
    Link each image to the most semantically similar text block using CLIP
    
    Args:
        blocks (list): List of blocks (text, tables, and images)
        img_dir: Not used, kept for compatibility
        
    Returns:
        list: Blocks with semantic links added to images
    """
    # Include both text and table blocks for semantic linking
    text_blocks = [b for b in blocks if b["type"] in ("text", "table")]
    img_blocks = [b for b in blocks if b["type"] == "image"]

    # Get text content (tables also have text field)
    texts = [t.get("clean_text") or t.get("text") for t in text_blocks]
    if len(texts) == 0:
        return blocks

    # Load CLIP model
    print(f"Loading CLIP model ({CLIP_MODEL}) on {DEVICE}...")
    clip_model = SentenceTransformer(CLIP_MODEL, device=DEVICE)

    # Encode all texts at once
    text_embs = clip_model.encode(
        texts,
        convert_to_tensor=True,
        batch_size=8,
        show_progress_bar=False
    )

    # Process each image
    for img in img_blocks:
        img_path = img.get("path")
        if not img_path:
            img["linked_text"] = None
            continue

        try:
            image = Image.open(img_path).convert("RGB")
            image_emb = clip_model.encode(image, convert_to_tensor=True)

            # Calculate cosine similarity
            sims = torch.nn.functional.cosine_similarity(
                image_emb.unsqueeze(0), text_embs
            )

            # Find best match
            best_idx = int(torch.argmax(sims))
            best_score = sims[best_idx].item()

            # Apply threshold
            if best_score < SIMILARITY_THRESHOLD:
                img["linked_text"] = None
            else:
                img["linked_text"] = texts[best_idx]

            img["similarity_score"] = round(float(best_score), 4)

        except Exception as e:
            img["linked_text"] = None
            img["error"] = str(e)

    return blocks


def create_semantic_links(input_path=None):
    """
    Main function to create semantic links between images and text
    
    Args:
        input_path (str): Path to layout_text_enriched.json
    """
    if input_path is None:
        input_path = OUTPUT_DIR / "layout_text_enriched.json"
    else:
        input_path = Path(input_path)

    with open(input_path, "r", encoding="utf-8") as f:
        pages = json.load(f)

    print("Creating semantic links between images and text...")
    for p in tqdm(pages, desc="Processing pages"):
        p["blocks"] = semantic_link_images_to_text(p["blocks"], None)

    out_path = OUTPUT_DIR / "layout_semantic_links.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(pages, f, ensure_ascii=False, indent=2)

    print(f"✅ Semantic linking completed: {out_path}")
    return pages


if __name__ == "__main__":
    create_semantic_links()
