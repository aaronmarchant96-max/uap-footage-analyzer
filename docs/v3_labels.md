<!--
CARDO REI methodology applied to this document.
Reference: [CARDO REI Methodology](PROMPTHOUND-DOCS/CARDO-REI.md)
-->

# V3 Labels

These labels are conservative review labels. They do not identify object origin.

## Known false positive labels

### scene_cut

A large frame transition where much of the image changes suddenly.

Common causes:

```text
edited footage
cut between camera feeds
hard transition
full scene replacement
```

### full_frame_brightness_shift

A broad brightness change across much of the frame.

Common causes:

```text
IR exposure change
auto gain adjustment
sensor mode change
sudden glare
flash or bloom
```

### camera_motion_or_tracking_shift

A frame wide movement pattern consistent with camera movement, tracking adjustment, panning, zoom shift, or stabilization changes.

### compression_artifact

A motion event likely caused by video encoding noise, block artifacts, corrupted frames, or bitrate related distortion.

## Review labels

### interesting_motion

Motion that passes the detection threshold and is not strongly explained by current V3 known false positive filters.

This label still requires manual review.

### residual_unexplained

A higher priority review candidate where local V3 filters did not strongly explain the event.

This does not mean unusual origin.

It means the event should be reviewed against surrounding frames.

## Labels intentionally not used yet

V3 does not assign these labels automatically:

```text
aircraft
satellite
star
meteor
bird
insect
drone
weather
UAP
```

Those labels require stronger metadata, external reference data, or human review.

## Interpretation rule

Use this wording:

```text
This event remains in the residual review queue.
```

Avoid this wording:

```text
This event is unexplained.
This event is anomalous.
This event is a UAP.
```
