"""
Tests for domain model JSON serialization and deserialization fidelity.
"""

from datetime import datetime, timezone
import json

from app.domain import (
    CalibratedMeasurements,
    CaptureInput,
    ImageQualityObservation,
    InspectionObservation,
    InspectionStatus,
    MarkerFailureCode,
    MarkerObservation,
    OnionObservation,
    PixelMeasurements,
    QualityFailureCode,
)
from app.version import get_processing_version


def test_capture_input_json_roundtrip() -> None:
    now = datetime.now(timezone.utc)
    original = CaptureInput(
        capture_id="cap-ser-1",
        image_path="data/raw/lot_12.png",
        captured_at=now,
        device_metadata={"device_id": "cam_01", "iso": 200},
        session_metadata={"batch": "B1"},
    )

    json_str = original.model_dump_json()
    reconstructed = CaptureInput.model_validate_json(json_str)

    assert reconstructed.capture_id == original.capture_id
    assert reconstructed.image_path == original.image_path
    assert reconstructed.device_metadata == original.device_metadata
    assert reconstructed.session_metadata == original.session_metadata


def test_inspection_observation_json_roundtrip() -> None:
    obs = InspectionObservation(
        capture_id="cap-ser-2",
        marker_result=MarkerObservation(
            detected=True,
            marker_id=0,
            corners_px=[(1.0, 1.0), (50.0, 1.0), (50.0, 50.0), (1.0, 50.0)],
            physical_size_mm=50.0,
            validation_status=InspectionStatus.VALID,
            failure_code=MarkerFailureCode.NONE,
        ),
        quality_result=ImageQualityObservation(
            blur_measure=180.5,
            brightness_measure=110.0,
            exposure_measure=0.02,
            quality_status=InspectionStatus.VALID,
            failure_codes=[],
        ),
        onion_observations=[
            OnionObservation(
                onion_id="onion-01",
                boundary_px=[(10.0, 10.0), (20.0, 10.0), (20.0, 20.0), (10.0, 20.0)],
                bbox=(10.0, 10.0, 20.0, 20.0),
                raw_pixel_measurements=PixelMeasurements(area_px=100.0),
                calibrated_measurements=CalibratedMeasurements(min_diameter_mm=45.0),
            )
        ],
        processing_version=get_processing_version(),
        overall_status=InspectionStatus.VALID,
    )

    json_str = obs.model_dump_json()
    data = json.loads(json_str)

    assert "capture_id" in data
    assert data["capture_id"] == "cap-ser-2"
    assert data["processing_version"] == get_processing_version()
    assert data["overall_status"] == "VALID"

    reconstructed = InspectionObservation.model_validate_json(json_str)
    assert reconstructed.capture_id == obs.capture_id
    assert reconstructed.overall_status == InspectionStatus.VALID
    assert len(reconstructed.onion_observations) == 1
    assert reconstructed.onion_observations[0].onion_id == "onion-01"
