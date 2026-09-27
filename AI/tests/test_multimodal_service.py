"""
Unit and integration tests for End-to-End Multimodal Inspection Service, Model Fusion, OCR & Benchmarks.
"""

from pathlib import Path
import numpy as np
import pytest

from app.cv.calibration import CalibrationProfile, CalibrationProfileStatus
from app.cv.calibration_data_collector import CalibrationDataCollector
from app.cv.clean_detector_benchmark import CleanDetectorBenchmarkSuite
from app.cv.model_fusion import MultimodalFusionEngine
from app.cv.multi_view_geometry import MultiViewDimensionResult
from app.cv.offline_ocr import OfflineOCREngine
from app.cv.real_weight_model import PairedWeightDataPoint, RealWeightEstimator
from app.pipeline.multimodal_inspection_service import MultimodalInspectionService


def test_clean_detector_benchmark():
    report = CleanDetectorBenchmarkSuite.get_benchmark_report()
    assert len(report["candidates"]) >= 4
    names = [c["candidate_name"] for c in report["candidates"]]
    assert "YOLOX-Nano" in names
    assert "RF-DETR-Nano" in names
    assert "RTMDet-Tiny" in names
    for c in report["candidates"]:
        assert c["license_type"]
        assert c["onion_val_ap50"] > 0.80
        assert c["cpu_latency_ms"] > 0.0


def test_offline_ocr_workflow():
    dummy_img = np.ones((200, 400, 3), dtype=np.uint8) * 200
    res = OfflineOCREngine.scan_image(dummy_img, scan_id="scan_lot_01")

    assert res.overall_status == "PENDING_INSPECTOR_CONFIRMATION"
    assert len(res.candidates) > 0
    first = res.candidates[0]
    assert first.status == "CANDIDATE_VALUE"
    assert first.inspector_confirmed is False

    # Inspector confirmation step
    confirmed = OfflineOCREngine.confirm_candidate(first, "LOT-MH-NSK-2026-B08")
    assert confirmed.status == "INSPECTOR_CONFIRMED"
    assert confirmed.inspector_confirmed is True
    assert confirmed.confirmed_text == "LOT-MH-NSK-2026-B08"


def test_calibration_data_collector(tmp_path):
    collector = CalibrationDataCollector(session_id="test_ses_01", storage_dir=tmp_path)
    calib = CalibrationProfile(
        calibration_id="c_01",
        marker_id=0,
        marker_size_mm=50.0,
        reprojection_residual=0.2,
        status=CalibrationProfileStatus.VALID,
    )
    geom = MultiViewDimensionResult(
        sample_unit_id="su_01",
        length_mm=55.0,
        width_mm=50.0,
        thickness_mm=45.0,
        geometric_diameter_mm=49.8,
        aspect_ratio=1.1,
        sphericity=0.90,
        volume_cm3=64.8,
        size_status="MEASUREMENT_AVAILABLE",
    )

    sample = collector.record_sample(
        sample_unit_id="su_01",
        lot_id="LOT_01",
        top_image_path="dummy_top.jpg",
        side_image_path="dummy_side.jpg",
        calibration=calib,
        geometry=geom,
        actual_scale_weight_g=65.2,
        condition="HEALTHY",
    )
    assert sample.actual_scale_weight_g == 65.2
    assert sample.certification_status == "CERTIFIED_PHYSICAL_CALIBRATION_RECORD"

    out_file = collector.save_dataset()
    assert Path(out_file).exists()
    points = collector.to_paired_data_points()
    assert len(points) == 1
    assert points[0].actual_scale_weight_g == 65.2


def test_multimodal_service_real_image():
    img_path = Path("data/raw/01_mixed_damaged_rotten_healthy.jpg")
    if not img_path.exists():
        pytest.skip("Test image not available")

    # Fast trained weight model
    paired = []
    for i in range(12):
        v = 30.0 + i * 10.0
        paired.append(
            PairedWeightDataPoint(
                sample_id=f"p_{i}",
                volume_cm3=v,
                geometric_diameter_mm=45.0,
                aspect_ratio=1.05,
                sphericity=0.91,
                defect_fraction=0.0,
                actual_scale_weight_g=round(v * 1.0, 1),
            )
        )
    artifact = RealWeightEstimator.train_and_calibrate(paired, coverage_target=0.90)
    weight_est = RealWeightEstimator(artifact=artifact)

    calib = CalibrationProfile(
        calibration_id="c_test",
        marker_id=0,
        marker_size_mm=50.0,
        reprojection_residual=0.3,
        status=CalibrationProfileStatus.VALID,
        diagnostic_scale_mm_per_px=0.15,
    )

    service = MultimodalInspectionService(weight_estimator=weight_est)
    report = service.inspect_lot_capture(
        top_image_path=img_path,
        calibration=calib,
        lot_id="LOT_TEST_01",
        weighbridge_net_kg=50.0,
        lot_population_n=800,
    )

    assert report.total_physical_sample_units == len(report.items)
    assert len(report.items) > 0
    assert len(report.evidence_root_hash) == 64
    assert len(report.defect_intervals) > 0
    assert report.quality_grade in ["PASS", "WARN", "FAIL"]
    assert report.sampling_decision.state in ["CONTINUE", "SUFFICIENT", "MANUAL_REVIEW", "REJECT_BOUNDARY"]
