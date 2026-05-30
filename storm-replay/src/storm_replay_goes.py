#!/usr/bin/env python3
"""
Storm Replay GOES calibration module.

Historical weather signal extraction for human review.
Limitation: not a forecasting system, not a warning system, and not a claim of tornado formation.

Core calculations are kept in pure functions. File I/O is isolated so the module
stays easy to test in isolation and easy to calibrate against Case 001.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import fmean
from typing import Any

import cv2
import numpy as np
from PIL import Image

try:  # Optional. The module still imports if the dependency is absent.
    import xarray as xr  # type: ignore
except ImportError:  # pragma: no cover - environment dependent
    xr = None  # type: ignore[assignment]

try:  # Optional. Importing rioxarray registers the rio accessor on xarray objects.
    import rioxarray  # noqa: F401
except ImportError:  # pragma: no cover - environment dependent
    rioxarray = None  # type: ignore[assignment]


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
GOES_EXTENSIONS = {".nc", ".nc4", ".cdf"}
SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS | GOES_EXTENSIONS

DEFAULT_THRESHOLDS = {
    "pixel_delta_threshold": 25,
    "motion_low_threshold": 0.05,
    "motion_medium_threshold": 0.12,
    "motion_high_threshold": 0.28,
    "intensity_high_threshold": 0.72,
}

CASE_001_CALIBRATION_THRESHOLDS = {
    "pixel_delta_threshold": 18,
    "motion_low_threshold": 0.0150,
    "motion_medium_threshold": 0.0300,
    "motion_high_threshold": 0.0500,
    "intensity_high_threshold": 0.6200,
}

CASE_001_ACTIVITY_WINDOW = "22:00-23:00 CST in Graves County"


def collect_frame_paths(input_dir: Path) -> list[Path]:
    """Collect image or GOES frame paths from a directory."""
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
    return [path for path in sorted(input_dir.iterdir()) if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS]


def build_case_001_thresholds(calibration_mode: bool = False) -> dict[str, float]:
    """Return the default or Case 001-calibrated thresholds."""
    thresholds = dict(DEFAULT_THRESHOLDS)
    if calibration_mode:
        thresholds.update(CASE_001_CALIBRATION_THRESHOLDS)
    return thresholds


def frame_timestamp_from_name(name: str) -> str:
    """Parse a timestamp from the current Storm Replay naming convention."""
    stem = Path(name).stem
    try:
        _, raw_ts = stem.split("_", 1)
        parsed = datetime.strptime(raw_ts, "%Y%m%d%H%M")
        return parsed.strftime("%Y-%m-%d %H:%M")
    except (ValueError, IndexError):
        return stem


def frame_timestamp_to_string(value: Any, fallback: str) -> str:
    """Coerce xarray / numpy timestamp values to a readable string."""
    if value is None:
        return fallback

    if isinstance(value, np.ndarray):
        if value.size == 0:
            return fallback
        value = value.reshape(-1)[0]

    if hasattr(value, "item"):
        try:
            value = value.item()
        except Exception:  # pragma: no cover - defensive fallback
            pass

    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")

    if isinstance(value, np.datetime64):
        return np.datetime_as_string(value, unit="m").replace("T", " ")

    text = str(value).strip()
    if not text:
        return fallback
    return text.replace("T", " ").replace("Z", "")


def extract_timestamp_from_dataset(dataset: Any, fallback_name: str) -> str:
    """Read a time coordinate or time-related attribute from a GOES dataset."""
    candidate_keys = ("time", "t", "valid_time")
    for key in candidate_keys:
        try:
            if key in dataset.coords:
                return frame_timestamp_to_string(dataset.coords[key].values, frame_timestamp_from_name(fallback_name))
        except Exception:  # pragma: no cover - defensive fallback
            continue

    candidate_attrs = ("time_coverage_start", "start_time", "date_created", "time_coverage_end")
    for key in candidate_attrs:
        value = getattr(dataset, "attrs", {}).get(key)
        if value:
            return frame_timestamp_to_string(value, frame_timestamp_from_name(fallback_name))

    return frame_timestamp_from_name(fallback_name)


def load_image_frame(frame_path: Path) -> dict[str, Any]:
    """Load a normal image frame for the same review pipeline."""
    image = Image.open(frame_path).convert("L")
    return {
        "frame_array": np.asarray(image),
        "frame_name": frame_path.name,
        "frame_path": str(frame_path),
        "frame_timestamp": frame_timestamp_from_name(frame_path.name),
    }


def load_goes16_frame(frame_path: Path, band_name: str = "CMI") -> dict[str, Any]:
    """Load a GOES-16 frame using xarray and rioxarray when available."""
    if xr is None:
        raise RuntimeError(
            "xarray is required to load GOES-16 frames. Install the storm-replay GOES dependencies first."
        )

    dataset = xr.open_dataset(frame_path)
    if rioxarray is not None:
        try:  # Keep the accessor available for geospatial datasets without forcing a projection step.
            dataset = dataset.rio.write_crs("EPSG:4326", inplace=False)  # type: ignore[attr-defined]
        except Exception:
            pass

    if band_name in getattr(dataset, "data_vars", {}):
        data_array = dataset[band_name]
    else:
        data_var_names = list(getattr(dataset, "data_vars", {}).keys())
        if not data_var_names:
            raise ValueError(f"No data variables were found in GOES file: {frame_path}")
        data_array = dataset[data_var_names[0]]

    frame_array = np.asarray(data_array.squeeze().values)
    timestamp = extract_timestamp_from_dataset(dataset, frame_path.name)
    return {
        "frame_array": frame_array,
        "frame_name": frame_path.name,
        "frame_path": str(frame_path),
        "frame_timestamp": timestamp,
    }


def load_frame_source(frame_path: Path, band_name: str = "CMI") -> dict[str, Any]:
    """Load either a GOES frame or a fallback image frame."""
    suffix = frame_path.suffix.lower()
    if suffix in GOES_EXTENSIONS:
        return load_goes16_frame(frame_path, band_name=band_name)
    if suffix in IMAGE_EXTENSIONS:
        return load_image_frame(frame_path)
    raise ValueError(f"Unsupported frame type: {frame_path}")


def normalize_frame_array(frame_array: np.ndarray) -> np.ndarray:
    """Convert a frame to an 8-bit grayscale array for OpenCV comparison."""
    array = np.asarray(frame_array)
    if array.size == 0:
        return np.zeros((1, 1), dtype=np.uint8)

    if array.ndim > 2:
        array = np.squeeze(array)
    if array.ndim > 2:
        array = array[..., 0]

    finite = np.isfinite(array)
    if not np.any(finite):
        return np.zeros(array.shape[:2], dtype=np.uint8)

    data = array.astype(np.float32, copy=False)
    data = np.where(finite, data, np.nan)

    if np.nanmax(data) <= 1.0 and np.nanmin(data) >= 0.0:
        scaled = np.clip(data, 0.0, 1.0) * 255.0
    else:
        low = float(np.nanpercentile(data, 2))
        high = float(np.nanpercentile(data, 98))
        if not np.isfinite(low) or not np.isfinite(high) or high <= low:
            low = float(np.nanmin(data))
            high = float(np.nanmax(data))
        if not np.isfinite(low) or not np.isfinite(high) or high <= low:
            scaled = np.zeros_like(data)
        else:
            scaled = (np.clip(data, low, high) - low) / (high - low) * 255.0

    return np.nan_to_num(scaled, nan=0.0).astype(np.uint8)


def extract_intensity_score(frame_array: np.ndarray) -> float:
    """Return a normalized mean intensity score for a frame."""
    normalized = normalize_frame_array(frame_array)
    if normalized.size == 0:
        return 0.0
    return float(np.mean(normalized) / 255.0)


def frame_intensity_score(frame_array: np.ndarray) -> float:
    """Backward-compatible alias for the intensity helper."""
    return extract_intensity_score(frame_array)


def extract_motion_signals_from_goes16_frame(
    previous_frame: np.ndarray,
    current_frame: np.ndarray,
    thresholds: dict[str, float],
) -> dict[str, float]:
    """Use OpenCV differencing to measure frame-to-frame motion anomalies."""
    prev_gray = normalize_frame_array(previous_frame)
    current_gray = normalize_frame_array(current_frame)

    diff = cv2.absdiff(prev_gray, current_gray)
    blurred = cv2.GaussianBlur(diff, (5, 5), 0)
    _, mask = cv2.threshold(blurred, int(thresholds["pixel_delta_threshold"]), 255, cv2.THRESH_BINARY)

    score = float(np.mean(blurred) / 255.0)
    return {
        "motion_score": round(score, 4),
        "motion_area_ratio": round(float(np.count_nonzero(mask) / max(mask.size, 1)), 4),
    }


def classify_candidate(motion_score: float, intensity_score: float, thresholds: dict[str, float]) -> str:
    """Assign a human-review label using calibrated thresholds."""
    if motion_score >= thresholds["motion_high_threshold"] or intensity_score >= thresholds["intensity_high_threshold"]:
        return "high_activity"
    if motion_score >= thresholds["motion_medium_threshold"]:
        return "medium_activity"
    if motion_score >= thresholds["motion_low_threshold"]:
        return "low_activity"
    return "low_activity"


def build_event_record(
    timestamp: str,
    motion_score: float,
    intensity_score: float,
    label: str,
) -> dict[str, Any]:
    """Build one JSONL record for the Storm Replay review stream."""
    return {
        "timestamp": timestamp,
        "motion_score": round(float(motion_score), 4),
        "intensity_score": round(float(intensity_score), 4),
        "label": label,
    }


def log_candidate_to_events_jsonl(candidate: dict[str, Any], output_path: Path) -> None:
    """Append one candidate record to the Storm Replay JSONL log."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(candidate, sort_keys=True) + "\n")


def write_events_jsonl(records: list[dict[str, Any]], output_path: Path) -> None:
    """Rewrite the JSONL log from a prepared candidate list."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def summarize_calibration_metrics(
    records: list[dict[str, Any]],
    thresholds: dict[str, float],
    combined_scores: list[float] | None = None,
) -> dict[str, Any]:
    """Summarize score ranges and label counts for calibration review."""
    motion_scores = [float(record["motion_score"]) for record in records]
    intensity_scores = [float(record["intensity_score"]) for record in records]
    combined_values = combined_scores if combined_scores is not None else [float(record.get("combined_score", 0.0)) for record in records]
    label_counts = Counter(str(record["label"]) for record in records)

    summary = {
        "frame_count": len(records),
        "motion_min": round(min(motion_scores), 4) if motion_scores else 0.0,
        "motion_max": round(max(motion_scores), 4) if motion_scores else 0.0,
        "motion_avg": round(fmean(motion_scores), 4) if motion_scores else 0.0,
        "intensity_min": round(min(intensity_scores), 4) if intensity_scores else 0.0,
        "intensity_max": round(max(intensity_scores), 4) if intensity_scores else 0.0,
        "intensity_avg": round(fmean(intensity_scores), 4) if intensity_scores else 0.0,
        "combined_min": round(min(combined_values), 4) if combined_values else 0.0,
        "combined_max": round(max(combined_values), 4) if combined_values else 0.0,
        "combined_avg": round(fmean(combined_values), 4) if combined_values else 0.0,
        "label_counts": dict(sorted(label_counts.items())),
        "thresholds": dict(thresholds),
    }
    summary["threshold_notes"] = build_threshold_notes(summary, label_counts, thresholds)
    return summary


def build_threshold_notes(summary: dict[str, Any], label_counts: Counter[str], thresholds: dict[str, float]) -> list[str]:
    """Explain what the current score ranges imply for calibration."""
    notes: list[str] = []
    motion_max = float(summary["motion_max"])
    intensity_max = float(summary["intensity_max"])
    combined_max = float(summary["combined_max"])

    if motion_max < thresholds["motion_low_threshold"]:
        notes.append(
            f"Motion scores top out at {motion_max:.4f}, below the conservative low-activity threshold."
        )
    elif motion_max < thresholds["motion_medium_threshold"]:
        notes.append(
            f"Motion scores stay below the review threshold, so the detector remains conservative."
        )
    else:
        notes.append("Motion scores reach the review band, so threshold calibration is surfacing candidates.")

    if intensity_max < thresholds["intensity_high_threshold"]:
        notes.append(
            f"Intensity scores max out at {intensity_max:.4f}, far below the intensity-change trigger."
        )
    else:
        notes.append("At least one frame reaches the intensity trigger.")

    if combined_max < thresholds["motion_medium_threshold"]:
        notes.append(
            f"Combined scores remain tight at {combined_max:.4f}, so feature weighting should stay evidence-led."
        )

    if label_counts and label_counts.get("low_activity", 0) == int(summary["frame_count"]):
        notes.append("All frames landed in low_activity on the first pass, which reads like a calibration issue.")

    return notes


def print_calibration_summary(summary: dict[str, Any]) -> None:
    """Print a compact calibration report for the CLI."""
    print("Calibration summary")
    print(f"  frames reviewed: {summary['frame_count']}")
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
    print("  thresholds:")
    for key, value in summary["thresholds"].items():
        print(f"    {key}: {value:.4f}")
    print("  label_counts:")
    for label, count in summary["label_counts"].items():
        print(f"    {label}: {count}")
    print("  threshold_notes:")
    for note in summary["threshold_notes"]:
        print(f"    - {note}")


def analyze_frame_sources(
    frame_paths: list[Path],
    calibration_mode: bool = False,
    band_name: str = "CMI",
) -> tuple[list[dict[str, Any]], dict[str, Any], Counter[str]]:
    """Analyze a sequence of frame sources and prepare review records."""
    thresholds = build_case_001_thresholds(calibration_mode=calibration_mode)
    frame_sources: list[dict[str, Any]] = [load_frame_source(path, band_name=band_name) for path in frame_paths]

    intensity_scores = [frame_intensity_score(source["frame_array"]) for source in frame_sources]
    baseline_intensity = fmean(intensity_scores) if intensity_scores else 0.0

    records: list[dict[str, Any]] = []
    label_counts: Counter[str] = Counter()
    combined_scores: list[float] = []

    for index, source in enumerate(frame_sources):
        current_frame = source["frame_array"]
        if index == 0:
            motion_score = 0.0
        else:
            motion_bundle = extract_motion_signals_from_goes16_frame(
                frame_sources[index - 1]["frame_array"],
                current_frame,
                thresholds,
            )
            motion_score = float(motion_bundle["motion_score"])

        intensity_score = float(intensity_scores[index])
        combined_score = float(motion_score + abs(intensity_score - baseline_intensity))
        label = classify_candidate(motion_score, intensity_score, thresholds)

        record = build_event_record(
            timestamp=source["frame_timestamp"],
            motion_score=motion_score,
            intensity_score=intensity_score,
            label=label,
        )
        records.append(record)
        label_counts[label] += 1
        combined_scores.append(combined_score)

    summary = summarize_calibration_metrics(records, thresholds, combined_scores=combined_scores)
    summary["baseline_intensity"] = round(baseline_intensity, 4)
    if calibration_mode:
        summary["case_001_activity_window"] = CASE_001_ACTIVITY_WINDOW
    return records, summary, label_counts


def analyze_goes16_sequence(
    frame_paths: list[Path],
    calibration_mode: bool = False,
    band_name: str = "CMI",
) -> tuple[list[dict[str, Any]], dict[str, Any], Counter[str]]:
    """Alias for sequence analysis to match the Storm Replay prompt language."""
    return analyze_frame_sources(frame_paths, calibration_mode=calibration_mode, band_name=band_name)


def process_input_directory(
    input_dir: Path,
    calibration_mode: bool = False,
    band_name: str = "CMI",
) -> tuple[list[dict[str, Any]], dict[str, Any], Counter[str]]:
    """Convenience wrapper used by the CLI and manual review passes."""
    frame_paths = collect_frame_paths(input_dir)
    if not frame_paths:
        raise SystemExit(f"No supported frames found in {input_dir}")
    return analyze_frame_sources(frame_paths, calibration_mode=calibration_mode, band_name=band_name)


def main() -> int:
    parser = argparse.ArgumentParser(description="Storm Replay GOES and frame calibration module.")
    parser.add_argument("input_dir", type=Path, help="Directory containing GOES or image frames.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("storm-replay/data/events.jsonl"),
        help="Path to the JSONL review log.",
    )
    parser.add_argument(
        "--calibration-mode",
        action="store_true",
        help="Use Case 001 calibration thresholds for the December 2021 Kentucky replay.",
    )
    parser.add_argument(
        "--band-name",
        default="CMI",
        help="GOES data variable name to read when processing NetCDF inputs.",
    )
    args = parser.parse_args()

    records, summary, _ = process_input_directory(
        args.input_dir,
        calibration_mode=args.calibration_mode,
        band_name=args.band_name,
    )
    write_events_jsonl(records, args.output)
    print_calibration_summary(summary)
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
