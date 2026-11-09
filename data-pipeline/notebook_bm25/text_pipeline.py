"""Shared document/query analyzer for the BM25 track.

The two normalization functions and their constants are copied verbatim from
notebooks/05_normalize_articles.ipynb. Their signatures intentionally stay intact.
"""

from collections import Counter
from functools import partial
from collections.abc import Mapping, Sequence
from importlib.metadata import version
from itertools import zip_longest
from pathlib import Path
from typing import Any
import hashlib
import json
import re
import unicodedata

import regex

from bm25_index import canonical_id

ZERO_WIDTH = '\u200b\u200c\u200d\ufeff'

SPELLING_VARIANTS = {
    'សំលៀកបំពាក់': 'សម្លៀកបំពាក់',
    'ចំរៀង': 'ចម្រៀង',
    'ជ័យជម្នះ': 'ជ័យជំនះ',
}

def normalize_khmer_cluster_order(text):
    # Canonically order combining marks without removing Khmer characters.
    decomposed = unicodedata.normalize('NFD', text)
    clusters, current = [], ''
    for char in decomposed:
        if unicodedata.combining(char) == 0 and current:
            clusters.append(current)
            current = ''
        current += char
    if current:
        clusters.append(current)
    ordered = []
    for cluster in clusters:
        if len(cluster) > 1:
            base, marks = cluster[0], list(cluster[1:])
            marks.sort(key=unicodedata.combining)
            cluster = base + ''.join(marks)
        ordered.append(cluster)
    return unicodedata.normalize('NFC', ''.join(ordered))

def normalize_khmer(value):
    text = normalize_khmer_cluster_order(str(value or ''))
    text = text.translate(str.maketrans('', '', ZERO_WIDTH))
    text = text.replace('\u00a0', ' ')
    lines = []
    for line in text.splitlines():
        line = re.sub(r'[ \t]+', ' ', line).strip()
        if line:
            lines.append(line)
    text = re.sub(r'\n{2,}', '\n', '\n'.join(lines))
    for source, target in SPELLING_VARIANTS.items():
        text = text.replace(source, target)
    return text

# These fixed rules are included in the saved configuration below.
DEFAULT_STOPWORDS = Path(__file__).with_name('stopwords_km.txt')
CONTEXT_FIELDS = ('document_title', 'article_number', 'chapter_title', 'section_title')
DIGIT_TRANSLATION = str.maketrans('០១២៣៤៥៦៧៨៩', '0123456789')
DIGIT_BOUNDARY_PATTERN = r'(?<=[\p{L}\p{M}])(?=[0-9])|(?<=[0-9])(?=[\p{L}\p{M}])'
# A base consonant/independent vowel, optional coeng stacks, and attached marks.
# This is an orthographic approximation, not a pronunciation model.
SYLLABLE_PATTERN = r'[\u1780-\u17b3](?:\u17d2[\u1780-\u17b3]|[\u17b4-\u17d1\u17d3\u17dd])*|.'
SCRIPT_RUN_PATTERN = r'[\p{Script=Khmer}\p{M}]+|[^\p{Script=Khmer}\p{M}\s]+'


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read one JSON object per nonblank UTF-8 line."""
    with path.open(encoding='utf-8') as source:
        return [json.loads(line) for line in source if line.strip()]


def read_stopwords(path: Path) -> frozenset[str]:
    """Read exact one-word entries, ignoring blank and comment lines."""
    words = [line.strip() for line in path.read_text(encoding='utf-8').splitlines()
             if line.strip() and not line.lstrip().startswith('#')]
    if any(len(word.split()) != 1 for word in words):
        raise ValueError('Stopword entries must contain one token per line')
    return frozenset(words)


def fold_digits(text: str) -> str:
    """Convert Khmer digits to ASCII and separate digit runs from letters/marks."""
    return regex.sub(DIGIT_BOUNDARY_PATTERN, ' ', text.translate(DIGIT_TRANSLATION))


def strip_punctuation(text: str) -> str:
    """Replace Unicode punctuation and symbols with spaces, preserving word breaks."""
    return ''.join(' ' if unicodedata.category(char)[0] in {'P', 'S'} else char for char in text)


def context_text(article: Mapping[str, Any]) -> str:
    """Join dense-track context fields; skip missing values and keep unknown titles."""
    values = [article.get('document_title'),
              f"មាត្រា {article['article_number']}" if article.get('article_number') is not None else None,
              article.get('chapter_title'), article.get('section_title')]
    return ' | '.join(str(value).strip() for value in values if value and str(value).strip())


def syllable_ngrams(text: str, minimum: int, maximum: int) -> list[str]:
    """Emit overlapping orthographic syllable n-grams within each Khmer run."""
    tokens = []
    for run in regex.findall(SCRIPT_RUN_PATTERN, text):
        if not regex.search(r'\p{Script=Khmer}', run):
            tokens.append(run)
            continue
        syllables = regex.findall(SYLLABLE_PATTERN, run)
        for size in range(minimum, maximum + 1):
            tokens.extend(''.join(syllables[start:start + size])
                          for start in range(len(syllables) - size + 1))
    return tokens


class Analyzer:
    """Apply identical ordered text processing to documents and search queries."""

    def __init__(self, tokenizer: str = 'khmercut', include_context: bool = False,
                 stopword_path: Path = DEFAULT_STOPWORDS,
                 syllable_ngram_min: int = 1, syllable_ngram_max: int = 2) -> None:
        """Choose a backend, context policy, stopword file, and syllable n-gram sizes."""
        if tokenizer not in {'khmercut', 'khmernltk', 'syllable_ngrams'}:
            raise ValueError(f'Unknown tokenizer: {tokenizer}')
        if not isinstance(include_context, bool):
            raise TypeError('include_context must be a boolean')
        if not 1 <= syllable_ngram_min <= syllable_ngram_max:
            raise ValueError('Syllable n-gram sizes must satisfy 1 <= minimum <= maximum')
        self.tokenizer = tokenizer
        self.include_context = include_context
        self.syllable_ngram_min = syllable_ngram_min
        self.syllable_ngram_max = syllable_ngram_max
        self.stopwords = read_stopwords(Path(stopword_path))
        self._backend = None
        if tokenizer == 'khmercut':
            from khmercut import tokenize
            self._backend = tokenize
        elif tokenizer == 'khmernltk':
            from khmernltk import word_tokenize
            self._backend = partial(word_tokenize, return_tokens=True)

    def document_text(self, article: Mapping[str, Any]) -> str:
        """Prepend optional document context before applying the shared analyzer."""
        text = article['text']
        if not isinstance(text, str):
            raise TypeError('Article text must be a string')
        prefix = context_text(article) if self.include_context else ''
        return f'{prefix}\n{text}' if prefix else text

    def prepare(self, text: str) -> str:
        """Normalize, fold/separate digits, lowercase, then strip punctuation/symbols."""
        return strip_punctuation(fold_digits(normalize_khmer(text)).lower())

    def segment(self, text: str) -> list[str]:
        """Segment prepared text, preserving whitespace boundaries and non-Khmer runs."""
        if self.tokenizer == 'syllable_ngrams':
            return syllable_ngrams(text, self.syllable_ngram_min, self.syllable_ngram_max)
        tokens = []
        for run in regex.findall(SCRIPT_RUN_PATTERN, text):
            if regex.search(r'\p{Script=Khmer}', run):
                tokens.extend(token for token in self._backend(run) if token.strip())
            else:
                tokens.append(run)
        return tokens

    def remove_stopwords(self, tokens: Sequence[str]) -> list[str]:
        """Remove exact stopword matches without stemming or further text changes."""
        return [token for token in tokens if token not in self.stopwords]

    def analyze(self, text: str) -> list[str]:
        """Return final tokens for query text or a prepared document string."""
        return self.remove_stopwords(self.segment(self.prepare(text)))

    def analyze_document(self, article: Mapping[str, Any]) -> list[str]:
        """Attach optional document-only context, then call the same query analyzer."""
        return self.analyze(self.document_text(article))

    def explain(self, text: str) -> dict[str, str | list[str]]:
        """Return the real intermediate output after each ordered analysis step."""
        normalized = normalize_khmer(text)
        digits = fold_digits(normalized)
        lowercase = digits.lower()
        stripped = strip_punctuation(lowercase)
        segmented = self.segment(stripped)
        return {'1. Normalized': normalized, '2. Digits folded and separated': digits,
                '3. Lowercase': lowercase, '4. Punctuation and symbols replaced': stripped,
                '5. Segmented': segmented, '6. Stopwords removed': self.remove_stopwords(segmented)}

    def config(self) -> dict[str, Any]:
        """Describe every option and fixed rule, with code and dependency fingerprints."""
        packages = ['regex']
        if self.tokenizer == 'khmercut':
            packages += ['khmercut', 'python-crfsuite']
        elif self.tokenizer == 'khmernltk':
            packages += ['khmer-nltk', 'sklearn-crfsuite', 'python-crfsuite', 'scikit-learn']
        return {
            'schema_version': 1,
            'steps': ['normalize_khmer', 'fold_digits', 'lowercase', 'strip_punctuation',
                      'segment', 'remove_stopwords'],
            'normalization': {'enabled': True, 'version': 'unicode-khmer-cluster-order-spelling-v2',
                              'zero_width': ZERO_WIDTH, 'spelling_variants': SPELLING_VARIANTS},
            'digits': {'enabled': True, 'source': '០១២៣៤៥៦៧៨៩', 'target': '0123456789',
                       'letter_boundary_pattern': DIGIT_BOUNDARY_PATTERN},
            'lowercase': {'enabled': True, 'method': 'str.lower'},
            'punctuation': {'enabled': True, 'unicode_category_prefixes': ['P', 'S'], 'replacement': ' '},
            'tokenizer': self.tokenizer,
            'backend_options': {'khmercut': 'default CRF', 'khmernltk_return_tokens': True},
            'script_run_pattern': SCRIPT_RUN_PATTERN,
            'syllable_pattern': SYLLABLE_PATTERN,
            'syllable_ngram_min': self.syllable_ngram_min,
            'syllable_ngram_max': self.syllable_ngram_max,
            'INCLUDE_CONTEXT': self.include_context,
            'context_fields': list(CONTEXT_FIELDS),
            'context_article_prefix': 'មាត្រា ',
            'context_separator': ' | ', 'context_text_separator': '\n',
            'context_missing_policy': 'skip empty values; retain literal unknown titles',
            'stopwords_enabled': True, 'stopwords': sorted(self.stopwords),
            'unicode_database_version': unicodedata.unidata_version,
            'package_versions': {package: version(package) for package in packages},
            'pipeline_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        }

    def save_config(self, path: Path) -> None:
        """Save the complete analyzer contract beside the preprocessed token records."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.config(), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    def assert_compatible(self, path: Path) -> None:
        """Refuse search when any saved setting, stopword, version, or code rule differs."""
        saved = json.loads(path.read_text(encoding='utf-8'))
        current = self.config()
        differences = [key for key in sorted(saved.keys() | current.keys()) if key not in saved or key not in current or saved[key] != current[key]]
        if differences:
            raise ValueError('Analyzer configuration mismatch: ' + ', '.join(differences))

    @classmethod
    def from_config(cls, path: Path, stopword_path: Path = DEFAULT_STOPWORDS) -> 'Analyzer':
        """Restore configurable options and verify local code, stopwords, and packages."""
        saved = json.loads(path.read_text(encoding='utf-8'))
        analyzer = cls(tokenizer=saved['tokenizer'], include_context=saved['INCLUDE_CONTEXT'],
                       stopword_path=stopword_path,
                       syllable_ngram_min=saved['syllable_ngram_min'],
                       syllable_ngram_max=saved['syllable_ngram_max'])
        analyzer.assert_compatible(path)
        return analyzer


def normalization_report(records: Sequence[Mapping[str, Any]], path: Path) -> dict[str, Any]:
    """Check every dense normalized record in source order, including repeated IDs."""
    if not path.exists():
        return {'available': False, 'checked': 0, 'matches': 0, 'mismatches': 0}
    reference = read_jsonl(path)
    matches = 0
    checked = 0
    for raw, dense in zip_longest(records, reference):
        checked += 1
        if raw is not None and dense is not None:
            same_record = canonical_id(raw) == canonical_id(dense) and raw['text'] == dense.get('text')
            matches += bool(same_record and normalize_khmer(raw['text']) == dense.get('search_text'))
    return {'available': True, 'checked': checked, 'matches': matches, 'mismatches': checked - matches}


def selected_record_indices(records: Sequence[Mapping[str, Any]]) -> list[int]:
    """Select the longest raw text per canonical ID, keeping first ties as notebook 01."""
    selected: dict[str, int] = {}
    for position, article in enumerate(records):
        article_id = canonical_id(article)
        previous = selected.get(article_id)
        if previous is None or len(article['text']) > len(records[previous]['text']):
            selected[article_id] = position
    return list(selected.values())


def token_statistics(documents: Sequence[Sequence[str]]) -> dict[str, Any]:
    """Count vocabulary, collection singletons, mean length, and ranked token totals."""
    counts = Counter(token for tokens in documents for token in tokens)
    vocabulary_size = len(counts)
    return {'documents': len(documents), 'vocabulary': vocabulary_size,
            'one_time_share': sum(count == 1 for count in counts.values()) / vocabulary_size if vocabulary_size else 0.0,
            'average_tokens': sum(map(len, documents)) / len(documents) if documents else 0.0,
            'ranked_tokens': sorted(counts.items(), key=lambda item: (-item[1], item[0]))}
