# 🚀 Quick Start Guide

## First Time Setup

### 1. Install Python Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 2. Install Frontend Dependencies

```bash
cd web
npm install
cd ..
```

### 3. Add API Key

Create a `.env` file and add your OpenAI API key:

```env
OPENAI_API_KEY=sk-your-api-key-here
```

Get API key from: https://platform.openai.com/api-keys

### 4. Process PDF Files

```bash
# Put PDFs in data/ folder
mkdir -p data
cp /path/to/your/file.pdf data/

# Run processing pipeline
source venv/bin/activate
python src/main.py
```

This step will:
- Extract text and images from PDF
- Perform OCR
- Create chunks
- Generate embeddings
- Build FAISS index

**Duration:** ~2-5 minutes for 100 pages

## Running the Application

### Automatic Start (Recommended)

```bash
./start.sh
```

This script starts both backend and frontend.

### Manual Start

**Terminal 1 - Backend:**
```bash
source venv/bin/activate
python api.py
```

**Terminal 2 - Frontend:**
```bash
cd web
npm start
```

## Open in Browser

http://localhost:3000

## Example Questions

- "How do I reset the device?"
- "What are the safety precautions?"
- "Show me the installation steps"
- "What tools do I need?"

## Troubleshooting

### "Index not loaded" error
Process documents first with `python src/main.py`.

### Port already in use
```bash
# For backend (8000)
lsof -ti:8000 | xargs kill -9

# For frontend (3000)
lsof -ti:3000 | xargs kill -9
```

### Memory error
Reduce `CHUNK_SIZE` in `config.py`.

### Slow model download
First run downloads models (~2GB). Check your internet connection.

## Folder Structure

```
rag_project/
├── data/              # Put PDFs here
├── output/            # Processed data saved here
│   ├── chunks.json
│   ├── embeddings.npy
│   ├── images/        # Extracted images
│   └── faiss_index/
├── src/               # Python backend code
├── web/               # React frontend
└── api.py             # FastAPI server
```

## Useful Commands

```bash
# Test with CLI interface (without web UI)
source venv/bin/activate
python src/interactive_search.py

# API health check
curl http://localhost:8000/api/health

# Add new PDF and reprocess
cp new_file.pdf data/
python src/main.py

# Clean logs
rm -rf output/
```

## Performance Tips

1. **First run:** May be slow due to model downloads
2. **CPU usage:** High CPU usage during processing is normal
3. **RAM:** ~4GB RAM required
4. **Query speed:** ~2 seconds (with reranking)
5. **Batch processing:** Process multiple PDFs together for efficiency

## Help

See `README.md` for detailed information.

---

**Note:** Works without GPU, but 5-10x faster with GPU.
