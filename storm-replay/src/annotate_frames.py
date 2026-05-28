"""Annotate storm frames with review labels and scores."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def load_events(events_path: Path) -> dict[str, dict]:
    events: dict[str, dict] = {}
    with events_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            events[str(record.get("frame_name"))] = record
    return events


def annotate_image(image_path: Path, record: dict, output_path: Path) -> None:
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    overlay = [
        f"{record.get('label', 'low_activity')}",
        f"motion {record.get('motion_score', 0):.4f}",
        f"intensity {record.get('intensity_score', 0):.4f}",
    ]
    padding = 10
    line_height = 14
    box_height = padding * 2 + line_height * len(overlay)
    draw.rectangle((12, 12, 240, 12 + box_height), fill=(17, 24, 39))

    y = 12 + padding
    for line in overlay:
        draw.text((22, y), line, fill=(255, 255, 255), font=font)
        y += line_height

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Annotate storm replay frames using events.jsonl.")
    parser.add_argument("frames_dir", type=Path, help="Directory containing the original frames.")
    parser.add_argument("events_path", type=Path, help="JSONL file produced by analyze_frames.py.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("storm-replay/data/processed/annotated"),
        help="Directory for annotated frames.",
    )
    args = parser.parse_args()

    events = load_events(args.events_path)
    for frame_path in sorted(args.frames_dir.iterdir()):
        if frame_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
            continue
        record = events.get(frame_path.name, {})
        annotate_image(frame_path, record, args.output_dir / frame_path.name)

    print(f"Wrote annotated frames to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
