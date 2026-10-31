# Semantic Search

Phase 6 article-level search is implemented in `article-level/semantic_search.ipynb`. It embeds a Khmer user query with each configured model, then returns one combined result object for comparison.

Open `article-level/semantic_search.ipynb` in VS Code after Phase 5 and select the project `.venv` kernel.

Change `query` to test another Khmer legal question. The notebook compares the `sealion` and `granite-r2` collections.

The output includes the rank, similarity distance, article text, article number, document title, and official source URLs. The query uses Unicode NFC and whitespace normalization only; it does not tokenize or segment Khmer.

The chunk-level notebook searches small chunks for precision, then returns the complete parent article together with the matched chunk and official source links.

The sentence-chunk notebook provides the same full-article flow using sentence-based chunks for comparison.
