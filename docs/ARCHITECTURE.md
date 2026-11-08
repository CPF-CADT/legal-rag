# LegalRAG architecture

This is the target architecture for the project. It separates reusable
production code from runnable applications, data pipelines, experiments, data,
tests, and deployment files.

The application layer and notebook layout have been migrated to the structure
below. The executable data pipeline remains in its compatibility location
until it is migrated separately.

## Target structure

```text
legal-rag/
├── apps/core/                     # Reusable Python package
│   └── domain.py                  # Shared domain contracts and models
├── apps/
│   ├── api/                       # FastAPI HTTP application
│   ├── telegram-bot/              # Telegram application
│   └── react-client/              # React browser application
├── pipelines/                     # Collection, OCR, preprocessing, indexing
├── experiments/                   # Notebooks and research only
├── data/                          # Runtime and generated artifacts
├── tests/                         # Unit, integration, API, frontend tests
├── deploy/                        # Docker and deployment configuration
├── docs/
├── .env.example
└── README.md
```

## Dependency direction

```text
React client ───────┐
Telegram bot ───────┼──> API contract
                    │
FastAPI API ────────┼──> apps/core
                    │
Pipelines ──────────┘    ├── domain ports
                         └── infrastructure adapters

Experiments ───────────> apps/core and pipeline utilities
```

The core directory contains only shared code used by both applications. It
must not import FastAPI, Telegram, React, notebook code, or deployment tooling.
API-only code stays under `apps/api/`; Telegram-only code stays under
`apps/telegram_bot/`. Experiments may import production code, but production
code must never import experiments.

## Responsibilities

### `apps/core/`

Contains only reusable business contracts and models shared by the API and
Telegram bot. Application-specific services and adapters stay in their app.

### `apps/`

Contains process entry points and delivery concerns. The API exposes HTTP
contracts, the Telegram app handles Telegram updates, and the React app
consumes the API. None of these applications access Chroma or local indexes
directly.

### `pipelines/`

Contains crawling, OCR, cleaning, article transformation, embedding, and index
construction jobs. Pipelines produce artifacts consumed by the applications;
they are not imported by API route handlers.

### `experiments/`

Contains notebooks, retrieval comparisons, chunking investigations, and
evaluation reports. Notebooks are grouped under `experiments/notebooks/` by
purpose. Notebook outputs are not runtime dependencies.

### `data/`

Contains source files, processed legal records, Chroma indexes, checkpoints,
logs, and evaluation fixtures. Secrets do not belong here.

### `deploy/`

Contains Dockerfiles, Compose files, environment templates, and deployment
configuration. Deployment configuration refers to application entry points but
does not contain application business logic.

## Clean-code rules

- Keep route and Telegram handlers thin.
- Put use-case orchestration in `apps/core/application/`.
- Define interfaces in the core domain; keep adapters behind those interfaces.
- Keep framework-specific schemas at the application boundary.
- Do not expose local paths, Chroma objects, prompts, or provider errors in
  public API responses.
- Keep notebooks and experiment helpers out of production imports.
- Treat generated data and indexes as runtime artifacts, not source code.
