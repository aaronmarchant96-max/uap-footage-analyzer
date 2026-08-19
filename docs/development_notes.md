<!--
CARDO REI methodology applied to this document.
Reference: [CARDO REI Methodology](PROMPTHOUND-DOCS/CARDO-REI.md)
-->

# Development Notes

## Purpose

This project was built as a lightweight computer vision pipeline for reviewing publicly released UAP footage datasets.

The goal is to reduce manual review workload by extracting high motion-delta candidate events from long video batches.

This is not an object classifier. It is an event extraction tool.

## V1

The first version used simple frame differencing.

Pipeline:

```text
Read video
Compare adjacent frames
Convert difference to grayscale
Blur image
Threshold changed pixels
Count changed pixels
Save frame if score exceeds threshold
V1 Problem

The detector worked, but it produced thousands of false positives.

Likely causes included:

Camera motion
Scene transitions
Compression noise
IR exposure changes
Tracking shifts
Zoom changes
Full-frame brightness changes

This made the initial output too noisy for practical manual review.

V2

V2 added filtering and output control.

Higher motion threshold
THRESHOLD = 300000

This reduced low-level noise detections.

Frame skipping
FRAME_SKIP = 10

This reduced duplicate frame comparisons and improved runtime.

Event cooldown
MIN_SECONDS_BETWEEN_EVENTS = 5

This prevented one continuous motion sequence from generating hundreds of adjacent keyframes.

Output cleanup

The script clears old generated keyframes and logs before a new run so results do not mix across experiments.

Final V2 Result
57 videos processed
286 candidate motion events extracted
Structured JSONL log created
Summary report created
Keyframes extracted for manual review
Interpretation

A high score means a large frame difference occurred.

It does not automatically mean an object is anomalous, artificial, nonconventional, or unidentified.

Manual review is required for every candidate event.


Save it:

```text
CTRL + O
Enter
CTRL + X
File 2: manual review notes

Run this command:

nano docs/manual_review_notes.md

Now paste only this text into nano:

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
