"""
UAP Footage Analyzer

Core package for ingesting, normalizing, and analyzing UAP footage from multiple sources.
"""

from .schemas import (
    NormalizedCase,
    Provenance,
    Credibility,
    SourceConfig,
    CredibilityLevel,
    ProcessingStatus,
    create_dod_case,
    create_brazil_case,
)
from .registry import (
    load_sources_registry,
    get_source,
    get_all_sources,
)
from .queue_io import load_review_queue, save_review_queue
from .detection import run_detection_on_case, run_on_case

__all__ = [
    "NormalizedCase",
    "Provenance",
    "Credibility",
    "SourceConfig",
    "CredibilityLevel",
    "ProcessingStatus",
    "create_dod_case",
    "create_brazil_case",
    "load_sources_registry",
    "get_source",
    "get_all_sources",
    "load_review_queue",
    "save_review_queue",
    "run_detection_on_case",
    "run_on_case",
]