# Storm Replay

> **Note:** Storm Replay is a semi-independent sub-project within the UAP Footage Analyzer repository. While it shares some GOES-related utilities, it has its own scope, methodology, and non-goals (see below). It is not part of the core UAP motion/residual detection pipeline.

Storm Replay is a historical weather signal extraction prototype that reviews public storm imagery, logs candidate activity to JSONL, and compares visual signals against known event timelines for human review.

## Beta Notice

Storm Replay is for human review of storm imagery and radar context. It is not intended for forecasting, alerting, research, or safety decisions.

## MVP Goal

Given a folder of historical weather frames, detect frame-to-frame visual changes, write candidate events to `data/events.jsonl`, create annotated frames, and generate a contact sheet for review.

## Minimal Workflow

```text
raw frames
→ normalized frames
→ motion / intensity extraction
→ candidate labels in events.jsonl
→ annotated frames + contact sheet
→ comparison against known event timeline
→ short validation report
```

## Scope

Keep the first build narrow:

- one historical storm case
- local frame input only
- no prediction language
- no UI
- no notebook layer
- no ingest abstraction until the source is fixed

## Folder Layout

```text
storm-replay/
├── README.md
├── data/
│   ├── raw/
│   ├── processed/
│   └── events.jsonl
├── src/
│   ├── analyze_frames.py
│   ├── annotate_frames.py
│   ├── storm_replay_goes.py
│   └── contact_sheet.py
└── docs/
    ├── methodology.md
    └── case_001_notes.md
```

## Files

- `src/analyze_frames.py`: reads frame sequences, detects visual change, and emits candidate labels.
- `src/annotate_frames.py`: writes annotated review frames with timestamps and scores.
- `src/storm_replay_goes.py`: GOES-16 calibration module with pure helpers, Case 001 thresholds, and JSONL logging.
- `src/contact_sheet.py`: builds a compact visual summary of flagged frames.
- `docs/methodology.md`: explains the replay method and what it does not claim.
- `docs/case_001_plan.md`: defines the first historical replay target and validation questions.
- `docs/case_001_methodology.md`: records the first replay pass and source set.
- `docs/case_001_notes.md`: records the first historical validation case.

## Current Case

- Event: 2021 Kentucky Tornado Outbreak, Dec. 10-11, 2021
- Case 001 contract: 20 to 100 historical weather frames
- Output: `events.jsonl`, annotated frames, contact sheet, methodology note
- Claim: visual signal extraction for human review, not forecasting
- Validation: compare extracted candidate activity against the known event timeline
- `data/events.jsonl`: first case review log
- `data/processed/case_001_contact_sheet.svg`: first contact sheet scaffold
- `docs/case_001_methodology.md`: first pass summary and source note

The current case is a review scaffold. Replace the placeholder frame inputs with a real historical archive before treating results as validation.

## Non-Goals

- forecasting
- alerting
- public safety automation
- complex machine learning
- full dashboard UI

The first proof should be about review quality, not prediction.
