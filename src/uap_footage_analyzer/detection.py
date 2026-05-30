"""
Thin integration layer between the new NormalizedCase model and the
existing detection engines (currently only V3).

This file exists to make the boundary explicit and to provide a place
where source-aware behavior can be added over time without immediately
refactoring the legacy detector code.
"""

from pathlib import Path
from typing import Optional

from .schemas import NormalizedCase


def run_detection_on_case(
    case: NormalizedCase,
    output_dir: Optional[Path] = None,
    **override_kwargs,
) -> dict:
    """
    Run detection on a NormalizedCase.

    Currently this is a very thin wrapper around the V3 engine.
    It extracts media paths from the case and passes them through.

    Future work: pull SourceConfig from the registry (or the case itself)
    and apply source-specific thresholds / artifact profiles.

    Args:
        case: A NormalizedCase (must have at least one media path)
        output_dir: Optional directory to write results
        **override_kwargs: Any parameters to pass through to the V3 runner

    Returns:
        The result dict from the underlying detector (for now).
    """
    if not case.media_paths:
        raise ValueError(f"Case {case.case_id} has no media paths")

    # For now we just take the first media path (common pattern in the old code)
    # In a more mature version we would handle multiple files per case.
    primary_media = Path(case.media_paths[0])

    # TODO: In the future, resolve SourceConfig from registry using case.source_id
    # and merge with any override_kwargs.
    _ = case.source_config  # placeholder for future source-aware logic

    # Lazy import to avoid circular imports and heavy dependencies at package load time
    from .sky_residual_v3 import process_video

    # Build kwargs, letting source_config influence defaults later
    kwargs = {
        "output_dir": output_dir,
        **override_kwargs,
    }

    # Current behavior: just call the V3 engine on the primary media
    # This is intentionally minimal so we can evolve it cleanly.
    result = process_video(primary_media, **kwargs)

    # We could attach the case_id and source_id to the result here
    if isinstance(result, dict):
        result.setdefault("source_id", case.source_id)
        result.setdefault("case_id", case.case_id)

    return result


# Convenience alias for now
run_on_case = run_detection_on_case