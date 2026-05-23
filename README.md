# UAP Footage Analyzer

Experimental OpenCV based analysis pipeline for extracting high motion-delta events from publicly released DOD UAP footage datasets.

## Overview

This project scans batches of aerial footage, detects high motion-delta events, extracts candidate keyframes, and logs structured anomaly metadata for manual review.

The goal is not object classification or origin attribution. The goal is reproducible event extraction from messy real world footage.

## V3 Result — May 22 2026 DOD Release

A full V3 run against the May 2026 DOD UAP footage drop processed:

\```text
57 videos processed
570 candidate motion events detected
329 residual review candidates retained
23 high-priority human review candidates
Dataset: uap052226.zip (DOD public release)
Threshold: 300000
Frame skip: every 10 frames
Cooldown: 5 seconds
\```

V3 introduced residual analysis and automated false positive labeling, reducing 570 raw motion events to 23 high-priority review candidates.

## V2 Result

\```text
57 videos
286 candidate motion events
Threshold: 300000
Frame skip: every 10 frames
Cooldown: 5 seconds
\```

## Pipeline

- `src/sky_residual_v3.py` — main V3 processor
- `uap_processor.py` — V2 batch processor
- `tools/make_priority_queue.py` — priority queue generator

## Docs

- `docs/v3_methodology.md` — detection and filtering methodology
- `docs/v3_labels.md` — false positive label definitions
- `docs/v3_quickstart.md` — setup and usage
- `docs/v3_initial_results.md` — full run results

## Requirements

\```bash
pip install opencv-python
\```

## Disclaimer

This tool identifies motion events for manual review. It does not classify objects or make claims about UAP origin.
