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

A separate helper can create:

```text
v3_priority_review_queue.jsonl
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

## Candidate event criteria

An event enters `v3_events.jsonl` when the frame difference count crosses the configured motion threshold and the cooldown window allows a new event.

The default V3 criteria are:

```text
motion_threshold: 300000
pixel_delta_threshold: 25
frame_skip: 10
cooldown_sec: 5.0
```

This means V3 compares sampled frames, counts changed pixels above the pixel delta threshold, records an event if the motion score is high enough, then waits at least 5 seconds before recording another event from the same video.

## Labeled false positive criteria

V3 treats an event as a labeled false positive when local video metrics strongly match a known video or sensor level explanation.

Current automatic false positive labels are:

```text
scene_cut
full_frame_brightness_shift
camera_motion_or_tracking_shift
compression_artifact
```

### scene_cut

Assigned when the scene cut score is above the configured threshold and the changed area is large enough.

Default criteria:

```text
scene_cut_score >= 0.75
motion_area_ratio >= 0.45
```

This is meant to catch hard cuts, feed changes, or large scene replacements.

### full_frame_brightness_shift

Assigned when a broad brightness change explains the motion event.

Default criteria:

```text
full_frame_brightness_shift_score >= 0.75
```

This is meant to catch IR exposure changes, gain shifts, bloom, glare, or sensor mode changes.

### camera_motion_or_tracking_shift

Assigned when phase correlation suggests the frame moved as a whole rather than only one object moving inside the frame.

Default criteria:

```text
camera_motion_score >= 0.65
```

This is meant to catch panning, tracking shifts, stabilization jumps, and whole-frame movement.

### compression_artifact

Assigned when blockiness and motion area indicate a possible encoding or frame artifact.

Default criteria:

```text
compression_artifact_score >= 0.55
```

This is meant to catch compression bursts, block artifacts, corrupted frames, or bitrate related distortion.

## Residual candidate criteria

If no known false positive label is assigned, the event is retained for manual review.

V3 uses two residual review labels:

```text
interesting_motion
residual_unexplained
```

### interesting_motion

Assigned when the event is not strongly explained by a current false positive filter, but the residual score is below the high residual threshold.

This still requires human review, but it is not the strongest residual category.

### residual_unexplained

Assigned when no known local explanation is found and the residual score is above the configured threshold.

Default criteria:

```text
known_explanation is null
residual_score >= 0.65
```

This label does not mean the object is truly unexplained. It only means current V3 local filters did not explain the event.

## Priority queue criteria

The priority queue is a narrower human review queue created from residual candidates.

The current helper selects events where:

```text
label is interesting_motion or residual_unexplained
motion_score > 800000
```

Those selected events are written to:

```text
v3_priority_review_queue.jsonl
```

Each priority event receives:

```text
priority_tier: high
priority_reason: high_motion_residual_candidate
human_review_result: null
```

## Priority queue ranking

The priority queue is ranked by `motion_score` in descending order.

This means the largest local frame-delta residual candidates appear first.

This ranking is intentionally simple for V3. It is not a final anomaly score. Future versions should rank by a weighted combination of motion score, residual score, object locality, duration, track consistency, and manual-review feedback.

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
