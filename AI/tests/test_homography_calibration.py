"""
Unit tests for projective homography, planar calibration, and reference measurement.
"""

import numpy as np
import pytest

from app.cv.calibration import (
    MEASUREMENT_DOMAIN_PLANAR,
    PLANAR_LIMITATION_DISCLAIMER,
    compute_marker_homography,
    evaluate_reference_object_measurement,
    measure_planar_contour_mm,
    measure_planar_distance_mm,
    transform_points_to_metric_plane,
)


def test_orthogonal_square_homography() -> None:
    # 4 corners of a 100x100 pixel square representing a 50mm marker
    corners_px = [(100.0, 100.0), (200.0, 100.0), (200.0, 200.0), (100.0, 200.0)]
    H, reproj_err, diag_scale = compute_marker_homography(corners_px, physical_size_mm=50.0)

    assert H is not None
    assert H.shape == (3, 3)
    assert reproj_err < 0.01  # Perfect square should have near-zero reprojection residual
    assert abs(diag_scale - 0.5) < 0.01  # 50mm / 100px = 0.5 mm/px

    # Verify transformation of original corners to physical plane coordinates
    metric_pts = transform_points_to_metric_plane(np.array(corners_px), H)
    expected_metric = np.array([[0.0, 0.0], [50.0, 0.0], [50.0, 50.0], [0.0, 50.0]])
    np.testing.assert_allclose(metric_pts, expected_metric, atol=1e-3)


def test_perspective_homography() -> None:
    # Tilted/trapezoidal perspective corners
    corners_px = [(120.0, 100.0), (280.0, 110.0), (310.0, 290.0), (90.0, 280.0)]
    H, reproj_err, diag_scale = compute_marker_homography(corners_px, physical_size_mm=50.0)

    assert H is not None
    assert reproj_err < 0.1
    assert diag_scale > 0.0


def test_invalid_corners_homography() -> None:
    # Less than 4 points
    H, reproj_err, diag_scale = compute_marker_homography([(10.0, 10.0)], physical_size_mm=50.0)
    assert H is None
    assert reproj_err == float("inf")
    assert diag_scale == 0.0


def test_measure_planar_distance_mm() -> None:
    # 100 px square = 50 mm -> 100 px = 50 mm
    corners_px = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]
    H, _, _ = compute_marker_homography(corners_px, physical_size_mm=50.0)

    # Distance between top-left and top-right (100px) must equal 50mm
    dist_mm = measure_planar_distance_mm((0.0, 0.0), (100.0, 0.0), H)
    assert abs(dist_mm - 50.0) < 1e-3

    # Distance between opposite diagonal corners must equal 50 * sqrt(2) mm
    diag_dist_mm = measure_planar_distance_mm((0.0, 0.0), (100.0, 100.0), H)
    expected_diag = 50.0 * np.sqrt(2)
    assert abs(diag_dist_mm - expected_diag) < 1e-3


def test_measure_planar_contour_mm() -> None:
    corners_px = [(0.0, 0.0), (200.0, 0.0), (200.0, 200.0), (0.0, 200.0)]
    H, _, _ = compute_marker_homography(corners_px, physical_size_mm=100.0)  # 0.5 mm/px

    # A square contour of 80x80 px on plane = 40x40 mm = 1600 mm^2
    contour_px = np.array([[50.0, 50.0], [130.0, 50.0], [130.0, 130.0], [50.0, 130.0]], dtype=np.float32)
    result = measure_planar_contour_mm(contour_px, H)

    assert result["measurement_domain"] == MEASUREMENT_DOMAIN_PLANAR
    assert result["limitation_disclaimer"] == PLANAR_LIMITATION_DISCLAIMER
    assert abs(result["planar_area_mm2"] - 1600.0) < 1.0
    assert abs(result["min_dimension_mm"] - 40.0) < 0.5
    assert abs(result["max_dimension_mm"] - 40.0) < 0.5


def test_evaluate_reference_object_measurement() -> None:
    eval_res = evaluate_reference_object_measurement(
        measured_diameter_mm=40.2,
        ground_truth_diameter_mm=40.0,
    )
    assert eval_res["ground_truth_diameter_mm"] == 40.0
    assert eval_res["measured_planar_diameter_mm"] == 40.2
    assert eval_res["absolute_error_mm"] == 0.2
    assert eval_res["relative_error_pct"] == 0.5
