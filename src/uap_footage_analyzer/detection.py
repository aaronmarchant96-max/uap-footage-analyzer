"""
Thin integration layer between the new NormalizedCase model and the
existing detection engines (currently only V3).

This file exists to make the boundary explicit and to provide a place
where source-aware behavior can be added over time without immediately
refactoring the legacy detector code.
"""

from collections import Counter
from pathlib import Path
from typing import Optional, Any, Dict

from .schemas import NormalizedCase, SourceConfig


def run_detection_on_case(
    case: NormalizedCase,
    output_dir: Optional[Path] = None,
    **override_kwargs,
) -> dict:
    """
    Run detection on a NormalizedCase.

    Wires NormalizedCase.source_config (if present) into the V3 detector's cfg
    so that source-specific thresholds from the registry drive the run.
    Builds per-case output paths.

    Supports Brazil and DOD cases (and any with source_config attached).

    Args:
        case: A NormalizedCase (must have at least one media path)
        output_dir: Optional base directory; will be scoped under source/case_id
        **override_kwargs: Extra cfg overrides (applied after source_config)

    Returns:
        Dict with counts + source_id, case_id, output_dir, cfg_used.
    """
    if not case.media_paths:
        raise ValueError(f"Case {case.case_id} has no media paths")

    primary_media = Path(case.media_paths[0])

    # Lazy imports
    from .sky_residual_v3 import process_video, reset_output_dir, DEFAULTS

    # Per-case output dir (prevents clobber; creates the standard v3 layout)
    if output_dir is None:
        output_dir = Path("uap_results") / case.source_id / case.case_id
    paths = reset_output_dir(output_dir)

    # Start from defaults, then apply source_config from the case (wired from registry)
    cfg: Dict[str, Any] = dict(DEFAULTS)
    if case.source_config:
        sc: SourceConfig = case.source_config
        if sc.motion_delta_threshold is not None:
            cfg["motion_threshold"] = sc.motion_delta_threshold
            cfg["pixel_delta_threshold"] = sc.motion_delta_threshold
        if sc.frame_skip is not None:
            cfg["frame_skip"] = sc.frame_skip
        if sc.cooldown_seconds is not None:
            cfg["cooldown_sec"] = sc.cooldown_seconds
        if sc.expected_artifacts:
            cfg["expected_artifacts"] = list(sc.expected_artifacts)

    # Overrides win
    cfg.update(override_kwargs)

    result = process_video(primary_media, paths, cfg)

    # Normalize to dict (process_video returns Counter of label counts)
    if isinstance(result, Counter):
        result = dict(result)
    elif not isinstance(result, dict):
        result = {"raw_counts": result}

    result.setdefault("source_id", case.source_id)
    result.setdefault("case_id", case.case_id)
    result["output_dir"] = str(output_dir)
    result["cfg_used"] = cfg

    return result


# Convenience alias for now
run_on_case = run_detection_on_case