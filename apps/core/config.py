"""Shared environment loading and configuration helpers."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(
    os.getenv("LEGALRAG_PROJECT_ROOT", Path(__file__).resolve().parents[1])
).resolve()


def load_environment() -> None:
    """Load the repository environment, then app-local overrides."""
    load_dotenv(PROJECT_ROOT / ".env")
    app_env = PROJECT_ROOT / "apps" / "telegram-bot" / ".env"
    load_dotenv(app_env, override=True)


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def env_int(name: str, default: int | None = None) -> int | None:
    value = env(name)
    return int(value) if value else default


def env_bool(name: str, default: bool = False) -> bool:
    value = env(name)
    return value.lower() == "true" if value else default
