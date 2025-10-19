# RAG System Verification Report

**Date:** 2025-10-19
**Status:** ✅ WORKING CORRECTLY

## Summary

The RAG (Retrieval-Augmented Generation) system for the `/incident` command is **functioning correctly**. All tests pass and the system successfully retrieves relevant knowledge base articles for incident queries.

## Test Results

### 1. RAG Initialization ✅
- **Status:** PASS
- Documents loaded: 13 markdown files from `data/docs/`
- Document chunks created: 71 chunks (1000 characters each, 200 overlap)
- ChromaDB initialized successfully
- OpenAI embeddings generated

### 2. Document Retrieval ✅
- **Status:** PASS
- Query: `"kafka issues"`
  - Sources retrieved: 3 documents
  - Relevant document found: `209731_2.9.4_KAFKA_OUTBOUND_MESSAGE_BACKLOG_OVERGROWING.md`
  - Contains resolution steps: Yes ✅

### 3. End-to-End Integration ✅
- **Status:** PASS
- `/incident kafka issues` command flow tested
- Provider: Anthropic Claude 3.5 Sonnet
- RAG sources: 3 articles retrieved
- Response includes: Resolution steps from knowledge base ✅

### 4. Response Quality ✅
- **Status:** PASS
- Response length: 4,547 characters
- Includes resolution steps: Yes ✅
- Includes source citations: Yes ✅
- Formatted correctly: Yes ✅

## How RAG Works for `/incident`

1. **User runs command:** `/incident kafka issues`

2. **RAG retrieval (ai/rag/__init__.py):**
   - Query is sent to ChromaDB vector store
   - Top 3 most relevant document chunks retrieved
   - Source documents are identified and tracked

3. **Context injection (ai/providers/anthropic.py):**
   - Retrieved articles are injected into system prompt
   - Enhanced instructions guide the LLM to use KB content
   - Anthropic generates response using knowledge base

4. **Response formatting (listeners/commands/incident_command.py):**
   - Response text extracted
   - RAG sources extracted (filename + GitHub URL)
   - Formatted with citations and resolution steps

5. **Slack message posted:**
   - Query shown as quote
   - Response with "Knowledge Base Resolution" header
   - Source citations with GitHub links
   - Professional incident response formatting

## Key Components

### RAG Module (`ai/rag/`)
- `__init__.py` - Public API: `initialize_rag()`, `retrieve_context()`
- `vector_store.py` - ChromaDB management and similarity search
- `document_loader.py` - Loads and chunks markdown documents
- `rag_config.py` - Configuration constants (chunk size, top-k, etc.)

### Provider Integration (`ai/providers/`)
- `__init__.py` - `get_provider_response()` with `use_rag` parameter
- `anthropic.py` - RAG context injection and response generation
- **Note:** Only Anthropic provider supports RAG currently

### Incident Command (`listeners/commands/incident_command.py`)
- Calls `get_provider_response()` with `use_rag=True`
- Extracts RAG sources and formats response
- Posts formatted message to Slack

## Important Requirements

### 1. User Must Use Anthropic Provider ⚠️
RAG **only works with Anthropic provider**. Users must:
- Open the Slack app Home tab
- Select "Anthropic" as their provider
- Select a Claude model

**User state files are stored in:** `data/{user_id}`

### 2. Environment Variables Required
```bash
OPENAI_API_KEY=...      # Required for embeddings (even if using Anthropic)
ANTHROPIC_API_KEY=...   # Required for Anthropic provider
SLACK_BOT_TOKEN=...     # Required for Slack
SLACK_APP_TOKEN=...     # Required for Socket Mode
```

### 3. Knowledge Base Documents
Documents must be placed in: `data/docs/*.md`

Currently available:
- Kafka issues (1 document)
- Message backlog issues (5 documents)
- AKKA node issues (4 documents)
- Other LVDS/system issues (3 documents)

## Verification Commands

### Run Full Test Suite
```bash
source .venv/bin/activate
python3 test_rag.py              # Test RAG retrieval only
python3 test_incident_flow.py    # Test complete /incident flow
python3 diagnose_rag.py          # Run full diagnostics
```

### Check Logs in Production
When running the Slack app, look for these log messages:

```
INFO - Requesting incident response for user U12345 with query: 'kafka issues'
INFO - RAG is ENABLED for this request
INFO - Provider: anthropic, Model: claude-3-5-sonnet-20240620, RAG requested: True
INFO - ✓ RAG will be used (Anthropic provider)
INFO - Retrieving RAG context for prompt: kafka issues...
INFO - RAG context retrieved: 1659 characters from 3 sources
INFO - Incident response - Provider: anthropic, RAG sources: 3
INFO - RAG sources retrieved:
INFO -   1. 209731_2.9.4_KAFKA_OUTBOUND_MESSAGE_BACKLOG_OVERGROWING.md
INFO -   2. 209731_DEACTIVATED_MESSAGE_BACKLOG_OVERGROWING.md
INFO -   3. 209731_117_MESSAGE_BACKLOG_OVERGROWING.md
```

### Troubleshooting: No RAG Sources

If you see:
```
WARNING - ⚠️  NO RAG SOURCES RETRIEVED for query: 'kafka issues'
```

**Possible causes:**
1. **User not using Anthropic provider**
   - Check: `cat data/{user_id}` - should show `"provider": "anthropic"`
   - Fix: User must select Anthropic in app Home

2. **RAG not initialized**
   - Check: `ls data/chroma_db/` - should contain database files
   - Fix: Restart app to trigger `initialize_rag()` in `app.py`

3. **No relevant documents**
   - Check: `ls data/docs/*.md` - should contain markdown files
   - Fix: Add knowledge base articles to `data/docs/`

4. **Query too specific**
   - RAG uses semantic similarity search
   - Fix: Try broader queries like "kafka" instead of very specific error codes

## Next Steps for Improvement

1. **Add more knowledge base articles**
   - Place `.md` files in `data/docs/`
   - Restart app to re-index

2. **Improve chunk size/overlap**
   - Edit `ai/rag/rag_config.py`
   - Adjust `CHUNK_SIZE` and `CHUNK_OVERLAP`

3. **Increase retrieved chunks**
   - Edit `ai/rag/rag_config.py`
   - Increase `TOP_K_CHUNKS` (currently 3)

4. **Support other providers**
   - Add RAG support to OpenAI provider
   - Add RAG support to VertexAI provider

## Conclusion

✅ **The RAG system is working correctly** for the `/incident` command.

**Verified behaviors:**
- Documents are loaded and indexed on app startup
- Queries retrieve relevant articles
- Articles are injected into system prompt
- Anthropic generates comprehensive responses with resolution steps
- Sources are tracked and returned with GitHub URLs
- Responses are formatted with citations

**To use in production:**
1. Ensure user has selected Anthropic provider in app Home
2. Run `/incident <query>` in Slack
3. System will retrieve relevant articles and provide resolution steps
4. Response will include source citations with links to GitHub

If you're experiencing issues where articles are not being retrieved, please:
1. Run `python3 diagnose_rag.py` to check system status
2. Check the logs when running `/incident` command
3. Verify the user is using Anthropic provider
4. Ensure knowledge base documents exist in `data/docs/`
