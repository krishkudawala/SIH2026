"""
Tests for Weight Estimation and Weighbridge Cross-Check Engine.
"""

import pytest
from app.cv.calibration import (
    CalibrationProfile,
    CalibrationProfileStatus,
    measure_onion_size_from_bbox,
)
from app.cv.weight_estimation import (
    PhysicalWeightCalibrationPath,
    PhysicalWeightCalibrationRecord,
    WeightEstimationStatus,
    estimate_bulb_weight,
)
from app.domain.weighbridge import (
    WeighbridgeCheckStatus,
    evaluate_weighbridge_cross_check,
)


def test_weight_estimation_uncalibrated_returns_unvalidated():
    # Anti-fabrication rule: without paired data, weight must return UNVALIDATED
    res = estimate_bulb_weight(diameter_mm=55.0, profile=None)
    assert res.weight_status == WeightEstimationStatus.CALIBRATION_NOT_AVAILABLE
    assert res.weight_estimate_g is None

    # Valid dummy profile
    valid_profile = CalibrationProfile(
        calibration_id="calib_001",
        marker_id=0,
        marker_size_mm=50.0,
        reprojection_residual=0.8,
        status=CalibrationProfileStatus.VALID,
    )
    res_no_data = estimate_bulb_weight(diameter_mm=55.0, profile=valid_profile, calibrated_report=None)
    assert res_no_data.weight_status == WeightEstimationStatus.UNVALIDATED
    assert res_no_data.weight_estimate_g is None
    assert "UNVALIDATED" in res_no_data.disclaimer


def test_physical_weight_calibration_path_insufficient_data():
    trainer = PhysicalWeightCalibrationPath()
    # Ingest only 2 records (< 15 threshold)
    trainer.ingest_record(
        PhysicalWeightCalibrationRecord(
            sample_id="s1",
            image_path="test.jpg",
            calibration_id="c1",
            measured_planar_diameter_mm=50.0,
            actual_scale_weight_g=85.0,
        )
    )
    trainer.ingest_record(
        PhysicalWeightCalibrationRecord(
            sample_id="s2",
            image_path="test.jpg",
            calibration_id="c1",
            measured_planar_diameter_mm=55.0,
            actual_scale_weight_g=110.0,
        )
    )
    report = trainer.fit_and_evaluate(min_records_required=15)
    assert report.status == "FIELD_VALIDATION_PENDING"
    assert report.coefficient_a is None
    assert "Insufficient" in report.notes


def test_weighbridge_within_expected_range():
    # Nominal: 100 bags * 50 kg = 5000 kg. Scale = 5050 kg (1% diff)
    wb = evaluate_weighbridge_cross_check(
        certified_lot_weight_kg=5050.0,
        declared_bag_count=100,
        sample_unit_count=20,
        tolerance_pct=10.0,
    )
    assert wb.status == WeighbridgeCheckStatus.WITHIN_EXPECTED_RANGE
    assert wb.requires_review is False
    assert "This is a review signal, not proof of fraud." in wb.review_message
    assert "FRAUD" not in wb.status.value


def test_weighbridge_divergence_review_signal():
    # Nominal: 100 bags * 50 kg = 5000 kg. Scale = 4100 kg (18% diff, > 10% tolerance)
    wb = evaluate_weighbridge_cross_check(
        certified_lot_weight_kg=4100.0,
        declared_bag_count=100,
        sample_unit_count=20,
        tolerance_pct=10.0,
    )
    assert wb.status == WeighbridgeCheckStatus.REVIEW_SIGNAL
    assert wb.requires_review is True
    assert wb.divergence_pct == 21.95
    assert "This is a review signal, not proof of fraud." in wb.review_message
    # Strictly NEVER emit "FRAUD DETECTED"
    assert "FRAUD DETECTED" not in wb.review_message


def test_weighbridge_unavailable_missing_input():
    wb = evaluate_weighbridge_cross_check(
        certified_lot_weight_kg=None,
        declared_bag_count=100,
        sample_unit_count=20,
    )
    assert wb.status == WeighbridgeCheckStatus.UNAVAILABLE
    assert wb.certified_lot_weight_kg is None
