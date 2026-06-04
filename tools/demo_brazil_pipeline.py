#!/usr/bin/env python3
"""
Self-contained demo of the Brazil UAP ingestion + normalization pipeline.

This script proves that the new multi-source architecture works end-to-end
without requiring any real footage.

Run it with:

    python tools/demo_brazil_pipeline.py

Or after `pip install -e .`:

    python -m tools.demo_brazil_pipeline
"""

import json
import sys
import tempfile
from pathlib import Path

# Make the package importable when running the script directly
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from uap_footage_analyzer import (
    NormalizedCase,
    save_review_queue,
    load_review_queue,
)


def create_fake_brazil_case(base_dir: Path, case_id: str, region: str) -> Path:
    """Create a fake Brazil case folder with dummy media and metadata.json."""
    case_dir = base_dir / case_id
    case_dir.mkdir(parents=True)

    # Create some dummy media files
    (case_dir / "raw").mkdir()
    (case_dir / "raw" / "clip_01.mp4").touch()
    (case_dir / "raw" / "clip_02.mov").touch()
    (case_dir / "frame_001.jpg").touch()

    # Create metadata.json following the recommended schema
    metadata = {
        "case_id": case_id,
        "title": f"{region} UAP Event",
        "date": "2023-07" if "colares" in case_id.lower() else "2024-03",
        "location": {
            "region": region,
            "city": region.split(",")[0] if "," in region else region,
        },
        "event_type": "sighting",
        "summary": f"Demo case for the Brazil ingestion pipeline ({region}).",
        "witnesses": "multiple",
        "media": {
            "videos": ["raw/clip_01.mp4", "raw/clip_02.mov"],
            "images": ["frame_001.jpg"],
            "other": [],
        },
        "source": {
            "original_source": "Brazil UFO Leaks (demo)",
            "credibility_notes": "Synthetic demo data for pipeline validation.",
            "registry_id": "brazil-leak-001",
        },
        "tags": ["demo", "brazil", region.lower().replace(" ", "-")],
        "notes": "This is synthetic data created by the demo script.",
        "review_status": "pending",
    }

    (case_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
    return case_dir


def main():
    print("UAP Footage Analyzer — Brazil Pipeline Demo\n")

    # Use a temporary directory so this demo is completely safe and self-contained
    with tempfile.TemporaryDirectory() as tmpdir:
        brazil_root = Path(tmpdir) / "brazil_demo_data"
        brazil_root.mkdir()

        # Create two realistic-looking fake cases
        create_fake_brazil_case(brazil_root, "colares-1977-demo", "Colares, Pará")
        create_fake_brazil_case(brazil_root, "sao-paulo-2024-demo", "São Paulo")

        print(f"Created synthetic Brazil test data in: {brazil_root}\n")

        # Use a minimal inline Brazil source for the demo (fully self-contained, no registry dependency)
        brazil_source = {
            "source_id": "brazil-demo",
            "name": "Brazil UAP Leaks (Demo)",
            "provenance": {
                "origin": "Synthetic demo data",
                "release_type": "demo",
                "classification": "unclassified",
            },
            "credibility": {
                "level": "medium",
                "notes": "This is synthetic data created solely to demonstrate the pipeline.",
            },
        }

        print(f"Using source: {brazil_source['name']}\n")

        # === Simulate what the real adapter + CLI does ===
        from uap_footage_analyzer.adapters.brazil import scan_brazil_cases

        cases = scan_brazil_cases(brazil_root, brazil_source)

        # Write a normalized review queue (just like the real CLI does)
        output_path = Path(tmpdir) / "brazil_review_queue.jsonl"
        save_review_queue(cases, output_path)

        print(f"Wrote normalized review queue to: {output_path}\n")

        # === Proof: Load it back and display ===
        loaded_cases = load_review_queue(output_path)

        print(f"Brazil Review Queue Demo ({len(loaded_cases)} cases)")
        print("─" * 55)

        for case in loaded_cases:
            meta_status = "has metadata" if case.metadata else "no metadata"
            print(f"{case.case_id:<28} {len(case.media_paths):>2} media files   ({meta_status})")

        print("\n" + "─" * 55)
        print("Pipeline proof complete.")
        print("The cases above are real NormalizedCase objects produced by the Brazil adapter.")
        print("They were written to a review queue and successfully loaded back.")

        # Show one full object for proof
        if loaded_cases:
            print("\nExample NormalizedCase (first case):")
            print(json.dumps(loaded_cases[0].to_dict(), indent=2, default=str))


if __name__ == "__main__":
    main()