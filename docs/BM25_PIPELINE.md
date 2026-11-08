# BM25 pipeline

Build the lexical artifacts from the current OCR corpus:

```bash
cd /Users/nak/CADT/projects/legal-rag
PYTHONPATH=data-pipeline .venv/bin/python -m bm25.build_pipeline
```

This creates `articles.jsonl`, `chunks.jsonl`, and `bm25.sqlite3` under
`data/dense_retrieval/`. The generated files are runtime data and are ignored
by Git.

Run the evaluation after adding manually judged article IDs to
`experiments/evaluation/bm25_queries.json`:

```bash
PYTHONPATH=data-pipeline .venv/bin/python -m bm25.evaluate
```

The evaluator reports Recall@5 and MRR. An empty `relevant_articles` list is
skipped because it is an unlabeled query, not a negative judgment.
