# Case 001 Plan

## Event

- Name: 2021 Kentucky Tornado Outbreak
- Replay focus: the Dec. 10-11, 2021 western Kentucky supercell sequence
- Why this case: it has strong public archive coverage and multiple storm cells for timeline comparison
- Quick stats: one of the deadliest December tornado outbreaks in U.S. history, with the long-tracked western Kentucky tornado crossing Tennessee, Kentucky, and Illinois and producing devastating Mayfield damage

## Case 001 Contract

- Input: 20 to 100 historical weather frames
- Output: `events.jsonl`, annotated frames, contact sheet, methodology note
- Claim: visual signal extraction for human review, not forecasting
- Validation: compare extracted candidate activity against the known event timeline

## Target Window

- Primary replay window: Dec. 10, 2021, evening through early Dec. 11, 2021 local time
- Anchor event: the long-track western Kentucky tornado surveyed by NWS Paducah

## Source Set

- NWS Paducah outbreak page with GOES-16 and radar imagery: https://www.weather.gov/pah/December-10th-11th-2021-Tornado
- NWS Louisville outbreak summary: https://www.weather.gov/lmk/December112021Tornadoes
- NWS Central Region summary with radar composite note: https://www.weather.gov/crh/dec112021
- NOAA NCEI NEXRAD archive and inventory: https://www.ncei.noaa.gov/products/radar/next-generation-weather-radar
- Official framing to preserve: this is a replay/review study, not a tornado prediction system

## Working Inputs

- Public storm imagery frames
- Radar loop frames or radar captures
- Timestamped event timeline from the NWS outbreak pages

## Outputs

- `data/raw/case_001/` for fetched frames
- `data/processed/case_001/` for normalized frames and annotations
- `data/events.jsonl` for candidate labels and motion scores
- `data/processed/case_001_contact_sheet.svg` for the review sheet
- `docs/case_001_notes.md` for the validation summary

## Validation Questions

- Did candidate activity increase inside the known outbreak window?
- Which candidate zones aligned with the storm cells called out by NWS?
- Which frames were false positives?
- Which frames were missed?
- Did the tool stay descriptive instead of predictive?

## Success Criteria

- A human can inspect the contact sheet in under a minute
- The JSONL output is readable and traceable to the frame inputs
- The notes clearly distinguish replay review from forecasting
- The writeup does not overclaim tornado prediction or safety value

## Notes

This case is a replay study, not an alerting system.
