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
from pathlib import Path
from statistics import fmean
from typing import Iterable

from PIL import Image

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


@dataclass(frozen=True)
class FrameSample:
    path: Path
    index: int
    name: str
    motion_score: float
    intensity_score: float
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


def score_motion(previous: Iterable[int], current: Iterable[int]) -> float:
    previous_list = list(previous)
    current_list = list(current)
    if not previous_list or not current_list:
        return 0.0
    delta = sum(abs(a - b) for a, b in zip(previous_list, current_list))
    return delta / (len(previous_list) * 255.0)


def label_frame(motion_score: float, intensity_score: float) -> str:
    if motion_score >= 0.28 or intensity_score >= 0.72:
        return "intensity_change"
    if motion_score >= 0.12:
        return "candidate_cell"
    if motion_score >= 0.05:
        return "needs_human_review"
    return "low_activity"


def analyze_frames(frame_paths: list[Path]) -> list[FrameSample]:
    samples: list[FrameSample] = []
    previous_signature: list[int] | None = None

    for index, path in enumerate(frame_paths):
        signature, intensity_score = load_signature(path)
        motion_score = 0.0 if previous_signature is None else score_motion(previous_signature, signature)
        label = label_frame(motion_score, intensity_score)
        samples.append(
            FrameSample(
                path=path,
                index=index,
                name=path.name,
                motion_score=round(motion_score, 4),
                intensity_score=round(intensity_score, 4),
                label=label,
            )
        )
        previous_signature = signature

    return samples


def write_events_jsonl(samples: list[FrameSample], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for sample in samples:
            record = {
                "frame_index": sample.index,
                "frame_name": sample.name,
                "frame_path": str(sample.path),
                "motion_score": sample.motion_score,
                "intensity_score": sample.intensity_score,
                "label": sample.label,
            }
            handle.write(json.dumps(record) + "\n")


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

    samples = analyze_frames(frame_paths)
    write_events_jsonl(samples, args.output)

    print(f"Analyzed {len(samples)} frame(s)")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
