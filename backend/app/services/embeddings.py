"""
Chroma vector store wrapper.

Stores product text chunks with metadata {product_id, user_id} and supports
hybrid retrieval: semantic (Chroma cosine) + keyword filtering.
"""

import logging
import threading
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: Optional[Any] = None
_collection = None
_init_lock = threading.Lock()  # Prevent race condition on first request (Issue 13)

COLLECTION_NAME = "nutritrack_products"


def _get_collection():
    global _client, _collection
    if _collection is None:
        with _init_lock:
            # Double-checked locking
            if _collection is None:
                logger.info("Initialising Chroma collection and embedding model…")
                import chromadb
                from chromadb.utils import embedding_functions

                _client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
                ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name="all-MiniLM-L6-v2"
                )
                _collection = _client.get_or_create_collection(
                    name=COLLECTION_NAME,
                    embedding_function=ef,
                    metadata={"hnsw:space": "cosine"},
                )
                logger.info("Chroma collection ready")
    return _collection


def warm_up_embeddings() -> None:
    """
    Pre-warm the SentenceTransformer model at application startup (Issue 13).
    Prevents the first real request from hanging for 30-90 seconds.
    """
    _get_collection()
    logger.info("Embedding warm-up complete")


def _chunk_product_text(product_name: str, brand: Optional[str], raw_text: str, serving_size_g: float) -> list[str]:
    header = f"{product_name}"
    if brand:
        header += f" by {brand}"
    header += f" (serving {serving_size_g}g)"

    chunks = [header]
    chunk_size = 400
    overlap = 50
    i = 0
    while i < len(raw_text):
        chunk = raw_text[i: i + chunk_size]
        if chunk.strip():
            chunks.append(f"{header}\n{chunk}")
        i += chunk_size - overlap

    return chunks[:10]


def index_product(
    product_id: str,
    user_id: str,
    product_name: str,
    brand: Optional[str],
    raw_text: str,
    serving_size_g: float,
) -> int:
    """Embed and store product chunks. Returns number of chunks stored."""
    col = _get_collection()
    chunks = _chunk_product_text(product_name, brand, raw_text, serving_size_g)

    ids = [f"{product_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [
        {"product_id": product_id, "user_id": user_id, "chunk_index": i}
        for i in range(len(chunks))
    ]

    col.upsert(ids=ids, documents=chunks, metadatas=metadatas)
    logger.info("Indexed %d chunks for product %s", len(chunks), product_id)
    return len(chunks)


def delete_product_embeddings(product_id: str) -> None:
    col = _get_collection()
    results = col.get(where={"product_id": product_id})
    if results["ids"]:
        col.delete(ids=results["ids"])
        logger.info("Deleted %d embeddings for product %s", len(results["ids"]), product_id)


def semantic_search(
    query: str,
    user_id: str,
    top_k: int = 5,
) -> list[dict]:
    """Returns list of {product_id, score} sorted by relevance, filtered to user's products."""
    col = _get_collection()

    try:
        results = col.query(
            query_texts=[query],
            n_results=min(top_k * 3, 30),
            where={"user_id": user_id},
        )
    except Exception as exc:
        logger.warning("Chroma query failed: %s", exc)
        return []

    seen_products: dict[str, float] = {}
    for meta, dist in zip(results["metadatas"][0], results["distances"][0]):
        pid = meta["product_id"]
        score = 1.0 - dist
        if pid not in seen_products or score > seen_products[pid]:
            seen_products[pid] = score

    return [
        {"product_id": pid, "score": score}
        for pid, score in sorted(seen_products.items(), key=lambda x: -x[1])
    ][:top_k]
