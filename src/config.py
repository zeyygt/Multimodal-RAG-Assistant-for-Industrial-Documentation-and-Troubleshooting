"""Configuration file for RAG project"""
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
IMG_DIR = OUTPUT_DIR / "images"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
IMG_DIR.mkdir(parents=True, exist_ok=True)

# Model settings (CPU-optimized)
USE_GPU = False  # Set to False for CPU-only execution
DEVICE = "cpu"

# OCR settings
USE_EASYOCR = False  # EasyOCR is slower on CPU, set to True if you want to use it
TESSERACT_AVAILABLE = True  # Will be checked at runtime

# Embedding models
TEXT_MODEL = "BAAI/bge-large-en-v1.5"  # Can use "all-MiniLM-L6-v2" for faster CPU inference
CLIP_MODEL = "clip-ViT-B-32"

# Processing settings
TEXT_MODEL_MAX_SEQ_LENGTH = 512
BATCH_SIZE = 8  # Reduced for CPU
IMAGE_QUALITY = 92
DPI = 300

# FAISS settings
FAISS_INDEX_TYPE = "flat"  # Can be "flat" or "hnsw"

# Semantic linking threshold
SIMILARITY_THRESHOLD = 0.12

# LLM Reranking settings
USE_LLM_RERANKING = True  # Enable LLM-based reranking
OPENAI_API_KEY = None  # Set via environment variable OPENAI_API_KEY
LLM_MODEL = "gpt-4o-mini"  # Most cost-effective: gpt-41-mini, gpt-3.5-turbo
MAX_CHUNKS_TO_RERANK = 10  # Don't rerank too many (costs money)
