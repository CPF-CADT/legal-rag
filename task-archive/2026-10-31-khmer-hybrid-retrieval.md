# Task Archive: Khmer Hybrid Retrieval Improvement

Date: 2026-10-31

## Objective

Improve legal search by combining character-based BM25 with SEA-LION dense retrieval.

## Planned flow

```text
User query
→ Khmer normalization
→ Character 2–4 gram BM25
→ SEA-LION dense retrieval
→ Score fusion or RRF
→ Parent-article grouping
→ Full article and official source
```

## Tasks

- Build a character 2–4 gram BM25 index from normalized legal articles.
- Retrieve the top 30 candidates from BM25.
- Retrieve the top 30 candidates from SEA-LION.
- Combine both result lists with RRF or normalized weighted scores.
- Deduplicate results by parent article.
- Return the complete article and matched passage.
- Compare dense, BM25, and hybrid retrieval using the 20-query benchmark.

## Evaluation metrics

- Hit@5
- Recall@5
- MRR@5
- nDCG@5

## Current baseline

The current system uses dense vector ranking only. On the 20-query benchmark, SEA-LION article retrieval achieved:

- Hit@5: 0.95
- Recall@5: 0.925
- MRR@5: 0.775
- nDCG@5: 0.803

## Important decisions

- Do not remove Khmer stop words before testing BM25.
- Do not depend on perfect Khmer word segmentation.
- Preserve original legal text and source references.
- Treat query expansion as a separate experiment because it may introduce topic drift.

## Reference

[Khmer Semantic Search](https://github.com/back-kh/Khmer-Semantic-Search)
