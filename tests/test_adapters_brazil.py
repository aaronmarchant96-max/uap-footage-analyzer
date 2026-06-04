"""Tests for the Brazil source adapter."""

import json
from pathlib import Path

import pytest

from uap_footage_analyzer.adapters.brazil import (
    find_media_files,
    load_case_metadata,
    scan_brazil_cases,
)
from uap_footage_analyzer.schemas import SourceConfig


@pytest.fixture
def brazil_source():
    """Minimal Brazil source entry for testing (with sample processing thresholds)."""
    return {
        "source_id": "brazil-test",
        "name": "Test Brazil Source",
        "provenance": {
            "origin": "Test Origin",
            "release_type": "leak",
            "classification": "unknown",
        },
        "credibility": {
            "level": "medium",
            "notes": "Test note",
        },
        "processing": {
            "thresholds": {
                "motion_delta": 123456,
                "frame_skip": 5,
                "cooldown_seconds": 3,
            }
        },
    }


def test_find_media_files_discovers_videos_and_images(tmp_path: Path):
    case_dir = tmp_path / "case-001"
    case_dir.mkdir()

    (case_dir / "video1.mp4").touch()
    (case_dir / "video2.mov").touch()
    (case_dir / "photo.jpg").touch()
    (case_dir / "notes.txt").touch()  # Should be ignored

    media = find_media_files(case_dir)
    assert len(media) == 3
    assert any("video1.mp4" in m for m in media)
    assert any("photo.jpg" in m for m in media)


def test_load_case_metadata_returns_empty_when_missing(tmp_path: Path):
    case_dir = tmp_path / "case-no-meta"
    case_dir.mkdir()

    meta = load_case_metadata(case_dir)
    assert meta == {}


def test_load_case_metadata_reads_json(tmp_path: Path):
    case_dir = tmp_path / "case-with-meta"
    case_dir.mkdir()

    data = {"region": "Test Region", "timestamps": ["2025-01-01"]}
    (case_dir / "metadata.json").write_text(json.dumps(data))

    meta = load_case_metadata(case_dir)
    assert meta["region"] == "Test Region"


def test_scan_brazil_cases_creates_normalized_cases(tmp_path: Path, brazil_source):
    # Create two case folders
    case1 = tmp_path / "colares-1977"
    case1.mkdir()
    (case1 / "video.mp4").touch()
    (case1 / "metadata.json").write_text(json.dumps({
        "region": "Colares",
        "timestamps": ["1977-10-15"]
    }))

    case2 = tmp_path / "empty-case"
    case2.mkdir()  # No media files

    # Manually build source_config like the run() does, since this test calls scan directly
    proc = brazil_source.get("processing", {}) or {}
    thresh = proc.get("thresholds") or {}
    source_config = SourceConfig(
        motion_delta_threshold=thresh.get("motion_delta"),
        frame_skip=thresh.get("frame_skip") or 10,
        cooldown_seconds=thresh.get("cooldown_seconds") or 5,
    )
    cases = scan_brazil_cases(tmp_path, brazil_source, source_config=source_config)

    # Only case1 should be included
    assert len(cases) == 1
    c = cases[0]
    assert c.case_id == "colares-1977"
    assert c.source_id == "brazil-test"
    assert c.region == "Colares"
    assert c.source_config is not None
    assert c.source_config.motion_delta_threshold == 123456
    assert c.source_config.frame_skip == 5


def test_load_case_metadata_handles_malformed_json(tmp_path: Path):
    case_dir = tmp_path / "bad-json"
    case_dir.mkdir()
    (case_dir / "metadata.json").write_text("{ not valid json }")

    # Should not raise; current implementation will raise on bad JSON.
    # For robustness we may want to catch it in the future.
    with pytest.raises(json.JSONDecodeError):
        load_case_metadata(case_dir)


def test_scan_brazil_cases_gracefully_handles_case_with_bad_metadata(tmp_path: Path, brazil_source):
    case_dir = tmp_path / "bad-meta-case"
    case_dir.mkdir()
    (case_dir / "video.mp4").touch()
    (case_dir / "metadata.json").write_text("{ invalid }")

    # The current adapter will fail when loading bad metadata.
    # This test documents current behavior.
    with pytest.raises(json.JSONDecodeError):
        scan_brazil_cases(tmp_path, brazil_source)


def test_scan_brazil_cases_returns_empty_for_missing_directory(brazil_source):
    cases = scan_brazil_cases(Path("/nonexistent/path"), brazil_source)
    assert cases == []