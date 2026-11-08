# Docker Compose runtime

The Compose stack runs three services:

- `chroma` — persistent Chroma HTTP server backed by the existing
  `data/dense_retrieval/chroma_db` index.
- `api` — FastAPI at `http://localhost:8000`.
- `telegram-bot` — long-running Telegram polling process.

The API and bot connect to Chroma through the internal hostname `chroma`. The
retrieval code still supports the existing local embedded Chroma mode when
`CHROMA_HOST` is empty.

## First run

1. Keep the generated root `.env` file.
2. Keep the existing credentials in `apps/telegram-bot/.env` and
   `apps/api/secrets/gemini_api_keys.txt`, or update those files if
   needed.
3. Ensure the prepared article metadata exists under `data/dense_retrieval/`.
4. Start the stack:

```bash
docker compose up -d --build
```

Check status and logs:

```bash
docker compose ps
docker compose logs -f api
docker compose logs -f telegram-bot
```

The API documentation is available at `http://localhost:8000/docs`.

## Stop and reset

Stop containers without deleting Chroma data:

```bash
docker compose down
```

To reset the persisted Chroma index, move the bind-mounted directory aside
after confirming that the index can be rebuilt:

```bash
mv data/dense_retrieval/chroma_db data/dense_retrieval/chroma_db.backup
```

Do this only when the vector index can be rebuilt.
