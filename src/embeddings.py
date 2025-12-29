"""Embedding generation module - creates text and image embeddings"""
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from PIL import Image
from tqdm import tqdm
from pathlib import Path
from config import (
    OUTPUT_DIR,
    TEXT_MODEL,
    CLIP_MODEL,
    TEXT_MODEL_MAX_SEQ_LENGTH,
    BATCH_SIZE,
    DEVICE
)


def build_text_for_embedding(ch):
    """
    Build text string for embedding from chunk
    
    Combines:
    - Section heading
    - Body text
    - OCR snippets from diagrams
    """
    parts = []

    if ch.get("section_heading"):
        parts.append(ch["section_heading"])

    if ch.get("text"):
        parts.append(ch["text"])

    if ch.get("ocr_snippets"):
        parts.append("[Diagram OCR] " + ch["ocr_snippets"])

    return "\n".join([p.strip() for p in parts if p.strip()])


def generate_text_embeddings():
    """
    Generate text embeddings for all chunks using BGE model
    
    Returns:
        tuple: (embeddings array, metadata dict)
    """
    # Load chunks
    with open(OUTPUT_DIR / "chunks_final.json", "r", encoding="utf-8") as f:
        chunks = json.load(f)

    # Load text model
    print(f"Loading text model ({TEXT_MODEL}) on {DEVICE}...")
    text_model = SentenceTransformer(TEXT_MODEL, device=DEVICE)
    text_model.max_seq_length = TEXT_MODEL_MAX_SEQ_LENGTH

    # Build texts for embedding
    texts = []
    index_map = []

    for i, ch in enumerate(chunks):
        txt = build_text_for_embedding(ch)
        if txt.strip():
            texts.append(txt)
            index_map.append(i)

    print(f"Generating embeddings for {len(texts)} text chunks...")

    # Generate embeddings
    text_embs = text_model.encode(
        texts,
        batch_size=BATCH_SIZE,
        normalize_embeddings=True,
        show_progress_bar=True,
        device=DEVICE
    )

    text_embs = np.asarray(text_embs, dtype="float32")

    # Save embeddings
    np.save(OUTPUT_DIR / "text_embeddings.npy", text_embs)

    # Save metadata
    metadata = {
        "model": TEXT_MODEL,
        "dim": int(text_embs.shape[1]),
        "chunk_index": index_map
    }
    with open(OUTPUT_DIR / "text_meta.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"✅ Text embeddings saved: {text_embs.shape}")
    return text_embs, metadata


def generate_image_embeddings():
    """
    Generate image embeddings for chunks with images using CLIP
    
    Returns:
        tuple: (embeddings array, metadata dict) or (None, None) if no images
    """
    # Load chunks
    with open(OUTPUT_DIR / "chunks_final.json", "r", encoding="utf-8") as f:
        chunks = json.load(f)

    # Load CLIP model
    print(f"Loading CLIP model ({CLIP_MODEL}) on {DEVICE}...")
    clip_model = SentenceTransformer(CLIP_MODEL, device=DEVICE)

    image_vectors = []
    image_chunk_idx = []
    image_paths = []

    for i, ch in enumerate(tqdm(chunks, desc="Embedding images")):
        imgs = ch.get("images", [])

        if not imgs:
            continue

        per_chunk_embs = []

        for obj in imgs:
            path = obj.get("path")
            if not path:
                continue
            try:
                img = Image.open(path).convert("RGB")
                emb = clip_model.encode(img, convert_to_tensor=True)
                per_chunk_embs.append(emb)
            except Exception as e:
                print(f"Failed to process image {path}: {e}")
                continue

        if not per_chunk_embs:
            continue

        # Average multiple images in same chunk
        import torch
        stacked = torch.stack(per_chunk_embs, 0)
        mean_emb = torch.mean(stacked, dim=0)
        mean_emb = torch.nn.functional.normalize(mean_emb, dim=0)

        image_vectors.append(mean_emb.cpu().numpy().astype("float32"))
        image_chunk_idx.append(i)
        image_paths.append(imgs[0]["path"])

    if not image_vectors:
        print("⚠️ No image embeddings produced")
        return None, None

    image_vectors = np.vstack(image_vectors)

    # Save embeddings
    np.save(OUTPUT_DIR / "image_embeddings.npy", image_vectors)

    # Save metadata
    metadata = {
        "model": CLIP_MODEL,
        "dim": int(image_vectors.shape[1]),
        "chunk_index": image_chunk_idx,
        "image_paths": image_paths
    }
    with open(OUTPUT_DIR / "image_meta.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"✅ Image embeddings saved: {image_vectors.shape}")
    return image_vectors, metadata


def generate_hybrid_embeddings():
    """
    Generate hybrid embeddings by concatenating text and image embeddings
    
    Returns:
        tuple: (hybrid embeddings array, metadata dict)
    """
    # Load text embeddings
    text_embs = np.load(OUTPUT_DIR / "text_embeddings.npy")
    with open(OUTPUT_DIR / "text_meta.json", "r") as f:
        text_meta = json.load(f)

    # Load image embeddings
    try:
        image_embs = np.load(OUTPUT_DIR / "image_embeddings.npy")
        with open(OUTPUT_DIR / "image_meta.json", "r") as f:
            image_meta = json.load(f)
        has_images = True
    except FileNotFoundError:
        print("⚠️ No image embeddings found, using zeros.")
        has_images = False

    # Number of chunks
    N = len(text_embs)
    text_dim = text_embs.shape[1]
    image_dim = 512  # CLIP ViT-B-32 dimension

    # Create image lookup
    img_lookup = {}
    if has_images:
        for i, chunk_id in enumerate(image_meta["chunk_index"]):
            img_lookup[chunk_id] = image_embs[i]

    # Build hybrid vectors
    hybrid_vectors = []

    for i in range(N):
        t_vec = text_embs[i]

        if i in img_lookup:
            im_vec = img_lookup[i]
        else:
            im_vec = np.zeros(image_dim, dtype="float32")

        # Concatenate
        hybrid = np.concatenate([t_vec, im_vec], axis=0)
        hybrid_vectors.append(hybrid)

    hybrid_vectors = np.vstack(hybrid_vectors).astype("float32")

    print(f"Hybrid vectors shape: {hybrid_vectors.shape}")

    # Save hybrid vectors
    np.save(OUTPUT_DIR / "hybrid_vectors.npy", hybrid_vectors)

    # Save metadata
    metadata = {
        "dim": hybrid_vectors.shape[1],
        "text_dim": text_dim,
        "image_dim": image_dim,
        "total_chunks": N,
        "bge_model": text_meta["model"],
        "clip_model": CLIP_MODEL
    }
    with open(OUTPUT_DIR / "hybrid_meta.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print("🔥 Hybrid vectors saved.")
    return hybrid_vectors, metadata


if __name__ == "__main__":
    print("Step 1: Generating text embeddings...")
    generate_text_embeddings()

    print("\nStep 2: Generating image embeddings...")
    generate_image_embeddings()

    print("\nStep 3: Generating hybrid embeddings...")
    generate_hybrid_embeddings()

    print("\n✅ All embeddings generated successfully!")
