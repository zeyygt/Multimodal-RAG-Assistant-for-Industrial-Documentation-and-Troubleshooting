"""Reranking module using cross-encoder model"""
import os
from typing import List
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass

from config import MAX_CHUNKS_TO_RERANK, DEVICE

try:
    from sentence_transformers import CrossEncoder
    CROSSENCODER_AVAILABLE = True
except ImportError:
    CROSSENCODER_AVAILABLE = False
    print("⚠️ sentence-transformers not installed. Install with: pip install sentence-transformers")


class Reranker:
    """Rerank chunks using cross-encoder model for semantic relevance"""
    
    def __init__(self, model_name="cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialize cross-encoder reranker
        
        Args:
            model_name (str): HuggingFace model name for cross-encoder
                            Options:
                            - "cross-encoder/ms-marco-MiniLM-L-6-v2" (default, fast, ~80MB)
                            - "BAAI/bge-reranker-base" (better quality, ~280MB)
                            - "BAAI/bge-reranker-large" (best quality, ~560MB, slow)
        """
        self.enabled = CROSSENCODER_AVAILABLE
        
        if not self.enabled:
            print("⚠️ Cross-encoder reranking disabled (sentence-transformers not available)")
            return
        
        try:
            print(f"📥 Loading reranker model: {model_name}...")
            self.model = CrossEncoder(model_name, max_length=512, device=DEVICE)
            print(f"✅ Reranker initialized on {DEVICE}")
        except Exception as e:
            print(f"⚠️ Failed to load reranker: {e}")
            self.enabled = False
    
    def rerank_chunks(self, query: str, chunks: List[dict], chunk_ids: List[int]) -> List[int]:
        """
        Rerank chunks using cross-encoder model
        
        Args:
            query (str): User query
            chunks (list): List of all chunks
            chunk_ids (list): List of chunk IDs to rerank
            
        Returns:
            list: Reranked chunk IDs (best first)
        """
        if not self.enabled:
            return chunk_ids  # Return as-is if disabled
        
        # Limit number of chunks to rerank (performance)
        chunk_ids = chunk_ids[:MAX_CHUNKS_TO_RERANK]
        
        if len(chunk_ids) <= 1:
            return chunk_ids  # No need to rerank 1 chunk
        
        # Prepare query-chunk pairs for cross-encoder
        pairs = []
        for cid in chunk_ids:
            chunk = chunks[cid]
            chunk_text = chunk.get("text", "")[:500]  # First 500 chars for efficiency
            pairs.append([query, chunk_text])
        
        try:
            # Get relevance scores from cross-encoder
            scores = self.model.predict(pairs)
            
            # Sort chunk IDs by scores (descending)
            scored_chunks = list(zip(chunk_ids, scores))
            scored_chunks.sort(key=lambda x: x[1], reverse=True)
            
            reranked_ids = [cid for cid, score in scored_chunks]
            
            print(f"🔄 Cross-encoder reranked {len(chunk_ids)} chunks (top score: {max(scores):.3f})")
            return reranked_ids
            
        except Exception as e:
            print(f"⚠️ Reranking failed: {e}")
            return chunk_ids  # Fallback to original order

# Singleton instance
_reranker = None

def get_reranker():
    """Get or create reranker instance"""
    global _reranker
    if _reranker is None:
        _reranker = Reranker()
    return _reranker
