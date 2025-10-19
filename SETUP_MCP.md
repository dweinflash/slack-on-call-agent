# Multi-Tool Setup: Incident Response + Code Analysis

This guide explains how to set up and use the bot's dual-mode functionality.

## Overview

The bot now supports two specialized modes:

1. **Incident Response** (`/incident`) - Uses RAG knowledge base for operational troubleshooting
2. **Code Analysis** (`/code`) - Uses MCP GitHub tools for codebase exploration

## Prerequisites

### 1. GitHub Personal Access Token

For the `/code` command to work, you need a GitHub Personal Access Token (PAT):

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a descriptive name (e.g., "Slack Bot Code Analysis")
4. Select scopes:
   - `repo` (Full control of private repositories) - if you want to analyze private repos
   - `public_repo` (Access public repositories) - if only analyzing public repos
5. Click "Generate token" and copy it

### 2. Environment Variables

Add your GitHub token to your environment:

```bash
export GITHUB_TOKEN=ghp_your_token_here
```

For permanent setup, add this to your `~/.bashrc`, `~/.zshrc`, or `.env` file.

### 3. Install GitHub MCP Server

The server will be automatically installed via npx when the bot starts, but ensure you have Node.js and npm installed:

```bash
node --version  # Should be v16 or higher
npm --version
```

## Commands

### `/incident` - Incident Response

Use this command for operational issues, alerts, and troubleshooting:

**Examples:**
```
/incident kafka backlog is growing
/incident lvds inbound message ratio underperforming
/incident akka node down in springfield
```

**What it does:**
- Searches the knowledge base (RAG) for relevant runbooks
- Provides detailed resolution steps from documentation
- Shows citations to knowledge base articles used
- Formatted with `:books: Knowledge Base Resolution` header

### `/code` - Code Analysis

Use this command for codebase questions, system design, and config variables:

**Examples:**
```
/code explain the authentication flow
/code what config variables control the kafka connection
/code show me how the RAG system works
/code where is error handling implemented
```

**What it does:**
- Uses GitHub MCP tools to search and read your repository
- Analyzes code structure, architecture, and configurations
- Provides file references with paths and line numbers
- Formatted with `:computer: Code Analysis` header

### `/ask-bolty` - General Questions

The original command still works for general-purpose queries:

```
/ask-bolty what's the weather like today
```

## Configuration

### Specifying Your Repository

By default, the GitHub MCP server will have access to repositories based on your PAT permissions. To specify which repository the bot should analyze, you'll need to update the system prompt or create configuration:

**Option 1: Update System Prompt**

Edit `ai/ai_constants.py` and add your repository to `CODE_ANALYSIS_SYSTEM_CONTENT`:

```python
CODE_ANALYSIS_SYSTEM_CONTENT = """
...
## Target Repository

Analyze code from: owner/repository-name

When using GitHub tools, focus on this repository unless otherwise specified.
...
"""
```

**Option 2: Use Repository Context in Queries**

Users can specify the repo in their query:

```
/code in myorg/myrepo, explain the auth flow
```

### Server Configuration

The MCP servers are configured in `server_config.json`:

```json
{
  "mcpServers": {
    "filesystem": { ... },  // Local file access
    "github": {             // GitHub repository access
      "command": "npx",
      "args": ["-y", "@github/github-mcp-server"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

## Usage in Slack

### Installing Commands

After updating `manifest.json`, you need to reinstall the Slack app:

1. Go to your Slack App settings (api.slack.com/apps)
2. Navigate to "Slash Commands"
3. The new commands should appear: `/code` and `/incident`
4. If they don't, go to "Reinstall App" and reinstall to your workspace

### Testing

**Test Incident Response:**
```
/incident kafka backlog overgrowing
```

Expected response:
- Header: `:books: Knowledge Base Resolution`
- Detailed resolution steps
- Citations to knowledge base articles

**Test Code Analysis:**
```
/code explain how the anthropic provider works
```

Expected response:
- Header: `:computer: Code Analysis`
- Code explanation with file references
- Footer: "Analyzed using MCP tools"

## Troubleshooting

### GitHub MCP Server Not Working

1. **Check GitHub Token:**
   ```bash
   echo $GITHUB_TOKEN
   ```
   Should output your token (starting with `ghp_`)

2. **Check Node.js:**
   ```bash
   npx -y @github/github-mcp-server --help
   ```
   Should show help output

3. **Check Logs:**
   Look for MCP initialization messages in your app logs:
   ```
   INFO - Connected to github with tools: [...]
   ```

### Commands Not Appearing in Slack

1. Update your manifest in Slack App settings
2. Reinstall the app to your workspace
3. Wait a few minutes for propagation
4. Type `/` in Slack and search for "code" or "incident"

### RAG Not Working for `/incident`

1. Verify knowledge base articles exist in `data/docs/`
2. Check RAG initialization logs on startup
3. Ensure `OPENAI_API_KEY` is set (required for embeddings)

## Architecture

```
User Query
    │
    ├─→ /incident → INCIDENT_RESPONSE_SYSTEM_CONTENT
    │                   │
    │                   └─→ Anthropic Provider
    │                           ├─→ RAG Retrieval (Knowledge Base)
    │                           └─→ Response with Citations
    │
    ├─→ /code → CODE_ANALYSIS_SYSTEM_CONTENT
    │              │
    │              └─→ Anthropic Provider
    │                      ├─→ MCP Tools (GitHub)
    │                      └─→ Response with File References
    │
    └─→ /ask-bolty → DEFAULT_SYSTEM_CONTENT
                        │
                        └─→ Anthropic Provider (General)
```

## Next Steps

1. Set up your `GITHUB_TOKEN` environment variable
2. Update the target repository in system prompts (optional)
3. Reinstall the Slack app to enable new commands
4. Test with sample queries
5. Monitor logs for any errors

For more details, see the main [CLAUDE.md](CLAUDE.md) documentation.
