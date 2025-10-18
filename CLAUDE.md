# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Slack AI chatbot built with Bolt for Python. It allows users to interact with multiple LLM providers (Anthropic, OpenAI, Vertex AI) through Slack mentions, DMs, slash commands, and Workflow Builder functions. Users can select their preferred API/model from the app home, and their preferences are persisted in per-user JSON files in `/data`.

## Architecture

### Entry Point and Request Routing
- `app.py` is the minimal entry point that initializes the Bolt app and registers all listeners via `listeners/register_listeners()`
- The app uses Socket Mode for development (requires `SLACK_APP_TOKEN` and `SLACK_BOT_TOKEN`)
- All incoming Slack requests are routed to listeners organized by feature type

### Listener System
Listeners are organized in `/listeners` by Slack Platform feature:
- `/listeners/events` - Slack Events API (e.g., `app_mentioned`, `app_messaged`, `app_home_opened`)
- `/listeners/commands` - Slash commands (e.g., `/ask-bolty`)
- `/listeners/actions` - Interactive components (e.g., user selects provider/model in app home)
- `/listeners/functions` - Workflow Builder functions (e.g., message summarization)

Each subdirectory has an `__init__.py` that registers its listeners with the app.

### AI Provider System
The AI provider architecture uses a plugin pattern:
1. `ai/providers/base_provider.py` defines the `BaseAPIProvider` interface with three methods: `set_model()`, `get_models()`, `generate_response()`
2. Each provider (Anthropic, OpenAI, VertexAI) implements this interface
3. `ai/providers/__init__.py` contains:
   - `get_available_providers()` - aggregates models from all providers
   - `_get_provider(provider_name)` - factory function returning the correct provider instance
   - `get_provider_response(user_id, prompt, context, system_content)` - main entry point that loads user state, selects provider, and generates response

**To add a new LLM provider:**
1. Create a new class in `ai/providers/` inheriting from `BaseAPIProvider`
2. Update `ai/providers/__init__.py` to import and include your provider in `get_available_providers()` and `_get_provider()`

### User State Management
The FileStateStore system persists user preferences:
- `state_store/user_identity.py` - defines UserIdentity class (user_id, provider, model)
- `state_store/file_state_store.py` - creates/manages JSON files in `/data/{user_id}` to store selections
- `state_store/set_user_state.py` - saves user's provider/model selection
- `state_store/get_user_state.py` - retrieves user's provider/model selection

### Conversation Context
- `listeners/listener_utils/parse_conversation.py` extracts conversation history for context
- For mentions in threads, retrieves up to 10 messages using `conversations.replies`
- For channel mentions, retrieves up to 10 messages using `conversations.history`
- Context is formatted as `"{user}: {text}"` and passed to the AI provider

### RAG (Retrieval-Augmented Generation) System
The RAG system enhances the Anthropic provider with knowledge base retrieval:
- `ai/rag/` - RAG module for document indexing and retrieval
- `ai/rag/rag_config.py` - Configuration constants (chunk size, top-k retrieval, etc.)
- `ai/rag/document_loader.py` - Loads and chunks markdown documents from `data/docs/`
- `ai/rag/vector_store.py` - Manages ChromaDB vector database and embeddings
- `ai/rag/__init__.py` - Public API: `initialize_rag()` and `retrieve_context()`

**How RAG works:**
1. On app startup (`app.py`), `initialize_rag()` loads markdown files from `data/docs/`
2. Documents are split into 1000-character chunks with 200-character overlap
3. OpenAI embeddings (text-embedding-3-small) are generated and stored in ChromaDB
4. When Anthropic provider receives a query, it retrieves the top 3 most relevant chunks
5. Retrieved context is injected into the system prompt before generating a response

**RAG is only active for the Anthropic provider.** OpenAI and Vertex AI providers work as before.

## Development Commands

### Setup
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set required environment variables
export SLACK_BOT_TOKEN=<your-bot-token>
export SLACK_APP_TOKEN=<your-app-token>

# Set at least one AI provider API key
export ANTHROPIC_API_KEY=<your-api-key>
export OPENAI_API_KEY=<your-api-key>  # Also required for RAG embeddings
export VERTEX_AI_PROJECT_ID=<your-project-id>
export VERTEX_AI_LOCATION=<location>

# Note: OPENAI_API_KEY is required even if you're only using Anthropic,
# because the RAG system uses OpenAI embeddings for document indexing
```

### Running the App
```bash
python3 app.py
```

### Linting and Formatting
```bash
# Run linting
ruff check .

# Run formatting
ruff format .
```

### Testing
```bash
# Run tests (pytest configured in pyproject.toml)
pytest

# Test output logs to logs/pytest.log
```

## Key Files
- `manifest.json` - Slack app configuration (scopes, events, commands, functions)
- `app_oauth.py` - OAuth implementation for multi-workspace distribution (requires ngrok)
- `ai/ai_constants.py` - Constants used throughout the AI module (e.g., DEFAULT_SYSTEM_CONTENT)
- `listeners/listener_utils/listener_constants.py` - Shared constants for listeners (e.g., DEFAULT_LOADING_TEXT)
