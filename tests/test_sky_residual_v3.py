"""Tests for the legacy V3 detection helpers in sky_residual_v3.py.

These tests focus on the pure/near-pure functions that contain the actual
decision logic. This is the start of real test coverage on the legacy detector.
"""

import numpy as np

from uap_footage_analyzer.sky_residual_v3 import (
    clamp01,
    motion_score,
    brightness_delta,
    edge_delta,
    phase_camera_motion,
    blockiness_score,
    score_explanations,
    classify_event,
    DEFAULTS,
)


def test_clamp01():
    assert clamp01(-0.5) == 0.0
    assert clamp01(0.0) == 0.0
    assert clamp01(0.5) == 0.5
    assert clamp01(1.0) == 1.0
    assert clamp01(1.7) == 1.0


def test_motion_score_basic():
    # Create two simple frames with a clear difference in one region
    prev = np.zeros((100, 100), dtype=np.uint8)
    curr = prev.copy()
    curr[10:20, 10:20] = 255  # small bright square

    score, area_ratio, mask = motion_score(prev, curr, pixel_delta_threshold=10)

    assert score > 0
    assert 0 < area_ratio < 0.1
    assert mask.shape == (100, 100)


def test_brightness_delta():
    prev = np.full((50, 50), 100, dtype=np.uint8)
    curr = np.full((50, 50), 150, dtype=np.uint8)

    delta = brightness_delta(prev, curr)
    assert abs(delta - 0.196) < 0.01  # (50/255)


def test_edge_delta():
    prev = np.zeros((64, 64), dtype=np.uint8)
    curr = prev.copy()
    curr[20:30, 20:30] = 255

    delta = edge_delta(prev, curr)
    assert delta > 0.0


def test_phase_camera_motion_distinguishes_global_vs_local():
    # Global camera motion (shifted frame)
    prev = np.random.randint(0, 256, (64, 64), dtype=np.uint8)
    curr = np.roll(prev, shift=5, axis=1)

    global_motion, local_motion, ratio, _ = phase_camera_motion(prev, curr)

    assert global_motion > local_motion
    assert ratio > 0.5

    # Local motion only (small bright blob)
    prev2 = np.zeros((64, 64), dtype=np.uint8)
    curr2 = prev2.copy()
    curr2[20:25, 20:25] = 255

    g2, l2, r2, _ = phase_camera_motion(prev2, curr2)
    # For pure local motion we expect the global motion component to be relatively low
    # compared to the local component in this synthetic case.
    assert l2 >= g2 or r2 < 0.6


def test_blockiness_score():
    clean = np.random.randint(0, 256, (64, 64), dtype=np.uint8).astype(np.float32)
    blocky = clean.copy()
    blocky[::8, :] = 255  # artificial block edges

    clean_score = blockiness_score(clean)
    blocky_score = blockiness_score(blocky)

    assert blocky_score > clean_score


def test_score_explanations_basic():
    metrics = {
        "motion_area_ratio": 0.01,
        "brightness_delta": 0.03,
        "edge_delta": 0.05,
        "phase_response": 0.2,
        "phase_shift_mag": 2.0,
        "blockiness_score": 0.1,
    }
    cfg = {
        "brightness_shift_threshold": 0.12,
        "scene_cut_threshold": 0.75,
        "camera_motion_threshold": 0.65,
        "compression_artifact_threshold": 0.55,
    }

    scores = score_explanations(metrics, cfg)

    assert "full_frame_brightness_shift_score" in scores
    assert "scene_cut_score" in scores
    assert "camera_motion_score" in scores
    assert "compression_artifact_score" in scores
    assert all(0.0 <= v <= 1.0 for v in scores.values())


def test_classify_event_labels():
    metrics = {
        "motion_area_ratio": 0.01,
        "brightness_delta": 0.03,
        "edge_delta": 0.05,
        "phase_response": 0.2,
        "phase_shift_mag": 2.0,
        "blockiness_score": 0.1,
    }
    cfg = {
        "small_local_motion_ratio": 0.02,
        "brightness_shift_threshold": 0.12,
        "scene_cut_threshold": 0.75,
        "scene_cut_motion_ratio": 0.45,
        "camera_motion_threshold": 0.65,
        "compression_artifact_threshold": 0.55,
        "residual_review_threshold": 0.65,
    }

    result = classify_event(metrics, cfg)

    assert "label" in result
    assert "residual_score" in result
    assert result["label"] in {
        "interesting_motion",
        "full_frame_brightness_shift",
        "scene_cut",
        "camera_motion_or_tracking_shift",
        "compression_artifact",
        "residual_unexplained",
    }


# =============================================================================
# Expanded edge case tests for classify_event and score_explanations
# =============================================================================

def test_classify_event_scene_cut():
    """High edge_delta + high motion should trigger scene_cut."""
    metrics = {
        "motion_area_ratio": 0.50,
        "brightness_delta": 0.05,
        "edge_delta": 0.30,      # high
        "phase_response": 0.1,
        "phase_shift_mag": 1.0,
        "blockiness_score": 0.05,
    }
    cfg = DEFAULTS.copy()

    result = classify_event(metrics, cfg)
    assert result["label"] == "scene_cut"
    assert result["known_explanation"] == "scene_cut"


def test_classify_event_full_frame_brightness_shift():
    """Very high brightness_delta + decent motion should trigger brightness shift label."""
    metrics = {
        "motion_area_ratio": 0.20,
        "brightness_delta": 0.25,     # very high relative to 0.12 threshold
        "edge_delta": 0.02,
        "phase_response": 0.05,
        "phase_shift_mag": 0.5,
        "blockiness_score": 0.05,
    }
    cfg = DEFAULTS.copy()

    result = classify_event(metrics, cfg)
    assert result["label"] == "full_frame_brightness_shift"


def test_classify_event_camera_motion():
    """High phase response + decent motion should trigger camera motion label."""
    metrics = {
        "motion_area_ratio": 0.30,
        "brightness_delta": 0.02,
        "edge_delta": 0.04,
        "phase_response": 0.95,
        "phase_shift_mag": 12.0,
        "blockiness_score": 0.06,
    }
    cfg = DEFAULTS.copy()

    result = classify_event(metrics, cfg)
    assert result["label"] == "camera_motion_or_tracking_shift"


def test_classify_event_compression_artifact():
    """High blockiness + decent motion + low edges should trigger compression artifact."""
    metrics = {
        "motion_area_ratio": 0.18,
        "brightness_delta": 0.01,
        "edge_delta": 0.02,          # low edges
        "phase_response": 0.1,
        "phase_shift_mag": 1.0,
        "blockiness_score": 0.85,    # very high
    }
    cfg = DEFAULTS.copy()

    result = classify_event(metrics, cfg)
    assert result["label"] == "compression_artifact"


def test_classify_event_residual_unexplained():
    """Low known explanation scores + decent motion → residual unexplained + needs review."""
    metrics = {
        "motion_area_ratio": 0.08,
        "brightness_delta": 0.01,
        "edge_delta": 0.02,
        "phase_response": 0.1,
        "phase_shift_mag": 1.5,
        "blockiness_score": 0.05,
    }
    cfg = DEFAULTS.copy()

    result = classify_event(metrics, cfg)
    assert result["label"] == "residual_unexplained"
    assert result["needs_manual_review"] is True
    assert result["residual_score"] >= cfg["residual_review_threshold"]


def test_classify_event_interesting_motion():
    """Decent but sub-threshold known signals → interesting_motion with manual review."""
    metrics = {
        "motion_area_ratio": 0.15,
        "brightness_delta": 0.08,
        "edge_delta": 0.12,
        "phase_response": 0.55,
        "phase_shift_mag": 6.0,
        "blockiness_score": 0.30,
    }
    cfg = DEFAULTS.copy()

    result = classify_event(metrics, cfg)
    assert result["label"] == "interesting_motion"
    assert result["needs_manual_review"] is True
    assert result["residual_score"] < cfg["residual_review_threshold"]


def test_classify_event_small_motion_increases_residual():
    """Very small motion should boost residual_score."""
    metrics = {
        "motion_area_ratio": 0.005,   # below small_local_motion_ratio
        "brightness_delta": 0.01,
        "edge_delta": 0.01,
        "phase_response": 0.05,
        "phase_shift_mag": 0.5,
        "blockiness_score": 0.02,
    }
    cfg = DEFAULTS.copy()

    result = classify_event(metrics, cfg)
    # Should get the +0.20 boost
    assert result["residual_score"] >= 0.80  # likely high enough for review


def test_score_explanations_respects_thresholds():
    """Changing a threshold should affect the resulting scores."""
    metrics = {
        "motion_area_ratio": 0.10,
        "brightness_delta": 0.10,
        "edge_delta": 0.08,
        "phase_response": 0.3,
        "phase_shift_mag": 4.0,
        "blockiness_score": 0.15,
    }

    cfg_low = DEFAULTS.copy()
    cfg_low["brightness_shift_threshold"] = 0.01   # very sensitive

    cfg_high = DEFAULTS.copy()
    cfg_high["brightness_shift_threshold"] = 0.50  # very insensitive

    scores_low = score_explanations(metrics, cfg_low)
    scores_high = score_explanations(metrics, cfg_high)

    assert scores_low["full_frame_brightness_shift_score"] > scores_high["full_frame_brightness_shift_score"]