"""Online pure-dense retriever for the Telegram/backend layer.

This module loads an already-built ChromaDB collection. It does not process
OCR files, create chunks, or rebuild the index during a user request.
"""

from __future__ import annotations

import json
import os
import csv
from datetime import date
import threading
from pathlib import Path
from typing import Any

from apps.core.retrieval_config import PipelineConfig
from apps.core.shared.query_correction import correct_query


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
        self._load_lock = threading.Lock()
        self.recency_similarity_threshold = 0.05

    def _load(self) -> None:
        if self._collection is not None:
            return
        with self._load_lock:
            if self._collection is not None:
                return

            import chromadb
            from sentence_transformers import SentenceTransformer

            chroma_host = os.getenv("CHROMA_HOST", "").strip()
            if not chroma_host and not self.config.chroma_path.exists():
                raise FileNotFoundError(
                    f"Dense index not found: {self.config.chroma_path}. "
                    "Run build_dense_index.ipynb first."
                )
            if not self.config.article_path.exists():
                raise FileNotFoundError(
                    f"Article metadata not found: {self.config.article_path}. "
                    "Run build_dense_index.ipynb first."
                )

            if chroma_host:
                client = chromadb.HttpClient(
                    host=chroma_host,
                    port=int(os.getenv("CHROMA_PORT", "8000")),
                    ssl=os.getenv("CHROMA_SSL", "false").lower() == "true",
                )
            else:
                client = chromadb.PersistentClient(path=str(self.config.chroma_path))

            collection = client.get_collection(self.config.collection_name)
            model = SentenceTransformer(self.config.model_name)
            articles = self._load_articles()

            self._collection = collection
            self._model = model
            self._articles = articles

    def load(self) -> None:
        """Load model weights, collection, and article metadata into memory."""
        self._load()

    def filter_options(self) -> dict[str, list[str]]:
        """Return stable filter values from the loaded article metadata."""
        self._load()
        articles = self._articles or {}
        return {
            "titles": sorted({str(article.get("title", "")).strip() for article in articles.values() if article.get("title")}),
            "chapters": sorted({str(article.get("chapter_number", "")).strip() for article in articles.values() if article.get("chapter_number")}),
            "articles": sorted({str(article.get("article_number", "")).strip() for article in articles.values() if article.get("article_number")}),
        }

    def _load_articles(self) -> dict[str, dict[str, Any]]:
        articles: dict[str, dict[str, Any]] = {}
        document_dates: dict[str, str] = {}
        if self.config.documents_csv.exists():
            with self.config.documents_csv.open("r", encoding="utf-8-sig", newline="") as stream:
                document_dates = {
                    str(row.get("document_id", "")).strip(): (row.get("publication_date", "") or row.get("publication_year", ""))
                    for row in csv.DictReader(stream)
                }
        for line in self.config.article_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            article = json.loads(line)
            if str(article.get("document_id", "")).startswith("core-") and not article.get("source_url"):
                article["source_url"] = "https://www.khmerlawcode.com/"
            if not article.get("publication_date"):
                article["publication_date"] = document_dates.get(str(article.get("document_id", "")), "")
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
        correction = correct_query(query)
        query_variants = correction.variants
        if not query_variants:
            raise ValueError("Query must not be empty")
        if top_k < 1 or candidate_count < top_k:
            raise ValueError("candidate_count must be at least top_k")

        by_article: dict[str, dict[str, Any]] = {}
        for variant in query_variants:
            query_vector = self._model.encode(
                [variant],
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            )[0]
            result = self._collection.query(
                query_embeddings=[query_vector.tolist()],
                n_results=min(self._collection.count(), candidate_count),
                include=["documents", "metadatas", "distances"],
            )
            for index, chunk_id in enumerate(result["ids"][0]):
                metadata = result["metadatas"][0][index] or {}
                article_id = str(metadata.get("article_id") or chunk_id)
                distance = float(result["distances"][0][index])
                matches = by_article.setdefault(article_id, {"matches": []})["matches"]
                existing = next((match for match in matches if match["chunk_id"] == chunk_id), None)
                match = {
                    "chunk_id": chunk_id,
                    "text": result["documents"][0][index] or "",
                    "distance": distance,
                    "similarity": 1.0 - distance,
                    "query_variant": variant,
                }
                if existing is None:
                    matches.append(match)
                elif distance < existing["distance"]:
                    existing.update(match)

        ranked = sorted(
            by_article.items(),
            key=lambda item: min(match["distance"] for match in item[1]["matches"]),
        )
        ranked = self._apply_recency_tiebreaker(ranked)
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
                    "chapter_number": article.get("chapter_number", "") or "",
                    "chapter_title": article.get("chapter_title", "") or "",
                    "document_id": article.get("document_id", ""),
                    "publication_date": article.get("publication_date", ""),
                    "answer_context": article.get("text", ""),
                    "article_text": article.get("text", ""),
                    "best_similarity": matches[0]["similarity"],
                    "matched_chunks": matches[:2],
                    "source_url": article.get("source_url", ""),
                    "pdf_url": article.get("pdf_url", ""),
                }
            )
        return output

    @staticmethod
    def _publication_date(article: dict[str, Any]) -> date | None:
        value = str(article.get("publication_date", "") or "").strip()
        for fmt, length in (("%Y-%m-%d", 10), ("%Y-%m", 7), ("%Y", 4)):
            try:
                from datetime import datetime
                return datetime.strptime(value[:length], fmt).date()
            except ValueError:
                continue
        return None

    def _apply_recency_tiebreaker(self, ranked: list[tuple[str, dict[str, Any]]]):
        """Prefer newer laws only inside the top semantic-relevance band."""
        if not ranked:
            return ranked
        scored = [
            (article_id, grouped, 1.0 - min(match["distance"] for match in grouped["matches"]),
             self._publication_date((self._articles or {}).get(article_id, {})))
            for article_id, grouped in ranked
        ]
        best_similarity = scored[0][2]
        threshold = best_similarity - self.recency_similarity_threshold
        return [
            (article_id, grouped)
            for article_id, grouped, _similarity, _published in sorted(
                scored,
                key=lambda item: (
                    item[2] < threshold,
                    -(item[3].toordinal() if item[3] else 0),
                    -item[2],
                ),
            )
        ]

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
