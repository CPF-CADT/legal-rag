"""Application configuration and environment loading."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BOT_ROOT = Path(__file__).resolve().parent
DATA_PIPELINE_ROOT = PROJECT_ROOT / "data-pipeline"

if str(DATA_PIPELINE_ROOT) not in sys.path:
    sys.path.insert(0, str(DATA_PIPELINE_ROOT))


def load_environment() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    load_dotenv(BOT_ROOT / ".env", override=True)


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def env_int(name: str, default: int | None = None) -> int | None:
    value = env(name)
    return int(value) if value else default


def env_bool(name: str, default: bool = False) -> bool:
    value = env(name)
    return value.lower() == "true" if value else default
