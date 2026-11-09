# BM25 pipeline

Build the lexical artifacts from the current OCR corpus:

```bash
cd /Users/nak/CADT/projects/legal-rag
PYTHONPATH=data-pipeline .venv/bin/python -m bm25.pipeline
```

This creates `articles.jsonl` and the article-level `bm25.sqlite3` under
`data/dense_retrieval/`. The generated files are runtime data and are ignored
by Git.

Run the evaluation after adding manually judged article IDs to
`experiments/evaluation/bm25_queries.json`:

```bash
PYTHONPATH=. .venv/bin/python experiments/evaluation/bm25_evaluate.py
```

The evaluator reports Recall@5 and MRR. An empty `relevant_articles` list is
skipped because it is an unlabeled query, not a negative judgment.
