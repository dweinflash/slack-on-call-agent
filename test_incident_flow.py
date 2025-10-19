"""
Test script to verify the complete /incident command flow with RAG.
This simulates what happens when a user runs /incident kafka issues
"""

import logging
import sys
from ai.providers import get_provider_response
from ai.ai_constants import INCIDENT_RESPONSE_SYSTEM_CONTENT
from ai.rag import initialize_rag

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_incident_flow():
    """Test the complete incident response flow."""

    print("\n" + "="*80)
    print("INCIDENT COMMAND FLOW TEST")
    print("="*80 + "\n")

    # Step 1: Initialize RAG (simulating app startup)
    print("Step 1: Initializing RAG system...")
    print("-" * 80)
    try:
        initialize_rag()
        print("✓ RAG system initialized successfully\n")
    except Exception as e:
        print(f"✗ RAG initialization failed: {e}\n")
        return False

    # Step 2: Simulate /incident command with "kafka issues"
    print("Step 2: Simulating '/incident kafka issues' command...")
    print("-" * 80)

    test_user_id = "U09K5SDF5MF"  # User with Anthropic provider selected
    prompt = "kafka issues"

    try:
        print(f"  User ID: {test_user_id}")
        print(f"  Query: {prompt}")
        print(f"  System prompt: INCIDENT_RESPONSE_SYSTEM_CONTENT")
        print(f"  RAG enabled: True\n")

        # Call get_provider_response with RAG enabled (exactly as /incident does)
        result = get_provider_response(
            user_id=test_user_id,
            prompt=prompt,
            context=[],
            system_content=INCIDENT_RESPONSE_SYSTEM_CONTENT,
            use_rag=True
        )

        print("✓ Provider response received\n")

        # Step 3: Verify response structure
        print("Step 3: Analyzing response...")
        print("-" * 80)

        response_text = result.get("response", "")
        rag_sources = result.get("rag_sources", [])
        provider = result.get("provider", "")

        print(f"  Provider used: {provider}")
        print(f"  Response length: {len(response_text)} characters")
        print(f"  RAG sources found: {len(rag_sources)}")

        if rag_sources:
            print("\n  Source documents:")
            for source in rag_sources:
                filename = source.get("filename", "Unknown")
                url = source.get("url", "No URL")
                print(f"    - {filename}")
                print(f"      {url}")
        else:
            print("\n  ⚠ WARNING: No RAG sources found!")

        print(f"\n  Response preview (first 500 chars):")
        print("  " + "-" * 76)
        print(f"  {response_text[:500]}")
        if len(response_text) > 500:
            print(f"  ... ({len(response_text) - 500} more characters)")
        print("  " + "-" * 76)

        # Step 4: Validate results
        print("\nStep 4: Validation")
        print("-" * 80)

        success = True

        if provider.lower() != "anthropic":
            print(f"  ✗ FAIL: Expected Anthropic provider, got {provider}")
            success = False
        else:
            print(f"  ✓ PASS: Using Anthropic provider")

        if len(rag_sources) == 0:
            print(f"  ✗ FAIL: No RAG sources retrieved for 'kafka issues'")
            success = False
        else:
            print(f"  ✓ PASS: Retrieved {len(rag_sources)} RAG sources")

        if "kafka" not in response_text.lower():
            print(f"  ⚠ WARNING: Response doesn't mention 'kafka'")
        else:
            print(f"  ✓ PASS: Response mentions 'kafka'")

        print("\n" + "="*80)
        if success:
            print("TEST PASSED: RAG system working correctly for /incident")
        else:
            print("TEST FAILED: Issues found with RAG integration")
        print("="*80 + "\n")

        return success

    except Exception as e:
        print(f"✗ Error during incident flow: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_incident_flow()
    sys.exit(0 if success else 1)
