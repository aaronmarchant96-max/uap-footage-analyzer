<!--
CARDO REI methodology applied to this document.
Reference: [CARDO REI Methodology](PROMPTHOUND-DOCS/CARDO-REI.md)
-->

# Documentation

This folder contains historical and technical documentation, much of it originally written around the DOD V3 pipeline.

## Key Documents

- `v3_methodology.md` — Details of the residual + motion detection approach (still the core of the detector)
- `v3_labels.md` — False positive categories used during review
- `v3_initial_results.md` — Results from the May 2026 DOD release
- `v3_quickstart.md` — Old quickstart (partially outdated)

## New Architecture

For the current multi-source model, normalized schema, and ingestion process, see:

- `../data/README.md` — Data organization and source adapter philosophy
- `../data/metadata/sources.json` — The registry
- `../src/uap_footage_analyzer/schemas.py` — The `NormalizedCase` model

The documentation in this folder is being gradually updated as the project evolves beyond its original DOD-only focus.