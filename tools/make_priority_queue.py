#!/usr/bin/env python3
"""
Create a high priority review queue from a V3 event log.

This does not classify origin. It only selects residual or interesting events above a motion score threshold.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_INPUT = Path("uap_results_v3/v3_events.jsonl")
DEFAULT_OUTPUT = Path("uap_results_v3/v3_priority_review_queue.jsonl")
DEFAULT_SCORE_THRESHOLD = 800000
REVIEW_LABELS = {"interesting_motion", "residual_unexplained"}


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a high priority V3 review queue")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--score-threshold", type=float, default=DEFAULT_SCORE_THRESHOLD)
    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Input file does not exist: {args.input}")

    events = load_jsonl(args.input)
    priority_events: List[Dict[str, Any]] = []

    for event in events:
        label = event.get("label")
        score = float(event.get("motion_score", 0) or 0)
        if label in REVIEW_LABELS and score > args.score_threshold:
            event["priority_tier"] = "high"
            event["priority_reason"] = "high_motion_residual_candidate"
            event["human_review_result"] = None
            priority_events.append(event)

    priority_events.sort(key=lambda item: float(item.get("motion_score", 0) or 0), reverse=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for event in priority_events:
            handle.write(json.dumps(event, sort_keys=True) + "\n")

    print(f"input_events: {len(events)}")
    print(f"priority_events: {len(priority_events)}")
    print(f"score_threshold: {args.score_threshold}")
    print(f"saved_to: {args.out}")


if __name__ == "__main__":
    main()
