<!--
CARDO REI methodology applied to this document.
Reference: [CARDO REI Methodology](PROMPTHOUND-DOCS/CARDO-REI.md)
-->

# Case 001 Validation Summary

## Case

- Event: 2021 Kentucky Tornado Outbreak
- Replay scope: 24 radar frames from the Dec. 10, 2021 evening window through late evening
- Goal: human-review signal extraction, not forecasting or alerting

## Quick Notes

Frames that look stable:
- Most frames hold a fairly steady radar background and do not spike into a stronger label band.

Frames that visually stand out:
- A few later frames show slightly higher motion scores, but they still stay within the low-activity range.

Possible false positives:
- None obvious in the current pass because the detector stayed conservative and did not promote any frame into a higher label.

Possible missed activity:
- If there is meaningful storm structure in this slice, the current thresholding is probably too conservative to surface it.

Does low_activity seem fair overall?
- Yes. For this first calibration pass, `low_activity` looks reasonable for the observed score range.

## Validation Takeaway

The first replay pass looks more like a calibration baseline than a detection pass. The scores are real, the timestamps are readable, and the contact sheet is usable for review, but the current thresholds do not yet separate storm structure from background radar motion in a strong way.

## What This Means

- The source archive is usable.
- The review artifacts are working.
- The detector needs further tuning before it can surface meaningful candidate activity.
- The project remains framed as historical replay and human review only.

## Status

Partial validation complete. The next step is threshold tuning or feature refinement, not stronger claims.
