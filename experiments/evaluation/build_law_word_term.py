"""Merge legal definition sources into the canonical law_word_term schema."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from apps.core.shared.normalization import normalize_khmer

RESOURCES = ROOT / "experiments" / "evaluation" / "resources"
OUTPUT = RESOURCES / "law_word_term.json"


def key(value: str) -> str:
    return re.sub(r"\s+", "", normalize_khmer(value)).casefold()


def read_records(path: Path, name_field: str) -> list[tuple[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    records = []
    for item in data:
        name = normalize_khmer(item.get(name_field, ""))
        description = normalize_khmer(item.get("description", ""))
        if name and description:
            records.append((name, description))
    return records


def main() -> None:
    sources = [
        (RESOURCES / "definition.json", "name"),
        (RESOURCES / "khmer_khmer_dictionary.json", "word"),
    ]
    merged: dict[str, tuple[str, str]] = {}
    for path, name_field in sources:
        for name, description in read_records(path, name_field):
            normalized_key = key(name)
            current = merged.get(normalized_key)
            # Prefer the first source (legal definitions), but fill an empty
            # or shorter definition from the second source when available.
            if current is None or len(description) > len(current[1]):
                merged[normalized_key] = (name, description)

    output = [
        {"id": index, "name": name, "description": description}
        for index, (name, description) in enumerate(
            sorted(merged.values(), key=lambda item: key(item[0])), start=1
        )
    ]
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "sources": [str(path) for path, _ in sources],
        "output": str(OUTPUT),
        "entries": len(output),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
