"""Shared JSONL and text utilities."""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from typing import Any, Iterable


def clean_text(value: Any) -> str:
    value = unicodedata.normalize("NFC", str(value or ""))
    value = value.replace("\u200b", "").replace("\u200c", "").replace("\u200d", "")
    return "\n".join(line.rstrip() for line in value.splitlines()).strip()


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )
