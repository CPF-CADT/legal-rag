# Search evaluation

This folder contains the manually verified test queries and the retrieval evaluation notebook.

- `search_queries.json` — realistic Khmer queries with expected article IDs.
- `search_evaluation.ipynb` — runs article-level, recursive-chunk, and sentence-chunk search for SEA-LION and Granite R2.

Metrics:

- `Hit@5` — whether at least one expected article appears in the top five.
- `Recall@5` — how many expected articles appear in the top five.
- `MRR` — how early the first expected result appears.
- `nDCG@5` — ranking quality when more than one expected article is relevant.

Review the expected IDs before using the scores as a final benchmark. Add more queries from different legal domains before selecting a production search method.
