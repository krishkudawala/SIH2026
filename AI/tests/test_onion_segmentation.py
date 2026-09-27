"""
Unit and integration tests for Onion Segmentation, Defect Area & MobileSAM Annotation Helper.
"""

import numpy as np
import pytest

from app.cv.onion_segmentation import (
    CompactUNet,
    MobileSAMAnnotationHelper,
    OnionSegmenter,
    SegmentationMaskResult,
)


def test_compact_unet_architecture():
    import torch
    model = CompactUNet(in_channels=3, num_classes=2)
    x = torch.randn(1, 3, 128, 128)
    out = model(x)
    assert out.shape == (1, 2, 128, 128)


def test_segment_healthy_crop():
    segmenter = OnionSegmenter()
    # Clean circular bulb on dark background
    crop = np.zeros((150, 150, 3), dtype=np.uint8)
    import cv2
    cv2.circle(crop, (75, 75), 55, (180, 140, 90), -1)

    res, onion_mask, defect_mask = segmenter.segment_crop(crop, crop_id="crop_healthy", condition_hint="HEALTHY")
    assert res.onion_area_px > 0
    assert 0.0 <= res.defect_fraction <= 1.0
    assert res.disclaimer == "Externally visible condition only."
    assert res.mask_quality > 0.5


def test_segment_sprouted_defect_crop():
    segmenter = OnionSegmenter()
    crop = np.zeros((150, 150, 3), dtype=np.uint8)
    import cv2
    cv2.circle(crop, (75, 75), 55, (160, 130, 80), -1)
    # Bright green sprout area
    cv2.rectangle(crop, (65, 30), (85, 70), (40, 200, 50), -1)

    res, onion_mask, defect_mask = segmenter.segment_crop(crop, crop_id="crop_sprouted", condition_hint="SPROUTED")
    assert res.onion_area_px > 0
    assert res.defect_area_px > 0
    assert res.defect_fraction > 0.0
    assert "Externally visible condition only." in res.disclaimer


def test_mobilesam_candidate_annotation():
    dummy_img = np.ones((500, 500, 3), dtype=np.uint8) * 100
    candidate = MobileSAMAnnotationHelper.generate_candidate_mask(dummy_img, (100, 100, 250, 250))
    assert candidate["candidate_mask_status"] == "CANDIDATE_REQUIRES_HUMAN_CORRECTION"
    assert candidate["candidate_area_px"] > 0
    assert "NOT ground truth until validated" in candidate["disclaimer"]
