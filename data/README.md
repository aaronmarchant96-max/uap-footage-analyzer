# Data Organization

This directory follows a **source adapter** model feeding into one normalized pipeline.

## Philosophy

- Every data source (DOD, Brazil, future sources) gets its own raw folder.
- All sources are registered in `metadata/sources.json` — this is the single source of truth.
- Raw material stays source-specific.
- After ingestion, everything is converted into a **normalized case schema**.
- The core detector remains source-aware (via config) but not source-specific in code.
- Review queues and analysis outputs can stay separate per source until we deliberately decide to compare them.

This structure prevents DOD assumptions from silently contaminating other datasets (and vice versa).

## Directory Structure

```
data/
├── dod/                    # U.S. Department of Defense releases
│   └── 2026-05/
├── brazil/                 # Brazilian UAP leaks / releases
│   └── [case or batch]/
└── metadata/
    └── sources.json        # The registry. Update this first when adding new material.
```

## Adding a New Source

1. Create a folder under the appropriate region (e.g. `data/brazil/colares-1977/`).
2. Add the raw media.
3. Update `metadata/sources.json` with full provenance and credibility assessment.
4. Write (or extend) a small source adapter that outputs the normalized case schema.
5. Run ingestion → it should land in the shared internal format.

## Normalized Case Schema (Target)

Every ingested item should eventually conform to a common shape containing at minimum:

- `source_id`
- `case_id`
- `media_paths`
- `timestamps`
- `region`
- `provenance`
- `credibility`
- `processing_status`

The normalized schema lives in `src/uap_footage_analyzer/schemas.py`.

## Current Status

- `dod-2026-05`: Fully processed under V3.
- `brazil-leak-001`: Placeholder only. Awaiting real material.

## Rules

- Never hardcode Brazil logic into the DOD path.
- Never assume DOD capture characteristics apply to other sources.
- `sources.json` is authoritative. Code should read from it when possible.