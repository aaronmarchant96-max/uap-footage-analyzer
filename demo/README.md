<!--
CARDO REI methodology applied to this document.
Reference: [CARDO REI Methodology](PROMPTHOUND-DOCS/CARDO-REI.md)
-->

# Demo

This folder is reserved for lightweight demonstration assets.

## Easiest Way to Prove the Pipeline Works

Run this single command from the repository root (after `pip install -e .` if desired):

```bash
python tools/demo_brazil_pipeline.py
```

This script:
- Creates completely synthetic Brazil case data in a temporary directory
- Runs the full Brazil ingestion adapter
- Produces real `NormalizedCase` objects
- Writes a normalized review queue
- Loads it back and prints a human-readable summary

No external data or complicated setup required. Perfect for quick validation or demos.

## Other Demo Options

- `uap-ingest brazil --dry-run --verbose` (after `pip install -e .`)
- `python -m pytest tests/ -q` (run the full test suite)

The full raw footage datasets are intentionally **not** included (they are large and should be obtained from official public sources).
