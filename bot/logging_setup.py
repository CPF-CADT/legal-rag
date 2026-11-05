"""Logging configuration and structured RAG/LLM request logging."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import threading


LOG_PATH = Path(__file__).resolve().parent / "logs" / "telegram_bot.log"
RAG_LLM_LOG_PATH = Path(__file__).resolve().parent / "logs" / "rag_llm_responses.jsonl"
RAG_LLM_LOG_LOCK = threading.Lock()
logger = logging.getLogger("legalrag.telegram_bot")


def configure_logging() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")

    file_handler = RotatingFileHandler(LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def write_rag_llm_log(record: dict[str, object]) -> None:
    """Append one JSON record containing retrieval and generation data."""
    RAG_LLM_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record_with_time = {"timestamp": datetime.now(timezone.utc).isoformat(), **record}
    line = json.dumps(record_with_time, ensure_ascii=False) + "\n"
    with RAG_LLM_LOG_LOCK:
        with RAG_LLM_LOG_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(line)
