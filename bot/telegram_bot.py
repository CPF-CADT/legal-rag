"""Direct Telegram bot integration for the dense-retrieval answer service."""

from __future__ import annotations

import asyncio
import html
import json
import logging
import os
import re
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env", override=True)
sys.path.insert(0, str(PROJECT_ROOT / "data-pipeline"))

from dense_retrieval.retriever import DenseRetriever
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from answer_service import AnswerService
from llm_generator import GeminiTextGenerator


LOG_PATH = Path(__file__).resolve().parent / "logs" / "telegram_bot.log"
logger = logging.getLogger("legalrag.telegram_bot")


def configure_logging() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s - %(message)s"
    )
    file_handler = RotatingFileHandler(
        LOG_PATH,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def log_value(value: object) -> str:
    """Keep one user value on one log line."""
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


def build_service() -> AnswerService:
    retriever = DenseRetriever(project_root=PROJECT_ROOT)
    logger.info("retriever_loading model=%s", retriever.config.model_name)
    retriever.load()
    logger.info(
        "retriever_loaded collection=%s",
        retriever.config.collection_name,
    )
    max_output_tokens = os.environ.get("GEMINI_MAX_OUTPUT_TOKENS", "").strip()
    generator = GeminiTextGenerator(
        api_key=os.environ.get("GEMINI_API_KEY", ""),
        model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        max_output_tokens=int(max_output_tokens) if max_output_tokens else None,
        thinking_budget=int(os.environ.get("GEMINI_THINKING_BUDGET", "0")),
    )
    logger.info(
        "gemini_loaded model=%s max_output_tokens=%s thinking_budget=%s",
        generator.model,
        generator.max_output_tokens,
        generator.thinking_budget,
    )
    return AnswerService(retriever, generator, candidate_count=50, top_k=5)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    del context
    if update.message:
        await update.message.reply_text("👋 សួស្តី! សូមផ្ញើសំណួរច្បាប់ជាភាសាខ្មែរ។")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service: AnswerService = context.application.bot_data["answer_service"]
    if not update.message or not update.message.text:
        return

    question = update.message.text.strip()
    waiting_message = await update.message.reply_text(
        "⏳ សូមរង់ចាំ កំពុងរកចម្លើយ..."
    )
    identity = user_label(update)
    logger.info(
        "question_received user_id=%s username=%s chat_id=%s chat_title=%s query=%s",
        identity["user_id"],
        identity["username"],
        identity["chat_id"],
        identity["chat_title"],
        log_value(question),
    )
    try:
        result = await asyncio.to_thread(service.answer, question)
        response = format_telegram_answer(result)
        logger.info(
            "answer_success user_id=%s chat_id=%s sufficient_evidence=%s sources=%d "
            "input_tokens=%s output_tokens=%s thinking_tokens=%s total_tokens=%s",
            identity["user_id"],
            identity["chat_id"],
            result.has_sufficient_evidence,
            len(result.sources),
            result.usage.get("prompt_token_count", 0),
            result.usage.get("candidates_token_count", 0),
            result.usage.get("thoughts_token_count", 0),
            result.usage.get("total_token_count", 0),
        )
        logger.info(
            "ai_response user_id=%s chat_id=%s answer=%s",
            identity["user_id"],
            identity["chat_id"],
            json.dumps(result.answer, ensure_ascii=False),
        )
    except Exception:
        logger.exception(
            "answer_failed user_id=%s chat_id=%s query=%s",
            identity["user_id"],
            identity["chat_id"],
            log_value(question),
        )
        response = "⚠️ ប្រព័ន្ធមានបញ្ហាបច្ចេកទេស។ សូមព្យាយាមម្តងទៀត។"

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
            "answer_sent user_id=%s chat_id=%s messages=%d",
            identity["user_id"],
            identity["chat_id"],
            len(message_parts),
        )
    except Exception:
        logger.exception(
            "answer_send_failed user_id=%s chat_id=%s",
            identity["user_id"],
            identity["chat_id"],
        )
        try:
            await waiting_message.edit_text(
                "⚠️ ចម្លើយត្រូវបានបង្កើត ប៉ុន្តែការផ្ញើទៅ Telegram មានបញ្ហា។ សូមព្យាយាមម្តងទៀត។"
            )
        except Exception:
            logger.exception("delivery_error_message_failed message_id=%s", waiting_message.message_id)


def format_telegram_answer(result) -> str:
    """Render an answer and its sources as Telegram HTML hyperlinks."""
    answer = sanitize_answer_html(result.answer)
    if not result.has_sufficient_evidence or not result.sources:
        return f"⚖️ {answer}"

    grouped_sources = {}
    for source in result.sources:
        label = source.get("title") or source.get("document_id") or "ប្រភពច្បាប់"
        url = source.get("source_url") or source.get("pdf_url") or ""
        key = (label, url)
        grouped_sources.setdefault(key, [])
        article_number = format_article_number(source.get("article_number"))
        if article_number and article_number not in grouped_sources[key]:
            grouped_sources[key].append(article_number)

    source_lines = []
    for (label, url), article_numbers in grouped_sources.items():
        article_text = " ".join(article_numbers)
        source_label = f"{label} មាត្រា {article_text}" if article_text else label
        if url:
            source_lines.append(
                f'• <a href="{html.escape(url, quote=True)}">{html.escape(source_label)}</a>'
            )
        else:
            source_lines.append(f"• {html.escape(source_label)}")

    return f"⚖️ {answer}\n\n<b>📚 ប្រភព៖</b>\n" + "\n".join(source_lines)


def split_telegram_html(message: str, max_length: int = 3800) -> list[str]:
    """Split HTML only between rendered lines, below Telegram's limit."""
    lines = message.splitlines()
    parts: list[str] = []
    current = ""
    for line in lines:
        candidate = line if not current else f"{current}\n{line}"
        if current and len(candidate) > max_length:
            parts.append(current)
            current = line
        else:
            current = candidate
    if current:
        parts.append(current)

    # A single unusually long line cannot be split safely without breaking a
    # tag. Keep it as one part and let the send error be logged explicitly.
    return parts or [""]


def sanitize_answer_html(answer: str) -> str:
    """Convert safe, limited Markdown from the LLM to Telegram HTML."""
    lines = []
    for raw_line in answer.splitlines():
        line = raw_line.strip()
        heading = re.match(r"^#{1,6}\s+(.+)$", line)
        bullet = re.match(r"^[*+•-]\s+(.+)$", line)
        if heading:
            lines.append(f"<b>{markdown_inline_to_html(heading.group(1))}</b>")
        elif bullet:
            lines.append(f"• {markdown_inline_to_html(bullet.group(1))}")
        else:
            lines.append(markdown_inline_to_html(line))
    return "\n".join(lines)


def markdown_inline_to_html(value: str) -> str:
    """Escape raw HTML, then convert only the Markdown syntax we support."""
    safe = html.escape(value, quote=False)
    placeholders: dict[str, str] = {}

    def protect(match: re.Match[str]) -> str:
        key = f"\x00{len(placeholders)}\x00"
        placeholders[key] = f"<code>{match.group(1)}</code>"
        return key

    safe = re.sub(r"`([^`\n]+)`", protect, safe)
    safe = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe)
    safe = re.sub(r"__(.+?)__", r"<b>\1</b>", safe)
    safe = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<i>\1</i>", safe)
    safe = re.sub(r"(?<!_)_([^_\n]+)_(?!_)", r"<i>\1</i>", safe)
    for key, replacement in placeholders.items():
        safe = safe.replace(key, replacement)
    return safe


def format_article_number(value: object) -> str:
    """Keep only the article number and remove trailing punctuation."""
    text = " ".join(str(value or "").split())
    if not text or text.lower() in {"document", "preamble"}:
        return ""
    match = re.search(r"មាត្រា\s*([០-៩0-9]+)", text, flags=re.IGNORECASE)
    if match:
        text = match.group(1).rstrip(".-៖:;")
    else:
        text = text.rstrip(".-៖:;")

    # Article numbers in the index may be Python integers. Telegram output
    # should consistently use Khmer digits, for example 25 -> ២៥.
    return text.translate(str.maketrans("0123456789", "០១២៣៤៥៦៧៨៩"))


def main() -> None:
    configure_logging()
    logger.info("bot_starting project_root=%s", PROJECT_ROOT)
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        logger.error("bot_start_failed reason=TELEGRAM_BOT_TOKEN_missing")
        raise SystemExit("TELEGRAM_BOT_TOKEN is required")

    try:
        application = Application.builder().token(token).build()
        application.bot_data["answer_service"] = build_service()
    except Exception:
        logger.exception("bot_start_failed reason=service_initialization")
        raise

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("bot_start_success log_file=%s", LOG_PATH)
    application.run_polling()


if __name__ == "__main__":
    main()
