"""Build the retriever and selected text-generation backend."""

from __future__ import annotations

import logging

from dense_retrieval.retriever import DenseRetriever

from answer_service import AnswerService
from config import PROJECT_ROOT, env, env_bool, env_int
from llm_generator import GeminiTextGenerator, OpenRouterTextGenerator


logger = logging.getLogger("legalrag.telegram_bot")


def build_service() -> AnswerService:
    retriever = DenseRetriever(project_root=PROJECT_ROOT)
    logger.info("retriever_loading model=%s", retriever.config.model_name)
    retriever.load()
    logger.info("retriever_loaded collection=%s", retriever.config.collection_name)

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
            model=env("GEMINI_MODEL", "gemini-2.5-flash"),
            max_output_tokens=env_int("GEMINI_MAX_OUTPUT_TOKENS"),
            thinking_budget=env_int("GEMINI_THINKING_BUDGET", 0) or 0,
            thinking_level=env("GEMINI_THINKING_LEVEL", "minimal"),
            api_keys_file=env("GEMINI_API_KEYS_FILE", "bot/secrets/gemini_api_keys.txt"),
        )
    else:
        raise ValueError(f"Unsupported LLM_BACKEND: {backend}")

    logger.info("llm_loaded backend=%s model=%s", backend, generator.model)
    return AnswerService(retriever, generator, candidate_count=50, top_k=5)
