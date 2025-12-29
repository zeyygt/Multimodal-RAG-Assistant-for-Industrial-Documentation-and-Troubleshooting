#!/bin/bash

# RAG Assistant Startup Script
# This script helps you start both the backend and frontend servers

echo "🚀 RAG Assistant - Starting Services"
echo "===================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Please run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if node_modules exists
if [ ! -d "web/node_modules" ]; then
    echo "❌ Frontend dependencies not found!"
    echo "   Please run: cd web && npm install"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "   Please create .env file with your OPENAI_API_KEY"
    echo ""
fi

# Check if index exists
if [ ! -d "output/faiss_index" ]; then
    echo "⚠️  Warning: FAISS index not found!"
    echo "   Please run: source venv/bin/activate && python src/main.py"
    echo "   to process your documents first."
    echo ""
fi

echo "Starting services..."
echo ""

# Start FastAPI backend
echo "📡 Starting Backend API (port 8000)..."
source venv/bin/activate
python3 api.py &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 5

# Start React frontend
echo "🌐 Starting Frontend (port 3000)..."
cd web
npm start &
FRONTEND_PID=$!

echo ""
echo "✅ Services started!"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for Ctrl+C
trap "echo ''; echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait
