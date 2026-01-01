# RAG Assistant - Multimodal Document Search & Q&A

A full-stack Retrieval-Augmented Generation (RAG) system with multimodal support (text + images). Features LLM-powered reranking and answer generation with a modern React frontend.

## 🌟 Features

- **PDF Processing**: Extract text, images, and layout information from PDFs
- **OCR Support**: Tesseract and EasyOCR for image text extraction
- **Semantic Search**: FAISS vector search with text and image embeddings
- **Relevance Filtering**: Similarity threshold (0.4) rejects irrelevant questions
- **Cross-Encoder Reranking**: Fast local reranking model (no API calls needed)
- **Multimodal Answers**: GPT-4o with vision generates answers with relevant images
- **Hallucination Prevention**: Strict prompts ensure answers only use provided context
- **Modern Web UI**: React frontend with solid purple theme and robot avatar
- **Cost Optimized**: Local reranking + query expansion disabled (~$0.008/query)
- **CPU-Optimized**: No GPU required

## 📁 Project Structure

```
rag_project/
├── src/                          # Python backend
│   ├── config.py                 # Configuration
│   ├── pdf_parser.py             # PDF extraction
│   ├── ocr_utils.py              # OCR integration
│   ├── text_enrichment.py        # Text structure detection
│   ├── semantic_linking.py       # Image-text linking
│   ├── chunking.py               # Semantic chunking
│   ├── embeddings.py             # Embedding generation
│   ├── search.py                 # FAISS search with relevance filtering
│   ├── llm_reranker.py           # Cross-encoder reranking (local model)
│   ├── answer_generator.py       # Answer generation with hallucination prevention
│   ├── query_expander.py         # Query expansion (disabled for cost optimization)
│   ├── interactive_search.py     # CLI interface
│   └── main.py                   # Pipeline runner
├── web/                          # React frontend
│   ├── src/
│   │   ├── App.js               # Main app
│   │   ├── components/
│   │   │   ├── Header.js        # Header component
│   │   │   ├── ChatMessage.js   # Message display
│   │   │   ├── ChatInput.js     # Input component
│   │   │   └── RobotIcon.js     # Custom robot avatar
│   │   └── index.css            # Tailwind styles
│   ├── package.json
│   └── tailwind.config.js
├── api.py                        # FastAPI server
├── data/                         # Input PDFs
├── output/                       # Processed data
│   ├── chunks.json
│   ├── embeddings.npy
│   ├── images/                   # Extracted images
│   └── faiss_index/
├── .env                          # API keys
└── requirements.txt
```

## 🚀 Setup Instructions

### 1. Backend Setup

#### Install Python Dependencies

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Install Tesseract OCR

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download from: https://github.com/UB-Mannheim/tesseract/wiki

#### Configure API Keys

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

Get your API key from: https://platform.openai.com/api-keys

### 2. Frontend Setup

```bash
cd web
npm install
```

## 📊 Processing Documents

### Step 1: Add Your PDFs

Place your PDF files in the `data/` directory:

```bash
mkdir -p data
cp /path/to/your/document.pdf data/
```

### Step 2: Run the Processing Pipeline

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Process all PDFs in data/ directory
python src/main.py
```

This will:
1. Extract text and images from PDFs
2. Perform OCR on images
3. Detect document structure (headings, lists, etc.)
4. Create semantic chunks
5. Generate embeddings (text + image)
6. Build FAISS index

**Output:** Processed data saved to `output/` directory.

## 🖥️ Running the Application

### Method 1: Run Both Servers Separately

**Terminal 1 - Backend API:**
```bash
# Activate virtual environment
source venv/bin/activate

# Start FastAPI server
python api.py
# Server runs on http://localhost:8000
```

**Terminal 2 - Frontend:**
```bash
cd web
npm start
# React app opens on http://localhost:3000
```

### Method 2: CLI Interface (No Web UI)

```bash
source venv/bin/activate
python src/interactive_search.py
```

Commands:
- Type your question and press Enter
- `chunks` - Show detailed chunk information
- `quit` or `exit` - Exit

## 🌐 Using the Web Interface

1. Open http://localhost:3000 in your browser
2. Type your question in the input box
3. Press Enter or click the send button
4. View the AI-generated answer with relevant images

## 🎨 UI Features

- **Solid Purple Theme**: Modern, professional design (#6D3AFF primary color)
- **Robot Avatar**: Custom cute robot icon for assistant messages
- **Rounded Message Bubbles**: Pill-shaped chat bubbles (rounded-3xl)
- **Markdown Support**: Formatted text in answers with proper syntax highlighting
- **Image Gallery**: Relevant images displayed when LLM mentions visual content
- **Source Attribution**: Pill-shaped badges showing number of sources used
- **White Text for Readability**: High contrast text on dark backgrounds
- **Minimal Header**: Clean design with status indicator dot
- **Loading Indicators**: Visual feedback during processing
- **Responsive Design**: Works on desktop and mobile

## 🔧 Configuration

Edit `src/config.py` to customize:

```python
# Model settings
TEXT_MODEL = "BAAI/bge-large-en-v1.5"  # Text embedding model
IMAGE_MODEL = "openai/clip-vit-base-patch32"  # Image model
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"  # Cross-encoder reranker
ANSWER_MODEL = "gpt-4o"  # Answer generation model (with vision)

# Search settings
DEFAULT_TOP_K = 10  # Number of results to retrieve
MAX_RERANK = 5  # Number of chunks for reranking
MIN_SIMILARITY = 0.4  # Minimum similarity threshold for relevance filtering

# Processing settings
CHUNK_SIZE = 1000  # Maximum chunk size in characters
USE_GPU = False  # Set to True if GPU available
DEVICE = "cpu"  # "cuda" for GPU
```

## 📝 API Endpoints

**POST /api/chat**
```json
{
  "message": "How do I insert the card?",
  "top_k": 10
}
```

Response:
```json
{
  "answer": "To insert the card...",
  "images": [
    {"path": "/api/image/page_1_img_0.png", "caption": "Card insertion"}
  ],
  "sources_count": 5,
  "chunks_used": 5
}
```

**Note:** If the question is irrelevant (similarity < 0.4), returns:
```json
{
  "answer": "I can only answer questions related to the documents...",
  "images": [],
  "sources_count": 0,
  "chunks_used": 0
}
```

**GET /api/image/{filename}**
- Serves extracted images

**GET /api/health**
- Health check and index status

## 🐛 Troubleshooting

### "Index not loaded" Error
Run `python src/main.py` first to process documents and create the index.

### CORS Errors
Make sure FastAPI is running on port 8000 and React on port 3000.

### OCR Issues
- Install Tesseract: See setup instructions above
- Check Tesseract path in system PATH
- Test: `tesseract --version`

### Out of Memory
- Reduce `CHUNK_SIZE` in `config.py`
- Process fewer PDFs at once
- Disable EasyOCR (uses only Tesseract)

### Poor Answer Quality
- Increase `MAX_RERANK` in `config.py` for better context
- Adjust reranking prompt in `src/llm_reranker.py`
- Try different `TOP_K` values
- Lower `MIN_SIMILARITY` threshold (e.g., 0.3) for more lenient filtering

### Answering Irrelevant Questions
- Increase `MIN_SIMILARITY` threshold (e.g., 0.5) for stricter filtering
- Check hallucination prevention prompts in `src/answer_generator.py`

### High API Costs
- Query expansion is already disabled for cost optimization
- Consider using GPT-4o-mini for answers instead of GPT-4o (90% cost reduction)
- Adjust `MAX_RERANK` to use fewer chunks

## 📦 Dependencies

**Backend:**
- PyMuPDF - PDF parsing
- Transformers - Embedding models
- FAISS-CPU - Vector search
- OpenAI - LLM API
- FastAPI - Web API
- Tesseract/EasyOCR - OCR

**Frontend:**
- React 18.2
- Tailwind CSS 3.4
- axios - HTTP client
- react-markdown - Markdown rendering

## 🎯 Example Queries

- "How do I reset the device?"
- "What are the safety precautions?"
- "Show me the installation steps"
- "What tools do I need?"
- "Explain the maintenance procedure"

## 📄 License

This project is for educational purposes.

## 🤝 Contributing

Feel free to open issues or submit pull requests!

## ⚡ Performance Tips

1. **First Run**: Model downloads ~2.5GB (embeddings + reranker, cached for future use)
2. **CPU Processing**: Initial indexing takes 2-5 minutes per 100 pages
3. **Search Speed**: <1 second per query with local reranking
4. **Memory Usage**: ~4GB RAM for typical documents
5. **Batch Processing**: Process multiple PDFs together for efficiency

## 💰 Cost Optimization

The system is optimized for low API costs:

- **Local Reranking**: Cross-encoder model runs locally (saves 100% of reranking costs)
- **Query Expansion**: Disabled (saves 40% on API calls)
- **Multi-Query Retrieval**: Disabled (saves additional 20%)
- **Current Cost**: ~$0.008 per query with GPT-4o (33% cheaper than LLM reranking)
- **Alternative**: Use GPT-4o-mini for answers → ~$0.001 per query (90% savings)
- **Relevance Filtering**: Prevents unnecessary LLM calls for irrelevant questions

**To Re-enable Advanced Features** (if cost is not a concern):
```python
# In api.py, change:
use_expansion=True,      # Enable query expansion
use_multi_query=True,    # Enable multi-query retrieval
min_similarity=0.3       # Lower threshold for more results
```

## 🛡️ Quality Assurance

**Hallucination Prevention:**
- Strict prompts: "ONLY use information from provided context"
- Explicit refusal instructions for unanswerable questions
- Similarity threshold filters out irrelevant queries

**Relevance Filtering:**
- Minimum similarity: 0.4 (adjustable)
- Questions below threshold receive polite refusal
- Prevents hallucinated answers to off-topic questions

## 🔐 Security Notes

- Never commit `.env` file
- Keep API keys secure
- Use environment variables in production
- Consider rate limiting for public deployments

---

**Built with ❤️ using Python, React, and OpenAI**
