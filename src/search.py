"""FAISS indexing and search module"""
import faiss
import numpy as np
import json
import re
from collections import Counter
from sentence_transformers import SentenceTransformer
from pathlib import Path
from config import OUTPUT_DIR, TEXT_MODEL, CLIP_MODEL, DEVICE
from llm_reranker import get_reranker
from query_expander import get_expander


class RAGSearchEngine:
    """RAG search engine with FAISS indexing"""
    
    def __init__(self):
        """Initialize search engine"""
        self.index = None
        self.chunks = None
        self.text_model = None
        self.clip_model = None
        self.reranker = None  # Will be initialized on first use
        self.expander = None  # Will be initialized on first use
        self.hybrid_meta = None
        
    def build_index(self):
        """Build FAISS index from hybrid embeddings"""
        # Load hybrid vectors
        hybrid_vectors = np.load(OUTPUT_DIR / "hybrid_vectors.npy")
        
        with open(OUTPUT_DIR / "hybrid_meta.json", "r") as f:
            self.hybrid_meta = json.load(f)
        
        dim = hybrid_vectors.shape[1]
        
        # Create FAISS index (Inner Product = cosine similarity for normalized vectors)
        self.index = faiss.IndexFlatIP(dim)
        
        # Normalize vectors for cosine similarity
        faiss.normalize_L2(hybrid_vectors)
        
        # Add to index
        self.index.add(hybrid_vectors)
        
        # Save index
        faiss.write_index(self.index, str(OUTPUT_DIR / "hybrid_faiss.index"))
        print(f"🔥 FAISS index built and saved ({hybrid_vectors.shape[0]} vectors)")
        
    def load_index(self):
        """Load existing FAISS index"""
        index_path = OUTPUT_DIR / "hybrid_faiss.index"
        if not index_path.exists():
            raise FileNotFoundError(f"Index not found at {index_path}. Run build_index() first.")
        
        self.index = faiss.read_index(str(index_path))
        
        with open(OUTPUT_DIR / "hybrid_meta.json", "r") as f:
            self.hybrid_meta = json.load(f)
            
        print(f"✅ FAISS index loaded ({self.index.ntotal} vectors)")
        
    def load_chunks(self):
        """Load chunks data"""
        with open(OUTPUT_DIR / "chunks_final.json", "r") as f:
            self.chunks = json.load(f)
        print(f"✅ Loaded {len(self.chunks)} chunks")
        
    def load_models(self):
        """Load embedding models"""
        print(f"Loading models on {DEVICE}...")
        self.text_model = SentenceTransformer(TEXT_MODEL, device=DEVICE)
        self.clip_model = SentenceTransformer(CLIP_MODEL, device=DEVICE)
        print("✅ Models loaded")
        
    def encode_query(self, query):
        """
        Encode query as hybrid vector (text + image embeddings)
        
        Args:
            query (str): Search query
            
        Returns:
            np.ndarray: Hybrid query vector
        """
        if self.text_model is None or self.clip_model is None:
            self.load_models()
        
        # Encode with text model
        q_text = self.text_model.encode(query, normalize_embeddings=True)
        
        # Encode with CLIP (text encoder)
        q_clip = self.clip_model.encode(query, normalize_embeddings=True)
        
        # Concatenate
        hybrid_q = np.concatenate([q_text, q_clip], axis=0).astype("float32")
        
        # Normalize for cosine similarity
        faiss.normalize_L2(hybrid_q.reshape(1, -1))
        
        return hybrid_q
    
    def search(self, query, k=5):
        """
        Search for top-k similar chunks
        
        Args:
            query (str): Search query
            k (int): Number of results
            
        Returns:
            tuple: (chunk_ids, similarity_scores)
        """
        if self.index is None:
            self.load_index()
        
        q_vec = self.encode_query(query)
        D, I = self.index.search(q_vec.reshape(1, -1), k)
        
        return I[0], D[0]
    
    def get_section_prefix(self, heading):
        """Extract section number prefix from heading (e.g., '1.2.3' from '1.2.3 Title')"""
        if not heading:
            return None
        m = re.match(r"^(\d+(\.\d+)*)", heading.strip())
        return m.group(1) if m else None
    
    def find_dominant_section(self, query, k=10):
        """
        Find the dominant section based on top-k search results
        
        Args:
            query (str): Search query
            k (int): Number of results to consider
            
        Returns:
            tuple: (chunk_ids, dominant_section_prefix)
        """
        if self.chunks is None:
            self.load_chunks()
        
        ids, scores = self.search(query, k=k)
        
        prefixes = []
        for cid in ids:
            heading = self.chunks[cid].get("section_heading", "")
            prefix = self.get_section_prefix(heading)
            if prefix:
                prefixes.append(prefix)
        
        if not prefixes:
            return ids, None
        
        counter = Counter(prefixes)
        dominant_prefix, _ = counter.most_common(1)[0]
        return ids, dominant_prefix
    
    def get_answer_chunks(self, query, k=10, use_multi_query=True, use_expansion=True, min_similarity=0.3):
        """
        Get all chunks from the dominant section identified by the query
        INCLUDING all subsections (e.g., 2.4, 2.4.1, 2.4.2)
        Sorted by relevance (similarity score)
        
        Args:
            query (str): Search query
            k (int): Number of initial results to consider
            use_multi_query (bool): Use query variations for better recall
            use_expansion (bool): Expand query with technical terms
            min_similarity (float): Minimum similarity threshold (0-1). Below this, return empty
            
        Returns:
            list: Chunk IDs from the dominant section, sorted by relevance
        """
        if self.chunks is None:
            self.load_chunks()
        
        # Initialize expander if needed
        if (use_multi_query or use_expansion) and self.expander is None:
            self.expander = get_expander()
        
        # Query expansion - add technical terms
        search_query = query
        if use_expansion and self.expander and self.expander.enabled:
            search_query = self.expander.expand_query(query)
        
        # Multi-query retrieval - get variations
        queries_to_search = [search_query]
        if use_multi_query and self.expander and self.expander.enabled:
            queries_to_search = self.expander.generate_multi_queries(search_query, num_queries=2)
        
        # Search with all query variations and collect results
        all_ids = []
        all_prefixes = []
        max_similarity = 0.0
        
        for q in queries_to_search:
            ids, scores = self.search(q, k=k)
            # Track max similarity score
            if len(scores) > 0:
                max_similarity = max(max_similarity, float(scores[0]))
            all_ids.extend(ids)
            
            # Get dominant prefix
            for cid in ids:
                heading = self.chunks[cid].get("section_heading", "")
                prefix = self.get_section_prefix(heading)
                if prefix:
                    all_prefixes.append(prefix)
        
        # Check if best match is below threshold
        print(f"🎯 Max similarity: {max_similarity:.3f} (threshold: {min_similarity})")
        if max_similarity < min_similarity:
            print(f"⚠️ Query not relevant to document (similarity {max_similarity:.3f} < {min_similarity})")
            return []
        
        # Find most common dominant prefix across all queries
        if all_prefixes:
            counter = Counter(all_prefixes)
            dominant_prefix, _ = counter.most_common(1)[0]
        elif all_ids:
            # Fallback to first result
            return list(dict.fromkeys(all_ids))[:k]  # Remove duplicates, keep order
        else:
            return []
        
        # Find all chunks with the same section prefix OR subsections
        # e.g., if dominant is "2.4", include "2.4", "2.4.1", "2.4.2" etc.
        candidate_ids = []
        for i, ch in enumerate(self.chunks):
            heading = ch.get("section_heading", "")
            prefix = self.get_section_prefix(heading)
            if prefix:
                # Match if prefix equals dominant OR starts with dominant + "."
                if prefix == dominant_prefix or prefix.startswith(dominant_prefix + "."):
                    # Filter out empty/header-only chunks
                    text = ch.get("text", "").strip()
                    has_content = (
                        len(text) > len(heading) + 10 or  # Has more than just heading
                        ch.get("images") or  # Has images
                        ch.get("ocr_snippets", "").strip()  # Has OCR text
                    )
                    if has_content:
                        candidate_ids.append(i)
        
        # Calculate similarity scores for all candidates using ORIGINAL query
        q_vec = self.encode_query(query)
        
        # Get embeddings for candidates
        if len(candidate_ids) == 0:
            return []
        
        candidate_vecs = []
        for cid in candidate_ids:
            # Get vector from index
            vec = self.index.reconstruct(int(cid))
            candidate_vecs.append(vec)
        
        import numpy as np
        candidate_vecs = np.vstack(candidate_vecs)
        
        # Calculate similarities
        similarities = np.dot(candidate_vecs, q_vec.reshape(-1, 1)).flatten()
        
        # Sort by similarity (highest first)
        sorted_indices = np.argsort(similarities)[::-1]
        answer_ids = [candidate_ids[i] for i in sorted_indices]
        
        # LLM Reranking (optional)
        if len(answer_ids) > 1:
            if self.reranker is None:
                self.reranker = get_reranker()
            
            if self.reranker.enabled:
                answer_ids = self.reranker.rerank_chunks(query, self.chunks, answer_ids)
        
        return answer_ids
    
    def pretty_print_chunk(self, chunk_id):
        """Print chunk in a readable format"""
        if self.chunks is None:
            self.load_chunks()
        
        chunk = self.chunks[chunk_id]
        
        print("=" * 60)
        print(f"CHUNK ID: {chunk['id']}")
        print(f"Page: {chunk['page_number']}")
        print(f"Section: {chunk['section_heading']}")
        print(f"Level: {chunk['section_level']}")
        print("-" * 60)
        
        print("\n📌 TEXT")
        print(chunk["text"].strip() if chunk.get("text") else "(no text)")
        print()
        
        print("📌 OCR SNIPPETS")
        print(chunk["ocr_snippets"].strip() if chunk.get("ocr_snippets") else "(no ocr)")
        print()
        
        print("📌 IMAGES")
        if chunk.get("images"):
            for i, img in enumerate(chunk["images"]):
                print(f"  {i+1}. path: {img['path']}")
                print(f"     linked_text: {img.get('linked_text')}")
                print(f"     ocr_text: {img.get('ocr_text')}")
                print(f"     similarity: {img.get('similarity_score')}")
                print()
        else:
            print("(no images)")
        print()
        
        print("📌 NORMALIZED BBOX")
        print(chunk.get("bbox_union_norm"))
        print("=" * 60)
        print("\n")


def main():
    """Example usage"""
    engine = RAGSearchEngine()
    
    # Build index (run once)
    print("Building FAISS index...")
    engine.build_index()
    
    # Load data
    engine.load_chunks()
    
    # Example search
    query = "How do I power on the CPU 1511-1 PN for the first time?"
    print(f"\nQuery: {query}\n")
    
    answer_ids = engine.get_answer_chunks(query, k=10)
    
    print(f"Found {len(answer_ids)} relevant chunks:\n")
    for cid in answer_ids:
        engine.pretty_print_chunk(cid)


if __name__ == "__main__":
    main()
