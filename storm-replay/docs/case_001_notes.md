# Case 001 Notes

## Event

- 2021 Kentucky Tornado Outbreak
- Replay focus: the Dec. 10-11, 2021 western Kentucky supercell sequence
- Source imagery: GOES-16 and radar frames from the NWS outbreak pages and NOAA archive
- Event window: evening of Dec. 10, 2021 through early Dec. 11, 2021 local time
- Official summary anchor: the western Kentucky tornado began in Tennessee, tracked into Kentucky, and continued into Illinois, with major damage around Mayfield and a long-track path that makes it useful for replay comparison

## Case 001 Contract

- Input: 20 to 100 historical weather frames
- Output: `events.jsonl`, annotated frames, contact sheet, methodology note
- Claim: visual signal extraction for human review, not forecasting
- Validation: compare extracted candidate activity against the known event timeline

## Review Questions

- Did extracted activity increase inside the known event window?
- Which candidate zones aligned with visible storm structure?
- Which frames were false positives?
- Which event cues were missed?

## Outcome Fields

- Frames reviewed: 24
- Candidate events detected: 0
- Known event window: Dec. 10-11, 2021
- Detected activity inside window: 0
- False positives: 0
- Missed events: unknown with the current conservative thresholding
- Conclusion: archive fetched and replayed; detector tuning is still needed before this becomes a useful review signal

## Notes

Keep this case written as a review artifact, not a prediction claim.
