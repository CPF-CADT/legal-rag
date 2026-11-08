"""Telegram command and message handlers."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from apps.telegram_bot.formatting import format_telegram_answer, split_telegram_html
from apps.telegram_bot.helpers import user_label
from apps.telegram_bot.logging_setup import write_rag_llm_log


logger = logging.getLogger("legalrag.telegram_bot")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    del context
    if update.message:
        await update.message.reply_text("👋 សួស្តី! សូមផ្ញើសំណួរច្បាប់ជាភាសាខ្មែរ។")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service: Any = context.application.bot_data["answer_service"]
    if not update.message or not update.message.text:
        return

    question = update.message.text.strip()
    waiting_message = await update.message.reply_text("⏳ សូមរង់ចាំ កំពុងរកចម្លើយ...")
    identity = user_label(update)
    result = None
    error_message = ""
    error_context = ""
    error_sources: list[dict[str, Any]] = []
    logger.info(
        "question_received user_id=%s username=%s chat_id=%s chat_title=%s",
        identity["user_id"], identity["username"], identity["chat_id"],
        identity["chat_title"],
    )

    try:
        result = await asyncio.to_thread(service.answer, question)
        response = format_telegram_answer(result)
        logger.info(
            "answer_success user_id=%s chat_id=%s sufficient_evidence=%s sources=%s "
            "input_tokens=%s output_tokens=%s thinking_tokens=%s total_tokens=%s",
            identity["user_id"], identity["chat_id"], result.has_sufficient_evidence,
            len(result.sources), result.usage.get("prompt_token_count", 0),
            result.usage.get("candidates_token_count", 0),
            result.usage.get("thoughts_token_count", 0),
            result.usage.get("total_token_count", 0),
        )
        logger.info("ai_response user_id=%s chat_id=%s", identity["user_id"], identity["chat_id"])
    except Exception as exc:
        error_message = f"{type(exc).__name__}: {exc}"
        error_context = getattr(exc, "context", "")
        error_sources = getattr(exc, "sources", [])
        logger.exception(
            "answer_failed user_id=%s chat_id=%s",
            identity["user_id"], identity["chat_id"],
        )
        response = "⚠️ ប្រព័ន្ធមានបញ្ហាបច្ចេកទេស។ សូមព្យាយាមម្តងទៀត។"

    try:
        write_rag_llm_log({
            "status": "success" if result is not None else "error",
            "user_id": identity["user_id"],
            "chat_id": identity["chat_id"],
            "username": identity["username"],
            "question": question,
            "retrieved_context": result.retrieved_context if result else error_context,
            "sources": result.sources if result else error_sources,
            "llm_answer": result.answer if result else "",
            "has_sufficient_evidence": result.has_sufficient_evidence if result else False,
            "usage": result.usage if result else {},
            "error": error_message,
        })
    except Exception:
        logger.exception(
            "rag_llm_json_log_failed user_id=%s chat_id=%s",
            identity["user_id"], identity["chat_id"],
        )

    try:
        message_parts = split_telegram_html(response)
        for part in message_parts:
            await update.message.reply_text(
                part,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=False,
            )
        await context.bot.delete_message(
            chat_id=waiting_message.chat_id,
            message_id=waiting_message.message_id,
        )
        logger.info(
            "answer_sent user_id=%s chat_id=%s messages=%s",
            identity["user_id"], identity["chat_id"], len(message_parts),
        )
    except Exception:
        logger.exception(
            "answer_send_failed user_id=%s chat_id=%s",
            identity["user_id"], identity["chat_id"],
        )
        try:
            await waiting_message.edit_text(
                "⚠️ ចម្លើយត្រូវបានបង្កើត ប៉ុន្តែការផ្ញើទៅ Telegram មានបញ្ហា។ សូមព្យាយាមម្តងទៀត។"
            )
        except Exception:
            logger.exception(
                "delivery_error_message_failed message_id=%s",
                waiting_message.message_id,
            )
