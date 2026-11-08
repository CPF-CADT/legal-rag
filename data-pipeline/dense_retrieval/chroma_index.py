"""Persist normalized vectors in a ChromaDB cosine collection."""

from __future__ import annotations

import os
from typing import Any

import numpy as np

from apps.core.retrieval_config import PipelineConfig


def build_index(
    chunks: list[dict[str, Any]], vectors: np.ndarray, config: PipelineConfig
) -> dict[str, Any]:
    import chromadb

    if len(chunks) != len(vectors):
        raise ValueError("Chunk and embedding counts do not match")
    if vectors.ndim != 2:
        raise ValueError("Embeddings must be a two-dimensional matrix")

    # The notebook executes stages individually, so ensure the persistent
    # database directory exists even when the orchestration function was not used.
    config.create_output_dirs()
    chroma_host = os.getenv("CHROMA_HOST", "").strip()
    if not chroma_host and not config.chroma_path.is_dir():
        raise RuntimeError(f"Unable to create ChromaDB directory: {config.chroma_path}")

    if chroma_host:
        client = chromadb.HttpClient(
            host=chroma_host,
            port=int(os.getenv("CHROMA_PORT", "8000")),
            ssl=os.getenv("CHROMA_SSL", "false").lower() == "true",
        )
    else:
        client = chromadb.PersistentClient(path=str(config.chroma_path))
    collection = client.get_or_create_collection(
        name=config.collection_name,
        metadata={"model": config.model_name, "hnsw:space": "cosine"},
    )
    for start in range(0, len(chunks), config.chroma_batch_size):
        batch = chunks[start : start + config.chroma_batch_size]
        collection.upsert(
            ids=[chunk["chunk_id"] for chunk in batch],
            embeddings=vectors[start : start + config.chroma_batch_size].tolist(),
            documents=[chunk["text"] for chunk in batch],
            metadatas=[
                {
                    key: value
                    for key, value in chunk.items()
                    if key not in {"text", "search_text"} and value is not None
                }
                for chunk in batch
            ],
        )
    return {
        "collection": config.collection_name,
        "path": f"http://{chroma_host}:{os.getenv('CHROMA_PORT', '8000')}" if chroma_host else str(config.chroma_path),
        "stored_vectors": collection.count(),
        "dimension": int(vectors.shape[1]),
        "metric": "cosine",
    }
