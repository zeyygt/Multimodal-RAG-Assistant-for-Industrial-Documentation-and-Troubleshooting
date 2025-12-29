"""LLM-based chunk reranking module"""
import os
import json
from typing import List, Tuple
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass

from config import USE_LLM_RERANKING, LLM_MODEL, MAX_CHUNKS_TO_RERANK

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI not installed. Install with: pip install openai")


class LLMReranker:
    """Rerank chunks using LLM to determine relevance"""
    
    def __init__(self, api_key=None):
        """
        Initialize LLM reranker
        
        Args:
            api_key (str): OpenAI API key (or set OPENAI_API_KEY env var)
        """
        self.enabled = USE_LLM_RERANKING and OPENAI_AVAILABLE
        
        if not self.enabled:
            return
        
        # Get API key
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        
        if not self.api_key:
            print("⚠️ OPENAI_API_KEY not set. LLM reranking disabled.")
            print("   Set it with: export OPENAI_API_KEY='your-key-here'")
            self.enabled = False
            return
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = LLM_MODEL
        print(f"✅ LLM Reranker initialized ({self.model})")
    
    def rerank_chunks(self, query: str, chunks: List[dict], chunk_ids: List[int]) -> List[int]:
        """
        Rerank chunks using LLM
        
        Args:
            query (str): User query
            chunks (list): List of all chunks
            chunk_ids (list): List of chunk IDs to rerank
            
        Returns:
            list: Reranked chunk IDs (best first)
        """
        if not self.enabled:
            return chunk_ids  # Return as-is if disabled
        
        # Limit number of chunks to rerank (cost control)
        chunk_ids = chunk_ids[:MAX_CHUNKS_TO_RERANK]
        
        if len(chunk_ids) <= 1:
            return chunk_ids  # No need to rerank 1 chunk
        
        # Prepare chunk summaries for LLM
        chunk_summaries = []
        for idx, cid in enumerate(chunk_ids):
            chunk = chunks[cid]
            summary = {
                "id": idx,  # Use local index for LLM
                "section": chunk.get("section_heading", "Unknown"),
                "page": chunk.get("page_number", "?"),
                "text_preview": chunk.get("text", "")[:300],  # First 300 chars
                "has_images": bool(chunk.get("images")),
                "has_procedure": any(kw in chunk.get("text", "").lower() 
                                    for kw in ["procedure", "step", "1.", "2.", "3."])
            }
            chunk_summaries.append(summary)
        
        # Create prompt
        prompt = self._create_reranking_prompt(query, chunk_summaries)
        
        try:
            # Call LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that ranks document chunks by relevance to a query."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=200
            )
            
            # Parse response
            ranking_text = response.choices[0].message.content.strip()
            reranked_indices = self._parse_ranking(ranking_text, len(chunk_ids))
            
            # Map back to original chunk IDs
            reranked_chunk_ids = [chunk_ids[i] for i in reranked_indices]
            
            print(f"🤖 LLM reranked {len(chunk_ids)} chunks")
            return reranked_chunk_ids
            
        except Exception as e:
            print(f"⚠️ LLM reranking failed: {e}")
            return chunk_ids  # Fallback to original order
    
    def _create_reranking_prompt(self, query: str, chunk_summaries: List[dict]) -> str:
        """Create prompt for LLM reranking"""
        chunks_text = "\n".join([
            f"Chunk {c['id']}: [{c['section']}] (Page {c['page']}) "
            f"{'[HAS_IMAGES] ' if c['has_images'] else ''}"
            f"{'[PROCEDURE] ' if c['has_procedure'] else ''}"
            f"\n  Text: {c['text_preview']}..."
            for c in chunk_summaries
        ])
        
        prompt = f"""Given this user query:
"{query}"

Rank these document chunks from MOST to LEAST relevant for answering the query.

RANKING RULES:
1. For "How to" questions: PRIORITIZE chunks with step-by-step procedures/instructions
2. Overview/introduction chunks should be LAST unless specifically asked for
3. Chunks with [PROCEDURE] tag are usually more valuable than general descriptions
4. Chunks with [HAS_IMAGES] showing visual instructions are more helpful
5. Match the query intent: actionable instructions > definitions > general info

Chunks:
{chunks_text}

Return ONLY the chunk IDs in order (most relevant first), as a comma-separated list.
Example: 1,2,0,3

Your ranking:"""
        
        return prompt
    
    def _parse_ranking(self, ranking_text: str, num_chunks: int) -> List[int]:
        """Parse LLM ranking response"""
        try:
            # Extract numbers from response
            import re
            numbers = re.findall(r'\d+', ranking_text)
            indices = [int(n) for n in numbers if int(n) < num_chunks]
            
            # Add missing indices at the end
            missing = [i for i in range(num_chunks) if i not in indices]
            indices.extend(missing)
            
            return indices[:num_chunks]
        except:
            # Fallback: return original order
            return list(range(num_chunks))


# Singleton instance
_reranker = None

def get_reranker():
    """Get or create reranker instance"""
    global _reranker
    if _reranker is None:
        _reranker = LLMReranker()
    return _reranker
