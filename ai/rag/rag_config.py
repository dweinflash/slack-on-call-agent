"""
RAG Configuration Constants

This module defines constants for the RAG (Retrieval-Augmented Generation) system.
"""

import os

# Document chunking parameters
CHUNK_SIZE = 1000  # Number of characters per chunk
CHUNK_OVERLAP = 200  # Character overlap between chunks to preserve context

# Retrieval parameters
TOP_K_CHUNKS = 3  # Number of most relevant chunks to retrieve

# ChromaDB configuration
CHROMA_COLLECTION_NAME = "knowledge_docs"
CHROMA_PERSIST_DIR = "data/chroma_db"

# Document source
DOCS_DIRECTORY = "data/docs"

# GitHub Repository Configuration for Article Links
# These can be overridden with environment variables
GITHUB_REPO_OWNER = os.environ.get("GITHUB_REPO_OWNER", "dweinflash")
GITHUB_REPO_NAME = os.environ.get("GITHUB_REPO_NAME", "slack-on-call-agent")
GITHUB_BRANCH = os.environ.get("GITHUB_BRANCH", "main")


def get_github_article_url(filename: str) -> str:
    """
    Generate a GitHub URL for a knowledge base article.

    Args:
        filename: The markdown filename (e.g., "209731_KAFKA_BACKLOG.md")

    Returns:
        Full GitHub URL to the article
    """
    return f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/blob/{GITHUB_BRANCH}/{DOCS_DIRECTORY}/{filename}"
