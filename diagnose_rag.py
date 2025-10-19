"""
Comprehensive diagnostic script for RAG system.
Run this to verify all components are working.
"""

import os
import json
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check environment variables."""
    print("\n" + "="*80)
    print("ENVIRONMENT CHECKS")
    print("="*80 + "\n")

    required_vars = {
        "OPENAI_API_KEY": "Required for RAG embeddings",
        "ANTHROPIC_API_KEY": "Required for Anthropic provider with RAG",
        "SLACK_BOT_TOKEN": "Required for Slack integration",
        "SLACK_APP_TOKEN": "Required for Socket Mode"
    }

    all_set = True
    for var, description in required_vars.items():
        value = os.environ.get(var)
        if value:
            # Show first 10 and last 4 characters for security
            masked = f"{value[:10]}...{value[-4:]}" if len(value) > 14 else "***"
            print(f"  ✓ {var}: {masked}")
        else:
            print(f"  ✗ {var}: NOT SET - {description}")
            all_set = False

    return all_set

def check_documents():
    """Check knowledge base documents."""
    print("\n" + "="*80)
    print("KNOWLEDGE BASE DOCUMENTS")
    print("="*80 + "\n")

    docs_dir = "data/docs"
    if not os.path.exists(docs_dir):
        print(f"  ✗ Directory '{docs_dir}' not found!")
        return False

    files = [f for f in os.listdir(docs_dir) if f.endswith('.md')]
    print(f"  Found {len(files)} markdown documents:\n")

    kafka_related = []
    for f in sorted(files):
        size = os.path.getsize(os.path.join(docs_dir, f))
        print(f"    - {f} ({size} bytes)")
        if 'kafka' in f.lower():
            kafka_related.append(f)

    print(f"\n  Kafka-related documents: {len(kafka_related)}")
    for f in kafka_related:
        print(f"    - {f}")

    return len(files) > 0

def check_user_states():
    """Check user state files."""
    print("\n" + "="*80)
    print("USER STATE FILES")
    print("="*80 + "\n")

    data_dir = "data"
    if not os.path.exists(data_dir):
        print(f"  ✗ Directory '{data_dir}' not found!")
        return False

    user_files = [f for f in os.listdir(data_dir) if not f.startswith('.') and not os.path.isdir(os.path.join(data_dir, f)) and f != 'docs']

    print(f"  Found {len(user_files)} user state files:\n")

    anthropic_users = []
    for f in user_files:
        try:
            with open(os.path.join(data_dir, f), 'r') as file:
                data = json.load(file)
                provider = data.get('provider', 'unknown')
                model = data.get('model', 'unknown')
                print(f"    - {f}:")
                print(f"        Provider: {provider}")
                print(f"        Model: {model}")

                if provider.lower() == 'anthropic':
                    anthropic_users.append(f)
        except Exception as e:
            print(f"    - {f}: Error reading ({e})")

    print(f"\n  Users with Anthropic provider: {len(anthropic_users)}")
    if anthropic_users:
        print("  (These users can use RAG-enabled /incident command)")
    else:
        print("  ⚠ WARNING: No users configured with Anthropic provider!")
        print("  Only Anthropic provider supports RAG. Users with OpenAI/VertexAI won't get RAG context.")

    return True

def check_chroma_db():
    """Check ChromaDB persistence."""
    print("\n" + "="*80)
    print("CHROMADB VECTOR STORE")
    print("="*80 + "\n")

    chroma_dir = "data/chroma_db"
    if not os.path.exists(chroma_dir):
        print(f"  ⚠ Directory '{chroma_dir}' not found (will be created on first run)")
        return True

    # Check for ChromaDB files
    files = os.listdir(chroma_dir)
    if not files:
        print(f"  ⚠ ChromaDB directory is empty (will be populated on initialization)")
    else:
        print(f"  ✓ ChromaDB directory contains {len(files)} files")
        print(f"    Database appears to be initialized")

    return True

def check_rag_imports():
    """Check if RAG modules can be imported."""
    print("\n" + "="*80)
    print("RAG MODULE IMPORTS")
    print("="*80 + "\n")

    try:
        print("  Testing imports...")
        from ai.rag import initialize_rag, retrieve_context
        print("    ✓ ai.rag.initialize_rag")
        print("    ✓ ai.rag.retrieve_context")

        from ai.rag.vector_store import get_vector_store
        print("    ✓ ai.rag.vector_store.get_vector_store")

        from ai.rag.document_loader import load_and_chunk_documents
        print("    ✓ ai.rag.document_loader.load_and_chunk_documents")

        from ai.providers import get_provider_response
        print("    ✓ ai.providers.get_provider_response")

        print("\n  ✓ All RAG modules imported successfully")
        return True
    except Exception as e:
        print(f"\n  ✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all diagnostic checks."""
    print("\n" + "#"*80)
    print("# RAG SYSTEM DIAGNOSTICS")
    print("#"*80)

    checks = [
        ("Environment Variables", check_environment),
        ("Knowledge Base Documents", check_documents),
        ("User State Files", check_user_states),
        ("ChromaDB Vector Store", check_chroma_db),
        ("RAG Module Imports", check_rag_imports),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n  ✗ Error during check: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80 + "\n")

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")

    all_passed = all(result for _, result in results)

    print("\n" + "="*80)
    if all_passed:
        print("ALL CHECKS PASSED")
        print("\nThe RAG system should be working correctly.")
        print("\nNext steps:")
        print("  1. Start the app: python3 app.py")
        print("  2. Use /incident command in Slack with an Anthropic-configured user")
        print("  3. Check logs for RAG retrieval messages")
    else:
        print("SOME CHECKS FAILED")
        print("\nPlease review the issues above before using the RAG system.")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
