# NCDD LegalRAG project guide

This guide describes the target project architecture and the current data
workflow. See [ARCHITECTURE.md](ARCHITECTURE.md) for dependency rules.

## Main folders

### `apps/core/`

Shared Python code only: legal domain models and contracts used by both the API
and Telegram bot. API-specific and Telegram-specific code stays in its app.

### `apps/`

Runnable user-facing applications:

- `apps/api/` — FastAPI HTTP service.
- `apps/telegram_bot/` — Telegram polling process and handlers.
- `apps/react-client/` — React browser client.

The applications consume `apps/core`; they do not access Chroma or pipeline
files directly.

### `pipelines/`

Repeatable data jobs for collection, OCR, preprocessing, embeddings, and
indexing. Pipelines create the artifacts used by the applications.

### `experiments/`

Jupyter notebooks and research code for retrieval, chunking, and evaluation.
Current notebook groups are:

- `experiments/notebooks/pipeline/` — the numbered data-processing workflow.
- `experiments/notebooks/dense_retrieval/` — dense-index experiments.
- `experiments/notebooks/test/` — exploratory and evaluation notebooks.

Experiments may import reusable production code, but production code must not
import notebooks or experiment modules.

### `data/`

Runtime and generated artifacts:

- `raw/` — downloaded source PDFs and source files.
- `processed/` — OCR and normalized legal records.
- `indexes/` — Chroma and other search indexes.
- `evaluation/` — test fixtures and relevance judgments.

Do not commit credentials or provider keys under `data/`.

### `tests/`

Tests are organized by boundary: `unit/`, `integration/`, `api/`, and
`frontend/`.

### `deploy/`

Dockerfiles, Compose files, environment templates, and deployment
configuration. Deployment files point to application entry points and do not
contain business logic.

## Current implementation note

The application migration is in progress. The API now runs from
`apps/api/`, reusable Python services live directly under `apps/core/`, the
Telegram runtime is under `apps/telegram_bot/`, and the React client is under
`apps/react-client/`. Notebook code has been moved to `experiments/notebooks/`.
The existing `data-pipeline/` directory remains the pipeline compatibility
location for executable pipeline modules and data artifacts until those jobs
are migrated to `pipelines/`.

## Current pipeline flow

The existing pipeline remains:

```text
NCDD website
    ↓
collection and download jobs
    ↓
downloaded PDFs
    ↓
Gemini OCR in page batches
    ↓
cleaned and structured legal articles
    ↓
BGE-M3 embeddings and Chroma index
    ↓
API and Telegram applications
```

During the eventual migration, these stages belong under `pipelines/` and
write artifacts under `data/`.

## Secrets and runtime data

Use environment variables or mounted secret files for API keys. Keep secrets
out of Git and out of public API responses. Bind-mounted PDFs, OCR output,
checkpoints, logs, and Chroma indexes should be treated as runtime data and
backed up independently from application source code.

## Migration rule

Each remaining migration must update imports, entry points, Docker/Compose
paths, tests, and documentation together, then verify the API, Telegram bot,
and pipeline commands.
