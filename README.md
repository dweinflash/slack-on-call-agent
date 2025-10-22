# Slack On-Call Support Agent

An AI-powered Slack bot designed to assist on-call teams with incident resolution and codebase analysis. The agent combines Retrieval-Augmented Generation (RAG) and Model Context Protocol (MCP) to provide intelligent, context-aware support.

## Overview

This application provides specialized support through three primary interfaces:

- **Incident Response** - Retrieves resolution steps from knowledge base using RAG
- **Code Analysis** - Explores GitHub repositories to answer system queries via MCP
- **General Assistance** - Handles ad-hoc queries through mentions, DMs, and slash commands

## Quick Start

### 1. Create Your Slack App

1. Navigate to [https://api.slack.com/apps/new](https://api.slack.com/apps/new) and select **"From an app manifest"**
2. Choose your target workspace
3. Copy the contents of [`manifest.json`](./manifest.json) into the JSON editor
4. Click **Create** → **Install to Workspace** → **Allow**

### 2. Configure Slack Tokens

1. **Bot Token**: Navigate to **OAuth & Permissions** and copy the **Bot User OAuth Token**
2. **App Token**: Navigate to **Basic Information** → **App-Level Tokens** and create a token with the `connections:write` scope

```bash
export SLACK_BOT_TOKEN=your-slack-bot-token
export SLACK_APP_TOKEN=your-slack-app-token
```

### 3. Configure Anthropic Provider

Configure Anthropic for RAG and MCP feature support.

#### Anthropic
```bash
export ANTHROPIC_API_KEY=your-anth-api-key
```

#### OpenAI (Required for RAG Embeddings)
```bash
export OPENAI_API_KEY=your-openai-api-key
```

### 4. Configure MCP for Code Analysis

To enable the `/code` command with GitHub repository access:

```bash
# Generate a GitHub Personal Access Token at:
# https://github.com/settings/tokens
export GITHUB_TOKEN=ghp_your_github_token

# Verify Node.js installation (v16 or higher required)
node --version
```

### 5. Install and Run

```bash
# Clone the repository
git clone <your-repo-url>
cd slack-on-call-agent

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the application
python3 app.py
```

## Usage

### `/incident` - Knowledge Base Search

Retrieve resolution steps from documented runbooks using RAG:

```
/incident kafka backlog is growing
/incident database connection timeout
/incident high memory usage on production servers
```

### `/code` - Repository Analysis

Explore your codebase and answer technical questions using MCP:

```
/code explain the authentication flow
/code what configuration variables control kafka
/code where is error handling implemented
```

### `/ask` - General Questions

Handle general queries not covered by specialized commands:

```
/ask what tools do you offer as an assistant
/ask what is the primary purpose of the application
```

### Mentions and Direct Messages

Interact with the bot by mentioning it in any channel or sending direct messages:

```
@On-Call Agent can you help diagnose this error?
```

## Architecture

```
User Request
    │
    ├─► /incident  → RAG Knowledge Base (data/docs/)
    │                   └─► Anthropic/OpenAI
    │
    ├─► /code      → MCP GitHub Tools (repository access)
    │                   └─► Anthropic with tool integration
    │
    └─► /ask       → Direct AI Provider
                        └─► Anthropic
```

## Key Features

- **RAG Knowledge Base** - Indexes markdown documentation for incident resolution
- **MCP Integration** - GitHub repository exploration via Model Context Protocol
- **Conversation Context** - Maintains thread history for contextual responses

## Documentation

- [CLAUDE.md](./CLAUDE.md) - Architecture and development guide
- [SETUP_MCP.md](./SETUP_MCP.md) - Detailed MCP configuration instructions
- [manifest.json](./manifest.json) - Slack app configuration

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `SLACK_BOT_TOKEN` | Yes | Bot authentication token |
| `SLACK_APP_TOKEN` | Yes | Socket Mode connection token |
| `ANTHROPIC_API_KEY` | Yes | Claude models with RAG/MCP support |
| `OPENAI_API_KEY` | Yes | Embedding generation for knowledge base |
| `GITHUB_TOKEN` | Yes | GitHub repository access via MCP |

## Technology Stack

- **[Bolt for Python](https://slack.dev/bolt-python/)** - Slack application framework
- **[LangChain](https://www.langchain.com/)** - RAG implementation
- **[ChromaDB](https://www.trychroma.com/)** - Vector database for embeddings
- **[Model Context Protocol](https://modelcontextprotocol.io/)** - Tool integration standard
