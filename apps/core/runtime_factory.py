"""Build the shared retrieval and grounded-answer runtime."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from apps.core.answer_service import AnswerService
from apps.core.config import env, env_bool, env_int
from apps.core.retrieval_config import PipelineConfig
from apps.core.bm25.sqlite_retriever import BM25Retriever
from apps.core.llm_generator import GeminiTextGenerator, OpenRouterTextGenerator


@dataclass(frozen=True)
class RuntimeServices:
    retriever: BM25Retriever
    answer_service: AnswerService


def build_runtime_services(
    project_root: Path,
    *,
    candidate_count: int = 50,
    top_k: int = 5,
    min_similarity: float = 0.35,
) -> RuntimeServices:
    """Create one consistent runtime for both API and Telegram applications."""
    retriever = BM25Retriever(
        project_root=project_root,
        config=PipelineConfig(project_root=project_root),
    )
    retriever.load()

    backend = env("LLM_BACKEND", "gemini").lower()
    if backend == "openrouter":
        generator = OpenRouterTextGenerator(
            api_key=env("OPENROUTER_API_KEY"),
            model=env("OPENROUTER_MODEL", "google/gemini-3.5-flash-lite"),
            max_tokens=env_int("OPENROUTER_MAX_TOKENS"),
            reasoning_enabled=env_bool("OPENROUTER_REASONING_ENABLED", True),
            timeout_seconds=env_int("OPENROUTER_TIMEOUT", 180) or 180,
        )
    elif backend == "gemini":
        generator = GeminiTextGenerator(
            model=env("GEMINI_MODEL", "gemini-3.8-flash"),
            max_output_tokens=env_int("GEMINI_MAX_OUTPUT_TOKENS"),
            thinking_budget=env_int("GEMINI_THINKING_BUDGET", 0) or 0,
            thinking_level=env("GEMINI_THINKING_LEVEL", "low"),
            retry_attempts=env_int("GEMINI_RETRY_ATTEMPTS", 3) or 3,
            retry_backoff_seconds=float(env("GEMINI_RETRY_BACKOFF_SECONDS", "1")),
            api_keys_file=env(
                "GEMINI_API_KEYS_FILE",
                "apps/api/secrets/gemini_api_keys.txt",
            ),
        )
    else:
        raise ValueError(f"Unsupported LLM_BACKEND: {backend}")

    return RuntimeServices(
        retriever=retriever,
        answer_service=AnswerService(
            retriever,
            generator,
            candidate_count=candidate_count,
            top_k=top_k,
            min_similarity=min_similarity,
        ),
    )
