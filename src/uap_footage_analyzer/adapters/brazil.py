"""
Brazil source adapter.

Contains the logic for scanning a Brazil material folder structure and
producing NormalizedCase objects.
"""

from pathlib import Path
from typing import List, Dict, Any
import json

from ..registry import load_sources_registry, get_source
from ..schemas import NormalizedCase, Provenance, Credibility, CredibilityLevel, ProcessingStatus
from ..queue_io import save_review_queue


MEDIA_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".m4v", ".jpg", ".jpeg", ".png"}


def find_media_files(case_dir: Path) -> List[str]:
    """Recursively find media files inside a case directory (relative to repo root)."""
    media_files: List[str] = []
    for ext in MEDIA_EXTENSIONS:
        for p in case_dir.rglob(f"*{ext}"):
            # Make path relative to the data/ directory for portability
            try:
                rel = p.relative_to(case_dir.parents[1])  # data/brazil/<case>/
                media_files.append(str(rel))
            except ValueError:
                media_files.append(str(p))
    return sorted(set(media_files))


def load_case_metadata(case_dir: Path) -> Dict[str, Any]:
    meta_path = case_dir / "metadata.json"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def scan_brazil_cases(brazil_root: Path, brazil_source: dict) -> List[NormalizedCase]:
    """Scan a Brazil root directory and return NormalizedCase objects."""
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
            continue

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


def run(
    input_dir: Path,
    output_path: Path,
    dry_run: bool = False,
    verbose: bool = False,
) -> None:
    """Main entry point for Brazil ingestion."""
    repo_root = Path(__file__).resolve().parents[3]
    registry = load_sources_registry(repo_root)

    try:
        brazil_source = get_source("brazil-leak-001", registry)
    except KeyError:
        raise RuntimeError("brazil-leak-001 not found in registry. Update data/metadata/sources.json first.")

    if verbose:
        print(f"Scanning Brazil material under: {input_dir}")
        print(f"Using source: {brazil_source['name']}")

    cases = scan_brazil_cases(input_dir, brazil_source)

    if not cases:
        print("No Brazil cases found with media files.")
        return

    if dry_run:
        print(f"[DRY RUN] Would write {len(cases)} cases to {output_path}")
        for c in cases:
            print(f"  - {c.case_id}: {len(c.media_paths)} media files")
        return

    save_review_queue(cases, output_path)
    print(f"Wrote {len(cases)} normalized cases to {output_path}")
