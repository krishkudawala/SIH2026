"""
Unit tests for V7 External Detector Semantic Mapping (Gate 4A).

Verifies:
1. External 0 maps to CanonicalLabel.HEALTHY
2. External 1 maps to CanonicalLabel.DAMAGED
3. External 2 maps to CanonicalLabel.SPROUTED
4. External 3 maps to CanonicalLabel.ROTTEN
5. MappingStatus is VERIFIED
6. Bijective non-ambiguous validation
7. Rejection of unverified or out-of-bounds class IDs
8. Adapter integration in CV Pipeline
"""

from pathlib import Path
import pytest
import numpy as np
import cv2

from app.cv.label_mapping import (
    CanonicalLabel,
    MappingStatus,
    ModelClassMapping,
    V7_EXTERNAL_ADAPTER_MAPPING,
    V7_MAPPING_VERIFIED,
    convert_model_class_id,
    validate_mapping,
)
from app.cv.model_adapter import YOLOModelAdapter, Detection
from app.pipeline.cv_pipeline import MandiNyaayCVPipeline


def test_v7_mapping_status_is_verified():
    """Verify that V7_EXTERNAL_ADAPTER_MAPPING has VERIFIED status."""
    assert V7_EXTERNAL_ADAPTER_MAPPING.status == MappingStatus.VERIFIED
    assert V7_MAPPING_VERIFIED.status == MappingStatus.VERIFIED
    assert V7_EXTERNAL_ADAPTER_MAPPING.mapping_id == "v7_canonical_verified_adapter"


def test_v7_class_id_to_canonical_labels():
    """
    Test that external model class IDs strictly map to verified canonical labels:
    0 -> HEALTHY
    1 -> DAMAGED
    2 -> SPROUTED
    3 -> ROTTEN
    """
    mapping = V7_EXTERNAL_ADAPTER_MAPPING

    # External 0 -> HEALTHY
    label_0, status_0 = convert_model_class_id(0, mapping, raw_class_name="healthy")
    assert label_0 == CanonicalLabel.HEALTHY
    assert status_0 == MappingStatus.VERIFIED

    # External 1 -> DAMAGED
    label_1, status_1 = convert_model_class_id(1, mapping, raw_class_name="damaged")
    assert label_1 == CanonicalLabel.DAMAGED
    assert status_1 == MappingStatus.VERIFIED

    # External 2 -> SPROUTED
    label_2, status_2 = convert_model_class_id(2, mapping, raw_class_name="sprouted")
    assert label_2 == CanonicalLabel.SPROUTED
    assert status_2 == MappingStatus.VERIFIED

    # External 3 -> ROTTEN
    label_3, status_3 = convert_model_class_id(3, mapping, raw_class_name="rotten")
    assert label_3 == CanonicalLabel.ROTTEN
    assert status_3 == MappingStatus.VERIFIED


def test_v7_mapping_validation_clean():
    """Verify that V7_EXTERNAL_ADAPTER_MAPPING passes bijective validation without errors."""
    is_valid, errors = validate_mapping(V7_EXTERNAL_ADAPTER_MAPPING)
    assert is_valid is True
    assert len(errors) == 0


def test_out_of_bounds_class_id_rejected():
    """Verify that any unrecognized class ID returns UNKNOWN_MAPPING with AMBIGUOUS status."""
    mapping = V7_EXTERNAL_ADAPTER_MAPPING
    label_invalid, status_invalid = convert_model_class_id(99, mapping)
    assert label_invalid == CanonicalLabel.UNKNOWN_MAPPING
    assert status_invalid == MappingStatus.AMBIGUOUS


def test_unverified_mapping_blocked():
    """Verify that if mapping status is UNVERIFIED, resolution is blocked."""
    unverified_mapping = ModelClassMapping(
        mapping_id="blocked_test",
        model_name="unverified.pt",
        id_to_canonical={
            0: CanonicalLabel.HEALTHY,
            1: CanonicalLabel.DAMAGED,
            2: CanonicalLabel.SPROUTED,
            3: CanonicalLabel.ROTTEN,
        },
        status=MappingStatus.UNVERIFIED,
    )
    for cid in (0, 1, 2, 3):
        label, status = convert_model_class_id(cid, unverified_mapping)
        assert label == CanonicalLabel.UNKNOWN_MAPPING
        assert status == MappingStatus.UNVERIFIED


def test_pipeline_defaults_to_verified_v7_mapping():
    """Verify that MandiNyaayCVPipeline defaults to V7_EXTERNAL_ADAPTER_MAPPING."""
    dummy_checkpoint = Path("../Onion_grading_system/onion-grading-v7.pt")
    pipeline = MandiNyaayCVPipeline(checkpoint_path=dummy_checkpoint)
    assert pipeline.mapping.status == MappingStatus.VERIFIED
    assert pipeline.mapping.id_to_canonical[2] == CanonicalLabel.SPROUTED
    assert pipeline.mapping.id_to_canonical[3] == CanonicalLabel.ROTTEN
