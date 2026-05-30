"""Basic tests for the normalized schema layer."""


from uap_footage_analyzer.schemas import (
    NormalizedCase,
    Provenance,
    Credibility,
    CredibilityLevel,
    SourceConfig,
    create_dod_case,
    create_brazil_case,
)


def test_provenance_and_credibility_creation():
    prov = Provenance(
        origin="Test Source",
        release_type="leak",
        classification="unclassified",
    )
    cred = Credibility(
        level=CredibilityLevel.MEDIUM,
        notes="Test credibility note",
    )
    assert prov.origin == "Test Source"
    assert cred.level == CredibilityLevel.MEDIUM


def test_normalized_case_roundtrip():
    """Test that to_dict + from_dict roundtrips cleanly."""
    case = NormalizedCase(
        source_id="test-source",
        case_id="test-case-001",
        media_paths=["data/test/video.mp4"],
        timestamps=["2025-01-01T00:00:00Z"],
        region="Test Region",
        provenance=Provenance(origin="Test Origin"),
        credibility=Credibility(level=CredibilityLevel.LOW),
        metadata={"key": "value"},
    )

    data = case.to_dict()
    reconstructed = NormalizedCase.from_dict(data)

    assert reconstructed.source_id == case.source_id
    assert reconstructed.case_id == case.case_id
    assert reconstructed.media_paths == case.media_paths
    assert reconstructed.metadata == case.metadata
    assert reconstructed.credibility.level == case.credibility.level


def test_create_dod_case_helper():
    case = create_dod_case(
        case_id="dod-test-001",
        media_paths=["data/dod/video.mp4"],
    )
    assert case.source_id == "dod-2026-05"
    assert case.credibility.level == CredibilityLevel.HIGH
    assert case.provenance.release_type == "official_public_release"


def test_create_brazil_case_helper():
    case = create_brazil_case(
        case_id="brazil-test-001",
        media_paths=["data/brazil/video.mp4"],
        credibility_level=CredibilityLevel.MEDIUM,
    )
    assert case.source_id == "brazil-leak-001"
    assert case.credibility.level == CredibilityLevel.MEDIUM
    assert case.provenance.release_type == "leak"


def test_source_config_defaults():
    config = SourceConfig()
    assert config.frame_skip == 10
    assert config.cooldown_seconds == 5
    assert config.expected_artifacts == []