## Semantic Search Plan for LegalRAG

### Goal

Build semantic search over the current dataset:

- 90 JSON documents
- 2,744 legal articles
- Khmer legal article text
- Official document and source metadata

The attached research recommends Khmer character normalization, spelling-aware search, and semantic word modeling. :codex-file-citation{path="/Users/nak/CADT/CADT_Fourth_Year/info-retrival/mer-word-search-challenges-solutions-and-semantic-aware-search.pdf" purpose="source"}

The referenced Khmer semantic-search implementation recommends LaBSE and vector storage with PostgreSQL/pgvector. [Khmer Semantic Search Using Text Embeddings](https://medium.com/@phylypo/khmer-semantic-search-using-text-embeddings-1b20f3e6e00c)

### Phase 1: Prepare article records

Read the existing nested JSON without changing it.

Create records with:

```json
{
  "id": "114-15",
  "text": "...",
  "document_id": "114",
  "article_number": 15,
  "chapter_title": "...",
  "section_title": "...",
  "document_title": "...",
  "source_url": "..."
}
```

Use `document_id-article_number` as the ID.

### Phase 2: Normalize Khmer text

Apply Unicode normalization before embedding:

```text
JSON text
→ Khmer character-order normalization
→ remove invisible noise
→ preserve legal wording
```

Do not automatically correct OCR errors or rewrite legal text.

### Phase 3: Start with unsegmented Khmer

For the first experiment, embed the article text without manually inserting word spaces. The referenced LaBSE experiment found that unsegmented Khmer performed comparably to manually segmented text. [Source](https://medium.com/@phylypo/khmer-semantic-search-using-text-embeddings-1b20f3e6e00c)

### Phase 4: Generate embeddings

Use LaBSE as the first baseline:

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("sentence-transformers/LaBSE")
vector = model.encode(article_text)
```

Generate one vector per normal-sized article.

For very long articles:

```text
long article
→ paragraph chunks
→ one embedding per chunk
→ keep parent article ID
```

### Phase 5: Store vectors

Use PostgreSQL with `pgvector`.

Store:

```text
id
embedding
text
document_id
article_number
chapter_title
section_title
document_title
source_url
```

LaBSE produces 768-dimensional vectors according to the referenced implementation. [Source](https://medium.com/@phylypo/khmer-semantic-search-using-text-embeddings-1b20f3e6e00c)

### Phase 6: Build query search

```text
User query
→ Khmer normalization
→ LaBSE query embedding
→ cosine similarity search
→ top-k article results
→ return article text and official source
```

Return:

- Article number
- Article text
- Document title
- Source PDF or detail URL
- Similarity score

### Phase 7: Evaluate

Create 30–50 Khmer legal queries covering:

- Exact legal terms
- Natural-language questions
- Article-number queries
- Different Khmer spelling forms
- Queries with OCR-like spelling errors

Measure:

- Precision@5
- Recall@5
- MRR
- NDCG

### Production direction

Start with semantic search alone. After evaluation, add BM25 and combine both using hybrid ranking:

```text
BM25 + LaBSE vector search
→ rank fusion
→ final legal results
→ question-answering layer
```

The research supports semantic search, but its examples are not legal-domain evaluations. Therefore, your own Khmer legal query set must decide whether LaBSE is strong enough for production.
