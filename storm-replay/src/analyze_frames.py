"""Analyze a sequence of storm frames and write review events.

This is a small MVP detector:
- compare adjacent frames
- assign a simple review label
- emit JSONL for human review and follow-on artifacts
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from collections import Counter
from pathlib import Path
from statistics import fmean
from typing import Iterable

from PIL import Image

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
MOTION_LOW_ACTIVITY_THRESHOLD = 0.05
MOTION_REVIEW_THRESHOLD = 0.12
MOTION_HIGH_THRESHOLD = 0.28
INTENSITY_HIGH_THRESHOLD = 0.72


@dataclass(frozen=True)
class FrameSample:
    path: Path
    index: int
    name: str
    timestamp: str
    motion_score: float
    intensity_score: float
    combined_score: float
    label: str


def collect_frame_paths(input_dir: Path) -> list[Path]:
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
    paths = [path for path in sorted(input_dir.iterdir()) if path.suffix.lower() in IMAGE_EXTENSIONS]
    return paths


def load_signature(path: Path, size: tuple[int, int] = (64, 64)) -> tuple[list[int], float]:
    image = Image.open(path).convert("L").resize(size)
    pixels = list(image.getdata())
    intensity = fmean(pixels) / 255.0 if pixels else 0.0
    return pixels, intensity


def frame_timestamp_from_name(name: str) -> str:
    stem = Path(name).stem
    try:
        _, raw_ts = stem.split("_", 1)
        parsed = datetime.strptime(raw_ts, "%Y%m%d%H%M")
        return parsed.strftime("%Y-%m-%d %H:%M")
    except (ValueError, IndexError):
        return stem


def score_motion(previous: Iterable[int], current: Iterable[int]) -> float:
    previous_list = list(previous)
    current_list = list(current)
    if not previous_list or not current_list:
        return 0.0
    delta = sum(abs(a - b) for a, b in zip(previous_list, current_list))
    return delta / (len(previous_list) * 255.0)


def label_frame(motion_score: float, intensity_score: float) -> str:
    if motion_score >= MOTION_HIGH_THRESHOLD or intensity_score >= INTENSITY_HIGH_THRESHOLD:
        return "intensity_change"
    if motion_score >= MOTION_REVIEW_THRESHOLD:
        return "candidate_cell"
    if motion_score >= MOTION_LOW_ACTIVITY_THRESHOLD:
        return "needs_human_review"
    return "low_activity"


def analyze_frames(frame_paths: list[Path]) -> tuple[list[FrameSample], dict[str, float], Counter[str]]:
    samples: list[FrameSample] = []
    previous_signature: list[int] | None = None
    motion_scores: list[float] = []
    intensity_scores: list[float] = []

    for index, path in enumerate(frame_paths):
        signature, intensity_score = load_signature(path)
        motion_score = 0.0 if previous_signature is None else score_motion(previous_signature, signature)
        label = label_frame(motion_score, intensity_score)
        samples.append(
            FrameSample(
                path=path,
                index=index,
                name=path.name,
                timestamp=frame_timestamp_from_name(path.name),
                motion_score=round(motion_score, 4),
                intensity_score=round(intensity_score, 4),
                combined_score=0.0,
                label=label,
            )
        )
        motion_scores.append(motion_score)
        intensity_scores.append(intensity_score)
        previous_signature = signature

    baseline_intensity = fmean(intensity_scores) if intensity_scores else 0.0
    samples = [
        FrameSample(
            path=sample.path,
            index=sample.index,
            name=sample.name,
            timestamp=sample.timestamp,
            motion_score=sample.motion_score,
            intensity_score=sample.intensity_score,
            combined_score=round(sample.motion_score + abs(sample.intensity_score - baseline_intensity), 4),
            label=sample.label,
        )
        for sample in samples
    ]

    summary = {
        "frame_count": float(len(samples)),
        "baseline_intensity": round(baseline_intensity, 4),
        "motion_min": round(min(motion_scores), 4) if motion_scores else 0.0,
        "motion_max": round(max(motion_scores), 4) if motion_scores else 0.0,
        "motion_avg": round(fmean(motion_scores), 4) if motion_scores else 0.0,
        "intensity_min": round(min(intensity_scores), 4) if intensity_scores else 0.0,
        "intensity_max": round(max(intensity_scores), 4) if intensity_scores else 0.0,
        "intensity_avg": round(fmean(intensity_scores), 4) if intensity_scores else 0.0,
        "combined_min": round(min(sample.combined_score for sample in samples), 4) if samples else 0.0,
        "combined_max": round(max(sample.combined_score for sample in samples), 4) if samples else 0.0,
        "combined_avg": round(fmean(sample.combined_score for sample in samples), 4) if samples else 0.0,
    }
    label_counts = Counter(sample.label for sample in samples)
    return samples, summary, label_counts


def write_events_jsonl(samples: list[FrameSample], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for sample in samples:
            record = {
                "frame_index": sample.index,
                "frame_name": sample.name,
                "frame_timestamp": sample.timestamp,
                "frame_path": str(sample.path),
                "motion_score": sample.motion_score,
                "intensity_score": sample.intensity_score,
                "combined_score": sample.combined_score,
                "label": sample.label,
            }
            handle.write(json.dumps(record) + "\n")


def build_threshold_notes(summary: dict[str, float], label_counts: Counter[str]) -> list[str]:
    notes: list[str] = []
    motion_max = summary["motion_max"]
    intensity_max = summary["intensity_max"]
    combined_max = summary["combined_max"]

    if motion_max < MOTION_LOW_ACTIVITY_THRESHOLD:
        notes.append(
            f"Motion scores top out at {motion_max:.4f}, below the {MOTION_LOW_ACTIVITY_THRESHOLD:.2f} low-activity threshold."
        )
    elif motion_max < MOTION_REVIEW_THRESHOLD:
        notes.append(
            f"Motion scores stay below the {MOTION_REVIEW_THRESHOLD:.2f} candidate threshold, so the detector will stay conservative."
        )
    else:
        notes.append(
            "Motion scores reach the review band, so the current thresholds are at least sensitive enough to surface candidates."
        )

    if intensity_max < INTENSITY_HIGH_THRESHOLD:
        notes.append(
            f"Intensity scores max out at {intensity_max:.4f}, far below the {INTENSITY_HIGH_THRESHOLD:.2f} intensity-change trigger."
        )
    else:
        notes.append(
            f"At least one frame reaches the intensity-change trigger at {INTENSITY_HIGH_THRESHOLD:.2f}."
        )

    if combined_max < MOTION_REVIEW_THRESHOLD:
        notes.append(
            f"Combined scores remain tight at {combined_max:.4f}, which suggests threshold calibration should come after feature inspection, not before it."
        )

    if label_counts.get("low_activity", 0) == int(summary["frame_count"]):
        notes.append(
            "All frames landed in low_activity on the first pass, so this looks like a calibration problem rather than a need to force storm labels."
        )

    return notes


def print_summary(summary: dict[str, float], label_counts: Counter[str]) -> None:
    print("Calibration summary")
    print(f"  frames reviewed: {int(summary['frame_count'])}")
    print(
        "  motion_score: "
        f"min={summary['motion_min']:.4f} max={summary['motion_max']:.4f} avg={summary['motion_avg']:.4f}"
    )
    print(
        "  intensity_score: "
        f"min={summary['intensity_min']:.4f} max={summary['intensity_max']:.4f} avg={summary['intensity_avg']:.4f}"
    )
    print(
        "  combined_score: "
        f"min={summary['combined_min']:.4f} max={summary['combined_max']:.4f} avg={summary['combined_avg']:.4f}"
    )
    print(f"  baseline_intensity: {summary['baseline_intensity']:.4f}")
    print(
        "  thresholds: "
        f"low_activity<{MOTION_LOW_ACTIVITY_THRESHOLD:.2f}, "
        f"candidate_cell>={MOTION_REVIEW_THRESHOLD:.2f}, "
        f"intensity_change>={MOTION_HIGH_THRESHOLD:.2f} or intensity>={INTENSITY_HIGH_THRESHOLD:.2f}"
    )
    print("  label_counts:")
    for label, count in sorted(label_counts.items()):
        print(f"    {label}: {count}")
    print("  threshold_notes:")
    for note in build_threshold_notes(summary, label_counts):
        print(f"    - {note}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze storm replay frames and write JSONL review events.")
    parser.add_argument("input_dir", type=Path, help="Directory containing storm frames.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("storm-replay/data/events.jsonl"),
        help="Path to the output JSONL file.",
    )
    args = parser.parse_args()

    frame_paths = collect_frame_paths(args.input_dir)
    if not frame_paths:
        raise SystemExit(f"No image frames found in {args.input_dir}")

    samples, summary, label_counts = analyze_frames(frame_paths)
    write_events_jsonl(samples, args.output)

    print_summary(summary, label_counts)
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
