"""
Test script to verify RAG integration with Anthropic provider
"""
import logging
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

# Initialize RAG
print("=== Initializing RAG System ===")
from ai.rag import initialize_rag
initialize_rag()

# Set up a test user
from state_store.set_user_state import set_user_state
from state_store.get_user_state import get_user_state

test_user_id = "TEST_USER"
print(f"\n=== Setting up test user: {test_user_id} ===")
set_user_state(test_user_id, "Anthropic", "claude-3-5-sonnet-20240620")
provider, model = get_user_state(test_user_id, False)
print(f"User configured: Provider={provider}, Model={model}")

# Test the full flow
print("\n=== Testing Query: 'How do I fix LVDS backlog?' ===")
from ai.providers import get_provider_response

try:
    response = get_provider_response(
        user_id=test_user_id,
        prompt="How do I fix LVDS backlog?",
        context=[],  # No conversation context
    )

    print("\n=== Response ===")
    print(response)

    # Check if response mentions knowledge base content
    if "LVDS" in response and ("backlog" in response.lower() or "Pulsar" in response or "Kafka" in response):
        print("\n✅ SUCCESS: Response appears to include RAG context")
    else:
        print("\n❌ WARNING: Response may not include RAG context")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
