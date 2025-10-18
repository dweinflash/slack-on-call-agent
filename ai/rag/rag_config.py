"""
RAG Configuration Constants

This module defines constants for the RAG (Retrieval-Augmented Generation) system.
"""

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
