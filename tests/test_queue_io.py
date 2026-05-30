"""Tests for review queue read/write utilities."""

from pathlib import Path

from uap_footage_analyzer import (
    NormalizedCase,
    Provenance,
    Credibility,
    CredibilityLevel,
    save_review_queue,
    load_review_queue,
)


def _make_sample_case(case_id: str) -> NormalizedCase:
    return NormalizedCase(
        source_id="test-source",
        case_id=case_id,
        media_paths=[f"data/test/{case_id}.mp4"],
        timestamps=["2025-01-01T00:00:00Z"],
        region="Testland",
        provenance=Provenance(origin="Test"),
        credibility=Credibility(level=CredibilityLevel.MEDIUM),
    )


def test_save_and_load_roundtrip(tmp_path: Path):
    cases = [
        _make_sample_case("case-001"),
        _make_sample_case("case-002"),
    ]

    queue_path = tmp_path / "test_queue.jsonl"
    save_review_queue(cases, queue_path)

    loaded = load_review_queue(queue_path)

    assert len(loaded) == 2
    assert loaded[0].case_id == "case-001"
    assert loaded[1].case_id == "case-002"
    assert loaded[0].media_paths == cases[0].media_paths


def test_load_nonexistent_queue_returns_empty_list(tmp_path: Path):
    queue_path = tmp_path / "does_not_exist.jsonl"
    loaded = load_review_queue(queue_path)
    assert loaded == []


def test_save_creates_parent_directories(tmp_path: Path):
    queue_path = tmp_path / "nested" / "dir" / "queue.jsonl"
    case = _make_sample_case("nested-case")

    save_review_queue([case], queue_path)

    assert queue_path.exists()
    loaded = load_review_queue(queue_path)
    assert len(loaded) == 1