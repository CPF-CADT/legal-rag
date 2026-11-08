"""FastAPI application factory, lifespan, routes, and stable errors."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from collections import defaultdict, deque
import time
import threading
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .application import SearchService, SummarizeService
from .config import Settings
from .infrastructure import build_runtime
from .schemas import FilterOptionsResponse, HealthResponse, QueryRequest, ReadyResponse, SearchResponse, SummarizeResponse
from apps.api.domain import AnswerPort, LLMUnavailableError, RetrievalUnavailableError, RetrieverPort

logger = logging.getLogger(__name__)


@dataclass
class AppState:
    settings: Settings
    retriever: RetrieverPort | None = None
    answer_service: AnswerPort | None = None
    startup_error: Exception | None = None
    filter_options: FilterOptionsResponse | None = None
    filter_options_expires_at: float = 0.0
    filter_options_lock: threading.Lock = field(default_factory=threading.Lock)


class RateLimiter:
    def __init__(self, limit_per_minute: int) -> None:
        self.limit = limit_per_minute
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        if self.limit <= 0:
            return True
        now = time.monotonic()
        requests = self._requests[key]
        while requests and now - requests[0] >= 60:
            requests.popleft()
        if len(requests) >= self.limit:
            return False
        requests.append(now)
        return True


def _error_response(request: Request, code: str, message: str, status_code: int) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid4()))
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "request_id": request_id}},
        headers={"X-Request-ID": request_id},
    )


def create_app(
    settings: Settings | None = None,
    *,
    retriever: RetrieverPort | None = None,
    answer_service: AnswerPort | None = None,
) -> FastAPI:
    app_settings = settings or Settings.from_environment()
    state = AppState(app_settings, retriever, answer_service)
    rate_limiter = RateLimiter(app_settings.rate_limit_per_minute)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        if state.retriever is None or state.answer_service is None:
            try:
                state.retriever, state.answer_service = build_runtime(app_settings)
            except Exception as exc:
                state.startup_error = exc
                logger.exception("legalrag_startup_failed")
        yield

    app = FastAPI(
        title="LegalRAG API",
        version="1.0.0",
        description="Semantic search and grounded Khmer legal summaries.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(app_settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-API-Key", "X-Request-ID"],
    )
    app.state.runtime = state

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request.state.request_id = request.headers.get("X-Request-ID", str(uuid4()))
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.middleware("http")
    async def access_control_middleware(request: Request, call_next):
        if request.url.path.startswith("/api/"):
            if app_settings.api_key:
                supplied_key = request.headers.get("X-API-Key", "")
                if supplied_key != app_settings.api_key:
                    return _error_response(request, "UNAUTHORIZED", "invalid API key", 401)
            client_key = request.client.host if request.client else "unknown"
            if not rate_limiter.allow(client_key):
                return _error_response(request, "RATE_LIMITED", "request limit exceeded", 429)
        return await call_next(request)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, _exc: RequestValidationError):
        return _error_response(request, "VALIDATION_ERROR", "invalid request data", 422)

    @app.exception_handler(Exception)
    async def unexpected_exception_handler(request: Request, _exc: Exception):
        logger.exception("legalrag_unhandled_error")
        return _error_response(request, "INTERNAL_ERROR", "an unexpected error occurred", 500)

    @app.get("/health", response_model=HealthResponse, tags=["operations"])
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.get("/ready", response_model=ReadyResponse, tags=["operations"])
    def ready(request: Request) -> ReadyResponse:
        runtime: AppState = request.app.state.runtime
        if runtime.startup_error or runtime.retriever is None or runtime.answer_service is None:
            return _error_response(
                request,
                "RETRIEVAL_UNAVAILABLE",
                "application dependencies are not ready",
                503,
            )
        return ReadyResponse(status="ready")

    @app.post("/api/search", response_model=SearchResponse, tags=["legal"])
    def search(payload: QueryRequest, request: Request) -> SearchResponse | JSONResponse:
        runtime: AppState = request.app.state.runtime
        if len(payload.query) > runtime.settings.max_query_length:
            return _error_response(request, "VALIDATION_ERROR", "query is too long", 422)
        if runtime.retriever is None:
            return _error_response(request, "RETRIEVAL_UNAVAILABLE", "retrieval is unavailable", 503)
        try:
            return SearchService(runtime.retriever, runtime.settings).search(
                payload.query, payload.top_k, payload.filters
            )
        except Exception:
            logger.exception("legalrag_search_failed")
            return _error_response(request, "RETRIEVAL_UNAVAILABLE", "retrieval is unavailable", 503)

    @app.get("/api/filters", response_model=FilterOptionsResponse, tags=["legal"])
    def filters(request: Request) -> FilterOptionsResponse | JSONResponse:
        runtime: AppState = request.app.state.runtime
        if runtime.retriever is None:
            return _error_response(request, "RETRIEVAL_UNAVAILABLE", "retrieval is unavailable", 503)
        now = time.monotonic()
        if runtime.filter_options is not None and now < runtime.filter_options_expires_at:
            return runtime.filter_options
        try:
            with runtime.filter_options_lock:
                now = time.monotonic()
                if runtime.filter_options is None or now >= runtime.filter_options_expires_at:
                    values = runtime.retriever.filter_options()
                    runtime.filter_options = FilterOptionsResponse(**values)
                    runtime.filter_options_expires_at = now + runtime.settings.filter_cache_ttl_seconds
            return runtime.filter_options
        except Exception:
            logger.exception("legalrag_filter_options_failed")
            return _error_response(request, "RETRIEVAL_UNAVAILABLE", "filter options unavailable", 503)

    @app.post("/api/summarize", response_model=SummarizeResponse, tags=["legal"])
    def summarize(payload: QueryRequest, request: Request) -> SummarizeResponse | JSONResponse:
        runtime: AppState = request.app.state.runtime
        if len(payload.query) > runtime.settings.max_query_length:
            return _error_response(request, "VALIDATION_ERROR", "query is too long", 422)
        if runtime.answer_service is None:
            return _error_response(request, "LLM_UNAVAILABLE", "summary generation is unavailable", 502)
        try:
            return SummarizeService(runtime.answer_service).summarize(payload.query, payload.top_k)
        except RetrievalUnavailableError:
            logger.exception("legalrag_summary_retrieval_failed")
            return _error_response(request, "RETRIEVAL_UNAVAILABLE", "retrieval is unavailable", 503)
        except LLMUnavailableError:
            logger.exception("legalrag_summary_llm_failed")
            return _error_response(request, "LLM_UNAVAILABLE", "summary generation is unavailable", 502)
        except Exception:
            logger.exception("legalrag_summary_failed")
            return _error_response(request, "LLM_UNAVAILABLE", "summary generation is unavailable", 502)

    return app


app = create_app()
