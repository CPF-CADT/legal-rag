"""Online pure-dense retriever for the Telegram/backend layer.

This module loads an already-built ChromaDB collection. It does not process
OCR files, create chunks, or rebuild the index during a user request.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import PipelineConfig
from .io_utils import clean_text


class DenseRetriever:
    """Retrieve complete legal articles from the persisted BGE-M3 index."""

    def __init__(
        self,
        project_root: Path,
        config: PipelineConfig | None = None,
    ) -> None:
        self.config = config or PipelineConfig(project_root=project_root)
        self._collection: Any | None = None
        self._model: Any | None = None
        self._articles: dict[str, dict[str, Any]] | None = None

    def _load(self) -> None:
        if self._collection is not None:
            return

        import chromadb
        from sentence_transformers import SentenceTransformer

        if not self.config.chroma_path.exists():
            raise FileNotFoundError(
                f"Dense index not found: {self.config.chroma_path}. "
                "Run build_dense_index.ipynb first."
            )
        if not self.config.article_path.exists():
            raise FileNotFoundError(
                f"Article metadata not found: {self.config.article_path}. "
                "Run build_dense_index.ipynb first."
            )

        client = chromadb.PersistentClient(path=str(self.config.chroma_path))
        self._collection = client.get_collection(self.config.collection_name)
        self._model = SentenceTransformer(self.config.model_name)
        self._articles = self._load_articles()

    def load(self) -> None:
        """Load model weights, collection, and article metadata into memory."""
        self._load()

    def _load_articles(self) -> dict[str, dict[str, Any]]:
        articles: dict[str, dict[str, Any]] = {}
        for line in self.config.article_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            article = json.loads(line)
            article_id = str(article["article_id"])
            articles[article_id] = article
        return articles

    def search(
        self,
        query: str,
        *,
        candidate_count: int = 100,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Return top-k complete articles ranked by their best chunk."""
        self._load()
        query = clean_text(query).replace("\n", " ")
        if not query:
            raise ValueError("Query must not be empty")
        if top_k < 1 or candidate_count < top_k:
            raise ValueError("candidate_count must be at least top_k")

        query_vector = self._model.encode(
            [query],
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )[0]
        result = self._collection.query(
            query_embeddings=[query_vector.tolist()],
            n_results=min(self._collection.count(), candidate_count),
            include=["documents", "metadatas", "distances"],
        )

        by_article: dict[str, dict[str, Any]] = {}
        for index, chunk_id in enumerate(result["ids"][0]):
            metadata = result["metadatas"][0][index] or {}
            article_id = str(metadata.get("article_id") or chunk_id)
            distance = float(result["distances"][0][index])
            by_article.setdefault(article_id, {"matches": []})["matches"].append(
                {
                    "chunk_id": chunk_id,
                    "text": result["documents"][0][index] or "",
                    "distance": distance,
                    "similarity": 1.0 - distance,
                }
            )

        ranked = sorted(
            by_article.items(),
            key=lambda item: min(match["distance"] for match in item[1]["matches"]),
        )
        output: list[dict[str, Any]] = []
        for rank, (article_id, grouped) in enumerate(ranked[:top_k], start=1):
            article = (self._articles or {}).get(article_id, {})
            matches = sorted(grouped["matches"], key=lambda match: match["distance"])
            output.append(
                {
                    "rank": rank,
                    "article_id": article_id,
                    "title": article.get("title", ""),
                    "article_number": article.get("article_number", ""),
                    "document_id": article.get("document_id", ""),
                    "answer_context": article.get("text", ""),
                    "best_similarity": matches[0]["similarity"],
                    "matched_chunks": matches[:2],
                    "source_url": article.get("source_url", ""),
                    "pdf_url": article.get("pdf_url", ""),
                }
            )
        return output

    @staticmethod
    def format_context(results: list[dict[str, Any]]) -> str:
        """Format retrieved articles as context for an answer-generation model."""
        sections = []
        for result in results:
            sections.append(
                "\n".join(
                    [
                        f"ប្រភព {result['rank']}: {result['title']}",
                        f"មាត្រា: {result['article_number']}",
                        result["answer_context"],
                    ]
                )
            )
        return "\n\n---\n\n".join(sections)
