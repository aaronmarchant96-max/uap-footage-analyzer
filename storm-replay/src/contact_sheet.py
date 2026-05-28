"""Build an SVG contact sheet for a Storm Replay case."""

from __future__ import annotations

import argparse
import base64
import json
from io import BytesIO
from pathlib import Path

from PIL import Image


def load_events(events_path: Path) -> list[dict]:
    events: list[dict] = []
    with events_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def image_data_uri(image_path: Path, size: tuple[int, int] = (240, 160)) -> str:
    image = Image.open(image_path).convert("RGB")
    image.thumbnail(size)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def build_contact_sheet(frames_dir: Path, events_path: Path, output_path: Path) -> None:
    events = load_events(events_path)
    frames = [path for path in sorted(frames_dir.iterdir()) if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}]

    tile_width = 300
    tile_height = 250
    margin = 32
    columns = 3
    rows = max(1, (len(frames) + columns - 1) // columns)
    width = margin * 2 + columns * tile_width
    height = margin * 2 + rows * tile_height + 80

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'.format(w=width, h=height),
        '<rect width="100%" height="100%" fill="#f3efe7" />',
        '<text x="32" y="48" font-family="Arial, sans-serif" font-size="30" font-weight="700" fill="#1f2933">Storm Replay Contact Sheet</text>',
        '<text x="32" y="80" font-family="Arial, sans-serif" font-size="16" fill="#4b5563">Historical review scaffold for human review.</text>',
    ]

    for index, frame_path in enumerate(frames):
        event = events[index] if index < len(events) else {}
        row = index // columns
        col = index % columns
        x = margin + col * tile_width
        y = 110 + row * tile_height
        label = str(event.get("label", "low_activity"))
        motion = event.get("motion_score", 0.0)
        intensity = event.get("intensity_score", 0.0)
        href = image_data_uri(frame_path)
        parts.extend(
            [
                f'<rect x="{x}" y="{y}" width="280" height="220" rx="16" fill="#ffffff" stroke="#cfd8dc" stroke-width="2" />',
                f'<image x="{x + 16}" y="{y + 12}" width="248" height="160" preserveAspectRatio="xMidYMid slice" href="{href}" />',
                f'<text x="{x + 16}" y="{y + 194}" font-family="Arial, sans-serif" font-size="16" font-weight="700" fill="#243447">{frame_path.name}</text>',
                f'<text x="{x + 16}" y="{y + 214}" font-family="Arial, sans-serif" font-size="14" fill="#57616d">{label} | motion {motion:.4f} | intensity {intensity:.4f}</text>',
            ]
        )

    parts.append("</svg>")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(parts), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a Storm Replay contact sheet SVG.")
    parser.add_argument("frames_dir", type=Path, help="Directory containing the frame images.")
    parser.add_argument("events_path", type=Path, help="JSONL file produced by analyze_frames.py.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("storm-replay/data/processed/contact_sheet.svg"),
        help="Output SVG path.",
    )
    args = parser.parse_args()

    build_contact_sheet(args.frames_dir, args.events_path, args.output)
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
