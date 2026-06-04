"""
Normalized data schemas for the UAP Footage Analyzer.

All sources (DOD, Brazil, future) should be converted into these structures
after ingestion. This is the contract between source adapters and the core pipeline.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

from .registry import load_sources_registry, get_source


class CredibilityLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class ProcessingStatus(str, Enum):
    PENDING_INGESTION = "pending_ingestion"
    INGESTED = "ingested"
    DETECTED = "detected"
    PROCESSED = "processed"
    PROCESSED_V3 = "processed_v3"          # Legacy/historical status for DOD 2026-05 run
    REVIEWED = "reviewed"
    ARCHIVED = "archived"


@dataclass
class Provenance:
    origin: str
    url: Optional[str] = None
    release_type: str = "unknown"          # e.g. "official_public_release", "leak"
    classification: str = "unknown"
    collected_by: Optional[str] = None
    additional: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Credibility:
    level: CredibilityLevel
    notes: str = ""
    assessed_by: Optional[str] = None
    assessment_date: Optional[str] = None


@dataclass
class SourceConfig:
    """Per-source configuration for the detector (thresholds, expected artifacts, etc.)."""
    motion_delta_threshold: Optional[int] = None
    frame_skip: int = 10
    cooldown_seconds: int = 5
    expected_artifacts: List[str] = field(default_factory=list)  # e.g. ["compression", "lens_flare", "sensor_noise"]
    notes: str = ""


def build_source_config_from_registry(
    source_id: str,
    registry: Optional[Dict[str, Any]] = None,
    source_dict: Optional[Dict[str, Any]] = None,
) -> SourceConfig:
    """Build SourceConfig from registry entry or explicit source_dict (for thresholds).

    Falls back to defaults if no thresholds info available. Used to wire NormalizedCase
    source_config into the detector.
    """
    thresh: Dict[str, Any] = {}
    if source_dict:
        proc = source_dict.get("processing", {}) or {}
        thresh = proc.get("thresholds") or {}
    else:
        try:
            if registry is None:
                registry = load_sources_registry()
            src = get_source(source_id, registry)
            proc = src.get("processing", {}) or {}
            thresh = proc.get("thresholds") or {}
        except Exception:
            pass

    defaults = SourceConfig()
    return SourceConfig(
        motion_delta_threshold=thresh.get("motion_delta", defaults.motion_delta_threshold),
        frame_skip=thresh.get("frame_skip", defaults.frame_skip),
        cooldown_seconds=thresh.get("cooldown_seconds", defaults.cooldown_seconds),
        expected_artifacts=thresh.get("expected_artifacts", defaults.expected_artifacts) or [],
        notes=thresh.get("notes", defaults.notes) or "",
    )


@dataclass
class NormalizedCase:
    """
    Canonical internal representation of a case from any source.

    After a source adapter runs, it should output one or more of these.
    The rest of the pipeline operates on NormalizedCase objects.
    """

    # Non-default fields must come first
    source_id: str
    case_id: str
    media_paths: List[str]
    provenance: Provenance
    credibility: Credibility

    # Fields with defaults come after
    timestamps: List[str] = field(default_factory=list)   # ISO format preferred
    region: Optional[str] = None
    processing_status: ProcessingStatus = ProcessingStatus.PENDING_INGESTION
    source_config: Optional[SourceConfig] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "case_id": self.case_id,
            "media_paths": self.media_paths,
            "timestamps": self.timestamps,
            "region": self.region,
            "provenance": self.provenance.__dict__,
            "credibility": {
                "level": self.credibility.level.value,
                "notes": self.credibility.notes,
                "assessed_by": self.credibility.assessed_by,
                "assessment_date": self.credibility.assessment_date,
            },
            "processing_status": self.processing_status.value,
            "source_config": self.source_config.__dict__ if self.source_config else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NormalizedCase":
        """Reconstruct a NormalizedCase from a dictionary (e.g. from JSONL)."""
        provenance = Provenance(**data["provenance"])

        cred_data = data["credibility"]
        credibility = Credibility(
            level=CredibilityLevel(cred_data["level"]),
            notes=cred_data.get("notes", ""),
            assessed_by=cred_data.get("assessed_by"),
            assessment_date=cred_data.get("assessment_date"),
        )

        source_config = None
        if data.get("source_config"):
            source_config = SourceConfig(**data["source_config"])

        return cls(
            source_id=data["source_id"],
            case_id=data["case_id"],
            media_paths=data["media_paths"],
            timestamps=data.get("timestamps", []),
            region=data.get("region"),
            provenance=provenance,
            credibility=credibility,
            processing_status=ProcessingStatus(data["processing_status"]),
            source_config=source_config,
            metadata=data.get("metadata", {}),
        )


def create_dod_case(
    case_id: str,
    media_paths: List[str],
    source_config: Optional["SourceConfig"] = None,
    **kwargs
) -> NormalizedCase:
    """Helper to create a NormalizedCase for DOD sources with sensible defaults."""
    if source_config is None:
        source_config = build_source_config_from_registry("dod-2026-05")
    return NormalizedCase(
        source_id="dod-2026-05",
        case_id=case_id,
        media_paths=media_paths,
        provenance=Provenance(
            origin="U.S. Department of Defense public release",
            release_type="official_public_release",
            classification="unclassified"
        ),
        credibility=Credibility(
            level=CredibilityLevel.HIGH,
            notes="Official government release"
        ),
        source_config=source_config,
        **kwargs
    )


def create_brazil_case(
    case_id: str,
    media_paths: List[str],
    credibility_level: CredibilityLevel = CredibilityLevel.MEDIUM,
    source_config: Optional["SourceConfig"] = None,
    **kwargs
) -> NormalizedCase:
    """Helper for Brazilian sources (adjust credibility as material is assessed)."""
    if source_config is None:
        source_config = build_source_config_from_registry("brazil-leak-001")
    return NormalizedCase(
        source_id="brazil-leak-001",
        case_id=case_id,
        media_paths=media_paths,
        provenance=Provenance(
            origin="Brazilian government / military / police leak or release",
            release_type="leak",
            classification="unknown"
        ),
        credibility=Credibility(
            level=credibility_level,
            notes="Source-specific credibility assessment pending detailed review."
        ),
        source_config=source_config,
        **kwargs
    )