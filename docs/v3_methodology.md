<!--
CARDO REI methodology applied to this document.
Reference: [CARDO REI Methodology](PROMPTHOUND-DOCS/CARDO-REI.md)
-->

# V3 Methodology: Sky Residual Analyzer

## Purpose

V3 reframes the project as a general purpose sky anomaly triage framework.

The goal is not to prove that an event is unusual, artificial, or unexplained.

The goal is to reduce obvious false positives and produce a smaller residual review queue for human analysis.

## Core idea

A candidate event becomes interesting only after the local filters fail to explain it as a common video or sensor issue.

In this version, the framework focuses on local video evidence only. It does not use ADS-B, satellite catalogs, star catalogs, weather feeds, radar, or external sensor data.

That is intentional. V3 is a baseline false positive suppression layer.

## Inputs

The script reads video files from an input directory.

Supported extensions:

```text
.mp4
.mov
.avi
.mkv
```

## Outputs

The V3 run creates:

```text
v3_events.jsonl
v3_residual_review_queue.jsonl
v3_summary.md
keyframes/all_candidates/
keyframes/residual_review/
```

## Metrics

Each detected event receives local video metrics:

```text
motion_score
motion_area_ratio
brightness_delta
edge_delta
phase_shift_x
phase_shift_y
phase_shift_mag
phase_response
blockiness_score
```

## False positive suppression labels

V3 attempts to identify common false positive causes:

```text
scene_cut
full_frame_brightness_shift
camera_motion_or_tracking_shift
compression_artifact
```

If no strong known explanation is found, the event receives one of these review labels:

```text
interesting_motion
residual_unexplained
```

## Residual score

The residual score is not a probability of unusual origin.

It is a review priority score based on how poorly the current local filters explain the event.

A high residual score means:

```text
The event was detected as motion, but current V3 filters did not strongly explain it as an obvious video artifact or full-frame change.
```

## Conservative interpretation

A residual event is not proof of a UAP.

A residual event only means:

```text
Needs manual review against surrounding video context.
```

## Current limitation

V3 does not yet know whether an event is an aircraft, satellite, star, meteor, bird, insect, drone, or weather event.

Those require better metadata or external data sources such as timestamp, camera location, field of view, pointing direction, ADS-B data, orbital elements, and weather data.

## Why this matters

The useful skill demonstrated by this project is not alien attribution.

The useful skill is:

```text
batch video processing
false positive suppression
structured logging
residual scoring
manual review queue generation
conservative evidence handling
```
