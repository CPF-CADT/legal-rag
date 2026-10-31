# Embedding

This folder contains the notebook-based embedding workflow.

## Notebooks

- `embedding_pipeline.ipynb` — shared configuration and output contract.
- `generate_article_embeddings.ipynb` — generate embeddings for complete legal articles.
- `generate_chunk_embeddings.ipynb` — create article chunks and generate chunk embeddings.
- `generate_sentence_chunk_embeddings.ipynb` — experimental sentence-based chunks and embeddings.
- `test/chunking_line_based.ipynb` — archived line-based chunking strategy for comparison.

Both generation notebooks process SEA-LION, Granite R2, LaBSE, and ALBERT and save vectors, aligned metadata, and manifests under `data/processed/embeddings/`.

The active chunker follows IBM's recursive strategy: it tries paragraph breaks, then newlines, spaces, and finally character boundaries. It uses a 1,200-character maximum and 200-character overlap while keeping every chunk inside its parent article.

The sentence-based notebook is a separate experiment. It splits at Khmer sentence punctuation such as `។` and `៕`, groups complete sentences up to 1,200 characters, and writes separate `sentence_chunks_*` embedding files.

Run the notebooks from the project root. Regenerate embeddings after changing normalized text or chunking rules.
