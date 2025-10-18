# RAG System Testing Guide

## Quick Test

To verify the RAG system is working:

```bash
source .venv/bin/activate
python3 test_rag_integration.py
```

This will:
1. Initialize the RAG system
2. Create a test user configured for Anthropic
3. Send a test query: "How do I fix LVDS backlog?"
4. Show the response and verify it includes knowledge base content

## Expected Output

You should see:
- `INFO:ai.rag:RAG system initialization complete`
- `INFO:ai.providers.anthropic:RAG context retrieved: XXXX characters`
- `INFO:ai.providers.anthropic:Enhanced prompt with RAG context`
- `✅ SUCCESS: Response appears to include RAG context`

## Troubleshooting

### Issue: "No RAG context retrieved"

**Possible Causes:**
1. **RAG not initialized**: Make sure the app has fully started (wait 10-15 seconds after startup)
2. **OPENAI_API_KEY not set**: RAG uses OpenAI embeddings, verify the env var is set
3. **No documents**: Check that `data/docs/` contains markdown files

**Solution:**
```bash
# Verify RAG initialization
grep "RAG system initialization complete" <app_logs>

# Check OpenAI API key
echo $OPENAI_API_KEY

# Check documents
ls -l data/docs/
```

### Issue: User gets generic response without knowledge base

**Possible Causes:**
1. **User not using Anthropic provider**: RAG only works for Anthropic, not OpenAI or Vertex AI
2. **User hasn't selected a provider**: New users need to configure their provider in App Home

**Solution:**
- Have the user go to the Slack App Home and select "Anthropic" as their provider
- Or use the test script which automatically configures a test user

### Issue: ChromaDB errors

**Note:** Errors like `ERROR:chromadb.telemetry.product.posthog` are **harmless** telemetry failures and don't affect functionality.

## How RAG Works

1. **On Startup**: App loads all markdown files from `data/docs/`, chunks them, generates embeddings, and stores in ChromaDB
2. **On Query** (Anthropic only):
   - User sends message to bot
   - System retrieves top 3 most relevant document chunks using semantic similarity
   - Chunks are injected into Claude's system prompt
   - Claude generates response using both knowledge base and general knowledge
3. **Other Providers**: OpenAI and Vertex AI work normally without RAG

## Monitoring RAG in Production

To see RAG in action, check logs for:
```
INFO:ai.providers.anthropic:Retrieving RAG context for prompt: ...
INFO:ai.rag.vector_store:Retrieved 3 relevant chunks for query
INFO:ai.providers.anthropic:RAG context retrieved: XXXX characters
INFO:ai.providers.anthropic:Enhanced prompt with RAG context
```

If you see:
```
WARNING:ai.providers.anthropic:No RAG context retrieved - responding without knowledge base
```

This means no relevant documents were found for the query (which is normal for non-technical questions).

## Adding New Documents

1. Add markdown files to `data/docs/`
2. Restart the app - RAG re-indexes on startup
3. Test with `python3 test_rag_integration.py`

## Configuration

Edit `ai/rag/rag_config.py` to adjust:
- `CHUNK_SIZE`: Characters per chunk (default: 1000)
- `CHUNK_OVERLAP`: Overlap between chunks (default: 200)
- `TOP_K_CHUNKS`: Number of chunks to retrieve (default: 3)
