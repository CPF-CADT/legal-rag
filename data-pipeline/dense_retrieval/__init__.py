"""Modular pure-dense retrieval pipeline for the selected legal corpus."""

from apps.core.retrieval_config import PipelineConfig

__all__ = ["PipelineConfig", "run_pipeline"]


def run_pipeline(*args, **kwargs):
    """Load and execute the embedding pipeline only when explicitly requested."""
    from .pipeline import run_pipeline as _run_pipeline

    return _run_pipeline(*args, **kwargs)
