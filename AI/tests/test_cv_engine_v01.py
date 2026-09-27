"""
Unit tests for Mandi Nyaay CV Engine v0.1:
1. Canonical labels
2. Unknown mapping rejection
3. Explicit mapping conversion
4. Bounding-box conversion
5. Malformed detection handling
6. Image quality metrics on real temporary fixture
7. Invalid image handling
8. Pipeline execution
9. JSON serialization
10. Mapping variant experiment helpers
"""

import json
from pathlib import Path

import cv2
import numpy as np
import pytest

from app.cv.label_mapping import (
    CanonicalLabel,
    MappingStatus,
    ModelClassMapping,
    V7_MAPPING_VARIANT_A,
    V7_MAPPING_VARIANT_B,
    convert_model_class_id,
    validate_mapping,
)
from app.cv.model_adapter import Detection, ModelMetadata
from app.cv.quality import QualityGrade, compute_image_quality
from app.domain.onion_observation import (
    ObservationProvenance,
    OnionObservationRecord,
    VisibilityStatus,
)
from app.domain.status import MeasurementStatus
from app.pipeline.cv_pipeline import CVPipelineResult, MandiNyaayCVPipeline
from scripts.evaluate_mapping_variants import prepare_variant_datasets


# 1. Canonical labels
def test_canonical_labels_enum():
    assert CanonicalLabel.HEALTHY.value == "HEALTHY"
    assert CanonicalLabel.DAMAGED.value == "DAMAGED"
    assert CanonicalLabel.ROTTEN.value == "ROTTEN"
    assert CanonicalLabel.SPROUTED.value == "SPROUTED"
    assert CanonicalLabel.UNKNOWN_MAPPING.value == "UNKNOWN_MAPPING"


# 2. Unknown mapping rejection
def test_unknown_mapping_rejection():
    # Null mapping returns UNKNOWN_MAPPING with UNVERIFIED status
    label, status = convert_model_class_id(0, None)
    assert label == CanonicalLabel.UNKNOWN_MAPPING
    assert status == MappingStatus.UNVERIFIED

    # Unverified mapping profile returns UNKNOWN_MAPPING
    unverified_mapping = ModelClassMapping(
        mapping_id="test_unverified",
        model_name="mock.pt",
        id_to_canonical={0: CanonicalLabel.HEALTHY},
        status=MappingStatus.UNVERIFIED,
    )
    label, status = convert_model_class_id(0, unverified_mapping)
    assert label == CanonicalLabel.UNKNOWN_MAPPING
    assert status == MappingStatus.UNVERIFIED

    # Ambiguous class ID not in mapping
    verified_mapping = ModelClassMapping(
        mapping_id="test_verified",
        model_name="mock.pt",
        id_to_canonical={0: CanonicalLabel.HEALTHY},
        status=MappingStatus.VERIFIED,
    )
    label, status = convert_model_class_id(99, verified_mapping)
    assert label == CanonicalLabel.UNKNOWN_MAPPING
    assert status == MappingStatus.AMBIGUOUS


# 3. Explicit mapping conversion
def test_explicit_mapping_conversion():
    mapping = ModelClassMapping(
        mapping_id="test_valid",
        model_name="test.pt",
        id_to_canonical={
            0: CanonicalLabel.HEALTHY,
            1: CanonicalLabel.DAMAGED,
            2: CanonicalLabel.ROTTEN,
            3: CanonicalLabel.SPROUTED,
        },
        raw_class_names={0: "healthy", 1: "damaged", 2: "rotten", 3: "sprouted"},
        status=MappingStatus.VERIFIED,
    )
    is_valid, errors = validate_mapping(mapping)
    assert is_valid is True
    assert len(errors) == 0

    assert convert_model_class_id(0, mapping)[0] == CanonicalLabel.HEALTHY
    assert convert_model_class_id(1, mapping)[0] == CanonicalLabel.DAMAGED
    assert convert_model_class_id(2, mapping)[0] == CanonicalLabel.ROTTEN
    assert convert_model_class_id(3, mapping)[0] == CanonicalLabel.SPROUTED


# 4. Bounding-box conversion
def test_bounding_box_conversion():
    det = Detection(
        detection_id="det_0",
        class_id_external=0,
        class_name_external="healthy",
        canonical_label=CanonicalLabel.HEALTHY,
        mapping_status=MappingStatus.VERIFIED,
        confidence=0.88,
        x1=10.0,
        y1=20.0,
        x2=110.0,
        y2=170.0,
        width_px=100.0,
        height_px=150.0,
    )
    assert det.width_px == 100.0
    assert det.height_px == 150.0
    assert det.x2 > det.x1
    assert det.y2 > det.y1


# 5. Malformed detection handling
def test_malformed_detection_handling():
    # Confidence out of bounds
    with pytest.raises(Exception):
        Detection(
            detection_id="det_err",
            class_id_external=0,
            class_name_external="healthy",
            confidence=1.5,  # Invalid confidence > 1.0
            x1=0.0, y1=0.0, x2=10.0, y2=10.0,
            width_px=10.0, height_px=10.0,
        )


# 6. Image quality metrics on real temporary fixture
def test_image_quality_metrics_on_fixture(tmp_path: Path):
    # Create sharp high-contrast test image (checkerboard)
    sharp = np.zeros((200, 200, 3), dtype=np.uint8)
    sharp[::20, :] = 255
    sharp[:, ::20] = 255
    sharp_metrics = compute_image_quality(sharp)

    assert sharp_metrics.width == 200
    assert sharp_metrics.height == 200
    assert sharp_metrics.blur_score > 100.0

    # Blur the image heavily
    blurred = cv2.GaussianBlur(sharp, (31, 31), 10.0)
    blurred_metrics = compute_image_quality(blurred)

    assert blurred_metrics.blur_score < sharp_metrics.blur_score
    assert blurred_metrics.grade in (QualityGrade.WARN, QualityGrade.FAIL)


# 7. Invalid image handling
def test_invalid_image_handling(tmp_path: Path):
    dummy_checkpoint = tmp_path / "dummy.pt"
    dummy_checkpoint.write_bytes(b"dummy")

    # Pass non-existent image
    pipeline = MandiNyaayCVPipeline(
        checkpoint_path=dummy_checkpoint,
        mapping=V7_MAPPING_VARIANT_A,
    )
    result = pipeline.process_image(tmp_path / "non_existent.jpg")
    assert result.pipeline_status == "INVALID_CAPTURE"
    assert len(result.observations) == 0

    # Pass empty numpy array
    result_empty = pipeline.process_image(np.array([]))
    assert result_empty.pipeline_status == "INVALID_CAPTURE"


# 8. Pipeline execution on real checkpoint
def test_pipeline_execution_real_checkpoint(tmp_path: Path):
    checkpoint_path = Path(r"../Onion_grading_system/onion-grading-v7.pt")
    if not checkpoint_path.exists():
        pytest.skip("onion-grading-v7.pt not found on machine")

    # Create sharp test image with high-contrast features
    test_img = np.zeros((300, 300, 3), dtype=np.uint8)
    test_img[::15, :] = 200
    test_img[:, ::15] = 200
    cv2.circle(test_img, (150, 150), 60, (50, 60, 220), -1)

    pipeline = MandiNyaayCVPipeline(
        checkpoint_path=checkpoint_path,
        mapping=V7_MAPPING_VARIANT_A,
    )
    result = pipeline.process_image(test_img, capture_id="test_cap")

    assert result.pipeline_status in ("SUCCESS", "QUALITY_WARN", "QUALITY_FAIL")
    assert result.image_metadata["width"] == 300
    assert result.image_metadata["height"] == 300
    assert result.model_metadata is not None
    assert result.model_metadata.task == "detect"


# 9. JSON serialization
def test_json_serialization():
    obs = OnionObservationRecord(
        observation_id="obs_1",
        capture_id="cap_1",
        bbox=(10.0, 10.0, 50.0, 50.0),
        class_semantic=CanonicalLabel.HEALTHY,
        confidence=0.92,
        visibility_status=VisibilityStatus.VISIBLE,
        measurement_status=MeasurementStatus.NOT_IMPLEMENTED,
        provenance=ObservationProvenance(
            model_checkpoint="onion-grading-v7.pt",
            raw_class_id=0,
            raw_class_name="healthy",
        ),
    )
    res = CVPipelineResult(
        capture_id="cap_1",
        image_path="test.jpg",
        image_metadata={"width": 100, "height": 100},
        quality=None,
        detections=[],
        observations=[obs],
        mapping_status=MappingStatus.NEEDS_CONTROLLED_VALIDATION,
        model_metadata=None,
        pipeline_status="SUCCESS",
        limitations=["Testing limitation"],
    )
    json_str = res.model_dump_json(indent=2)
    parsed = json.loads(json_str)

    assert parsed["capture_id"] == "cap_1"
    assert parsed["observations"][0]["class_semantic"] == "HEALTHY"
    assert parsed["observations"][0]["confidence"] == 0.92


# 10. Mapping variant experiment helpers
def test_mapping_variant_experiment_helpers(tmp_path: Path):
    source_valid = tmp_path / "source_valid"
    (source_valid / "images").mkdir(parents=True)
    (source_valid / "labels").mkdir(parents=True)

    # Create dummy image and label
    (source_valid / "images" / "test1.jpg").write_bytes(b"image")
    (source_valid / "labels" / "test1.txt").write_text("2 0.5 0.5 0.2 0.2\n3 0.6 0.6 0.3 0.3\n0 0.1 0.1 0.1 0.1\n")

    audit_root = tmp_path / "audit"
    var_a_yaml, var_b_yaml = prepare_variant_datasets(source_valid, audit_root)

    assert var_a_yaml.exists()
    assert var_b_yaml.exists()

    # Check Variant A untouched
    lines_a = (audit_root / "variant_A" / "labels" / "test1.txt").read_text().splitlines()
    assert lines_a[0].startswith("2 ")
    assert lines_a[1].startswith("3 ")
    assert lines_a[2].startswith("0 ")

    # Check Variant B swapped (2 -> 3, 3 -> 2, 0 unchanged)
    lines_b = (audit_root / "variant_B" / "labels" / "test1.txt").read_text().splitlines()
    assert lines_b[0].startswith("3 ")
    assert lines_b[1].startswith("2 ")
    assert lines_b[2].startswith("0 ")
