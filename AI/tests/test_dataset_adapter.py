"""
Unit tests for external dataset adapter, validation logic, and manifest creation.
"""

import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest

from app.cv.dataset_adapter import (
    AnnotationType,
    ExternalDatasetAdapter,
    compute_sha256,
    polygon_area_shoelace,
)


def test_shoelace_area_calculation():
    """Verify Shoelace formula on known geometric shapes."""
    # 10x10 square
    square = [[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0]]
    assert polygon_area_shoelace(square) == pytest.approx(100.0, rel=1e-3)

    # Right triangle: base 10, height 5 -> area = 25
    triangle = [[0.0, 0.0], [10.0, 0.0], [0.0, 5.0]]
    assert polygon_area_shoelace(triangle) == pytest.approx(25.0, rel=1e-3)

    # Degenerate polygon (< 3 points)
    assert polygon_area_shoelace([[0.0, 0.0], [10.0, 10.0]]) == 0.0


def test_sha256_computation(tmp_path: Path):
    """Verify deterministic SHA-256 calculation."""
    test_file = tmp_path / "test.bin"
    test_file.write_bytes(b"mandi_nyaay_real_data_test")
    h1 = compute_sha256(test_file)
    h2 = compute_sha256(test_file)
    assert h1 == h2
    assert len(h1) == 64


def test_adapter_with_clean_synthetic_dataset(tmp_path: Path):
    """
    Test adapter discovery and parsing using an isolated temporary folder structure.
    Does NOT affect production data or external directories.
    """
    dataset_dir = tmp_path / "synthetic_dataset"
    images_dir = dataset_dir / "train" / "images"
    labels_dir = dataset_dir / "train" / "labels"
    images_dir.mkdir(parents=True)
    labels_dir.mkdir(parents=True)

    # Create dummy 100x100 white image
    img = np.ones((100, 100, 3), dtype=np.uint8) * 255
    img_path = images_dir / "onion_001.jpg"
    cv2.imwrite(str(img_path), img)

    # Create valid YOLO polygon annotation: class 0, square from (0.2, 0.2) to (0.8, 0.8)
    label_path = labels_dir / "onion_001.txt"
    label_path.write_text("0 0.2 0.2 0.8 0.2 0.8 0.8 0.2 0.8\n")

    adapter = ExternalDatasetAdapter(dataset_id="test_ds", class_map={0: "onion"})
    manifest = adapter.inspect_and_validate(dataset_dir)

    assert manifest.total_images_found == 1
    assert manifest.total_labels_found == 1
    assert manifest.valid_records_count == 1
    assert manifest.detected_annotation_type == AnnotationType.POLYGON_SEGMENTATION
    assert manifest.duplicate_images_count == 0
    assert manifest.corrupt_images_count == 0
    assert manifest.missing_labels_count == 0
    assert manifest.orphan_labels_count == 0

    record = manifest.records[0]
    assert record.is_valid is True
    assert record.width == 100
    assert record.height == 100
    assert len(record.instances) == 1
    inst = record.instances[0]
    assert inst.class_name == "onion"
    # Polygon is 60x60 pixels in a 100x100 image -> area = 3600
    assert inst.area_px == pytest.approx(3600.0, rel=1e-2)


def test_adapter_flags_corrupt_and_out_of_bounds(tmp_path: Path):
    """Verify corrupted images and out-of-bounds annotations are flagged as invalid."""
    dataset_dir = tmp_path / "dirty_dataset"
    dataset_dir.mkdir(parents=True)

    # 1. Corrupt image file
    corrupt_img = dataset_dir / "corrupt.jpg"
    corrupt_img.write_bytes(b"not an image file")

    # 2. Valid image with out-of-bounds polygon
    valid_img = dataset_dir / "valid_image.png"
    cv2.imwrite(str(valid_img), np.zeros((100, 100, 3), dtype=np.uint8))

    # YOLO polygon coords > 1.0 (outside boundaries)
    label_file = dataset_dir / "valid_image.txt"
    label_file.write_text("0 0.1 0.1 1.5 0.1 1.5 1.5 0.1 1.5\n")

    # 3. Orphan label
    orphan_label = dataset_dir / "orphan.txt"
    orphan_label.write_text("0 0.2 0.2 0.4 0.2 0.4 0.4 0.2 0.4\n")

    adapter = ExternalDatasetAdapter(dataset_id="dirty_ds")
    manifest = adapter.inspect_and_validate(dataset_dir)

    assert manifest.total_images_found == 2
    assert manifest.corrupt_images_count == 1
    assert manifest.orphan_labels_count == 1

    # Record 1 (corrupt) should be invalid
    rec_corrupt = next(r for r in manifest.records if "corrupt" in r.image_path)
    assert rec_corrupt.is_valid is False

    # Record 2 (out of bounds) should be invalid
    rec_oob = next(r for r in manifest.records if "valid_image" in r.image_path)
    assert rec_oob.is_valid is False
    assert any("outside image boundaries" in err for err in rec_oob.validation_errors)
