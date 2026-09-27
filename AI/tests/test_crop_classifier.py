"""
Unit and integration tests for Second-Stage Onion Crop Classifier & Confidence Calibration.
"""

import numpy as np
import pytest

from app.cv.crop_classifier import (
    CropClassificationResult,
    LightweightCropNet,
    OnionCropClassifier,
    TemperatureScaler,
    compute_ece,
)
from app.cv.label_mapping import CanonicalLabel
from app.domain.onion_observation import ObservationStatus


def test_crop_extraction():
    dummy_img = np.ones((400, 400, 3), dtype=np.uint8) * 128
    crop = OnionCropClassifier.extract_crop(dummy_img, (50, 50, 150, 150), padding_fraction=0.1)
    assert crop.shape[0] > 0
    assert crop.shape[1] > 0
    assert crop.shape[2] == 3


def test_temperature_scaler():
    scaler = TemperatureScaler(temperature=1.5, calibration_version="test_v1")
    logits = np.array([2.0, 1.0, 0.5, -1.0], dtype=np.float32)
    probs = scaler.calibrate_logits(logits)

    assert abs(np.sum(probs) - 1.0) < 1e-5
    assert np.argmax(probs) == 0
    assert probs[0] > probs[1] > probs[2] > probs[3]


def test_crop_classifier_inference():
    clf = OnionCropClassifier()
    dummy_crop = np.ones((120, 120, 3), dtype=np.uint8) * 100
    res = clf.classify_crop(dummy_crop, crop_id="test_crop_01")

    assert res.predicted_class in [
        CanonicalLabel.HEALTHY,
        CanonicalLabel.DAMAGED,
        CanonicalLabel.SPROUTED,
        CanonicalLabel.ROTTEN,
    ]
    assert 0.0 <= res.raw_confidence <= 1.0
    assert 0.0 <= res.calibrated_confidence <= 1.0
    assert "HEALTHY" in res.class_probabilities
    assert res.temperature_applied > 0


def test_arbitration_agree():
    clf = OnionCropClassifier()
    crop_res = CropClassificationResult(
        crop_id="det_1",
        predicted_class=CanonicalLabel.HEALTHY,
        raw_confidence=0.88,
        calibrated_confidence=0.82,
        class_probabilities={"HEALTHY": 0.82, "DAMAGED": 0.08, "SPROUTED": 0.05, "ROTTEN": 0.05},
        temperature_applied=1.25,
        calibration_version="test_v1",
        validation_dataset_hash="hash_01",
    )

    arb = clf.arbitrate_detection_and_crop(
        detector_label=CanonicalLabel.HEALTHY,
        detector_confidence=0.85,
        crop_result=crop_res,
        detection_id="det_1",
    )
    assert arb.arbitration_status == "AGREE"
    assert arb.final_canonical_label == CanonicalLabel.HEALTHY
    assert arb.final_observation_status == ObservationStatus.OBSERVED
    assert arb.review_required is False


def test_arbitration_disagree_triggers_class_conflict():
    clf = OnionCropClassifier()
    # Detector says HEALTHY, Classifier says ROTTEN
    crop_res = CropClassificationResult(
        crop_id="det_2",
        predicted_class=CanonicalLabel.ROTTEN,
        raw_confidence=0.78,
        calibrated_confidence=0.74,
        class_probabilities={"HEALTHY": 0.10, "DAMAGED": 0.10, "SPROUTED": 0.06, "ROTTEN": 0.74},
        temperature_applied=1.25,
        calibration_version="test_v1",
        validation_dataset_hash="hash_01",
    )

    arb = clf.arbitrate_detection_and_crop(
        detector_label=CanonicalLabel.HEALTHY,
        detector_confidence=0.79,
        crop_result=crop_res,
        detection_id="det_2",
    )
    assert arb.arbitration_status == "DISAGREE"
    assert arb.final_canonical_label == CanonicalLabel.CLASS_CONFLICT
    assert arb.final_observation_status == ObservationStatus.CLASS_CONFLICT
    assert arb.review_required is True
    assert "Review required" in arb.title
    assert "CLASS_CONFLICT" in arb.explanation
