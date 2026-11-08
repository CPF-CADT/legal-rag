"""Configuration for the pure BGE-M3 dense-retrieval pipeline."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PipelineConfig:
    project_root: Path
    model_name: str = "BAAI/bge-m3"
    max_chunk_tokens: int = 450
    embedding_batch_size: int = 2
    chroma_batch_size: int = 256
    collection_name: str = "legal_dense_bge_m3_450"

    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"

    @property
    def ocr_dir(self) -> Path:
        return self.data_dir / "text-ocr"

    @property
    def documents_csv(self) -> Path:
        return self.data_dir / "documents.csv"

    @property
    def output_dir(self) -> Path:
        return self.data_dir / "dense_retrieval"

    @property
    def article_path(self) -> Path:
        return self.output_dir / "articles.jsonl"

    @property
    def chunk_path(self) -> Path:
        return self.output_dir / "chunks.jsonl"

    @property
    def embedding_path(self) -> Path:
        return self.output_dir / "embeddings.npy"

    @property
    def metadata_path(self) -> Path:
        return self.output_dir / "metadata.jsonl"

    @property
    def manifest_path(self) -> Path:
        return self.output_dir / "manifest.json"

    @property
    def chroma_path(self) -> Path:
        return self.output_dir / "chroma_db"

    @property
    def bm25_path(self) -> Path:
        return self.output_dir / "bm25.sqlite3"

    def create_output_dirs(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_path.mkdir(parents=True, exist_ok=True)
