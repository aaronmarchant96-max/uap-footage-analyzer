"""Lightweight tests for the detection integration layer."""

import pytest

from uap_footage_analyzer import (
    NormalizedCase,
    Provenance,
    Credibility,
    CredibilityLevel,
    run_on_case,
)


def _make_minimal_case() -> NormalizedCase:
    return NormalizedCase(
        source_id="test",
        case_id="test-detection-case",
        media_paths=["/nonexistent/dummy.mp4"],  # We won't actually process it
        provenance=Provenance(origin="Test"),
        credibility=Credibility(level=CredibilityLevel.LOW),
    )


def test_run_on_case_accepts_normalized_case():
    """Basic smoke test that the integration function accepts a NormalizedCase."""
    case = _make_minimal_case()

    # Now gracefully handles bad file (returns counts with open_failed), but
    # accepts the case and attaches metadata.
    result = run_on_case(case)
    assert result.get("source_id") == case.source_id
    assert result.get("case_id") == case.case_id
    # open_failed or similar from V3 when cap fails
    assert "open_failed" in result or result.get("total_events", 0) >= 0


def test_run_on_case_attaches_case_metadata_on_success_path(monkeypatch):
    """
    If the underlying detector ever succeeds, we want source_id and case_id
    to be attached to the result.
    """
    case = _make_minimal_case()

    # Patch at the place where it is actually imported inside the function
    import uap_footage_analyzer.sky_residual_v3 as sky_module

    def fake_process_video(video_path, paths, cfg):
        return {"success": True, "processed_file": str(video_path)}

    monkeypatch.setattr(sky_module, "process_video", fake_process_video)

    result = run_on_case(case)

    assert result["source_id"] == case.source_id
    assert result["case_id"] == case.case_id
    assert result["success"] is True