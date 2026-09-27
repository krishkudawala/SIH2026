"""
Tests for ONNX Model Adapter and Mobile Inference Parity.
"""

from pathlib import Path
import pytest
import numpy as np

from app.cv.onnx_adapter import ONNXModelAdapter
from app.cv.label_mapping import CanonicalLabel, MappingStatus


@pytest.fixture
def onnx_model_path():
    p = Path("models/onion-grading-v7.onnx")
    if not p.exists():
        pytest.skip(f"ONNX model file not found at {p}")
    return p


@pytest.fixture
def test_image_path():
    p = Path("data/raw/01_mixed_damaged_rotten_healthy.jpg")
    if not p.exists():
        pytest.skip(f"Real test image not found at {p}")
    return p


def test_onnx_model_metadata(onnx_model_path):
    adapter = ONNXModelAdapter(onnx_model_path)
    meta = adapter.metadata
    assert meta.task == "detect"
    assert meta.num_classes == 4
    assert meta.classes_exposed[0] == "healthy"
    assert meta.classes_exposed[1] == "damaged"
    assert meta.classes_exposed[2] == "sprouted"
    assert meta.classes_exposed[3] == "rotten"


def test_onnx_inference_on_real_image(onnx_model_path, test_image_path):
    adapter = ONNXModelAdapter(onnx_model_path, conf_threshold=0.25, iou_threshold=0.45)
    detections = adapter.predict(test_image_path, capture_id="cap_test")

    # In 01_mixed_damaged_rotten_healthy.jpg, exactly 17 detections are expected
    assert len(detections) == 17

    # Verify every detection has required attributes
    for det in detections:
        assert det.detection_id.startswith("cap_test_det_")
        assert det.confidence >= 0.25
        assert det.canonical_label in (
            CanonicalLabel.HEALTHY,
            CanonicalLabel.DAMAGED,
            CanonicalLabel.SPROUTED,
            CanonicalLabel.ROTTEN,
        )
        assert det.mapping_status == MappingStatus.VERIFIED
        assert det.width_px > 0
        assert det.height_px > 0
        assert det.x2 > det.x1
        assert det.y2 > det.y1


def test_onnx_pure_numpy_inference(onnx_model_path):
    adapter = ONNXModelAdapter(onnx_model_path)
    dummy_img = np.zeros((640, 640, 3), dtype=np.uint8)
    dets = adapter.predict(dummy_img, capture_id="cap_dummy")
    assert isinstance(dets, list)
    for d in dets:
        assert d.detection_id.startswith("cap_dummy_det_")

