"""
Unit and integration tests for Multi-View Physical Geometry & Depth-AI Assist.
"""

import numpy as np
import pytest

from app.cv.calibration import CalibrationProfile, CalibrationProfileStatus
from app.cv.label_mapping import CanonicalLabel
from app.cv.multi_view_geometry import DepthAIAssistant, MultiViewGeometryCalculator
from app.domain.sample_unit import SampleUnit


def test_uncalibrated_geometry():
    su = SampleUnit(
        sample_unit_id="su_uncalib_01",
        lot_id="LOT_01",
        resolved_class_semantic=CanonicalLabel.HEALTHY,
    )
    res = MultiViewGeometryCalculator.compute_sample_unit_geometry(su)
    assert res.size_status == "ONION_DIAMETER_UNVALIDATED"
    assert res.length_mm is None
    assert res.width_mm is None
    assert res.geometric_diameter_mm is None
    assert res.volume_cm3 is None
    assert res.model_name == "MULTI_VIEW_ELLIPSOID_ESTIMATE"


def test_calibrated_multi_view_geometry():
    su = SampleUnit(
        sample_unit_id="su_calib_01",
        lot_id="LOT_01",
        resolved_class_semantic=CanonicalLabel.HEALTHY,
    )
    calib = CalibrationProfile(
        calibration_id="calib_01",
        marker_id=0,
        marker_size_mm=50.0,
        reprojection_residual=0.25,
        status=CalibrationProfileStatus.VALID,
        diagnostic_scale_mm_per_px=0.20,
    )

    # 250 x 200 px contour
    top_contour = np.array([[100, 100], [350, 100], [350, 300], [100, 300]], dtype=np.float32)
    side_contour = np.array([[100, 100], [330, 100], [330, 280], [100, 280]], dtype=np.float32)

    res = MultiViewGeometryCalculator.compute_sample_unit_geometry(
        su,
        top_contour_px=top_contour,
        side_contour_px=side_contour,
        top_calibration=calib,
        side_calibration=calib,
    )

    assert res.size_status == "MEASUREMENT_AVAILABLE"
    assert res.length_mm == pytest.approx(50.0, abs=1.0)
    assert res.width_mm == pytest.approx(40.0, abs=1.0)
    assert res.thickness_mm == pytest.approx(36.0, abs=1.0)
    assert res.geometric_diameter_mm > 0.0
    assert res.volume_cm3 > 0.0
    assert 0.0 < res.sphericity <= 1.0
    assert res.aspect_ratio > 1.0
    assert "TOP" in res.views_utilized
    assert "SIDE" in res.views_utilized


def test_depth_ai_assist_consistency():
    rgb = np.ones((100, 100, 3), dtype=np.uint8) * 120
    # Consistent ratio: thickness ~ 38, width ~ 40
    res_ok = DepthAIAssistant.evaluate_relative_depth_consistency(rgb, measured_thickness_mm=38.0, measured_width_mm=40.0)
    assert res_ok.status in ["CONSISTENT", "MEASUREMENT_REQUIRES_REVIEW"]

    # Inconsistent ratio: thickness ~ 10, width ~ 60 (highly flat shape mismatch)
    res_inconsistent = DepthAIAssistant.evaluate_relative_depth_consistency(
        rgb, measured_thickness_mm=10.0, measured_width_mm=60.0, discrepancy_threshold=0.30
    )
    assert res_inconsistent.status == "MEASUREMENT_REQUIRES_REVIEW"
