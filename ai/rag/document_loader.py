"""
Document Loader Module

This module handles loading and chunking markdown documents from the knowledge base.
"""

import os
import logging
from typing import List
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

from .rag_config import CHUNK_SIZE, CHUNK_OVERLAP, DOCS_DIRECTORY

logger = logging.getLogger(__name__)


def load_and_chunk_documents() -> List[Document]:
    """
    Load markdown documents from the docs directory and split them into chunks.

    Returns:
        List[Document]: List of chunked documents with metadata
    """
    try:
        # Check if docs directory exists
        if not os.path.exists(DOCS_DIRECTORY):
            logger.warning(f"Documents directory not found: {DOCS_DIRECTORY}")
            return []

        # Load all markdown files from the directory
        loader = DirectoryLoader(
            DOCS_DIRECTORY,
            glob="**/*.md",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"}
        )

        documents = loader.load()
        logger.info(f"Loaded {len(documents)} documents from {DOCS_DIRECTORY}")

        if len(documents) == 0:
            logger.warning(f"No markdown files found in {DOCS_DIRECTORY}")
            return []

        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""]
        )

        chunked_docs = text_splitter.split_documents(documents)

        # Add chunk index to metadata
        for i, doc in enumerate(chunked_docs):
            doc.metadata["chunk_index"] = i

        logger.info(f"Split documents into {len(chunked_docs)} chunks")
        return chunked_docs

    except Exception as e:
        logger.error(f"Error loading documents: {e}")
        return []
