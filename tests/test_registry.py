"""Tests for the source registry loader."""

import json
from pathlib import Path

import pytest

from uap_footage_analyzer.registry import (
    load_sources_registry,
    get_source,
    get_all_sources,
)


def test_load_sources_registry_finds_real_file():
    """Smoke test that the real registry in the repo can be loaded."""
    # Explicitly pass the repo root so the test works regardless of cwd
    repo_root = Path(__file__).resolve().parents[1]
    registry = load_sources_registry(repo_root=repo_root)
    assert "sources" in registry
    assert isinstance(registry["sources"], list)
    assert len(registry["sources"]) >= 1


def test_get_source_returns_correct_entry():
    repo_root = Path(__file__).resolve().parents[1]
    registry = load_sources_registry(repo_root=repo_root)
    source = get_source("dod-2026-05", registry)
    assert source["source_id"] == "dod-2026-05"
    assert "DOD" in source["name"]


def test_get_source_raises_on_missing():
    repo_root = Path(__file__).resolve().parents[1]
    registry = load_sources_registry(repo_root=repo_root)
    with pytest.raises(KeyError):
        get_source("nonexistent-source", registry)


def test_get_all_sources_returns_list():
    repo_root = Path(__file__).resolve().parents[1]
    registry = load_sources_registry(repo_root=repo_root)
    sources = get_all_sources(registry)
    assert isinstance(sources, list)
    assert all("source_id" in s for s in sources)


def test_load_sources_registry_with_custom_root(tmp_path: Path):
    """Test loading from a custom directory with a minimal registry."""
    custom_data = tmp_path / "data" / "metadata"
    custom_data.mkdir(parents=True)

    registry_content = {
        "version": "1.0",
        "sources": [
            {
                "source_id": "custom-test",
                "name": "Custom Test Source",
                "provenance": {"origin": "Test"},
                "credibility": {"level": "medium", "notes": ""},
            }
        ],
    }
    (custom_data / "sources.json").write_text(json.dumps(registry_content))

    # Pass the custom repo root so get_repo_root is bypassed
    registry = load_sources_registry(repo_root=tmp_path)
    source = get_source("custom-test", registry)
    assert source["name"] == "Custom Test Source"


def test_get_source_works_with_custom_registry_dict():
    """Test that get_source works when a pre-loaded registry dict is passed."""
    registry = {
        "sources": [
            {"source_id": "inline-source", "name": "Inline Source"}
        ]
    }
    source = get_source("inline-source", registry)
    assert source["name"] == "Inline Source"