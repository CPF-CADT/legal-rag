"""Combine dense and lexical candidates with normalized score fusion."""

from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Any

from apps.core.bm25.sqlite_retriever import BM25Retriever
from apps.core.retrieval_config import PipelineConfig
from apps.core.dense.retriever import DenseRetriever

logger = logging.getLogger(__name__)


class HybridRetriever:
    def __init__(self, project_root: Path, config: PipelineConfig | None = None, *, bm25_weight: float = 0.5, dense_weight: float = 0.5) -> None:
        config = config or PipelineConfig(project_root=project_root)
        self.dense = DenseRetriever(project_root, config)
        self.bm25 = BM25Retriever(project_root, config)
        total_weight = bm25_weight + dense_weight
        if total_weight <= 0:
            raise ValueError("Hybrid retrieval weights must add up to more than zero")
        self.bm25_weight = bm25_weight / total_weight
        self.dense_weight = dense_weight / total_weight
        self._bm25_available = True

    def load(self) -> None:
        self.dense.load()
        try:
            self.bm25.load()
        except Exception as exc:
            self._bm25_available = False
            logger.warning("bm25_index_unavailable_using_dense_only: %s", exc)

    def search(self, query: str, *, candidate_count: int = 100, top_k: int = 5) -> list[dict[str, Any]]:
        dense_results = self.dense.search(query, candidate_count=candidate_count, top_k=candidate_count)
        if self._bm25_available:
            try:
                bm25_results = self.bm25.search(query, candidate_count=candidate_count, top_k=candidate_count)
            except Exception as exc:
                self._bm25_available = False
                logger.warning("bm25_search_failed_using_dense_only: %s", exc)
                bm25_results = []
        else:
            bm25_results = []
        dense_scores = {result["article_id"]: float(result.get("best_similarity", 0.0)) for result in dense_results}
        bm25_scores = {result["article_id"]: float(result.get("bm25_score", 0.0)) for result in bm25_results}
        dense_normalized = self._min_max(dense_scores)
        bm25_normalized = self._min_max(bm25_scores)
        fused: dict[str, dict[str, Any]] = {}
        for result in [*dense_results, *bm25_results]:
            article_id = result["article_id"]
            item = fused.setdefault(article_id, {**result})
            item["hybrid_score"] = self.dense_weight * dense_normalized.get(article_id, 0.0) + self.bm25_weight * bm25_normalized.get(article_id, 0.0)
            if result.get("best_similarity", 0) > item.get("best_similarity", 0):
                item["best_similarity"] = result["best_similarity"]
            if result.get("matched_chunks") and result.get("bm25_score", 0) > item.get("bm25_score", 0):
                item["matched_chunks"] = result["matched_chunks"]
        ranked = sorted(fused.values(), key=lambda item: item["hybrid_score"], reverse=True)[:top_k]
        for rank, result in enumerate(ranked, start=1):
            result["rank"] = rank
        return ranked

    @staticmethod
    def _min_max(scores: dict[str, float]) -> dict[str, float]:
        if not scores:
            return {}
        minimum, maximum = min(scores.values()), max(scores.values())
        if math.isclose(minimum, maximum):
            return {key: 1.0 for key in scores}
        return {key: (value - minimum) / (maximum - minimum) for key, value in scores.items()}

    def filter_options(self) -> dict[str, list[str]]:
        return self.dense.filter_options()

    @staticmethod
    def format_context(results: list[dict[str, Any]]) -> str:
        return DenseRetriever.format_context(results)
