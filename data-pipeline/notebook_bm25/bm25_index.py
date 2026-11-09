"""Raw/token inverted indexes and configurable Okapi BM25 article search."""

from collections import Counter
from pathlib import Path
from collections.abc import Sequence
from typing import Any, TYPE_CHECKING
import hashlib
import math

if TYPE_CHECKING:
    from text_pipeline import Analyzer
from typing import Iterable, Mapping
import json


def canonical_id(article: Mapping) -> str:
    """Use the same article ID rule as dense notebooks 08 and 09."""
    if article.get('article_id'):
        return str(article['article_id'])
    if article.get('document_id') is None or article.get('article_number') is None:
        raise ValueError('Article needs article_id or document_id and article_number')
    return f"{article['document_id']}-{article['article_number']}"


class InvertedIndex:
    """Store raw tokens, per-document frequencies, and document lengths."""

    def __init__(self) -> None:
        """Create an empty index."""
        self.tokenization = 'str.split'
        self.postings: dict[str, dict[str, int]] = {}
        self.document_lengths: dict[str, int] = {}

    @classmethod
    def build(cls, articles: Iterable[Mapping]) -> 'InvertedIndex':
        """Keep the longest raw text per canonical ID, then split on whitespace."""
        selected: dict[str, str] = {}
        for article in articles:
            article_id = canonical_id(article)
            text = article['text']
            if not isinstance(text, str):
                raise ValueError(f'Text must be a string: {article_id}')
            if article_id not in selected or len(text) > len(selected[article_id]):
                selected[article_id] = text
        index = cls()
        for article_id, text in selected.items():
            index._add_tokens(article_id, text.split())
        return index

    def _add_tokens(self, document_id: str, tokens: Sequence[str]) -> None:
        """Add one document's existing tokens to the shared posting structures."""
        if document_id in self.document_lengths:
            raise ValueError(f'Duplicate internal document ID: {document_id}')
        if any(not isinstance(token, str) or not token or any(char.isspace() for char in token)
               for token in tokens):
            raise ValueError('Tokens must be nonempty strings without whitespace')
        self.document_lengths[document_id] = len(tokens)
        for token, frequency in Counter(tokens).items():
            self.postings.setdefault(token, {})[document_id] = frequency

    @classmethod
    def from_tokens(cls, documents: Mapping[str, Sequence[str]]) -> 'InvertedIndex':
        """Index precomputed tokens by unique internal record ID without reanalysis."""
        index = cls()
        index.tokenization = 'preprocessed_tokens'
        for document_id, tokens in documents.items():
            index._add_tokens(str(document_id), tokens)
        return index

    @property
    def total_documents(self) -> int:
        """Return the number of unique canonical articles, including empty ones."""
        return len(self.document_lengths)

    @property
    def average_document_length(self) -> float:
        """Return mean whitespace-token count, or zero for an empty index."""
        return sum(self.document_lengths.values()) / self.total_documents if self.total_documents else 0.0

    @property
    def document_frequencies(self) -> dict[str, int]:
        """Count how many documents contain each token."""
        return {token: len(postings) for token, postings in self.postings.items()}

    @property
    def collection_frequencies(self) -> dict[str, int]:
        """Count every occurrence of each token across the collection."""
        return {token: sum(postings.values()) for token, postings in self.postings.items()}

    def boolean_and(self, tokens: Iterable[str]) -> list[str]:
        """Return sorted IDs containing every exact token; an empty query returns none."""
        terms = set(tokens)
        if not terms:
            return []
        posting_lists = sorted((self.postings.get(term, {}) for term in terms), key=len)
        matches = set(posting_lists[0])
        for postings in posting_lists[1:]:
            matches.intersection_update(postings)
        return sorted(matches)

    def save(self, directory: Path) -> None:
        """Save postings, lengths, and corpus statistics as readable UTF-8 JSON."""
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        payload = {
            'format_version': 1,
            'tokenization': self.tokenization,
            'postings': self.postings,
            'document_lengths': self.document_lengths,
            'total_documents': self.total_documents,
            'average_document_length': self.average_document_length,
            'document_frequencies': self.document_frequencies,
        }
        (directory / 'index.json').write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')

    @classmethod
    def load(cls, directory: Path) -> 'InvertedIndex':
        """Reload a saved index and check its stored corpus statistics."""
        payload = json.loads((Path(directory) / 'index.json').read_text(encoding='utf-8'))
        if payload['format_version'] != 1 or payload['tokenization'] not in {'str.split', 'preprocessed_tokens'}:
            raise ValueError('Unsupported index format or tokenizer')
        index = cls()
        index.tokenization = payload['tokenization']
        index.postings = payload['postings']
        index.document_lengths = payload['document_lengths']
        if (payload['total_documents'] != index.total_documents
                or payload['average_document_length'] != index.average_document_length
                or payload['document_frequencies'] != index.document_frequencies):
            raise ValueError('Saved index statistics do not match its contents')
        return index


class BM25:
    """Score token queries with Okapi BM25 and positive Lucene-style IDF."""

    def __init__(self, index: InvertedIndex, k1: float = 1.5, b: float = 0.75) -> None:
        """Choose scoring parameters without modifying or rebuilding the index."""
        if not math.isfinite(k1) or k1 < 0:
            raise ValueError('k1 must be finite and nonnegative')
        if not math.isfinite(b) or not 0 <= b <= 1:
            raise ValueError('b must be finite and between zero and one')
        self.index = index
        self.k1 = k1
        self.b = b
        self.document_frequencies = index.document_frequencies
        self.average_length = index.average_document_length

    def idf(self, term: str) -> float:
        """Return ln(1 + (N - df + 0.5)/(df + 0.5)); return zero for an empty index."""
        count = self.index.total_documents
        frequency = self.document_frequencies.get(term, 0)
        return math.log1p((count - frequency + 0.5) / (frequency + 0.5)) if count else 0.0

    def term_score(self, term: str, frequency: int, document_length: int) -> float:
        """Calculate one occurrence of a query term's BM25 contribution."""
        if frequency == 0 or self.average_length == 0:
            return 0.0
        length_factor = 1 - self.b + self.b * document_length / self.average_length
        return self.idf(term) * frequency * (self.k1 + 1) / (frequency + self.k1 * length_factor)

    def scores(self, query_tokens: Iterable[str]) -> dict[str, float]:
        """Visit only matching postings; repeated query terms contribute repeatedly."""
        scores: dict[str, float] = {}
        for term, query_frequency in Counter(query_tokens).items():
            for record_id, frequency in self.index.postings.get(term, {}).items():
                partial = self.term_score(term, frequency, self.index.document_lengths[record_id])
                scores[record_id] = scores.get(record_id, 0.0) + query_frequency * partial
        return scores

    def score(self, query_tokens: Iterable[str], record_id: str) -> float:
        """Score one indexed record, including zero contributions for absent terms."""
        length = self.index.document_lengths[record_id]
        return sum(query_frequency * self.term_score(term, self.index.postings.get(term, {}).get(record_id, 0), length)
                   for term, query_frequency in Counter(query_tokens).items())

    def contributions(self, query_tokens: Iterable[str], record_id: str) -> list[dict[str, Any]]:
        """Describe tf, df, IDF, query frequency, and partial score for each unique term."""
        length = self.index.document_lengths[record_id]
        rows = []
        for term, query_frequency in Counter(query_tokens).items():
            frequency = self.index.postings.get(term, {}).get(record_id, 0)
            rows.append({'term': term, 'tf': frequency, 'df': self.document_frequencies.get(term, 0),
                         'idf': self.idf(term), 'query_frequency': query_frequency,
                         'partial_score': query_frequency * self.term_score(term, frequency, length)})
        return rows


def naive_bm25(documents: Mapping[str, Sequence[str]], query_tokens: Sequence[str],
               k1: float = 1.5, b: float = 0.75) -> dict[str, float]:
    """Independently scan every token list for BM25, without using postings or BM25 methods."""
    if not math.isfinite(k1) or k1 < 0 or not math.isfinite(b) or not 0 <= b <= 1:
        raise ValueError('Require finite k1 >= 0 and 0 <= b <= 1')
    total = len(documents)
    average = sum(len(tokens) for tokens in documents.values()) / total if total else 0.0
    query_counts = Counter(query_tokens)
    frequencies = {term: sum(term in tokens for tokens in documents.values()) for term in query_counts}
    result = {}
    for record_id, tokens in documents.items():
        score = 0.0
        for term, query_frequency in query_counts.items():
            frequency = tokens.count(term)
            if frequency and average:
                df = frequencies[term]
                idf = math.log(1 + (total - df + 0.5) / (df + 0.5))
                denominator = frequency + k1 * (1 - b + b * len(tokens) / average)
                score += query_frequency * idf * frequency * (k1 + 1) / denominator
        result[record_id] = score
    return result


HASH_BLOCK_BYTES = 1024 * 1024  # Read one MiB at a time to hash large saved files.


def file_sha256(path: Path) -> str:
    """Fingerprint an artifact without loading its whole contents into memory."""
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(HASH_BLOCK_BYTES), b''):
            digest.update(block)
    return digest.hexdigest()


class BM25Searcher:
    """Load a verified token index and return dense-compatible canonical article results."""

    @staticmethod
    def build_index(tokens_path: Path, articles_path: Path, preprocess_config_path: Path,
                    index_dir: Path, analyzer: 'Analyzer | None' = None) -> dict[str, Any]:
        """Save a parameter-independent index, record metadata, and analyzer manifest."""
        from text_pipeline import Analyzer, read_jsonl
        analyzer = analyzer if analyzer is not None else Analyzer.from_config(preprocess_config_path)
        analyzer.assert_compatible(preprocess_config_path)
        tokens = read_jsonl(tokens_path)
        articles = read_jsonl(articles_path)
        if len(tokens) != len(articles):
            raise ValueError('Token and raw article record counts differ; rerun notebook 02')
        documents, records = BM25Searcher._align_records(tokens, articles)
        index = InvertedIndex.from_tokens(documents)
        index.save(index_dir)
        records_path = index_dir / 'records.jsonl'
        with records_path.open('w', encoding='utf-8') as output:
            for record_id, article in records.items():
                output.write(json.dumps({'record_id': record_id, 'article': article}, ensure_ascii=False) + '\n')
        manifest = BM25Searcher._manifest(index, records, analyzer.config())
        manifest['files'] = {name: file_sha256(index_dir / name) for name in ['index.json', 'records.jsonl']}
        manifest['input_sha256'] = {'articles_tokens.jsonl': file_sha256(tokens_path),
                                    'articles.jsonl': file_sha256(articles_path)}
        (index_dir / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        return manifest

    @staticmethod
    def _align_records(tokens: Sequence[Mapping], articles: Sequence[Mapping]) -> tuple[dict, dict]:
        """Validate source positions and canonical IDs before attaching article metadata."""
        documents, records = {}, {}
        for position, token_record in enumerate(tokens):
            source_index = token_record.get('source_record_index', position)
            if not isinstance(source_index, int) or not 0 <= source_index < len(articles):
                raise ValueError(f'Invalid source_record_index: {source_index}')
            record_id = str(source_index)
            article = dict(articles[source_index])
            article_id = canonical_id(article)
            if record_id in records or str(token_record['article_id']) != article_id:
                raise ValueError(f'Duplicate record or mismatched canonical article ID: {record_id}')
            article['article_id'] = article_id
            documents[record_id] = token_record['tokens']
            records[record_id] = article
        return documents, records

    @staticmethod
    def _manifest(index: InvertedIndex, records: Mapping, config: Mapping) -> dict[str, Any]:
        """Record corpus counting, collapse rules, and the exact analyzer configuration."""
        return {'schema_version': 1, 'analyzer_config': dict(config),
                'document_count': index.total_documents,
                'canonical_article_count': len({article['article_id'] for article in records.values()}),
                'document_unit': 'input record; duplicates contribute separately to N and df',
                'collapse_policy': 'highest record score per canonical article_id; never sum duplicates',
                'query_term_policy': 'each occurrence contributes; repeated query terms repeat scores',
                'tie_policy': 'descending score, then canonical article_id, then internal record_id',
                'index_tokenization': 'preprocessed_tokens'}

    def __init__(self, index_dir: Path, preprocess_config_path: Path,
                 analyzer: 'Analyzer | None' = None, k1: float = 1.5, b: float = 0.75) -> None:
        """Verify manifest/config/artifacts, then choose BM25 parameters at query time."""
        from text_pipeline import Analyzer, read_jsonl
        self.config_path = Path(preprocess_config_path)
        self.manifest = json.loads((index_dir / 'manifest.json').read_text(encoding='utf-8'))
        if self.manifest.get('schema_version') != 1:
            raise ValueError('Unsupported BM25 index manifest version')
        self.analyzer = analyzer if analyzer is not None else Analyzer.from_config(self.config_path)
        self._check_analyzer()
        for name in ['index.json', 'records.jsonl']:
            if self.manifest['files'].get(name) != file_sha256(index_dir / name):
                raise ValueError(f'BM25 index artifact does not match manifest: {name}; rebuild notebook 03')
        self.index = InvertedIndex.load(index_dir)
        rows = read_jsonl(index_dir / 'records.jsonl')
        self.records = {row['record_id']: row['article'] for row in rows}
        self._check_records(len(rows))
        self.scorer = BM25(self.index, k1=k1, b=b)

    def _check_analyzer(self) -> None:
        """Reject stale preprocessing, altered query settings, or a mismatched manifest."""
        saved = json.loads(self.config_path.read_text(encoding='utf-8'))
        indexed = self.manifest['analyzer_config']
        if saved != indexed:
            raise ValueError('Index manifest analyzer settings differ from preprocess_config.json; rebuild notebook 03')
        self.analyzer.assert_compatible(self.config_path)

    def _check_records(self, row_count: int) -> None:
        """Ensure saved metadata and the manifest cover exactly the indexed records."""
        canonical_count = len({article['article_id'] for article in self.records.values()})
        if (row_count != len(self.records) or set(self.records) != set(self.index.document_lengths)
                or self.index.total_documents != self.manifest['document_count']
                or canonical_count != self.manifest['canonical_article_count']
                or self.index.tokenization != self.manifest['index_tokenization']):
            raise ValueError('BM25 index records or counts differ from manifest; rebuild notebook 03')

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Rank every matching record, then keep the best record per canonical article."""
        if not isinstance(top_k, int) or top_k < 0:
            raise ValueError('top_k must be a nonnegative integer')
        self._check_analyzer()
        tokens = self.analyzer.analyze(query)
        scores = self.scorer.scores(tokens)
        ranked = sorted(scores, key=lambda record_id: (-scores[record_id], self.records[record_id]['article_id'], record_id))
        grouped: dict[str, list[str]] = {}
        for record_id in ranked:
            grouped.setdefault(self.records[record_id]['article_id'], []).append(record_id)
        output = []
        for rank, (article_id, record_ids) in enumerate(list(grouped.items())[:top_k], start=1):
            output.append(self._result(rank, article_id, record_ids, scores, tokens))
        return output

    def _result(self, rank: int, article_id: str, record_ids: Sequence[str],
                scores: Mapping[str, float], tokens: Sequence[str]) -> dict[str, Any]:
        """Preserve notebook 08's result fields and add score and matched_terms."""
        best_id = record_ids[0]
        article = self.records[best_id]
        terms = [term for term in dict.fromkeys(tokens) if best_id in self.index.postings.get(term, {})]
        matches = [{'chunk_id': f'bm25-record-{record_id}',
                    'chunk_text': self.records[record_id]['text'], 'distance': None}
                   for record_id in record_ids[:2]]
        return {'rank': rank, 'article_id': article_id, 'title': article.get('document_title'),
                'document_id': article.get('document_id'), 'article_number': article.get('article_number'),
                'full_article': article.get('text', ''), 'matched_chunks': matches,
                'source_url': article.get('source_url'), 'pdf_url': article.get('pdf_url'),
                'score': scores[best_id], 'matched_terms': terms}

    def explain(self, query: str, article_id: str) -> dict[str, Any]:
        """Print each term's contribution for the highest-scoring record of an article."""
        self._check_analyzer()
        tokens = self.analyzer.analyze(query)
        candidates = [record_id for record_id, article in self.records.items() if article['article_id'] == str(article_id)]
        if not candidates:
            raise KeyError(f'Unknown canonical article ID: {article_id}')
        scored = {record_id: self.scorer.score(tokens, record_id) for record_id in candidates}
        best_id = min(candidates, key=lambda record_id: (-scored[record_id], record_id))
        terms = self.scorer.contributions(tokens, best_id)
        print(f'Article {article_id}, best record {best_id}, length {self.index.document_lengths[best_id]}')
        print('term | query frequency | tf | df | IDF | partial score')
        for row in terms:
            print(f"{row['term']!r} | {row['query_frequency']} | {row['tf']} | {row['df']} | {row['idf']:.12f} | {row['partial_score']:.12f}")
        print(f'Total: {scored[best_id]:.12f}')
        return {'article_id': str(article_id), 'record_id': best_id, 'score': scored[best_id], 'terms': terms}
