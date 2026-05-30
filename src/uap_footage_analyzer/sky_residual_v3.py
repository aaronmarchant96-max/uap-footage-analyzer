#!/usr/bin/env python3
"""
Sky Residual Analyzer V3

Purpose:
    Process sky footage, extract high motion delta events, suppress obvious false positives,
    and write a structured residual review queue.

This script does not classify origin. It only assigns conservative review labels.

=============================================================================
CURRENT INTEGRATION STATUS (May 2026)
=============================================================================
This module is the core detection engine. It was originally developed and
tuned against DOD-style UAP footage (see V3 results).

It is **not yet** fully integrated with the new multi-source ingestion layer:
- It does not currently consume `NormalizedCase` objects directly.
- Source-specific configuration (thresholds, expected artifacts) is still
  mostly hardcoded or passed via CLI args rather than coming from the registry.

Work is planned to make the detector source-aware using `SourceConfig`
from the new schemas. Until then, when running on non-DOD material,
manual adjustment of parameters is expected.

See README.md → "Current Integration Status" for the broader picture.
=============================================================================
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

import cv2
import numpy as np


VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}


DEFAULTS = {
    "motion_threshold": 300000,
    "pixel_delta_threshold": 25,
    "frame_skip": 10,
    "cooldown_sec": 5.0,
    "residual_review_threshold": 0.65,
    "small_local_motion_ratio": 0.02,
    "scene_cut_motion_ratio": 0.45,
    "brightness_shift_threshold": 0.12,
    "camera_motion_threshold": 0.65,
    "scene_cut_threshold": 0.75,
    "compression_artifact_threshold": 0.55,
}


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def iter_videos(input_dir: Path) -> Iterable[Path]:
    for path in sorted(input_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
            yield path


def reset_output_dir(out_dir: Path) -> Dict[str, Path]:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    keyframes_all = out_dir / "keyframes" / "all_candidates"
    keyframes_residual = out_dir / "keyframes" / "residual_review"
    keyframes_all.mkdir(parents=True, exist_ok=True)
    keyframes_residual.mkdir(parents=True, exist_ok=True)
    return {
        "out_dir": out_dir,
        "keyframes_all": keyframes_all,
        "keyframes_residual": keyframes_residual,
        "events_jsonl": out_dir / "v3_events.jsonl",
        "residual_jsonl": out_dir / "v3_residual_review_queue.jsonl",
        "summary_md": out_dir / "v3_summary.md",
    }


def motion_score(prev_gray: np.ndarray, gray: np.ndarray, pixel_delta_threshold: int) -> Tuple[int, float, np.ndarray]:
    diff = cv2.absdiff(prev_gray, gray)
    blurred = cv2.GaussianBlur(diff, (5, 5), 0)
    _, mask = cv2.threshold(blurred, pixel_delta_threshold, 255, cv2.THRESH_BINARY)
    score = int(np.count_nonzero(mask))
    area_ratio = float(score / mask.size)
    return score, area_ratio, mask


def brightness_delta(prev_gray: np.ndarray, gray: np.ndarray) -> float:
    return float(abs(np.mean(gray) - np.mean(prev_gray)) / 255.0)


def edge_delta(prev_gray: np.ndarray, gray: np.ndarray) -> float:
    prev_edges = cv2.Canny(prev_gray, 80, 160)
    edges = cv2.Canny(gray, 80, 160)
    edge_diff = cv2.absdiff(prev_edges, edges)
    return float(np.count_nonzero(edge_diff) / edge_diff.size)


def phase_camera_motion(prev_gray: np.ndarray, gray: np.ndarray) -> Tuple[float, float, float, float]:
    h, w = gray.shape[:2]
    target_w = 320
    scale = target_w / max(w, 1)
    target_h = max(1, int(h * scale))

    prev_small = cv2.resize(prev_gray, (target_w, target_h), interpolation=cv2.INTER_AREA)
    gray_small = cv2.resize(gray, (target_w, target_h), interpolation=cv2.INTER_AREA)

    prev_float = np.float32(prev_small)
    gray_float = np.float32(gray_small)

    try:
        (shift_x, shift_y), response = cv2.phaseCorrelate(prev_float, gray_float)
    except cv2.error:
        return 0.0, 0.0, 0.0, 0.0

    shift_mag = math.sqrt(shift_x * shift_x + shift_y * shift_y)
    response = clamp01(response)
    return float(shift_x), float(shift_y), float(shift_mag), response


def blockiness_score(gray: np.ndarray) -> float:
    """Rough JPEG or video block artifact estimate based on 8 pixel boundaries."""
    gray_f = gray.astype(np.float32)
    h, w = gray_f.shape[:2]

    if h < 16 or w < 16:
        return 0.0

    vertical_boundary = np.abs(gray_f[:, 7:w - 1:8] - gray_f[:, 8:w:8]).mean() if w > 8 else 0.0
    vertical_regular = np.abs(gray_f[:, 3:w - 1:8] - gray_f[:, 4:w:8]).mean() if w > 4 else 0.0
    horizontal_boundary = np.abs(gray_f[7:h - 1:8, :] - gray_f[8:h:8, :]).mean() if h > 8 else 0.0
    horizontal_regular = np.abs(gray_f[3:h - 1:8, :] - gray_f[4:h:8, :]).mean() if h > 4 else 0.0

    boundary = (vertical_boundary + horizontal_boundary) / 2.0
    regular = (vertical_regular + horizontal_regular) / 2.0
    return clamp01((boundary - regular) / 35.0)


def score_explanations(metrics: Dict[str, float], cfg: Dict[str, Any]) -> Dict[str, float]:
    motion_area = metrics["motion_area_ratio"]
    bright = metrics["brightness_delta"]
    edges = metrics["edge_delta"]
    phase_response = metrics["phase_response"]
    phase_shift_mag = metrics["phase_shift_mag"]
    blockiness = metrics["blockiness_score"]

    brightness_shift = clamp01((bright / cfg["brightness_shift_threshold"]) * clamp01(motion_area / 0.35))

    scene_cut = clamp01(
        0.55 * clamp01(motion_area / 0.70)
        + 0.35 * clamp01(edges / 0.20)
        + 0.10 * clamp01(bright / 0.18)
    )

    camera_motion = clamp01(
        phase_response
        * clamp01(phase_shift_mag / 15.0)
        * clamp01(motion_area / 0.35)
    )

    compression_artifact = clamp01(
        blockiness
        * clamp01(motion_area / 0.25)
        * (1.0 - clamp01(edges / 0.30) * 0.6)
    )

    return {
        "full_frame_brightness_shift_score": brightness_shift,
        "scene_cut_score": scene_cut,
        "camera_motion_score": camera_motion,
        "compression_artifact_score": compression_artifact,
    }


def classify_event(metrics: Dict[str, float], cfg: Dict[str, Any]) -> Dict[str, Any]:
    scores = score_explanations(metrics, cfg)
    motion_area = metrics["motion_area_ratio"]

    known_explanation = None
    label = "interesting_motion"

    if (
        scores["scene_cut_score"] >= cfg["scene_cut_threshold"]
        and motion_area >= cfg["scene_cut_motion_ratio"]
    ):
        known_explanation = "scene_cut"
        label = "scene_cut"
    elif scores["full_frame_brightness_shift_score"] >= 0.75:
        known_explanation = "full_frame_brightness_shift"
        label = "full_frame_brightness_shift"
    elif scores["camera_motion_score"] >= cfg["camera_motion_threshold"]:
        known_explanation = "camera_motion_or_tracking_shift"
        label = "camera_motion_or_tracking_shift"
    elif scores["compression_artifact_score"] >= cfg["compression_artifact_threshold"]:
        known_explanation = "compression_artifact"
        label = "compression_artifact"

    max_known_score = max(scores.values())
    residual_score = 1.0 - max_known_score

    if motion_area <= cfg["small_local_motion_ratio"]:
        residual_score += 0.20
    if motion_area >= 0.35:
        residual_score -= 0.25

    residual_score = clamp01(residual_score)
    needs_manual_review = False

    if known_explanation is None and residual_score >= cfg["residual_review_threshold"]:
        label = "residual_unexplained"
        needs_manual_review = True
    elif known_explanation is None:
        label = "interesting_motion"
        needs_manual_review = True

    return {
        **scores,
        "known_explanation": known_explanation,
        "residual_score": residual_score,
        "label": label,
        "needs_manual_review": needs_manual_review,
    }


def write_jsonl(path: Path, record: Dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def keyframe_name(video_path: Path, timestamp_sec: float, frame_index: int, label: str) -> str:
    safe_stem = video_path.stem.replace(" ", "_")
    return f"{safe_stem}_t{timestamp_sec:.2f}_f{frame_index}_{label}.png"


def process_video(video_path: Path, paths: Dict[str, Path], cfg: Dict[str, Any]) -> Counter:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"Could not open video: {video_path}")
        return Counter({"open_failed": 1})

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = 30.0

    frame_index = 0
    prev_gray = None
    last_event_sec = -cfg["cooldown_sec"]
    counts = Counter()

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        frame_index += 1
        if frame_index % int(cfg["frame_skip"]) != 0:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if prev_gray is None:
            prev_gray = gray
            continue

        timestamp_sec = float(frame_index / fps)
        score, area_ratio, _ = motion_score(prev_gray, gray, int(cfg["pixel_delta_threshold"]))
        prev_for_metrics = prev_gray
        prev_gray = gray

        if score < int(cfg["motion_threshold"]):
            continue

        if timestamp_sec - last_event_sec < float(cfg["cooldown_sec"]):
            continue

        shift_x, shift_y, shift_mag, phase_response = phase_camera_motion(prev_for_metrics, gray)

        metrics = {
            "motion_score": float(score),
            "motion_area_ratio": float(area_ratio),
            "brightness_delta": brightness_delta(prev_for_metrics, gray),
            "edge_delta": edge_delta(prev_for_metrics, gray),
            "phase_shift_x": shift_x,
            "phase_shift_y": shift_y,
            "phase_shift_mag": shift_mag,
            "phase_response": phase_response,
            "blockiness_score": blockiness_score(gray),
        }

        classification = classify_event(metrics, cfg)
        label = classification["label"]

        all_keyframe_path = paths["keyframes_all"] / keyframe_name(video_path, timestamp_sec, frame_index, label)
        cv2.imwrite(str(all_keyframe_path), frame)

        residual_keyframe_path = None
        if classification["needs_manual_review"]:
            residual_keyframe_path = paths["keyframes_residual"] / all_keyframe_path.name
            cv2.imwrite(str(residual_keyframe_path), frame)

        record = {
            "file": video_path.name,
            "path": str(video_path),
            "timestamp_sec": round(timestamp_sec, 3),
            "frame": frame_index,
            "threshold": cfg["motion_threshold"],
            "frame_skip": cfg["frame_skip"],
            "cooldown_sec": cfg["cooldown_sec"],
            "keyframe": str(all_keyframe_path),
            "residual_keyframe": str(residual_keyframe_path) if residual_keyframe_path else None,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            **metrics,
            **classification,
        }

        write_jsonl(paths["events_jsonl"], record)
        if classification["needs_manual_review"]:
            write_jsonl(paths["residual_jsonl"], record)

        counts[label] += 1
        counts["total_events"] += 1
        if classification["needs_manual_review"]:
            counts["manual_review"] += 1

        last_event_sec = timestamp_sec

    cap.release()
    return counts


def write_summary(paths: Dict[str, Path], input_dir: Path, total_videos: int, counts: Counter, cfg: Dict[str, Any]) -> None:
    lines = [
        "# Sky Residual Analyzer V3 Summary",
        "",
        f"Input directory: `{input_dir}`",
        f"Processed videos: {total_videos}",
        f"Total candidate events: {counts.get('total_events', 0)}",
        f"Residual review candidates: {counts.get('manual_review', 0)}",
        "",
        "## Configuration",
        "",
        "```json",
        json.dumps(cfg, indent=2, sort_keys=True),
        "```",
        "",
        "## Label counts",
        "",
    ]

    for label, count in counts.most_common():
        if label not in {"total_events", "manual_review"}:
            lines.append(f"* {label}: {count}")

    lines.extend([
        "",
        "## Interpretation",
        "",
        "A residual review candidate is not proof of unusual origin.",
        "It means the current local filters did not explain the event as an obvious scene cut, brightness shift, camera motion, tracking shift, or compression artifact.",
        "Every residual candidate still requires manual review against surrounding video context.",
        "",
    ])

    paths["summary_md"].write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sky Residual Analyzer V3")
    parser.add_argument("--input", default="uap_footage", help="Directory containing sky footage videos")
    parser.add_argument("--out", default="uap_results_v3", help="Output directory")
    parser.add_argument("--motion-threshold", type=int, default=DEFAULTS["motion_threshold"])
    parser.add_argument("--pixel-delta-threshold", type=int, default=DEFAULTS["pixel_delta_threshold"])
    parser.add_argument("--frame-skip", type=int, default=DEFAULTS["frame_skip"])
    parser.add_argument("--cooldown-sec", type=float, default=DEFAULTS["cooldown_sec"])
    parser.add_argument("--residual-review-threshold", type=float, default=DEFAULTS["residual_review_threshold"])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_dir = Path(args.input)
    out_dir = Path(args.out)

    cfg = dict(DEFAULTS)
    cfg.update({
        "motion_threshold": args.motion_threshold,
        "pixel_delta_threshold": args.pixel_delta_threshold,
        "frame_skip": args.frame_skip,
        "cooldown_sec": args.cooldown_sec,
        "residual_review_threshold": args.residual_review_threshold,
    })

    if not input_dir.exists():
        raise SystemExit(f"Input directory does not exist: {input_dir}")

    paths = reset_output_dir(out_dir)
    videos = list(iter_videos(input_dir))

    total_counts = Counter()
    for index, video_path in enumerate(videos, start=1):
        print(f"[{index}/{len(videos)}] Processing {video_path.name}")
        total_counts.update(process_video(video_path, paths, cfg))

    write_summary(paths, input_dir, len(videos), total_counts, cfg)

    print("\nDone")
    print(f"Events log: {paths['events_jsonl']}")
    print(f"Residual queue: {paths['residual_jsonl']}")
    print(f"Summary: {paths['summary_md']}")


if __name__ == "__main__":
    main()
