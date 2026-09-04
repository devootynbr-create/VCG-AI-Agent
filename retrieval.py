"""
VCG knowledge retrieval layer.

Uses ChromaDB for persistent vector storage.

Responsibilities:
- connect to knowledge base
- add documents (flexible dict list or explicit lists)
- search documents
- inspect knowledge-base size
- reset knowledge base
"""

import os
from typing import Any, Dict, List, Optional, Union

import chromadb


# -------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------

VECTORSTORE_PATH = os.getenv(
    "VCG_VECTORSTORE_PATH",
    "./vectorstore",
)

COLLECTION_NAME = os.getenv(
    "VCG_COLLECTION_NAME",
    "vcg_knowledge",
)


# -------------------------------------------------------------------
# CHROMA CLIENT
# -------------------------------------------------------------------

chroma_client = chromadb.PersistentClient(
    path=VECTORSTORE_PATH
)


# -------------------------------------------------------------------
# COLLECTION
# -------------------------------------------------------------------

collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME,
)


# -------------------------------------------------------------------
# ADD DOCUMENTS
# -------------------------------------------------------------------

def add_documents(
    documents: Union[List[Dict[str, Any]], List[str]],
    metadatas: Optional[List[Dict[str, Any]]] = None,
    ids: Optional[List[str]] = None,
) -> int:
    """
    Add document chunks to ChromaDB.

    Supports two calling formats:
    1. Single argument of dicts: add_documents([{"id": ..., "text": ..., "metadata": ...}])
    2. Three separate lists: add_documents(documents=[...], metadatas=[...], ids=[...])

    Returns the total number of added chunks.
    """
    if not documents:
        return 0

    # Unpack list of dicts if returned directly from ingestion.py
    if isinstance(documents, list) and len(documents) > 0 and isinstance(documents[0], dict):
        doc_dicts = documents
        docs_list = [item.get("text", "") for item in doc_dicts]
        meta_list = [item.get("metadata", {}) for item in doc_dicts]
        ids_list = [item.get("id", f"chunk_{i}") for i, item in enumerate(doc_dicts)]
    else:
        docs_list = documents
        meta_list = metadatas if metadatas is not None else []
        ids_list = ids if ids is not None else []

    if not (len(docs_list) == len(meta_list) == len(ids_list)):
        raise ValueError(
            "documents, metadatas and ids must have the same length."
        )

    collection.add(
        documents=docs_list,
        metadatas=meta_list,
        ids=ids_list,
    )

    return len(docs_list)


# -------------------------------------------------------------------
# ADD KNOWLEDGE TEXT
# -------------------------------------------------------------------

def add_knowledge_text(
    text: str,
    document_name: str = "manual_input",
) -> int:
    """
    Convenience function for adding a plain text document.

    Useful for quick testing from Streamlit.
    """

    if not text or not text.strip():
        return 0

    # Simple chunking
    chunk_size = 1200
    overlap = 200

    chunks = []
    start = 0

    while start < len(text):
        end = min(
            start + chunk_size,
            len(text),
        )

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - overlap

    documents = []
    metadatas = []
    ids = []

    for index, chunk in enumerate(chunks):
        documents.append(f"[PAGE N/A]\n{chunk}")

        metadatas.append({
            "document": document_name,
            "page": "N/A",
            "chunk": index + 1,
            "source_type": "manual_text",
        })

        ids.append(
            f"{document_name}_{index}"
        )

    return add_documents(
        documents=documents,
        metadatas=metadatas,
        ids=ids,
    )


# -------------------------------------------------------------------
# SEARCH
# -------------------------------------------------------------------

def search_knowledge(
    query: str,
    top_k: int = 5,
) -> Dict[str, Any]:
    """
    Search the VCG knowledge base.

    Returns:
        {
            "documents": [[...]],
            "metadatas": [[...]],
            "distances": [[...]]
        }
    """

    if not query or not query.strip():
        return {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }

    result = collection.query(
        query_texts=[query],
        n_results=max(1, top_k),
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    return result


# -------------------------------------------------------------------
# KNOWLEDGE COUNT
# -------------------------------------------------------------------

def get_document_count() -> int:
    """
    Return number of chunks currently stored.
    """

    try:
        return collection.count()
    except Exception:
        return 0


# -------------------------------------------------------------------
# RESET
# -------------------------------------------------------------------

def reset_knowledge_base() -> None:
    """
    Delete and recreate the VCG knowledge collection.
    """

    global collection

    try:
        chroma_client.delete_collection(
            name=COLLECTION_NAME
        )
    except Exception:
        pass

    collection = chroma_client.get_or_create_collection(
        name=COLLECTION_NAME
    )