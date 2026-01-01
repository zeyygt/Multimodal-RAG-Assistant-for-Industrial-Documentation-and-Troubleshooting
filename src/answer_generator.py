"""LLM-based answer generation module"""
import os
import json
import base64
from typing import List, Dict, Optional
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI not installed. Install with: pip install openai")


class AnswerGenerator:
    """Generate answers using LLM with multimodal context"""
    
    def __init__(self, api_key=None, model="gpt-4o"):
        """
        Initialize answer generator
        
        Args:
            api_key (str): OpenAI API key (or set OPENAI_API_KEY env var)
            model (str): Model to use (gpt-4o for vision support)
        """
        self.enabled = OPENAI_AVAILABLE
        
        if not self.enabled:
            return
        
        # Get API key
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        
        if not self.api_key:
            print("⚠️ OPENAI_API_KEY not set. Answer generation disabled.")
            self.enabled = False
            return
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        print(f"✅ Answer Generator initialized ({self.model})")
    
    def encode_image(self, image_path: str) -> Optional[str]:
        """Encode image to base64"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"⚠️ Failed to encode image {image_path}: {e}")
            return None
    
    def generate_answer(self, query: str, chunks: List[dict], chunk_ids: List[int]) -> Dict:
        """
        Generate answer using LLM with chunks and images
        
        Args:
            query (str): User query
            chunks (list): All chunks
            chunk_ids (list): Relevant chunk IDs
            
        Returns:
            dict: {
                "answer": str,
                "referenced_images": [{"path": str, "description": str}],
                "source_chunks": [chunk_id, ...]
            }
        """
        if not self.enabled:
            return {
                "answer": "Answer generation disabled. Install OpenAI and set API key.",
                "referenced_images": [],
                "source_chunks": chunk_ids
            }
        
        # Prepare context from chunks
        context_parts = []
        all_images = []
        
        for idx, cid in enumerate(chunk_ids):
            chunk = chunks[cid]
            
            # Add text context
            section = chunk.get("section_heading", "Unknown Section")
            page = chunk.get("page_number", "?")
            text = chunk.get("text", "").strip()
            
            context_parts.append(f"[Source {idx+1}] {section} (Page {page})")
            context_parts.append(text)
            
            # Collect images
            for img in chunk.get("images", []):
                img_path = img.get("path")
                if img_path and Path(img_path).exists():
                    all_images.append({
                        "path": img_path,
                        "linked_text": img.get("linked_text", ""),
                        "ocr_text": img.get("ocr_text", ""),
                        "source_chunk": idx + 1
                    })
            
            context_parts.append("")  # Empty line between chunks
        
        context_text = "\n".join(context_parts)
        
        # Build messages for GPT-4o
        messages = [
            {
                "role": "system",
                "content": """You are a technical documentation assistant. Answer questions ONLY using the provided document context below.

**CRITICAL RULES:**
1. Answer questions using ONLY the information in the provided context
2. If the context contains the answer: provide a detailed, well-formatted response
3. If the context does NOT contain the answer: say "I don't have information about this in the provided documents."
4. DO NOT use external knowledge, training data, or assumptions
5. **WHEN READING TABLES:** Pay extreme attention to matching row/column headers with the specific item mentioned in the question

**TABLE READING RULES (CRITICAL):**
- Tables are marked with [TABLE] and [/TABLE] tags
- Tables use pipe (|) to separate columns
- **HEADER ROW**: The first non-empty row after [TABLE] contains column headers
- **MATCHING STRATEGY**:
  1. Read the header row carefully to identify all column names
  2. Match the EXACT term from the question to the correct column header
  3. Then read down that column to find the value for the requested row
- **COMMON MISTAKES TO AVOID**:
  - Don't assume column order - always read headers first
  - Don't confuse similar column names (e.g., "CPU" vs "CPU 40-pin front connector")
  - If question asks about "X", find the column header that contains "X" exactly
  - Some columns may have multi-line headers - read the full header
- **EXAMPLE WORKFLOW**:
  - Question: "What is the value for stranded wires on the CPU 40-pin front connector?"
  - Step 1: Find header row, locate column with "40-pin front connector" (NOT just "CPU")
  - Step 2: Find row with "stranded wires"
  - Step 3: Read the intersection of that column and row
- **VERIFICATION**: After reading a value, double-check you're in the correct column by re-reading the header

**HOW TO KNOW IF YOU SHOULD ANSWER:**
✅ Answer if: The context directly addresses the question with specific information
❌ Don't answer if: The question is about topics completely unrelated to the documentation (e.g., cooking, fashion, geography, general knowledge)

**FORMATTING (when answering from context):**
1. Use numbered lists (1., 2., 3.) for sequential steps/procedures
2. Use bullet points (-) for features or non-sequential items  
3. Use **bold** for important terms and key actions
4. Use > blockquotes for warnings or important notes
5. Keep answers clear and structured
6. For table values: Quote the exact specification (e.g., "For CPU 40-pin front connector: 0.4 Nm to 0.7 Nm")

**IMAGE USAGE:**
- Only mention images if they directly help answer the question
- Say "See the related images below" when relevant
- Don't mention images for simple text-only answers
"""
            },
            {
                "role": "user",
                "content": self._build_multimodal_content(query, context_text, all_images)
            }
        ]
        
        try:
            # Call GPT-4o
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=1000
            )
            
            answer_text = response.choices[0].message.content.strip()
            
            # Extract referenced images from answer
            referenced_images = self._extract_referenced_images(answer_text, all_images)
            
            result = {
                "answer": answer_text,
                "referenced_images": referenced_images,
                "source_chunks": chunk_ids,
                "total_chunks": len(chunk_ids),
                "total_images": len(all_images)
            }
            
            print(f"🤖 Generated answer from {len(chunk_ids)} chunks, {len(all_images)} images")
            return result
            
        except Exception as e:
            print(f"⚠️ Answer generation failed: {e}")
            return {
                "answer": f"Error generating answer: {str(e)}",
                "referenced_images": [],
                "source_chunks": chunk_ids
            }
    
    def _build_multimodal_content(self, query: str, context_text: str, images: List[dict]):
        """Build multimodal content with text and images"""
        content = [
            {
                "type": "text",
                "text": f"""USER QUESTION:
{query}

DOCUMENT CONTEXT:
{context_text}

"""
            }
        ]
        
        # Add images
        if images:
            content.append({
                "type": "text",
                "text": f"\nRELATED IMAGES ({len(images)} total):\n"
            })
            
            for idx, img in enumerate(images[:10]):  # Limit to 10 images (cost control)
                encoded = self.encode_image(img["path"])
                if encoded:
                    content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{encoded}",
                            "detail": "low"  # Use "high" for better quality but higher cost
                        }
                    })
                    
                    # Add image metadata
                    metadata = f"\nImage {idx+1} (from Source {img['source_chunk']})"
                    if img.get("linked_text"):
                        metadata += f": {img['linked_text']}"
                    if img.get("ocr_text"):
                        metadata += f"\nOCR: {img['ocr_text'][:100]}"
                    
                    content.append({
                        "type": "text",
                        "text": metadata + "\n"
                    })
        
        content.append({
            "type": "text",
            "text": "\nBased on the above context and images, please answer the user's question."
        })
        
        return content
    
    def _extract_referenced_images(self, answer_text: str, all_images: List[dict]) -> List[dict]:
        """Extract images that were referenced in the answer"""
        import re
        
        referenced = []
        
        # Check if answer explicitly mentions images
        image_keywords = [
            'image', 'diagram', 'figure', 'illustration', 'visual', 
            'shown below', 'see below', 'related image', 'picture',
            'shown in', 'displayed', 'depicted'
        ]
        
        answer_lower = answer_text.lower()
        mentions_images = any(keyword in answer_lower for keyword in image_keywords)
        
        # If answer doesn't mention images at all, return empty list
        if not mentions_images:
            print("💬 Answer doesn't reference images - skipping image display")
            return []
        
        # If answer mentions images, return relevant ones (max 4)
        print(f"🖼️ Answer references images - including {min(len(all_images), 4)} relevant image(s)")
        
        referenced = [
            {
                "path": img["path"],
                "description": img.get("linked_text", "")[:100] if img.get("linked_text") else ""
            }
            for img in all_images[:4]  # Limit to 4 images max
        ]
        
        return referenced


# Singleton instance
_generator = None

def get_generator():
    """Get or create generator instance"""
    global _generator
    if _generator is None:
        _generator = AnswerGenerator()
    return _generator
