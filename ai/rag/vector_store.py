"""
Vector Store Module

This module manages the ChromaDB vector database for document embeddings and retrieval.
"""

import os
import logging
from typing import List, Optional
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.schema import Document

from .rag_config import CHROMA_COLLECTION_NAME, CHROMA_PERSIST_DIR, TOP_K_CHUNKS
from .document_loader import load_and_chunk_documents

logger = logging.getLogger(__name__)


class VectorStore:
    """Manages ChromaDB vector store for document retrieval."""

    def __init__(self):
        self.vector_store: Optional[Chroma] = None
        self.embeddings = None

    def initialize(self):
        """
        Initialize the vector store by loading documents, creating embeddings,
        and persisting to ChromaDB.
        """
        try:
            # Verify OpenAI API key exists
            if not os.environ.get("OPENAI_API_KEY"):
                logger.error("OPENAI_API_KEY not found. RAG initialization skipped.")
                return

            # Initialize OpenAI embeddings
            self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            logger.info("Initialized OpenAI embeddings")

            # Create persist directory if it doesn't exist
            os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)

            # Load and chunk documents
            documents = load_and_chunk_documents()

            if len(documents) == 0:
                logger.warning("No documents to index. RAG system inactive.")
                return

            # Create or load ChromaDB collection
            self.vector_store = Chroma(
                collection_name=CHROMA_COLLECTION_NAME,
                embedding_function=self.embeddings,
                persist_directory=CHROMA_PERSIST_DIR,
            )

            # Check if collection already has documents
            collection = self.vector_store._collection
            existing_count = collection.count()

            if existing_count > 0:
                logger.info(f"Found existing ChromaDB collection with {existing_count} chunks")
                logger.info("Clearing existing collection and re-indexing")
                # Clear the collection
                collection.delete(ids=collection.get()["ids"])

            # Add documents to vector store
            self.vector_store.add_documents(documents)
            logger.info(f"Successfully indexed {len(documents)} document chunks")

        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
            self.vector_store = None

    def retrieve(self, query: str, k: int = TOP_K_CHUNKS) -> List[Document]:
        """
        Retrieve the top k most relevant document chunks for a query.

        Args:
            query: The user's query text
            k: Number of chunks to retrieve (default from config)

        Returns:
            List of relevant document chunks
        """
        if not self.vector_store:
            logger.warning("Vector store not initialized. Returning empty results.")
            return []

        try:
            # Perform similarity search
            results = self.vector_store.similarity_search(query, k=k)
            logger.info(f"Retrieved {len(results)} relevant chunks for query")
            return results

        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []


# Global vector store instance
_vector_store_instance: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get or create the global vector store instance."""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance
