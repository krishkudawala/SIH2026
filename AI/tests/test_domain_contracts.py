"""
Unit tests for domain contracts and typed data structures.
"""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from app.domain import (
    CalibratedMeasurements,
    CaptureInput,
    ImageQualityObservation,
    InspectionObservation,
    InspectionStatus,
    MarkerFailureCode,
    MarkerObservation,
    MeasurementStatus,
    OnionObservation,
    PixelMeasurements,
    QualityFailureCode,
)
from app.version import get_processing_version


def test_capture_input_creation() -> None:
    capture = CaptureInput(
        capture_id="cap-001",
        image_path="data/raw/sample.jpg",
        captured_at=datetime.now(timezone.utc),
        device_metadata={"camera_model": "TestSensor", "iso": 100},
        session_metadata={"mandi": "Nashik", "lot_id": "LOT-99"},
    )
    assert capture.capture_id == "cap-001"
    assert capture.device_metadata["camera_model"] == "TestSensor"
    assert capture.session_metadata["lot_id"] == "LOT-99"


def test_capture_input_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        CaptureInput(
            capture_id="cap-002",
            image_path="data/raw/sample.jpg",
            captured_at=datetime.now(timezone.utc),
            fabricated_score=99.9,  # Disallowed extra field
        )


def test_marker_observation_types() -> None:
    obs = MarkerObservation(
        detected=True,
        marker_id=42,
        corners_px=[(10.0, 10.0), (60.0, 10.0), (60.0, 60.0), (10.0, 60.0)],
        physical_size_mm=50.0,
        validation_status=InspectionStatus.VALID,
        failure_code=MarkerFailureCode.NONE,
    )
    assert obs.detected is True
    assert obs.marker_id == 42
    assert len(obs.corners_px) == 4
    assert obs.validation_status == InspectionStatus.VALID
    assert obs.failure_code == MarkerFailureCode.NONE


def test_quality_observation_failure_codes() -> None:
    obs = ImageQualityObservation(
        blur_measure=45.2,
        brightness_measure=120.0,
        exposure_measure=0.01,
        quality_status=InspectionStatus.RETRY,
        failure_codes=[QualityFailureCode.BLUR_EXCEEDED],
    )
    assert obs.quality_status == InspectionStatus.RETRY
    assert QualityFailureCode.BLUR_EXCEEDED in obs.failure_codes


def test_onion_observation_defaults() -> None:
    onion = OnionObservation(
        onion_id="onion-1",
        bbox=(50.0, 50.0, 150.0, 150.0),
        raw_pixel_measurements=PixelMeasurements(area_px=7850.0, major_axis_px=100.0, minor_axis_px=100.0),
        calibrated_measurements=CalibratedMeasurements(min_diameter_mm=55.0, max_diameter_mm=56.0),
    )
    assert onion.onion_id == "onion-1"
    # Unverified metrics remain None
    assert onion.calibrated_measurements.estimated_weight_g is None
    # Default status in Phase 0 is NOT_IMPLEMENTED
    assert onion.measurement_status == MeasurementStatus.NOT_IMPLEMENTED


def test_inspection_observation_version_and_status() -> None:
    obs = InspectionObservation(
        capture_id="cap-123",
        marker_result=MarkerObservation(
            detected=False,
            validation_status=InspectionStatus.CALIBRATION_INVALID,
            failure_code=MarkerFailureCode.MARKER_NOT_DETECTED,
        ),
        quality_result=ImageQualityObservation(
            quality_status=InspectionStatus.VALID,
            failure_codes=[],
        ),
        onion_observations=[],
        overall_status=InspectionStatus.CALIBRATION_INVALID,
    )
    assert obs.capture_id == "cap-123"
    assert obs.processing_version == get_processing_version()
    assert obs.overall_status == InspectionStatus.CALIBRATION_INVALID
