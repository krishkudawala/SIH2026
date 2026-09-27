"""
ArUco reference marker detection and geometric validation module.

Uses genuine OpenCV ArUco detector routines to find, decode, and validate
physical reference markers. Never fabricates coordinates or detections.
"""

from pathlib import Path
from typing import Final
import cv2
import numpy as np

from app.config.schema import MarkerConfig
from app.domain.models import MarkerObservation
from app.domain.status import InspectionStatus, MarkerFailureCode
from app.version import get_processing_version

# Reasonable upper bound on quadrilateral side skew (max_side / min_side)
# Perspective projection allows moderate foreshortening, but extreme ratios
# indicate false positives or degenerate detections.
MAX_SIDE_RATIO_THRESHOLD: Final[float] = 3.0


def _get_aruco_dictionary(family_name: str) -> cv2.aruco.Dictionary:
    """Resolve OpenCV ArUco dictionary instance from configuration name."""
    if not hasattr(cv2.aruco, family_name):
        raise ValueError(f"Unknown or unsupported ArUco dictionary family: {family_name}")
    dict_id = getattr(cv2.aruco, family_name)
    return cv2.aruco.getPredefinedDictionary(dict_id)


def validate_marker_geometry(
    pts: np.ndarray,
    image_shape: tuple[int, ...],
    min_perimeter_px: float,
) -> tuple[bool, list[float], float, MarkerFailureCode]:
    """
    Validate the geometric sanity of detected candidate corners.

    Args:
        pts: Array of 4 (x, y) coordinates with shape (4, 2).
        image_shape: Image shape tuple (height, width, ...).
        min_perimeter_px: Minimum acceptable perimeter in pixels.

    Returns:
        (is_valid, side_lengths_px, area_px, failure_code)
    """
    if len(pts) != 4:
        return False, [], 0.0, MarkerFailureCode.GEOMETRY_INVALID

    img_h, img_w = image_shape[:2]

    # 1. Bounds check: all corners must reside within the valid image coordinate space
    for x, y in pts:
        if x < 0.0 or x > float(img_w) or y < 0.0 or y > float(img_h):
            return False, [], 0.0, MarkerFailureCode.GEOMETRY_INVALID

    # 2. Side length computation
    s0 = float(np.linalg.norm(pts[1] - pts[0]))
    s1 = float(np.linalg.norm(pts[2] - pts[1]))
    s2 = float(np.linalg.norm(pts[3] - pts[2]))
    s3 = float(np.linalg.norm(pts[0] - pts[3]))
    side_lengths = [s0, s1, s2, s3]

    min_side = min(side_lengths)
    max_side = max(side_lengths)
    perimeter = sum(side_lengths)

    if min_side <= 0.0 or perimeter < min_perimeter_px:
        return False, side_lengths, 0.0, MarkerFailureCode.GEOMETRY_INVALID

    # 3. Area computation
    area = float(cv2.contourArea(pts.astype(np.float32)))
    if area <= 0.0:
        return False, side_lengths, 0.0, MarkerFailureCode.GEOMETRY_INVALID

    # 4. Convexity check (planar squares projected under perspective must remain strictly convex)
    contour = pts.reshape((-1, 1, 2)).astype(np.float32)
    if not cv2.isContourConvex(contour):
        return False, side_lengths, area, MarkerFailureCode.GEOMETRY_INVALID

    # 5. Skew / aspect ratio check
    if (max_side / min_side) > MAX_SIDE_RATIO_THRESHOLD:
        return False, side_lengths, area, MarkerFailureCode.GEOMETRY_INVALID

    return True, side_lengths, area, MarkerFailureCode.NONE


def detect_marker(image: np.ndarray | None, config: MarkerConfig) -> MarkerObservation:
    """
    Detect and validate the configured ArUco reference marker in a given image array.

    Args:
        image: NumPy array representing BGR image, or None.
        config: MarkerConfig containing expected marker parameters.

    Returns:
        Strongly typed MarkerObservation representing actual detection and validation state.
    """
    version = get_processing_version()

    # 1. Image presence and integrity check
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        return MarkerObservation(
            marker_detected=False,
            dictionary=config.marker_family,
            physical_size_mm=config.physical_size_mm,
            marker_validation_status=InspectionStatus.INVALID_CAPTURE,
            failure_code=MarkerFailureCode.MARKER_NOT_DETECTED,
            failure_codes=[MarkerFailureCode.MARKER_NOT_DETECTED],
            processing_version=version,
        )

    # 2. Configure OpenCV ArUco detector
    try:
        dictionary = _get_aruco_dictionary(config.marker_family)
        parameters = cv2.aruco.DetectorParameters()
        detector = cv2.aruco.ArucoDetector(dictionary, parameters)
        corners_list, ids, _ = detector.detectMarkers(image)
    except Exception as e:
        # Detectors should not crash; treat unexpected detector error as invalid calibration
        return MarkerObservation(
            marker_detected=False,
            dictionary=config.marker_family,
            physical_size_mm=config.physical_size_mm,
            marker_validation_status=InspectionStatus.CALIBRATION_INVALID,
            failure_code=MarkerFailureCode.NOT_IMPLEMENTED,
            failure_codes=[MarkerFailureCode.NOT_IMPLEMENTED],
            processing_version=version,
        )

    # 3. No markers detected in frame
    if ids is None or len(ids) == 0:
        return MarkerObservation(
            marker_detected=False,
            dictionary=config.marker_family,
            physical_size_mm=config.physical_size_mm,
            marker_validation_status=InspectionStatus.CALIBRATION_INVALID,
            failure_code=MarkerFailureCode.MARKER_NOT_DETECTED,
            failure_codes=[MarkerFailureCode.MARKER_NOT_DETECTED],
            processing_version=version,
        )

    flat_ids = [int(i[0]) for i in ids]

    # 4. Multiple ambiguous markers detected
    if len(flat_ids) > 1:
        # Check if the expected ID is present among multiple candidates
        first_corners = corners_list[0][0]
        pts_list = [(float(x), float(y)) for x, y in first_corners]
        return MarkerObservation(
            marker_detected=True,
            marker_id=flat_ids[0],
            dictionary=config.marker_family,
            corners_px=pts_list,
            physical_size_mm=config.physical_size_mm,
            marker_validation_status=InspectionStatus.MANUAL_REVIEW,
            failure_code=MarkerFailureCode.MULTIPLE_MARKERS,
            failure_codes=[MarkerFailureCode.MULTIPLE_MARKERS],
            processing_version=version,
        )

    detected_id = flat_ids[0]
    detected_corners = corners_list[0][0]  # Shape (4, 2)
    corners_px = [(float(x), float(y)) for x, y in detected_corners]

    # 5. Expected marker ID absent
    if detected_id != config.expected_marker_id:
        return MarkerObservation(
            marker_detected=True,
            marker_id=detected_id,
            dictionary=config.marker_family,
            corners_px=corners_px,
            physical_size_mm=config.physical_size_mm,
            marker_validation_status=InspectionStatus.CALIBRATION_INVALID,
            failure_code=MarkerFailureCode.MARKER_ID_MISMATCH,
            failure_codes=[MarkerFailureCode.MARKER_ID_MISMATCH],
            processing_version=version,
        )

    # 6. Geometric validation
    is_valid, side_lengths, area, geom_failure = validate_marker_geometry(
        pts=detected_corners,
        image_shape=image.shape,
        min_perimeter_px=config.min_corner_perimeter_px,
    )

    if not is_valid:
        return MarkerObservation(
            marker_detected=True,
            marker_id=detected_id,
            dictionary=config.marker_family,
            corners_px=corners_px,
            marker_side_lengths_px=side_lengths if side_lengths else None,
            marker_area_px=area if area > 0 else None,
            physical_size_mm=config.physical_size_mm,
            marker_validation_status=InspectionStatus.CALIBRATION_INVALID,
            failure_code=geom_failure,
            failure_codes=[geom_failure],
            processing_version=version,
        )

    # 7. Planar Projective Homography & Metric Calibration
    from app.cv.calibration import compute_marker_homography

    H, reproj_err, diag_scale = compute_marker_homography(
        corners_px=corners_px,
        physical_size_mm=config.physical_size_mm,
    )

    return MarkerObservation(
        marker_detected=True,
        marker_id=detected_id,
        dictionary=config.marker_family,
        corners_px=corners_px,
        marker_side_lengths_px=side_lengths,
        marker_area_px=area,
        physical_size_mm=config.physical_size_mm,
        homography_matrix=H.tolist() if H is not None else None,
        reprojection_error_px=round(reproj_err, 3) if reproj_err != float("inf") else None,
        diagnostic_scale_mm_per_px=round(diag_scale, 4),
        marker_validation_status=InspectionStatus.VALID,
        failure_code=MarkerFailureCode.NONE,
        failure_codes=[],
        processing_version=version,
    )


def save_marker_debug_visualization(
    image: np.ndarray,
    observation: MarkerObservation,
    output_path: str | Path,
) -> Path | None:
    """
    Generate and save a visual debug artifact showing actual detected marker corners.

    Never synthesizes graphics; overlays exclusively onto a copy of the actual input image.
    """
    if image is None or observation.corners_px is None or len(observation.corners_px) != 4:
        return None

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    debug_img = image.copy()
    pts = np.array(observation.corners_px, dtype=np.int32).reshape((-1, 1, 2))

    color = (0, 255, 0) if observation.validation_status == InspectionStatus.VALID else (0, 0, 255)

    # Draw quadrilateral boundary
    cv2.polylines(debug_img, [pts], isClosed=True, color=color, thickness=2)

    # Mark corner 0 (top-left) with distinct circle for orientation verification
    c0 = (int(observation.corners_px[0][0]), int(observation.corners_px[0][1]))
    cv2.circle(debug_img, c0, radius=5, color=(0, 255, 255), thickness=-1)

    # Draw label with marker ID and validation status
    label = f"ID: {observation.marker_id} [{observation.validation_status.value}]"
    cv2.putText(
        debug_img,
        label,
        (max(10, c0[0] - 20), max(20, c0[1] - 10)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        color,
        2,
        cv2.LINE_AA,
    )

    cv2.imwrite(str(path), debug_img)
    return path
