"""Modular pure-dense retrieval pipeline for the selected legal corpus."""

from .config import PipelineConfig
from .pipeline import run_pipeline
from .retriever import DenseRetriever

__all__ = ["DenseRetriever", "PipelineConfig", "run_pipeline"]
