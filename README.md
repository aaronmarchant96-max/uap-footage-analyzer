# UAP Footage Analyzer

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-motion%20analysis-green)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status](https://img.shields.io/badge/status-experimental-orange)

A multi-source framework for ingesting, normalizing, and analyzing UAP footage from different origins using computer vision and structured review workflows.

## Overview

This project extracts reproducible motion events and residual anomalies from real-world UAP footage. It is designed to handle **multiple data sources** (DOD releases, Brazilian leaks, and others) through a consistent pipeline rather than treating each source as a one-off analysis.

Core ideas:
- Source-specific raw data + ingestion adapters
- A single normalized internal representation (`NormalizedCase`)
- Source-aware but not source-specific detection logic
- Separate review queues per source until deliberate cross-source analysis is wanted

The goal is **not** object classification or claims about origin. The goal is clean, reviewable event extraction from messy real footage across different capture conditions.

## Architecture

```
Raw Data (by source)
        │
        ▼
Source Adapters → NormalizedCase
        │
        ▼
Core Detector (source-aware config)
        │
        ▼
Review Queues + Human Analysis
```

See `data/README.md` for the data organization model and `data/metadata/sources.json` for the current registry.

## Current Integration Status (as of late May 2026)

**What is working well:**
- Strong normalized data model (`NormalizedCase`)
- Registry + source adapters (Brazil adapter is functional)
- Ability to ingest new sources and produce consistent review queues
- Legacy V3 residual + motion detector (battle-tested on DOD data)

**What is not yet integrated:**
- The new ingestion layer (NormalizedCase + adapters) is only lightly wired into the core detector via the new `detection.py` module (`run_on_case` / `run_detection_on_case`).
- Full source-aware configuration (pulling thresholds and expected artifacts from `SourceConfig` / the registry) is not yet implemented.
- `sky_residual_v3.py` is still primarily tuned and documented against DOD-style footage.

This is intentional for now. We are prioritizing getting real multi-source data cleanly into the system before tightly coupling the detector. Full source-aware detection configuration is planned as the next major phase.

## Current Components

### Core Package

- `src/uap_footage_analyzer/` — The main library and ingestion framework
  - `schemas.py` — `NormalizedCase` and supporting types (the canonical internal model)
  - `registry.py` — Source registry loader (`data/metadata/sources.json`)
  - `queue_io.py` — Read/write normalized review queues
  - `adapters/brazil.py` — Brazil source adapter
  - `sky_residual_v3.py` — Residual + motion detection engine
  - `detection.py` — Thin integration layer (`run_on_case`) between NormalizedCase and the detector
  - `cli.py` — `uap-ingest` command line tool

- `tools/`
  - `ingest_brazil.py` — Supporting script for Brazil material ingestion

### Sub-projects

- **`storm-replay/`** — A semi-independent toolkit for historical storm imagery analysis and calibration.  
  It is intentionally scoped as a separate tool (not part of the core UAP motion/residual pipeline).  
  See [storm-replay/README.md](storm-replay/README.md) for full details.

Note: `goes_anomaly_hunter/` (GOES satellite thermal analysis) was previously developed in parallel but is now maintained as a separate project and is no longer part of this repository.

## Getting Started

```bash
git clone https://github.com/aaronmarchant96-max/uap-footage-analyzer.git
cd uap-footage-analyzer
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Basic usage

```bash
# Preview Brazil material ingestion
uap-ingest brazil --dry-run --verbose

# Actually write the normalized review queue
uap-ingest brazil

# Inspect current queue
uap-ingest brazil --list
```

See `data/README.md` for how to add new sources and `data/brazil/README.md` for Brazil-specific layout.

See `docs/README.md` for technical and historical documentation.

## Data Organization

All raw material lives under `data/<source>/`.

- `data/dod/` — U.S. Department of Defense public releases
- `data/brazil/` — Brazilian UAP leaks and releases
- `data/metadata/sources.json` — The single source of truth for provenance and credibility

See `data/README.md` for the full philosophy and how to add new sources.

## Current Status (as of May 2026)

- Strong normalized data model and ingestion path for new sources
- Mature V3 residual detection pipeline (originally tuned on DOD 2026-05 release)
- Working CLI for Brazil material ingestion and queue management
- Separate review queues per source

**Notable past run (DOD 2026-05 release):**
- 57 videos
- 570 raw motion events → 23 high-priority review candidates after residual filtering

## Requirements

```bash
pip install -e .
```

### Running tests

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -q
```

## Disclaimer

This tool identifies motion events for manual review. It does not classify objects or make claims about UAP origin. Different capture conditions (gun cameras, consumer video, etc.) produce very different artifact profiles — always treat source context as first-class data.
