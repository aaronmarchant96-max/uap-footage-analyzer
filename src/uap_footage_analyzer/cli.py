"""
Command line interface for uap-footage-analyzer.

This tool ingests UAP footage from different sources into a normalized schema
for consistent analysis and review.

Run `uap-ingest --help` or `uap-ingest brazil --help` for usage and examples.
"""

import argparse
import sys
from pathlib import Path

from .adapters.brazil import run as run_brazil_ingestion
from .queue_io import load_review_queue


def main():
    parser = argparse.ArgumentParser(
        prog="uap-ingest",
        description="Ingest UAP footage from different sources into normalized review queues.",
        epilog="See the project README and data/README.md for the overall data model and ingestion philosophy.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # === brazil subcommand ===
    brazil_parser = subparsers.add_parser(
        "brazil",
        help="Ingest material from the Brazilian UAP leaks collection.",
        description="Scan a folder structure under data/brazil/ (or a custom path),\n"
                    "convert discovered cases into the normalized schema, and write a review queue.",
        epilog="""Examples:
  # Preview what would be ingested
  uap-ingest brazil --dry-run --verbose

  # Actually write the normalized queue
  uap-ingest brazil

  # Point at a specific leak folder
  uap-ingest brazil --input data/brazil/colares-1977 --output queues/colares.jsonl

Each immediate subdirectory under the input path is treated as one case.
Place a metadata.json inside a case folder for timestamps, region, and extra notes.
See data/brazil/README.md for the expected folder layout.""",
        formatter_class=argparse.RawTextHelpFormatter
    )
    brazil_parser.add_argument(
        "--input", "-i",
        type=Path,
        default=Path("data/brazil"),
        help="Root folder containing Brazil case subdirectories (default: data/brazil)"
    )
    brazil_parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("data/brazil/brazil_review_queue.jsonl"),
        help="Where to write the normalized review queue in JSONL format"
    )
    brazil_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan the input and show what would be written, without creating any files."
    )
    brazil_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed progress and per-case information."
    )
    brazil_parser.add_argument(
        "--list",
        action="store_true",
        help="List the current contents of the review queue (does not perform ingestion)."
    )

    args = parser.parse_args()

    if args.command == "brazil":
        if args.list:
            # List mode - show current state of the queue
            try:
                cases = load_review_queue(args.output)
            except Exception as e:
                print(f"Error loading queue: {e}", file=sys.stderr)
                sys.exit(1)

            print(f"Brazil Review Queue ({len(cases)} cases)")
            print("─" * 40)

            if not cases:
                print("(queue is empty)")
                return

            for c in cases:
                meta_status = "has metadata" if c.metadata else "no metadata"
                print(f"{c.case_id:<30} {len(c.media_paths):>2} media files   ({meta_status})")

            if args.verbose:
                print()
                for c in cases:
                    print(f"  {c.case_id}")
                    print(f"    Region:     {c.region or 'N/A'}")
                    print(f"    Timestamps: {c.timestamps}")
                    print(f"    Files:      {c.media_paths}")
                    print()

            return

        # Normal ingestion path
        try:
            run_brazil_ingestion(
                input_dir=args.input,
                output_path=args.output,
                dry_run=args.dry_run,
                verbose=args.verbose,
            )
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Should not normally be reached because subparsers are required
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()