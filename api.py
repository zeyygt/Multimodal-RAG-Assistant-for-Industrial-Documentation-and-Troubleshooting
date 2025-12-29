import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import json

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config import OUTPUT_DIR, IMG_DIR
from search import RAGSearchEngine
from answer_generator import AnswerGenerator

app = FastAPI(title="RAG Assistant API")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
search_engine = None
answer_gen = None

@app.on_event("startup")
async def startup_event():
    global search_engine, answer_gen
    print("Loading FAISS index...")
    try:
        search_engine = RAGSearchEngine()
        search_engine.load_index()
        search_engine.load_chunks()
        print(f"✓ Search engine ready with {search_engine.index.ntotal} vectors")
        
        answer_gen = AnswerGenerator()
        print("✓ Answer generator ready")
    except Exception as e:
        print(f"⚠ Warning: Could not load index: {e}")
        print("Run src/main.py first to create the index.")

class ChatRequest(BaseModel):
    message: str
    top_k: Optional[int] = 10

class ImageInfo(BaseModel):
    path: str
    caption: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    images: List[ImageInfo]
    sources_count: int
    chunks_used: int

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message and return answer with images"""
    if search_engine is None:
        raise HTTPException(status_code=503, detail="Index not loaded. Run src/main.py first.")
    
    try:
        # Search for relevant chunks (without expensive query expansion)
        chunk_ids = search_engine.get_answer_chunks(
            query=request.message,
            k=request.top_k,
            use_multi_query=False,    # Disabled - saves cost, no quality loss
            use_expansion=False,       # Disabled - prevents false positives
            min_similarity=0.5         # Higher threshold for better precision
        )
        
        if not chunk_ids:
            return ChatResponse(
                answer="I couldn't find any relevant information in the documents to answer your question. Please ask questions related to the technical documentation.",
                images=[],
                sources_count=0,
                chunks_used=0
            )
        
        # Get chunks from IDs
        chunks = [search_engine.chunks[idx] for idx in chunk_ids]
        
        # Generate answer with images
        answer_data = answer_gen.generate_answer(
            query=request.message,
            chunks=search_engine.chunks,
            chunk_ids=chunk_ids
        )
        
        # Convert image paths to frontend-accessible URLs
        images = []
        for img in answer_data.get('referenced_images', []):
            # Extract filename from path
            img_path = img.get('path', '')
            img_filename = os.path.basename(img_path)
            images.append(ImageInfo(
                path=f"/api/image/{img_filename}",
                caption=img.get('description', '')
            ))
        
        return ChatResponse(
            answer=answer_data['answer'],
            images=images,
            sources_count=len(chunk_ids),
            chunks_used=len(chunk_ids)
        )
        
    except Exception as e:
        print(f"Error processing chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/image/{filename}")
async def get_image(filename: str):
    """Serve an image file"""
    image_path = os.path.join(IMG_DIR, filename)
    
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(image_path)

@app.get("/api/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "index_loaded": search_engine is not None,
        "vectors": search_engine.index.ntotal if search_engine and search_engine.index else 0
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
