# Vector Storage

Phase 5 stores article-level and chunk-level embeddings in persistent ChromaDB collections. The article or chunk text is stored as the Chroma document, while identifiers, titles, article numbers, and source URLs are stored as metadata.

Install ChromaDB in the project environment:

```bash
pip install chromadb
```

Open and run the notebooks from the project root:

- `store_article_embeddings.ipynb` — stores article-level vectors.
- `store_chunk_embeddings.ipynb` — stores chunk-level vectors.
- `store_sentence_chunk_embeddings.ipynb` — stores sentence-based chunk vectors.

ChromaDB is persisted at:

```text
data-pipeline/data/processed/chroma_db/
```

Each model and level uses a separate collection because vector spaces differ. Running the notebook again safely updates records using their existing article or chunk IDs.
