"""
Test script to verify RAG system is working correctly.
This will test document loading, embedding, and retrieval.
"""

import logging
import sys
from ai.rag import initialize_rag, retrieve_context

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_rag_system():
    """Test the RAG system end-to-end."""

    print("\n" + "="*80)
    print("RAG SYSTEM TEST")
    print("="*80 + "\n")

    # Step 1: Initialize RAG
    print("Step 1: Initializing RAG system...")
    print("-" * 80)
    try:
        initialize_rag()
        print("✓ RAG system initialized successfully\n")
    except Exception as e:
        print(f"✗ RAG initialization failed: {e}\n")
        return False

    # Step 2: Test retrieval with different queries
    test_queries = [
        "kafka issues",
        "kafka backlog",
        "message backlog overgrowing",
        "LVDS kafka outbound",
        "akka node down",
    ]

    print("Step 2: Testing document retrieval...")
    print("-" * 80)

    for i, query in enumerate(test_queries, 1):
        print(f"\nTest Query {i}: '{query}'")
        print("-" * 40)

        try:
            result = retrieve_context(query)
            context = result.get("context", "")
            sources = result.get("sources", [])

            if not context:
                print(f"✗ No context retrieved for query: '{query}'")
                print(f"  Sources found: {len(sources)}")
                continue

            print(f"✓ Retrieved context ({len(context)} characters)")
            print(f"  Sources found: {len(sources)}")

            if sources:
                print("  Source documents:")
                for source in sources:
                    filename = source.get("filename", "Unknown")
                    url = source.get("url", "No URL")
                    print(f"    - {filename}")
                    print(f"      {url}")

            # Show a snippet of the retrieved context
            print(f"\n  Context preview (first 300 chars):")
            print(f"  {context[:300]}...")

        except Exception as e:
            print(f"✗ Retrieval failed for query '{query}': {e}")

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80 + "\n")

    return True

if __name__ == "__main__":
    success = test_rag_system()
    sys.exit(0 if success else 1)
