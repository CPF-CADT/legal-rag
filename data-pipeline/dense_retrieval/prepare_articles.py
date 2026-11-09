"""Prepare cleaned, normalized, structure-aware article records."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from apps.core.retrieval_config import PipelineConfig
from .io_utils import write_jsonl
from .legal_parser import parse_document
from apps.core.shared.normalization import normalize_khmer

def load_documents(path: Path) -> dict[str, dict[str, str]]:
    with path.open('r', encoding='utf-8-sig', newline='') as stream:
        return {str(row['document_id']).strip(): row for row in csv.DictReader(stream) if row.get('document_id')}

def prepare_articles(
    config: PipelineConfig,
    ocr_paths: list[Path] | None = None,
    extra_articles: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    documents = load_documents(config.documents_csv)
    records: list[dict[str, Any]] = []
    paths = ocr_paths if ocr_paths is not None else list(config.ocr_dir.glob('*.txt'))
    for text_path in sorted(paths, key=lambda item: item.name):
        document_id = text_path.stem
        document = documents.get(document_id)
        if document is None:
            continue
        raw_text = text_path.read_text(encoding='utf-8-sig', errors='replace')
        preamble, articles, _chapters = parse_document(raw_text)
        # Match the original preprocessing notebook: documents without a
        # reliable article boundary are skipped instead of indexing an entire
        # noisy document as one article.
        if not articles:
            continue
        for index, article in enumerate(articles, start=1):
            text = normalize_khmer(article['text'])
            if not text:
                continue
            title = normalize_khmer(document.get('title', ''))
            article_number = article['article_number']
            records.append({
                'article_id': f'{document_id}-article-{index}',
                'document_id': document_id,
                'article_number': article_number,
                'chapter_number': article.get('chapter_number'),
                'chapter_title': normalize_khmer(article.get('chapter_title', '')),
                'section_number': article.get('section_number'),
                'section_title': normalize_khmer(article.get('section_title', '')),
                'title': title,
                'document_type': normalize_khmer(document.get('document_type', '')),
                'domain': normalize_khmer(document.get('category', '')),
                'publication_date': document.get('publication_date', '') or document.get('publication_year', ''),
                'source_url': document.get('detail_url') or document.get('pdf_url', ''),
                'pdf_url': document.get('pdf_url', ''),
                'text_file': str(text_path),
                'preamble': normalize_khmer(preamble),
                'text': text,
                'search_text': normalize_khmer(f'{title}\n{article_number}\n{text}'),
                'normalization_version': 'legal-cleaning-v1-khmer-normalization-v2',
            })
    records.extend(extra_articles or [])
    write_jsonl(config.article_path, records)
    return records
