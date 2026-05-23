# V3 Initial Results

## Run summary

V3 was run locally against the public DOD footage batch used for this project.

```text
Processed videos: 57
Total candidate events: 570
Residual review candidates: 329
High priority review candidates: 23
```

## Label counts

```text
interesting_motion: 236
full_frame_brightness_shift: 200
residual_unexplained: 93
scene_cut: 41
```

## Triage interpretation

The framework did not classify object origin.

It performed layered triage:

```text
570 total candidate motion events
329 retained for residual/manual review
23 selected as high priority review candidates using a motion score threshold above 800000
```

## Conservative result statement

V3 processed 57 public DOD footage clips and extracted 570 candidate motion events. The framework automatically labeled 241 events as likely scene cuts or full-frame brightness shifts, retained 329 residual review candidates, then reduced the high-priority human review queue to 23 events using a motion-score threshold.

## What this demonstrates

This result demonstrates:

```text
batch video processing
motion-event extraction
false-positive suppression
structured JSONL logging
residual queue generation
priority review filtering
conservative evidence handling
```

## What this does not demonstrate

This result does not prove that any event is anomalous, artificial, nonconventional, or unexplained.

A priority event only means the frame sequence deserves human review against surrounding video context.
