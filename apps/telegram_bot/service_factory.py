"""Build the Telegram service client."""

from __future__ import annotations

import logging

from apps.core.config import env
from apps.telegram_bot.api_client import LegalRagApiClient


logger = logging.getLogger("legalrag.telegram_bot")


def build_service() -> LegalRagApiClient:
    api_url = env("LEGALRAG_API_URL", "http://api:8000")
    client = LegalRagApiClient(api_url)
    logger.info("api_client_ready base_url=%s", api_url)
    return client
