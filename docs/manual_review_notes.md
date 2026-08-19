<!--
CARDO REI methodology applied to this document.
Reference: [CARDO REI Methodology](PROMPTHOUND-DOCS/CARDO-REI.md)
-->

# Manual Review Notes

This document is for human review of extracted candidate motion events.

The labels below are observational only. They do not identify object origin.

## Conservative Review Labels

```text
unknown
camera_motion
scene_cut
tracking_shift
zoom_change
ir_polarity_change
possible_bird
possible_aircraft
possible_drone
possible_artifact
interesting_motion
needs_review
Review Template
File:
Timestamp:
Score:
Initial label:
Visible object:
Motion description:
Known false positive possibility:
Notes:
High Priority Review Candidates

From the V2 run, the highest scoring events should be reviewed first.

video_2605_DOD_111719718_DOD_111719718.mp4 at 123.29s
video_2605_DOD_111721747_DOD_111721747.mp4 at 211.18s
video_2605_DOD_111719752_DOD_111719752.mp4 at 70.30s
video_2605_DOD_111719739_DOD_111719739.mp4 at 62.63s
video_2605_DOD_111720830_DOD_111720830.mp4 at 112.63s
video_2605_DOD_111720899_DOD_111720899.mp4 at 22.63s
Notes

A high anomaly score only means strong frame delta.

Each event must be checked against the surrounding video context before interpretation.
