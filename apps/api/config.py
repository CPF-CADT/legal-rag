"""Environment-driven API settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    project_root: Path
    host: str = "0.0.0.0"
    port: int = 8000
    candidate_count: int = 50
    default_top_k: int = 5
    max_top_k: int = 20
    min_similarity: float = 0.35
    neighbor_count: int = 1
    api_key: str = ""
    cors_origins: tuple[str, ...] = ("http://localhost:5173", "http://127.0.0.1:5173")
    max_query_length: int = 4000
    rate_limit_per_minute: int = 0
    filter_cache_ttl_seconds: int = 3600

    @classmethod
    def from_environment(cls) -> "Settings":
        root = Path(os.getenv("LEGALRAG_PROJECT_ROOT", Path(__file__).resolve().parents[2]))
        return cls(
            project_root=root,
            host=os.getenv("FASTAPI_HOST", "0.0.0.0"),
            port=int(os.getenv("FASTAPI_PORT", "8000")),
            candidate_count=int(os.getenv("DENSE_RETRIEVAL_CANDIDATE_COUNT", "50")),
            default_top_k=int(os.getenv("DENSE_RETRIEVAL_TOP_K", "5")),
            max_top_k=int(os.getenv("FASTAPI_MAX_TOP_K", "20")),
            min_similarity=float(os.getenv("DENSE_RETRIEVAL_MIN_SIMILARITY", "0.35")),
            neighbor_count=int(os.getenv("DENSE_RETRIEVAL_NEIGHBOR_COUNT", "1")),
            api_key=os.getenv("LEGALRAG_API_KEY", ""),
            cors_origins=tuple(
                origin.strip()
                for origin in os.getenv(
                    "LEGALRAG_CORS_ORIGINS",
                    "http://localhost:5173,http://127.0.0.1:5173",
                ).split(",")
                if origin.strip()
            ),
            max_query_length=int(os.getenv("LEGALRAG_MAX_QUERY_LENGTH", "4000")),
            rate_limit_per_minute=int(os.getenv("LEGALRAG_RATE_LIMIT_PER_MINUTE", "0")),
            filter_cache_ttl_seconds=int(os.getenv("LEGALRAG_FILTER_CACHE_TTL_SECONDS", "3600")),
        )
