# UAP Footage Analyzer

Experimental OpenCV based analysis pipeline for extracting high motion-delta events from publicly released UAP footage datasets.

## Overview

This project scans batches of aerial footage, detects high motion-delta events, extracts candidate keyframes, and logs structured anomaly metadata for manual review.

The goal is not object classification or origin attribution. The goal is reproducible event extraction from messy real world footage.

## Current V2 Result

A full V2 run processed:

```text
57 videos
286 candidate motion events
Threshold: 300000
Frame skip: every 10 frames
Cooldown: 5 seconds
