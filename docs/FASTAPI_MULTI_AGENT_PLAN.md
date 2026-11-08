# LegalRAG FastAPI MVP — Multi-Agent Implementation Plan

## 1. Coordination model

The supervisor keeps the API contract and integration branch stable. Agents work
in isolated worktrees with disjoint write scopes. Each agent must report:

- changed files and commit SHA;
- commands run and exit codes;
- test output or log path;
- blockers and remaining work.

No agent may change the retrieval algorithm, delete existing tests, or weaken
validation to make a test pass.

## 2. Target architecture

```text
HTTP request
  → apps/api/routes.py
  → apps/core/application/search_service.py or summarize_service.py
  → apps/core/domain DTOs and ports
  → apps/core/infrastructure/retrieval_adapter.py
  → Chroma/retrieval adapter

apps/core/application/summarize_service.py
  → apps/core/infrastructure LLM adapter
```

Target package and application boundaries:

```text
apps/core/
  domain/
  application/
  infrastructure/
  config/
  prompts/
apps/api/
  main.py
  dependencies.py
  routes/
  schemas/
tests/api/
tests/unit/
tests/integration/
```

The reusable package is located at `apps/core`. The API owns HTTP schemas and
composition only; business logic belongs in the core package.

## 3. Agent workstreams

### Agent 1 — API architecture and settings

Objective: create the FastAPI application shell, settings, lifespan, health
endpoints, error envelope, and dependency injection boundaries.

Write scope:

- new FastAPI package only;
- API requirements/dependency file entries if needed;
- no changes to existing retriever or Telegram modules.

Non-goals:

- no business route implementation beyond health/readiness;
- no real model loading in unit tests.

Checks:

```bash
python -m compileall <fastapi-package>
pytest tests/api -q
```

### Agent 2 — Search application and adapter

Objective: expose the existing retriever through a framework-independent
application service and map results to the public search response.

Write scope:

- search application service;
- domain search DTOs/ports;
- retrieval adapter;
- search route and its tests.

Non-goals:

- no LLM prompt changes;
- no changes to Chroma index construction;
- no changes to Telegram behavior.

Checks:

```bash
pytest tests/application tests/api -q
```

Important review points:

- return complete article text;
- preserve string article numbers;
- do not expose `local_pdf_path` or `source_text_path`;
- enforce `top_k` bounds;
- use fake retrievers in unit tests.

### Agent 3 — Summarization application and LLM adapter

Objective: expose grounded summarization using the existing `AnswerService` and
generator abstraction.

Write scope:

- summarize application service;
- summarize schemas and route;
- LLM/retrieval port adapters;
- summary tests with fake generator and fake retrieval results.

Non-goals:

- no new prompt behavior unless required to make the HTTP response contract
  explicit;
- no provider-specific credentials in code.

Checks:

```bash
pytest tests/application tests/api -q
```

Important review points:

- preserve insufficient-evidence behavior;
- return sources separately from the summary;
- map provider failures to stable application errors;
- never return prompt text or raw exception text.

### Agent 4 — Test and contract reviewer

Objective: independently test the public API contract and identify gaps in
validation, security, error mapping, and OpenAPI output.

Write scope:

- tests only, unless a tiny test fixture change is required;
- review notes in the handoff.

Checks:

```bash
pytest -q
python -m compileall bot data-pipeline <fastapi-package>
```

Review cases:

- blank and oversized queries;
- `top_k` below 1 and above the maximum;
- missing index/model;
- insufficient evidence;
- LLM timeout/failure;
- response does not leak local paths or secrets;
- OpenAPI contains both endpoint contracts.

### Agent 5 — Integration reviewer

Objective: inspect the combined diff after the implementation agents finish,
resolve interface mismatches, and decide whether the work is safe to merge.

Write scope:

- review and integration fixes only;
- no unrelated refactoring.

Checks:

```bash
pytest -q
python -m compileall .
```

Gate criteria:

- one settings source;
- one dependency/lifespan strategy;
- no circular imports;
- routes contain no retrieval or LLM business logic;
- existing Telegram imports still work;
- all public fields match the PRD;
- failures are stable and non-sensitive.

## 4. Dependency order

```text
Agent 1: application shell/settings
       ├── Agent 2: search
       └── Agent 3: summarize
Agent 2 + Agent 3
       ↓
Agent 4: contract tests
       ↓
Agent 5: integration review
       ↓
Supervisor: final verification and user handoff
```

Agents 2 and 3 can work in parallel after the shared shell and port conventions
are agreed. If parallel agents cannot share the shell safely, Agent 1 must first
commit the DTO/port skeleton and explicitly hand it off.

## 5. Supervisor ledger template

| Agent | Role | Worktree/branch | Commit | Status | Tests | Blocker | Next action |
|---|---|---|---|---|---|---|---|
| 1 | API shell | isolated | — | planned | — | — | implement |
| 2 | Search | isolated | — | planned | — | — | wait for ports |
| 3 | Summarize | isolated | — | planned | — | — | wait for ports |
| 4 | Contract tests | isolated | — | planned | — | — | wait for routes |
| 5 | Integration review | isolated | — | planned | — | — | wait for all commits |

## 6. Delivery sequence

1. Freeze and review the API contract in `FASTAPI_PRD.md`.
2. Add FastAPI dependencies and the application shell.
3. Implement search and summarization services against ports.
4. Add API tests using fakes, then run integration tests with real configured
   dependencies when available.
5. Review the combined diff and update the React client only after the API
   response contract is stable.
6. Document local startup, environment variables, and model/index prerequisites.

## 7. Definition of done

- `POST /api/search` and `POST /api/summarize` work with the current index and
  configured LLM backend.
- Unit tests do not require downloading model weights.
- Integration checks are clearly separated from environment-blocked checks.
- Existing bot and retrieval behavior is preserved.
- OpenAPI documentation is accurate.
- No merge, push, deployment, or external message occurs without explicit user
  authorization.
