"""Small Telegram and user-data helpers."""

from __future__ import annotations

from telegram import Update


def log_value(value: object) -> str:
    return " ".join(str(value or "").split())


def user_label(update: Update) -> dict[str, str]:
    user = update.effective_user
    chat = update.effective_chat
    return {
        "user_id": str(user.id if user else "unknown"),
        "username": log_value(user.username if user else ""),
        "chat_id": str(chat.id if chat else "unknown"),
        "chat_title": log_value(chat.title if chat else ""),
    }
