"""
Registry loader for UAP data sources.

This module is the single point of contact for reading data/metadata/sources.json.
All ingestion code should go through this instead of reading the JSON directly.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import json


def get_repo_root() -> Path:
    """Return the repository root.

    This is a bit heuristic. In production it assumes the package lives in
    src/uap_footage_analyzer/. In tests you should usually pass an explicit
    repo_root to load_sources_registry().
    """
    return Path(__file__).resolve().parents[3]


def load_sources_registry(repo_root: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load and return the sources registry.

    Returns the full parsed JSON as a dictionary.
    """
    if repo_root is None:
        repo_root = get_repo_root()

    registry_path = repo_root / "data" / "metadata" / "sources.json"

    if not registry_path.exists():
        raise FileNotFoundError(f"Sources registry not found at {registry_path}")

    with open(registry_path, "r", encoding="utf-8") as f:
        registry = json.load(f)

    return registry


def get_source(source_id: str, registry: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Retrieve a single source entry by source_id.

    Raises KeyError if the source is not found.
    """
    if registry is None:
        registry = load_sources_registry()

    sources = registry.get("sources", [])

    for source in sources:
        if source.get("source_id") == source_id:
            return source

    raise KeyError(f"Source with source_id '{source_id}' not found in registry")


def get_all_sources(registry: Optional[Dict[str, Any]] = None) -> list[Dict[str, Any]]:
    """Return the list of all source entries."""
    if registry is None:
        registry = load_sources_registry()
    return registry.get("sources", [])