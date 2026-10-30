"""CSV-backed Gemini API key rotation and health tracking."""

import csv
import time
from datetime import datetime, timezone
from pathlib import Path


KEY_FIELDS = ["key_id", "status", "limited_until", "failure_count", "last_error", "updated_at"]


class NoUsableKeyError(RuntimeError):
    """Raised when no API key can currently be used."""


def now_timestamp() -> float:
    return time.time()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_key_values(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"API key file not found: {path}")
    keys = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    keys = list(dict.fromkeys(key for key in keys if key and not key.startswith("#")))
    if not keys:
        raise ValueError(f"No API keys found in {path}")
    return keys


def load_states(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return {row["key_id"]: row for row in csv.DictReader(file) if row.get("key_id")}


def save_states(path: Path, states: dict[str, dict]) -> None:
    """Atomically save key status without writing actual API keys."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=KEY_FIELDS)
        writer.writeheader()
        writer.writerows({field: state.get(field, "") for field in KEY_FIELDS} for state in states.values())
    temporary.replace(path)


def classify_error(error: Exception) -> str:
    message = str(error).lower()
    if any(
        marker in message
        for marker in (
            "429",
            "503",
            "rate limit",
            "rate_limit",
            "resource exhausted",
            "quota",
            "temporarily unavailable",
            "high demand",
        )
    ):
        return "rate_limited"
    if any(marker in message for marker in ("invalid api key", "api key not valid", "unauthenticated", "permission denied")):
        return "invalid"
    return "transient"


class KeyManager:
    def __init__(self, keys_path: Path, checkpoint_path: Path, cooldown_seconds: int):
        values = load_key_values(keys_path)
        self.cooldown_seconds = cooldown_seconds
        self.checkpoint_path = checkpoint_path
        self.states = load_states(checkpoint_path)
        self.key_ids = {}
        for index, value in enumerate(values, start=1):
            key_id = f"key-{index:03d}"
            self.key_ids[key_id] = value
            self.states.setdefault(key_id, {
                "key_id": key_id,
                "status": "available",
                "limited_until": "",
                "failure_count": "0",
                "last_error": "",
                "updated_at": now_utc(),
            })
        save_states(self.checkpoint_path, self.states)
        self.position = 0

    def _is_available(self, state: dict) -> bool:
        if state.get("status") == "disabled":
            return False
        limited_until = float(state.get("limited_until") or 0)
        if limited_until and limited_until > now_timestamp():
            return False
        if state.get("status") == "rate_limited":
            state.update(status="available", limited_until="", updated_at=now_utc())
        return state.get("status", "available") == "available"

    def next_key(self) -> tuple[str, str]:
        if not self.key_ids:
            raise NoUsableKeyError("No API keys are configured")
        ordered_ids = list(self.key_ids)
        for offset in range(len(ordered_ids)):
            index = (self.position + offset) % len(ordered_ids)
            key_id = ordered_ids[index]
            if self._is_available(self.states[key_id]):
                self.position = (index + 1) % len(ordered_ids)
                self.states[key_id]["updated_at"] = now_utc()
                save_states(self.checkpoint_path, self.states)
                return key_id, self.key_ids[key_id]
        raise NoUsableKeyError("All API keys are disabled or temporarily rate-limited")

    def record_error(self, key_id: str, error: Exception) -> str:
        state = self.states[key_id]
        category = classify_error(error)
        state["failure_count"] = str(int(state.get("failure_count") or 0) + 1)
        state["last_error"] = str(error)[-1000:]
        state["updated_at"] = now_utc()
        if category == "invalid":
            state["status"] = "disabled"
            state["limited_until"] = ""
        elif category == "rate_limited":
            state["status"] = "rate_limited"
            state["limited_until"] = str(now_timestamp() + self.cooldown_seconds)
        save_states(self.checkpoint_path, self.states)
        return category

    def record_success(self, key_id: str) -> None:
        self.states[key_id].update(status="available", last_error="", updated_at=now_utc())
        save_states(self.checkpoint_path, self.states)


def load_primary_key(path: Path) -> str:
    """Backward-compatible helper retained from Phase 3."""

    return load_key_values(path)[0]
