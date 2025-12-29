"""Main pipeline script - runs the complete RAG pipeline"""
import sys
from pathlib import Path

# Import all pipeline modules
from pdf_parser import parse_pdf
from text_enrichment import enrich_layout
from semantic_linking import create_semantic_links
from chunking import create_chunks
from embeddings import (
    generate_text_embeddings,
    generate_image_embeddings,
    generate_hybrid_embeddings
)
from search import RAGSearchEngine


def run_pipeline(pdf_path):
    """
    Run the complete RAG pipeline
    
    Args:
        pdf_path (str): Path to PDF file
    """
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        print(f"❌ Error: PDF file not found: {pdf_path}")
        sys.exit(1)
    
    print("=" * 60)
    print("RAG PIPELINE - Processing PDF")
    print("=" * 60)
    
    # Step 1: Parse PDF
    print("\n📄 Step 1/7: Parsing PDF...")
    parse_pdf(pdf_path)
    
    # Step 2: Enrich text
    print("\n📝 Step 2/7: Enriching text blocks...")
    enrich_layout()
    
    # Step 3: Semantic linking
    print("\n🔗 Step 3/7: Creating semantic links...")
    create_semantic_links()
    
    # Step 4: Chunking
    print("\n📦 Step 4/7: Creating chunks...")
    create_chunks()
    
    # Step 5: Generate text embeddings
    print("\n🔤 Step 5/7: Generating text embeddings...")
    generate_text_embeddings()
    
    # Step 6: Generate image embeddings
    print("\n🖼️ Step 6/7: Generating image embeddings...")
    generate_image_embeddings()
    
    # Step 7: Generate hybrid embeddings
    print("\n🔄 Step 7/7: Generating hybrid embeddings...")
    generate_hybrid_embeddings()
    
    # Build FAISS index
    print("\n🔍 Building FAISS index...")
    engine = RAGSearchEngine()
    engine.build_index()
    
    print("\n" + "=" * 60)
    print("✅ Pipeline completed successfully!")
    print("=" * 60)
    print("\nYou can now search using:")
    print("  python src/search.py")
    print("\nOr use the interactive search:")
    print("  python src/interactive_search.py")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <pdf_file_path>")
        print("Example: python main.py data/document.pdf")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    run_pipeline(pdf_file)
