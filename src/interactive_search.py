"""Interactive search interface for RAG system"""
from search import RAGSearchEngine
from answer_generator import get_generator


def display_answer(result: dict):
    """Display generated answer with images"""
    print("\n" + "=" * 60)
    print("🤖 GENERATED ANSWER")
    print("=" * 60)
    print(result["answer"])
    
    if result.get("referenced_images"):
        print("\n" + "-" * 60)
        print("📷 REFERENCED IMAGES:")
        for idx, img in enumerate(result["referenced_images"], 1):
            print(f"  {idx}. {img['path']}")
            print(f"     Description: {img['description']}")
    
    print("\n" + "-" * 60)
    print(f"📚 Sources: {result['total_chunks']} chunks, {result['total_images']} images")
    print("=" * 60)


def main():
    """Interactive search loop"""
    print("=" * 60)
    print("RAG INTERACTIVE SEARCH WITH ANSWER GENERATION")
    print("=" * 60)
    
    # Initialize search engine
    engine = RAGSearchEngine()
    generator = get_generator()
    
    try:
        engine.load_index()
        engine.load_chunks()
        engine.load_models()
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\nPlease run the pipeline first:")
        print("  python src/main.py <pdf_file>")
        return
    
    print("\n✅ Search engine ready!")
    print("\nTips:")
    print("  - Type your question and press Enter")
    print("  - Type 'quit' or 'exit' to stop")
    print("  - Type 'help' for more options")
    print("  - Type 'chunks' to see detailed chunks (default: answer only)")
    print("\n" + "-" * 60)
    
    show_chunks = False  # By default, show only answer
    
    while True:
        try:
            query = input("\n🔍 Query: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if query.lower() == 'help':
                print("\nAvailable commands:")
                print("  help   - Show this help message")
                print("  quit   - Exit the program")
                print("  chunks - Toggle detailed chunk display")
                print("  top5   - Search and show top 5 chunks")
                print("  top10  - Search and show top 10 chunks")
                print("\nOtherwise, just type your question!")
                continue
            
            if query.lower() == 'chunks':
                show_chunks = not show_chunks
                status = "enabled" if show_chunks else "disabled"
                print(f"✅ Detailed chunk display {status}")
                continue
            
            # Handle special commands
            k = 10  # default
            if query.lower().startswith('top'):
                try:
                    k = int(query[3:])
                    query = input("  Enter your query: ").strip()
                except:
                    pass
            
            print(f"\n🔍 Searching for: {query}")
            print("-" * 60)
            
            # Get answer chunks
            answer_ids = engine.get_answer_chunks(query, k=k)
            
            if not answer_ids:
                print("\n❌ No relevant chunks found.")
                continue
            
            print(f"\n📊 Found {len(answer_ids)} relevant chunks")
            
            # Generate answer
            if generator.enabled:
                result = generator.generate_answer(query, engine.chunks, answer_ids)
                display_answer(result)
            else:
                print("\n⚠️ Answer generation disabled. Showing chunks instead.")
                show_chunks = True
            
            # Optionally show detailed chunks
            if show_chunks:
                print("\n" + "=" * 60)
                print("DETAILED CHUNKS")
                print("=" * 60)
                for cid in answer_ids:
                    engine.pretty_print_chunk(cid)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            continue


if __name__ == "__main__":
    main()
