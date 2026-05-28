# Methodology

Storm Replay is a historical review tool, not a forecasting system.

It takes a sequence of public storm frames from a known event window, looks for frame-to-frame visual change, assigns simple review labels, and records those labels in `data/events.jsonl`.

The output is meant for human inspection:

- annotated frames
- a contact sheet of flagged moments
- a short comparison against the known event timeline

## What It Does

- detects visible change between frames
- marks candidate zones for review
- preserves timestamps and review labels
- helps compare extracted signals with the known storm window

## What It Does Not Do

- predict tornadoes or hurricanes
- issue alerts
- replace radar, forecasters, or official weather services
- claim that visual change alone equals ground truth

## Validation Rule

The first version should be tested against at least one known historical event so the output can be compared with the actual event window.
