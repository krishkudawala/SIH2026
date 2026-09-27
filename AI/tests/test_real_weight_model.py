"""
Unit and integration tests for Real Weight Model & Conformal Uncertainty Estimation.
"""

import math
import pytest

from app.cv.real_weight_model import (
    PairedWeightDataPoint,
    RealWeightEstimator,
    WeightModelArtifact,
)


def test_uncalibrated_weight_estimator():
    estimator = RealWeightEstimator(artifact=None)
    pred = estimator.predict(volume_cm3=60.0)
    assert pred.weight_status == "UNVALIDATED"
    assert pred.point_estimate_g is None
    assert pred.prediction_interval_low_g is None
    assert pred.prediction_interval_high_g is None
    assert "UNVALIDATED" in pred.disclaimer


def test_train_and_calibrate_weight_model():
    # Build 14 paired points with physical onion density ~ 1.0 g/cm³
    paired_data = []
    for i, vol in enumerate([25.0, 35.0, 45.0, 55.0, 65.0, 75.0, 85.0, 95.0, 105.0, 115.0, 125.0, 135.0, 145.0, 155.0]):
        actual_weight = round(vol * 1.00 + (0.5 if i % 2 == 0 else -0.5), 1)
        paired_data.append(
            PairedWeightDataPoint(
                sample_id=f"onion_{i}",
                volume_cm3=vol,
                geometric_diameter_mm=round((vol * 6 / math.pi * 1000) ** (1 / 3), 1),
                aspect_ratio=1.05,
                sphericity=0.92,
                defect_fraction=0.0,
                actual_scale_weight_g=actual_weight,
            )
        )

    artifact = RealWeightEstimator.train_and_calibrate(paired_data, coverage_target=0.90)

    assert artifact.train_sample_count > 0
    assert artifact.calibration_sample_count > 0
    assert artifact.holdout_sample_count > 0
    assert artifact.conformal_quantile_q > 0.0
    assert artifact.holdout_metrics.mae_g < 5.0
    assert artifact.holdout_metrics.mape_pct < 10.0

    # Calibrated prediction
    estimator = RealWeightEstimator(artifact=artifact)
    pred = estimator.predict(volume_cm3=65.0, geometric_diameter_mm=50.0)

    assert pred.weight_status == "ESTIMATE_AVAILABLE"
    assert pred.point_estimate_g is not None
    assert pred.prediction_interval_low_g is not None
    assert pred.prediction_interval_high_g is not None
    assert pred.prediction_interval_low_g < pred.point_estimate_g < pred.prediction_interval_high_g
    assert pred.coverage_target == 0.90
