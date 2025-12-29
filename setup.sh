#!/bin/bash

# Setup script for RAG project

echo "=================================="
echo "RAG Project Setup"
echo "=================================="

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo ""
echo "Installing Python packages..."
pip install -r requirements.txt

# Check if Tesseract is installed
echo ""
echo "Checking for Tesseract OCR..."
if command -v tesseract &> /dev/null; then
    tesseract_version=$(tesseract --version 2>&1 | head -n 1)
    echo "✓ $tesseract_version"
else
    echo "⚠ Tesseract OCR not found!"
    echo "  Install with: sudo apt install tesseract-ocr"
    echo "  (Optional but recommended for OCR)"
fi

# Create directories
echo ""
echo "Creating directories..."
mkdir -p data
mkdir -p output
mkdir -p output/images

echo ""
echo "=================================="
echo "✅ Setup complete!"
echo "=================================="
echo ""
echo "To activate the environment in the future:"
echo "  source venv/bin/activate"
echo ""
echo "To run the pipeline:"
echo "  python src/main.py data/your_pdf.pdf"
echo ""
echo "To use interactive search:"
echo "  python src/interactive_search.py"
echo ""
