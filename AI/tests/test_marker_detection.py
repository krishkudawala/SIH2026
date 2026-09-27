"""
Tests for ArUco reference marker detection, geometric validation, and failure states.
"""

from pathlib import Path
import numpy as np
import pytest

from app.config import load_config
from app.config.schema import MarkerConfig
from app.cv.marker import (
    detect_marker,
    validate_marker_geometry,
)
from app.domain.status import InspectionStatus, MarkerFailureCode


@pytest.fixture
def marker_config() -> MarkerConfig:
    config = load_config("configs/inspection_config.yaml")
    return config.marker


def test_missing_or_invalid_image_detection(marker_config: MarkerConfig) -> None:
    # None image
    obs_none = detect_marker(None, marker_config)
    assert obs_none.detected is False
    assert obs_none.validation_status == InspectionStatus.INVALID_CAPTURE
    assert MarkerFailureCode.MARKER_NOT_DETECTED in obs_none.failure_codes

    # Empty array
    obs_empty = detect_marker(np.array([], dtype=np.uint8), marker_config)
    assert obs_empty.detected is False
    assert obs_empty.validation_status == InspectionStatus.INVALID_CAPTURE


def test_blank_image_no_marker(marker_config: MarkerConfig) -> None:
    # A blank or uniform image has no ArUco patterns
    blank_image = np.full((500, 500, 3), 200, dtype=np.uint8)
    obs = detect_marker(blank_image, marker_config)

    assert obs.detected is False
    assert obs.marker_id is None
    assert obs.corners_px is None
    assert obs.validation_status == InspectionStatus.CALIBRATION_INVALID
    assert obs.failure_code == MarkerFailureCode.MARKER_NOT_DETECTED
    assert MarkerFailureCode.MARKER_NOT_DETECTED in obs.failure_codes


def test_geometry_validation_out_of_bounds() -> None:
    pts = np.array([[-10.0, 10.0], [50.0, 10.0], [50.0, 50.0], [10.0, 50.0]], dtype=np.float32)
    is_valid, sides, area, failure = validate_marker_geometry(
        pts=pts,
        image_shape=(100, 100, 3),
        min_perimeter_px=50.0,
    )
    assert is_valid is False
    assert failure == MarkerFailureCode.GEOMETRY_INVALID


def test_geometry_validation_non_convex() -> None:
    # Self-intersecting / bowtie quadrilateral
    pts = np.array([[10.0, 10.0], [60.0, 60.0], [60.0, 10.0], [10.0, 60.0]], dtype=np.float32)
    is_valid, sides, area, failure = validate_marker_geometry(
        pts=pts,
        image_shape=(200, 200, 3),
        min_perimeter_px=50.0,
    )
    assert is_valid is False
    assert failure == MarkerFailureCode.GEOMETRY_INVALID


def test_geometry_validation_degenerate_skew() -> None:
    # Extreme aspect ratio (needle-like line)
    pts = np.array([[10.0, 10.0], [100.0, 10.0], [100.0, 11.0], [10.0, 11.0]], dtype=np.float32)
    is_valid, sides, area, failure = validate_marker_geometry(
        pts=pts,
        image_shape=(200, 200, 3),
        min_perimeter_px=50.0,
    )
    assert is_valid is False
    assert failure == MarkerFailureCode.GEOMETRY_INVALID


def test_geometry_validation_valid_quadrilateral() -> None:
    pts = np.array([[20.0, 20.0], [80.0, 22.0], [78.0, 82.0], [21.0, 79.0]], dtype=np.float32)
    is_valid, sides, area, failure = validate_marker_geometry(
        pts=pts,
        image_shape=(200, 200, 3),
        min_perimeter_px=50.0,
    )
    assert is_valid is True
    assert failure == MarkerFailureCode.NONE
    assert len(sides) == 4
    assert area > 0.0


def test_real_raw_images_if_present(marker_config: MarkerConfig) -> None:
    raw_dir = Path("data/raw")
    image_files = []
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.bmp"):
        image_files.extend(raw_dir.glob(ext))

    if not image_files:
        pytest.skip("No real image files found in data/raw/; skipping real-photograph test until user provides image.")

    for img_path in image_files:
        import cv2
        image = cv2.imread(str(img_path))
        assert image is not None, f"Failed to read image at {img_path}"
        obs = detect_marker(image, marker_config)
        assert obs.validation_status in (
            InspectionStatus.VALID,
            InspectionStatus.CALIBRATION_INVALID,
            InspectionStatus.MANUAL_REVIEW,
        )


def test_wrong_marker_id_detected(marker_config: MarkerConfig, monkeypatch) -> None:
    # Simulate detector finding ID 99 when config expects ID 0
    import cv2

    dummy_corners = [np.array([[[20.0, 20.0], [80.0, 20.0], [80.0, 80.0], [20.0, 80.0]]], dtype=np.float32)]
    dummy_ids = np.array([[99]], dtype=np.int32)

    class MockDetector:
        def detectMarkers(self, image):
            return dummy_corners, dummy_ids, []

    monkeypatch.setattr(cv2.aruco, "ArucoDetector", lambda dict_obj, params: MockDetector())

    dummy_img = np.zeros((200, 200, 3), dtype=np.uint8)
    obs = detect_marker(dummy_img, marker_config)

    assert obs.detected is True
    assert obs.marker_id == 99
    assert obs.validation_status == InspectionStatus.CALIBRATION_INVALID
    assert obs.failure_code == MarkerFailureCode.MARKER_ID_MISMATCH
    assert MarkerFailureCode.MARKER_ID_MISMATCH in obs.failure_codes


def test_multiple_markers_ambiguity(marker_config: MarkerConfig, monkeypatch) -> None:
    import cv2

    dummy_corners = [
        np.array([[[10.0, 10.0], [40.0, 10.0], [40.0, 40.0], [10.0, 40.0]]], dtype=np.float32),
        np.array([[[60.0, 60.0], [90.0, 60.0], [90.0, 90.0], [60.0, 90.0]]], dtype=np.float32),
    ]
    dummy_ids = np.array([[0], [1]], dtype=np.int32)

    class MockDetector:
        def detectMarkers(self, image):
            return dummy_corners, dummy_ids, []

    monkeypatch.setattr(cv2.aruco, "ArucoDetector", lambda dict_obj, params: MockDetector())

    dummy_img = np.zeros((200, 200, 3), dtype=np.uint8)
    obs = detect_marker(dummy_img, marker_config)

    assert obs.detected is True
    assert obs.validation_status == InspectionStatus.MANUAL_REVIEW
    assert obs.failure_code == MarkerFailureCode.MULTIPLE_MARKERS
    assert MarkerFailureCode.MULTIPLE_MARKERS in obs.failure_codes


def test_canonical_validation_json_schema(marker_config: MarkerConfig, monkeypatch) -> None:
    import cv2

    dummy_corners = [np.array([[[20.0, 20.0], [80.0, 20.0], [80.0, 80.0], [20.0, 80.0]]], dtype=np.float32)]
    dummy_ids = np.array([[0]], dtype=np.int32)

    class MockDetector:
        def detectMarkers(self, image):
            return dummy_corners, dummy_ids, []

    monkeypatch.setattr(cv2.aruco, "ArucoDetector", lambda dict_obj, params: MockDetector())

    dummy_img = np.zeros((200, 200, 3), dtype=np.uint8)
    obs = detect_marker(dummy_img, marker_config)

    data = obs.to_validation_json(capture_id="cap-test-01")

    # Assert all canonical keys requested in Gate 1 specification
    expected_keys = {
        "capture_id",
        "marker_detected",
        "marker_id",
        "dictionary",
        "corners_px",
        "marker_side_lengths_px",
        "marker_area_px",
        "configured_physical_size_mm",
        "homography_matrix",
        "reprojection_error_px",
        "diagnostic_scale_mm_per_px",
        "measurement_domain",
        "limitation_disclaimer",
        "marker_validation_status",
        "failure_codes",
        "processing_version",
    }
    assert set(data.keys()) == expected_keys
    assert data["marker_detected"] is True
    assert data["marker_id"] == 0
    assert data["marker_validation_status"] == "VALID"
    assert data["configured_physical_size_mm"] == marker_config.physical_size_mm
    assert data["measurement_domain"] == "PLANAR_METRIC_MEASUREMENT"
    assert "homography_matrix" in data and data["homography_matrix"] is not None
    assert len(data["corners_px"]) == 4
    assert len(data["marker_side_lengths_px"]) == 4
    assert data["marker_area_px"] > 0
    assert data["failure_codes"] == []
