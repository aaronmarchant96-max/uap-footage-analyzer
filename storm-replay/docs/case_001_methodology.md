<!--
CARDO REI methodology applied to this document.
Reference: [CARDO REI Methodology](PROMPTHOUND-DOCS/CARDO-REI.md)
-->

# Case 001 Methodology Note

## Replay Source

- Event: 2021 Kentucky Tornado Outbreak
- Source: official NWS Paducah outbreak page plus the IEM/NWS radar archive
- Frame set: 24 radar frames from 2021-12-10 18:00 CST through 23:45 CST at 15-minute intervals
- Replay scope: start with one storm sequence from the broader outbreak so the first pass stays readable

## Replay Goal

Review frame-to-frame visual change in a known outbreak window and log candidate activity for human review.

## First Pass Result

- Frames analyzed: 24
- Labels emitted: `low_activity` only
- Candidate review signal: not yet strong enough to separate storm cells with the current thresholding

## Calibration Note

The first pass labeled all 24 frames `low_activity`, which is being treated as a threshold calibration issue rather than a reason to force stronger storm labels.

The goal here is to make the detector explain its scoring more clearly so the next calibration pass can adjust thresholds with evidence instead of guesswork.

## Interpretation

This first pass is a format check and source check, not a performance claim.

The archive path is valid, the frames are real, and the pipeline produces review artifacts.

The next step is to tune the detector so it can distinguish meaningful storm structure from background radar stability.

## Limits

- This is not a forecasting system
- This is not a public alert system
- This is not a validated tornado predictor
- The output is for human review only
