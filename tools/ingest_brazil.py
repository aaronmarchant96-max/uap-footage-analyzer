#!/usr/bin/env python3
"""
Brazil source adapter.

Scans the data/brazil/ directory for case folders, builds NormalizedCase
objects using data from the registry, and writes a normalized review queue.

Folder convention:
    data/brazil/<case_id>/
        - any video or image files directly inside (or in subfolders)
        - optional metadata.json with extra fields (timestamps, region, notes, etc.)

This is the real ingestion path. Replace or extend the media discovery logic
as needed when actual Brazil material is added.
"""

from pathlib import Path
from typing import List, Dict, Any
import json

from uap_footage_analyzer import (
    load_sources_registry,
    get_source,
    NormalizedCase,
    Provenance,
    Credibility,
    CredibilityLevel,
    ProcessingStatus,
    save_review_queue,
)

# Supported media extensions for automatic discovery
MEDIA_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".m4v", ".jpg", ".jpeg", ".png"}


def find_media_files(case_dir: Path) -> List[str]:
    """Recursively find media files inside a case directory."""
    media_files: List[str] = []
    for ext in MEDIA_EXTENSIONS:
        media_files.extend(str(p.relative_to(case_dir.parent.parent)) for p in case_dir.rglob(f"*{ext}"))
    return sorted(media_files)


def load_case_metadata(case_dir: Path) -> Dict[str, Any]:
    """Optionally load per-case metadata.json if it exists."""
    meta_path = case_dir / "metadata.json"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def build_brazil_cases(repo_root: Path, brazil_source: dict) -> List[NormalizedCase]:
    """Scan data/brazil/ and return a list of NormalizedCase objects."""
    brazil_root = repo_root / "data" / "brazil"
    cases: List[NormalizedCase] = []

    if not brazil_root.exists():
        return cases

    source_id = brazil_source["source_id"]
    provenance = Provenance(
        origin=brazil_source["provenance"]["origin"],
        url=brazil_source["provenance"].get("url"),
        release_type=brazil_source["provenance"]["release_type"],
        classification=brazil_source["provenance"]["classification"],
    )
    credibility = Credibility(
        level=CredibilityLevel(brazil_source["credibility"]["level"]),
        notes=brazil_source["credibility"]["notes"],
    )

    for case_dir in sorted(brazil_root.iterdir()):
        if not case_dir.is_dir():
            continue

        case_id = case_dir.name
        media_paths = find_media_files(case_dir)

        if not media_paths:
            continue  # Skip empty folders

        meta = load_case_metadata(case_dir)

        case = NormalizedCase(
            source_id=source_id,
            case_id=case_id,
            media_paths=media_paths,
            timestamps=meta.get("timestamps", []),
            region=meta.get("region", "Brazil"),
            provenance=provenance,
            credibility=credibility,
            processing_status=ProcessingStatus.PENDING_INGESTION,
            metadata=meta.get("metadata", {}),
        )
        cases.append(case)

    return cases


def main():
    repo_root = Path(__file__).resolve().parents[1]
    registry = load_sources_registry(repo_root)

    try:
        brazil_source = get_source("brazil-leak-001", registry)
    except KeyError:
        print("ERROR: brazil-leak-001 not found in registry.")
        print("Please update data/metadata/sources.json with real Brazil source information.")
        return

    print(f"Scanning Brazil material for source: {brazil_source['name']}")

    cases = build_brazil_cases(repo_root, brazil_source)

    if not cases:
        print("No Brazil cases found. Create folders under data/brazil/<case_id>/ with media files.")
        return

    output_path = repo_root / "data" / "brazil" / "brazil_review_queue.jsonl"
    save_review_queue(cases, output_path)

    print(f"Successfully wrote {len(cases)} normalized cases to {output_path}")


if __name__ == "__main__":
    main()