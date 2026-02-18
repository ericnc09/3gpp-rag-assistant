"""
Query the 3GPP RAG assistant from the command line.

Usage:
    python scripts/query.py "What is the gNB-CU architecture?"
    python scripts/query.py --stream --show-sources
"""
import sys
import argparse
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.retriever import DocumentRetriever
from src.core.llm import OllamaLLM, build_rag_prompt


def parse_args():
    parser = argparse.ArgumentParser(description="Query the 3GPP RAG assistant")
    parser.add_argument("question", nargs="?", help="Question to ask")
    parser.add_argument("--stream", action="store_true", help="Stream the response token by token")
    parser.add_argument("--show-sources", action="store_true", help="Print retrieved source chunks")
    parser.add_argument("--top-k", type=int, default=5, help="Number of chunks to retrieve (default: 5)")
    parser.add_argument("--model", default="llama3.2", help="Ollama model to use (default: llama3.2)")
    return parser.parse_args()


def run_query(question: str, retriever: DocumentRetriever, llm: OllamaLLM,
              stream: bool, show_sources: bool):
    print(f"\nQuestion: {question}")
    print("=" * 60)

    # Retrieve relevant chunks
    print("Retrieving relevant documents...")
    docs = retriever.retrieve(question)
    context = retriever.format_context(docs)

    if show_sources:
        print("\n--- Retrieved Sources ---")
        for i, doc in enumerate(docs, 1):
            print(f"\n[{i}] Source: {doc['source']}  (similarity: {doc['similarity']:.3f})")
            print(f"    {doc['text'][:200].strip()}...")
        print("\n" + "-" * 60)

    # Build prompt and generate answer
    prompt = build_rag_prompt(question, context)

    print("\nAnswer:")
    print("-" * 60)

    if stream:
        for token in llm.stream(prompt):
            print(token, end="", flush=True)
        print()
    else:
        answer = llm.generate(prompt)
        print(answer)

    print("=" * 60)


def interactive_mode(retriever: DocumentRetriever, llm: OllamaLLM,
                     stream: bool, show_sources: bool):
    print("\n3GPP RAG Assistant — Interactive Mode")
    print("Type your question and press Enter. Type 'quit' or 'exit' to stop.\n")

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not question:
            continue
        if question.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        try:
            run_query(question, retriever, llm, stream, show_sources)
        except Exception as e:
            print(f"Error: {e}")


def main():
    logging.basicConfig(level=logging.WARNING)  # Suppress verbose logs during query

    args = parse_args()

    # Initialize retriever
    print("Initializing retriever...")
    try:
        retriever = DocumentRetriever(top_k=args.top_k)
    except Exception as e:
        print(f"Error initializing retriever: {e}")
        print("Make sure the vector index is built: python scripts/build_index.py")
        sys.exit(1)

    # Check vector store has data
    stats = retriever.vector_store.get_stats()
    if stats["total_chunks"] == 0:
        print("Vector store is empty. Run: python scripts/build_index.py")
        sys.exit(1)

    print(f"Vector store: {stats['total_chunks']:,} chunks loaded")

    # Initialize LLM
    print(f"Connecting to Ollama ({args.model})...")
    try:
        llm = OllamaLLM(model=args.model)
    except RuntimeError as e:
        print(f"\nError: {e}")
        print("\nTo start Ollama:")
        print("  /Applications/Ollama.app/Contents/MacOS/Ollama serve &")
        print("  ollama pull llama3.2")
        sys.exit(1)

    print("Ready!\n")

    if args.question:
        run_query(args.question, retriever, llm, args.stream, args.show_sources)
    else:
        interactive_mode(retriever, llm, args.stream, args.show_sources)


if __name__ == "__main__":
    main()
