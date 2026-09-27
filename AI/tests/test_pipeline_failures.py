"""
Tests verifying failure states and explicit uncertainty handling in the pipeline.
"""

from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import cv2
import pytest

from app.config import load_config
from app.domain import (
    CaptureInput,
    InspectionStatus,
    MarkerFailureCode,
    QualityFailureCode,
)
from app.pipeline import run_inspection


@pytest.fixture
def config():
    return load_config("configs/inspection_config.yaml")


def test_pipeline_missing_image_file(config, tmp_path: Path) -> None:
    non_existent = tmp_path / "missing.jpg"
    capture = CaptureInput(
        capture_id="cap-fail-1",
        image_path=str(non_existent),
        captured_at=datetime.now(timezone.utc),
    )

    observation = run_inspection(capture, config)

    assert observation.capture_id == "cap-fail-1"
    assert observation.overall_status == InspectionStatus.INVALID_CAPTURE
    assert observation.marker_result.validation_status == InspectionStatus.INVALID_CAPTURE
    assert observation.quality_result.quality_status == InspectionStatus.INVALID_CAPTURE
    assert QualityFailureCode.RESOLUTION_INSUFFICIENT in observation.quality_result.failure_codes
    assert len(observation.onion_observations) == 0


def test_pipeline_corrupted_image_file(config, tmp_path: Path) -> None:
    corrupted_file = tmp_path / "corrupted.jpg"
    corrupted_file.write_bytes(b"not an actual image content")

    capture = CaptureInput(
        capture_id="cap-fail-2",
        image_path=str(corrupted_file),
        captured_at=datetime.now(timezone.utc),
    )

    observation = run_inspection(capture, config)

    assert observation.overall_status == InspectionStatus.INVALID_CAPTURE
    assert observation.marker_result.validation_status == InspectionStatus.INVALID_CAPTURE
    assert observation.quality_result.quality_status == InspectionStatus.INVALID_CAPTURE
    assert len(observation.onion_observations) == 0


def test_pipeline_phase0_unimplemented_slice(config, tmp_path: Path) -> None:
    # Create a real, readable test image array
    valid_image_path = tmp_path / "blank_test.png"
    dummy_frame = np.full((400, 400, 3), 128, dtype=np.uint8)
    cv2.imwrite(str(valid_image_path), dummy_frame)

    capture = CaptureInput(
        capture_id="cap-phase0-1",
        image_path=str(valid_image_path),
        captured_at=datetime.now(timezone.utc),
    )

    observation = run_inspection(capture, config)

    # In Phase 1, real ArUco detection runs. For an image lacking the reference marker,
    # the failure state must be CALIBRATION_INVALID with MARKER_NOT_DETECTED.
    assert observation.overall_status == InspectionStatus.CALIBRATION_INVALID
    assert observation.marker_result.validation_status == InspectionStatus.CALIBRATION_INVALID
    assert observation.marker_result.failure_code == MarkerFailureCode.MARKER_NOT_DETECTED
    assert MarkerFailureCode.MARKER_NOT_DETECTED in observation.marker_result.failure_codes
    # Zero fabricated produce observations
    assert len(observation.onion_observations) == 0
