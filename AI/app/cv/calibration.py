"""
Planar homography and metric calibration module.

Computes a projective homography from the 4 detected ArUco marker corners to
a known metric reference plane.

CRITICAL ARCHITECTURE RULE:
Distinguishes PLANAR METRIC MEASUREMENT (valid strictly on the tray/marker plane)
from 3D OBJECT MEASUREMENT. Does NOT claim a planar marker provides true 3D dimensions.
"""

from typing import Any, Final
import cv2
import numpy as np

MEASUREMENT_DOMAIN_PLANAR: Final[str] = "PLANAR_METRIC_MEASUREMENT"
PLANAR_LIMITATION_DISCLAIMER: Final[str] = (
    "Measurement valid strictly for features and objects coplanar with the reference marker plane. "
    "Does NOT establish 3D object height, vertical profile, or elevation-corrected dimensions."
)


def compute_marker_homography(
    corners_px: list[tuple[float, float]] | np.ndarray,
    physical_size_mm: float,
) -> tuple[np.ndarray | None, float, float]:
    """
    Establish a projective homography from 4 detected marker corners to metric plane coordinates.

    Args:
        corners_px: 4 (x, y) coordinates in clockwise order:
                    [top-left, top-right, bottom-right, bottom-left].
        physical_size_mm: Caliper-verified edge length of the square marker in mm.

    Returns:
        (H, reprojection_error_px, diagnostic_scale_mm_per_px)
        H: 3x3 projective transformation matrix mapping (u, v, 1) -> (X_mm, Y_mm, 1).
        reprojection_error_px: RMS reprojection residual in image pixels.
        diagnostic_scale_mm_per_px: Diagnostic simple scale for sanity checking only.
    """
    pts_src = np.array(corners_px, dtype=np.float32)
    if pts_src.shape != (4, 2):
        return None, float("inf"), 0.0

    # Metric destination coordinates on the marker plane:
    # Corner 0: (0, 0)
    # Corner 1: (physical_size_mm, 0)
    # Corner 2: (physical_size_mm, physical_size_mm)
    # Corner 3: (0, physical_size_mm)
    pts_dst = np.array(
        [
            [0.0, 0.0],
            [physical_size_mm, 0.0],
            [physical_size_mm, physical_size_mm],
            [0.0, physical_size_mm],
        ],
        dtype=np.float32,
    )

    try:
        H = cv2.getPerspectiveTransform(pts_src, pts_dst)
    except Exception:
        return None, float("inf"), 0.0

    # Calculate RMS reprojection error
    try:
        H_inv = np.linalg.inv(H)
        pts_reprojected = cv2.perspectiveTransform(
            pts_dst.reshape(-1, 1, 2),
            H_inv,
        ).reshape(-1, 2)
        residuals = np.linalg.norm(pts_src - pts_reprojected, axis=1)
        reprojection_error_px = float(np.sqrt(np.mean(residuals**2)))
    except Exception:
        reprojection_error_px = float("inf")

    # Diagnostic simple scale factor (sanity check only, not the primary measurement architecture)
    s0 = float(np.linalg.norm(pts_src[1] - pts_src[0]))
    s1 = float(np.linalg.norm(pts_src[2] - pts_src[1]))
    s2 = float(np.linalg.norm(pts_src[3] - pts_src[2]))
    s3 = float(np.linalg.norm(pts_src[0] - pts_src[3]))
    mean_side_px = (s0 + s1 + s2 + s3) / 4.0
    diagnostic_scale_mm_per_px = float(physical_size_mm / mean_side_px) if mean_side_px > 0 else 0.0

    return H, reprojection_error_px, diagnostic_scale_mm_per_px


def transform_points_to_metric_plane(
    points_px: np.ndarray,
    H: np.ndarray,
) -> np.ndarray:
    """
    Transform image pixel coordinates (u, v) to metric coordinates (X_mm, Y_mm) on the reference plane.
    """
    pts = np.asarray(points_px, dtype=np.float32).reshape(-1, 1, 2)
    transformed = cv2.perspectiveTransform(pts, H)
    return transformed.reshape(-1, 2)


def measure_planar_distance_mm(
    pt1_px: tuple[float, float],
    pt2_px: tuple[float, float],
    H: np.ndarray,
) -> float:
    """
    Measure the Euclidean distance in millimeters between two points on the reference plane.
    """
    pts_px = np.array([pt1_px, pt2_px], dtype=np.float32)
    pts_metric = transform_points_to_metric_plane(pts_px, H)
    distance = float(np.linalg.norm(pts_metric[1] - pts_metric[0]))
    return distance


def measure_planar_contour_mm(
    contour_px: np.ndarray,
    H: np.ndarray,
) -> dict[str, Any]:
    """
    Calculate planar geometric dimensions for a contour on the reference plane.

    Returns:
        Structured measurement dictionary with explicit domain classification and limitations.
    """
    metric_pts = transform_points_to_metric_plane(contour_px, H)

    # 1. Planar metric area in mm^2
    area_mm2 = float(cv2.contourArea(metric_pts.astype(np.float32)))

    # 2. Minimum-area bounding box in metric coordinates
    rect = cv2.minAreaRect(metric_pts.astype(np.float32))
    (_, _), (w, h), angle = rect
    min_dim_mm = float(min(w, h))
    max_dim_mm = float(max(w, h))

    # 3. Equivalent circular diameter from area: D = 2 * sqrt(Area / pi)
    equiv_diameter_mm = float(2.0 * np.sqrt(area_mm2 / np.pi)) if area_mm2 > 0 else 0.0

    return {
        "measurement_domain": MEASUREMENT_DOMAIN_PLANAR,
        "limitation_disclaimer": PLANAR_LIMITATION_DISCLAIMER,
        "planar_area_mm2": round(area_mm2, 2),
        "min_dimension_mm": round(min_dim_mm, 2),
        "max_dimension_mm": round(max_dim_mm, 2),
        "equivalent_circular_diameter_mm": round(equiv_diameter_mm, 2),
    }


def evaluate_reference_object_measurement(
    measured_diameter_mm: float,
    ground_truth_diameter_mm: float,
) -> dict[str, Any]:
    """
    Compare measured planar dimension of a physical reference object against caliper ground truth.

    Returns:
        Structured accuracy audit containing absolute and relative error metrics.
    """
    abs_error_mm = abs(measured_diameter_mm - ground_truth_diameter_mm)
    rel_error_pct = (abs_error_mm / ground_truth_diameter_mm) * 100.0 if ground_truth_diameter_mm > 0 else float("inf")

    return {
        "ground_truth_diameter_mm": round(ground_truth_diameter_mm, 3),
        "measured_planar_diameter_mm": round(measured_diameter_mm, 3),
        "absolute_error_mm": round(abs_error_mm, 3),
        "relative_error_pct": round(rel_error_pct, 2),
    }


from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class CalibrationProfileStatus(str, Enum):
    """Lifecycle and audit status of a physical calibration profile."""
    VALID = "VALID"
    INVALID = "INVALID"
    DRIFT_REVIEW = "DRIFT_REVIEW"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class CalibrationProfile(BaseModel):
    """
    Formal reference marker calibration profile.
    Guarantees full provenance, residual tracking, and explicit invalidation.
    """
    model_config = ConfigDict(extra="forbid")

    calibration_id: str = Field(..., description="Unique calibration profile identifier")
    marker_id: int = Field(..., description="ArUco fiducial marker identifier")
    marker_size_mm: float = Field(..., gt=0.0, description="Calibrated marker edge dimension in mm")
    creation_time: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp of calibration creation"
    )
    verification_time: str | None = Field(
        default=None,
        description="ISO timestamp when calibration was last verified"
    )
    reference_set: list[str] = Field(
        default_factory=list,
        description="IDs of reference captures or targets used for calibration"
    )
    reprojection_residual: float = Field(
        ...,
        ge=0.0,
        description="RMS reprojection error in pixels"
    )
    status: CalibrationProfileStatus = Field(
        default=CalibrationProfileStatus.VALID,
        description="Current profile operational validity status"
    )
    version: str = Field(
        default="calib.v1.0",
        description="Calibration software version"
    )
    homography_matrix: list[list[float]] | None = Field(
        default=None,
        description="3x3 projective homography matrix mapping pixels to metric plane (mm)"
    )
    diagnostic_scale_mm_per_px: float | None = Field(
        default=None,
        description="Simple diagnostic scale in mm/pixel"
    )
    protocol_status: str = Field(
        default="FIELD_VALIDATION_PENDING",
        description="Field validation status of physical calibration setup"
    )


class SizeMeasurementResult(BaseModel):
    """
    Produce size measurement outcome.
    Explicitly tracks status, provenance, and field validation limits.
    """
    model_config = ConfigDict(extra="forbid")

    size_mm: float | None = Field(default=None, description="Planar diameter estimate in mm")
    min_diameter_mm: float | None = Field(default=None, description="Minor equatorial diameter in mm")
    max_diameter_mm: float | None = Field(default=None, description="Major equatorial diameter in mm")
    size_status: str = Field(
        default="ONION_DIAMETER_UNVALIDATED",
        description="Status: MEASUREMENT_AVAILABLE, ONION_DIAMETER_UNVALIDATED, MEASUREMENT_REQUIRES_REVIEW, CALIBRATION_INVALID, CALIBRATION_NOT_AVAILABLE"
    )
    provenance: str = Field(
        default="planar_homography_bbox_projection",
        description="Algorithmic pipeline that generated size estimate"
    )
    calibration_id: str | None = Field(default=None, description="ID of calibration profile used")
    measurement_requires_review: bool = Field(
        default=True,
        description="Whether this size measurement requires human review"
    )
    disclaimer: str = Field(
        default="Planar homography does NOT establish true 3D onion diameter. FIELD_VALIDATION_PENDING.",
        description="Mandatory scientific limitation disclaimer"
    )


def create_calibration_profile(
    marker_id: int,
    marker_size_mm: float,
    corners_px: list[tuple[float, float]] | np.ndarray,
    calibration_id: str | None = None,
    max_acceptable_residual_px: float = 3.0,
) -> CalibrationProfile:
    """
    Create and validate a new CalibrationProfile from detected marker corners.
    """
    import uuid
    H, res_px, diag_scale = compute_marker_homography(corners_px, marker_size_mm)

    cid = calibration_id or f"calib_{uuid.uuid4().hex[:8]}"

    if H is None or np.isinf(res_px):
        status = CalibrationProfileStatus.INVALID
    elif res_px > max_acceptable_residual_px:
        status = CalibrationProfileStatus.DRIFT_REVIEW
    else:
        status = CalibrationProfileStatus.VALID

    h_list = H.tolist() if H is not None else None

    return CalibrationProfile(
        calibration_id=cid,
        marker_id=marker_id,
        marker_size_mm=marker_size_mm,
        creation_time=datetime.now(timezone.utc).isoformat(),
        verification_time=datetime.now(timezone.utc).isoformat(),
        reprojection_residual=round(float(res_px), 4) if not np.isinf(res_px) else 999.0,
        status=status,
        homography_matrix=h_list,
        diagnostic_scale_mm_per_px=round(float(diag_scale), 5) if diag_scale > 0 else None,
        protocol_status="FIELD_VALIDATION_PENDING",
    )


def measure_onion_size_from_bbox(
    bbox: tuple[float, float, float, float],
    profile: CalibrationProfile | None,
) -> SizeMeasurementResult:
    """
    Project 2D bounding box through planar homography to estimate planar bulb dimensions.

    CRITICAL RULE:
    Planar homography does NOT establish true 3D diameter.
    Returns ONION_DIAMETER_UNVALIDATED even when calibration is valid.
    Blocks measurement when calibration is INVALID or NOT_AVAILABLE.
    """
    if profile is None or profile.status == CalibrationProfileStatus.NOT_AVAILABLE:
        return SizeMeasurementResult(
            size_mm=None,
            size_status="CALIBRATION_NOT_AVAILABLE",
            measurement_requires_review=True,
            calibration_id=None,
        )

    if profile.status == CalibrationProfileStatus.INVALID:
        return SizeMeasurementResult(
            size_mm=None,
            size_status="CALIBRATION_INVALID",
            measurement_requires_review=True,
            calibration_id=profile.calibration_id,
        )

    if profile.homography_matrix is None:
        return SizeMeasurementResult(
            size_mm=None,
            size_status="CALIBRATION_INVALID",
            measurement_requires_review=True,
            calibration_id=profile.calibration_id,
        )

    H = np.array(profile.homography_matrix, dtype=np.float32)
    x1, y1, x2, y2 = bbox

    # Project the 4 bbox corners onto metric plane
    corners = np.array([
        [x1, y1],
        [x2, y1],
        [x2, y2],
        [x1, y2],
    ], dtype=np.float32)

    try:
        metric_pts = transform_points_to_metric_plane(corners, H)
        width_mm = float(np.linalg.norm(metric_pts[1] - metric_pts[0]))
        height_mm = float(np.linalg.norm(metric_pts[2] - metric_pts[1]))
        min_d = round(min(width_mm, height_mm), 2)
        max_d = round(max(width_mm, height_mm), 2)
        # Equatorial diameter approximation (mean of projected axes)
        equiv_d = round((width_mm + height_mm) / 2.0, 2)

        if profile.status == CalibrationProfileStatus.DRIFT_REVIEW:
            status = "MEASUREMENT_REQUIRES_REVIEW"
        else:
            status = "ONION_DIAMETER_UNVALIDATED"

        return SizeMeasurementResult(
            size_mm=equiv_d,
            min_diameter_mm=min_d,
            max_diameter_mm=max_d,
            size_status=status,
            provenance="planar_homography_bbox_projection",
            calibration_id=profile.calibration_id,
            measurement_requires_review=True,
            disclaimer="Planar homography does NOT establish true 3D onion diameter. FIELD_VALIDATION_PENDING.",
        )
    except Exception:
        return SizeMeasurementResult(
            size_mm=None,
            size_status="MEASUREMENT_REQUIRES_REVIEW",
            measurement_requires_review=True,
            calibration_id=profile.calibration_id,
        )

