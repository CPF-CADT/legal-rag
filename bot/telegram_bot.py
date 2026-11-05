"""Application entry point for the Legal RAG Telegram bot."""

from __future__ import annotations

import logging

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from config import env, load_environment
from logging_setup import LOG_PATH, configure_logging
from service_factory import build_service
from telegram_handlers import handle_message, start


logger = logging.getLogger("legalrag.telegram_bot")


def main() -> None:
    load_environment()
    configure_logging()
    logger.info("bot_starting")
    token = env("TELEGRAM_BOT_TOKEN")
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
