"""
RAG (Retrieval-Augmented Generation) Module

This module provides document indexing and retrieval capabilities
for the Anthropic AI provider.

Public API:
    - initialize_rag(): Initialize the RAG system on app startup
    - retrieve_context(query): Retrieve relevant document chunks for a query
"""

import logging
from typing import List

from .vector_store import get_vector_store

logger = logging.getLogger(__name__)


def initialize_rag():
    """
    Initialize the RAG system by loading documents and creating embeddings.
    Should be called once during application startup.
    """
    logger.info("Initializing RAG system...")
    vector_store = get_vector_store()
    vector_store.initialize()
    logger.info("RAG system initialization complete")


def retrieve_context(query: str) -> str:
    """
    Retrieve relevant document chunks for a given query.

    Args:
        query: The user's query text

    Returns:
        Formatted string containing retrieved document chunks,
        or empty string if no relevant documents found
    """
    vector_store = get_vector_store()
    documents = vector_store.retrieve(query)

    if not documents:
        return ""

    # Format retrieved documents
    context_parts = []
    for i, doc in enumerate(documents, 1):
        source = doc.metadata.get("source", "Unknown")
        # Extract just the filename from the full path
        filename = source.split("/")[-1] if "/" in source else source
        context_parts.append(f"### Document {i}: {filename}\n{doc.page_content}")

    formatted_context = "\n\n".join(context_parts)
    return formatted_context
