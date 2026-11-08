"""BGE-M3 embedding generation and persistence."""

from __future__ import annotations

import json
from typing import Any

import numpy as np

from apps.core.retrieval_config import PipelineConfig
from .io_utils import write_jsonl


def embed_chunks(chunks: list[dict[str, Any]], config: PipelineConfig) -> np.ndarray:
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(config.model_name)
    vectors = model.encode(
        [chunk["search_text"] for chunk in chunks],
        batch_size=config.embedding_batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype("float32")
    np.save(config.embedding_path, vectors)
    write_jsonl(
        config.metadata_path,
        [{key: value for key, value in chunk.items() if key != "search_text"} for chunk in chunks],
    )
    config.manifest_path.write_text(
        json.dumps(
            {
                "model": config.model_name,
                "chunk_count": len(chunks),
                "embedding_dimension": int(vectors.shape[1]),
                "normalized_embeddings": True,
                "max_chunk_tokens": config.max_chunk_tokens,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return vectors
