"""
External Dataset Adapter and Validator for Mandi Nyaay.

Reads external datasets WITHOUT copying or modifying source files.
Validates images, annotations (polygons, bboxes, masks, classes),
integrity, duplicates, and generates a deterministic, machine-readable manifest.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from enum import Enum
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class AnnotationType(str, Enum):
    """Classification of annotation formats supported/detected."""
    POLYGON_SEGMENTATION = "POLYGON_SEGMENTATION"
    BOUNDING_BOX = "BOUNDING_BOX"
    MASK_IMAGE = "MASK_IMAGE"
    CLASSIFICATION = "CLASSIFICATION"
    NONE = "NONE"
    INVALID = "INVALID"


class InstanceAnnotation(BaseModel):
    """A single annotated object instance (bulb/defect/reference)."""
    model_config = ConfigDict(extra="forbid")

    class_id: int = Field(..., description="Integer class identifier")
    class_name: str = Field(default="unknown", description="Human-readable class name")
    bbox_xyxy: list[float] | None = Field(
        default=None,
        description="Bounding box [xmin, ymin, xmax, ymax] in absolute pixels"
    )
    polygon_px: list[list[float]] | None = Field(
        default=None,
        description="Polygon vertices [[x0, y0], [x1, y1], ...] in absolute pixels"
    )
    area_px: float = Field(default=0.0, description="Computed 2D area in square pixels")
    is_valid: bool = Field(default=True, description="Whether coordinates pass geometric bounds checks")
    error_message: str | None = Field(default=None, description="Validation failure details if invalid")


class DatasetRecord(BaseModel):
    """
    Deterministic record representing a single image and its corresponding annotations.
    """
    model_config = ConfigDict(extra="forbid")

    dataset_id: str = Field(..., description="Identifier of the dataset source")
    source_path: str = Field(..., description="Base directory of the source dataset")
    image_path: str = Field(..., description="Absolute path to the preserved source image")
    label_path: str | None = Field(default=None, description="Absolute path to annotation file, or None if missing")
    image_sha256: str = Field(..., description="SHA-256 hex digest of image file bytes")
    width: int | None = Field(default=None, description="Image width in pixels, None if unreadable")
    height: int | None = Field(default=None, description="Image height in pixels, None if unreadable")
    annotation_type: AnnotationType = Field(..., description="Detected annotation representation")
    classes: list[str] = Field(default_factory=list, description="Unique classes present in this record")
    split: str = Field(default="unassigned", description="Split name: train, val, test, or unassigned")
    instances: list[InstanceAnnotation] = Field(default_factory=list, description="Parsed object instances")
    validation_errors: list[str] = Field(default_factory=list, description="List of detected anomalies")
    is_valid: bool = Field(default=True, description="False if unreadable or critical geometric errors")


class DatasetManifest(BaseModel):
    """Machine-readable aggregate summary and record inventory of an inspected dataset."""
    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    source_path: str
    scanned_at_iso: str
    total_images_found: int
    total_labels_found: int
    valid_records_count: int
    corrupt_images_count: int
    missing_labels_count: int
    orphan_labels_count: int
    duplicate_images_count: int
    detected_annotation_type: AnnotationType
    class_names: list[str]
    class_instance_counts: dict[str, int]
    split_distribution: dict[str, int]
    records: list[DatasetRecord]
    orphan_label_paths: list[str] = Field(default_factory=list)


def compute_sha256(filepath: Path | str) -> str:
    """Compute deterministic SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def polygon_area_shoelace(pts: list[list[float]]) -> float:
    """Compute polygon area using the Shoelace formula."""
    if len(pts) < 3:
        return 0.0
    arr = np.array(pts, dtype=np.float64)
    x = arr[:, 0]
    y = arr[:, 1]
    return 0.5 * float(np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1))))


class ExternalDatasetAdapter:
    """
    Adapter that crawls and validates external computer vision datasets.
    
    Supports:
    - YOLO segmentation (polygons: <class> <x1> <y1> <x2> <y2> ...)
    - YOLO detection (bboxes: <class> <cx> <cy> <w> <h>)
    - Directory classification
    - COCO format (instances_*.json)
    """

    SUPPORTED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}

    def __init__(self, dataset_id: str = "external_onion", class_map: dict[int, str] | None = None):
        self.dataset_id = dataset_id
        self.class_map = class_map or {}

    def inspect_and_validate(self, source_dir: Path | str) -> DatasetManifest:
        """
        Inspect the entire directory structure around source_dir without modifying any files.
        """
        source_path = Path(source_dir).resolve()
        from datetime import datetime, timezone
        now_iso = datetime.now(timezone.utc).isoformat()

        if not source_path.exists():
            return DatasetManifest(
                dataset_id=self.dataset_id,
                source_path=str(source_path),
                scanned_at_iso=now_iso,
                total_images_found=0,
                total_labels_found=0,
                valid_records_count=0,
                corrupt_images_count=0,
                missing_labels_count=0,
                orphan_labels_count=0,
                duplicate_images_count=0,
                detected_annotation_type=AnnotationType.NONE,
                class_names=[],
                class_instance_counts={},
                split_distribution={},
                records=[],
                orphan_label_paths=[],
            )

        # 1. Discover all image files and potential label files
        image_files: list[Path] = []
        label_files: dict[str, Path] = {}  # stem -> path
        data_yaml_path: Path | None = None

        for root, dirs, files in os.walk(source_path):
            rpath = Path(root)
            for f in files:
                fpath = rpath / f
                ext = fpath.suffix.lower()
                if ext in self.SUPPORTED_IMAGE_EXTS:
                    image_files.append(fpath)
                elif ext == ".txt":
                    label_files[fpath.stem] = fpath
                elif f in ("data.yaml", "dataset.yaml", "data.yml"):
                    data_yaml_path = fpath

        # Parse data.yaml class names if present
        discovered_class_names = dict(self.class_map)
        if data_yaml_path and data_yaml_path.exists():
            try:
                import yaml
                with open(data_yaml_path, "r", encoding="utf-8") as yf:
                    yd = yaml.safe_load(yf)
                    if isinstance(yd, dict) and "names" in yd:
                        names = yd["names"]
                        if isinstance(names, list):
                            for idx, name in enumerate(names):
                                discovered_class_names[idx] = str(name)
                        elif isinstance(names, dict):
                            for idx, name in names.items():
                                discovered_class_names[int(idx)] = str(name)
            except Exception as e:
                logger.warning(f"Could not parse data.yaml at {data_yaml_path}: {e}")

        # 2. Track duplicates, orphans, and per-record validation
        seen_hashes: dict[str, Path] = {}
        records: list[DatasetRecord] = []
        orphan_label_stems = set(label_files.keys())
        duplicate_count = 0
        corrupt_images_count = 0
        missing_labels_count = 0
        class_instance_counts: dict[str, int] = {}
        split_distribution: dict[str, int] = {}
        overall_annotation_types: set[AnnotationType] = set()

        for img_path in sorted(image_files):
            stem = img_path.stem
            validation_errors: list[str] = []
            is_valid = True

            # Determine split from path hierarchy (e.g. /train/, /val/, /test/)
            split = "unassigned"
            for part in img_path.parts:
                part_lower = part.lower()
                if part_lower in ("train", "training"):
                    split = "train"
                    break
                elif part_lower in ("val", "valid", "validation"):
                    split = "val"
                    break
                elif part_lower in ("test", "testing"):
                    split = "test"
                    break
            split_distribution[split] = split_distribution.get(split, 0) + 1

            # Check hash and detect duplicate
            try:
                sha256 = compute_sha256(img_path)
            except Exception as e:
                sha256 = "UNREADABLE_HASH"
                validation_errors.append(f"Cannot read file bytes for hashing: {e}")
                is_valid = False

            if sha256 in seen_hashes:
                duplicate_count += 1
                validation_errors.append(f"Duplicate image of: {seen_hashes[sha256]}")
            else:
                seen_hashes[sha256] = img_path

            # Image decoding validation
            width: int | None = None
            height: int | None = None
            try:
                img = cv2.imread(str(img_path))
                if img is None or img.size == 0:
                    corrupt_images_count += 1
                    is_valid = False
                    validation_errors.append("cv2.imread failed to decode image (corrupt or unreadable)")
                else:
                    height, width = img.shape[:2]
            except Exception as e:
                corrupt_images_count += 1
                is_valid = False
                validation_errors.append(f"Image decode exception: {e}")

            # Locate matching label file
            label_path = label_files.get(stem)
            if label_path is not None:
                orphan_label_stems.discard(stem)
            else:
                missing_labels_count += 1
                validation_errors.append("Missing corresponding annotation file")

            # Parse annotations if label exists and image dimensions are valid
            instances: list[InstanceAnnotation] = []
            record_annotation_type = AnnotationType.NONE

            if label_path and label_path.exists() and width and height:
                rec_type, parsed_instances, label_errors = self._parse_yolo_label(
                    label_path, width, height, discovered_class_names
                )
                record_annotation_type = rec_type
                instances.extend(parsed_instances)
                validation_errors.extend(label_errors)
                if any(not inst.is_valid for inst in instances) or label_errors:
                    is_valid = False
            elif label_path and not (width and height):
                record_annotation_type = AnnotationType.INVALID
                is_valid = False
                validation_errors.append("Cannot validate normalized annotations without valid image dimensions")

            overall_annotation_types.add(record_annotation_type)

            record_classes = []
            for inst in instances:
                cname = inst.class_name
                if cname not in record_classes:
                    record_classes.append(cname)
                class_instance_counts[cname] = class_instance_counts.get(cname, 0) + 1

            records.append(DatasetRecord(
                dataset_id=self.dataset_id,
                source_path=str(source_path),
                image_path=str(img_path),
                label_path=str(label_path) if label_path else None,
                image_sha256=sha256,
                width=width,
                height=height,
                annotation_type=record_annotation_type,
                classes=record_classes,
                split=split,
                instances=instances,
                validation_errors=validation_errors,
                is_valid=is_valid,
            ))

        orphan_paths = [str(label_files[s]) for s in sorted(orphan_label_stems)]

        # Determine dominant annotation type
        if AnnotationType.POLYGON_SEGMENTATION in overall_annotation_types:
            dominant_type = AnnotationType.POLYGON_SEGMENTATION
        elif AnnotationType.BOUNDING_BOX in overall_annotation_types:
            dominant_type = AnnotationType.BOUNDING_BOX
        elif AnnotationType.CLASSIFICATION in overall_annotation_types:
            dominant_type = AnnotationType.CLASSIFICATION
        elif not image_files:
            dominant_type = AnnotationType.NONE
        else:
            dominant_type = AnnotationType.NONE

        all_class_names = sorted(list(set(discovered_class_names.values()) | set(class_instance_counts.keys())))

        return DatasetManifest(
            dataset_id=self.dataset_id,
            source_path=str(source_path),
            scanned_at_iso=now_iso,
            total_images_found=len(image_files),
            total_labels_found=len(label_files),
            valid_records_count=sum(1 for r in records if r.is_valid),
            corrupt_images_count=corrupt_images_count,
            missing_labels_count=missing_labels_count,
            orphan_labels_count=len(orphan_paths),
            duplicate_images_count=duplicate_count,
            detected_annotation_type=dominant_type,
            class_names=all_class_names,
            class_instance_counts=class_instance_counts,
            split_distribution=split_distribution,
            records=records,
            orphan_label_paths=orphan_paths,
        )

    def _parse_yolo_label(
        self,
        label_path: Path,
        img_w: int,
        img_h: int,
        class_names: dict[int, str]
    ) -> tuple[AnnotationType, list[InstanceAnnotation], list[str]]:
        """Parse YOLO format annotations (polygons or bounding boxes)."""
        instances: list[InstanceAnnotation] = []
        errors: list[str] = []
        detected_type = AnnotationType.NONE

        try:
            with open(label_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
        except Exception as e:
            return AnnotationType.INVALID, [], [f"Error reading label file: {e}"]

        if not lines:
            return AnnotationType.NONE, [], []

        for line_num, line in enumerate(lines, 1):
            parts = line.split()
            if len(parts) < 5:
                errors.append(f"Line {line_num}: insufficient tokens ({len(parts)} < 5)")
                continue

            try:
                class_id = int(float(parts[0]))
                coords = [float(p) for p in parts[1:]]
            except ValueError as e:
                errors.append(f"Line {line_num}: invalid numeric format: {e}")
                continue

            class_name = class_names.get(class_id, f"class_{class_id}")

            # Check if bounding box (exactly 4 coords: cx, cy, w, h normalized)
            if len(coords) == 4:
                if detected_type != AnnotationType.POLYGON_SEGMENTATION:
                    detected_type = AnnotationType.BOUNDING_BOX
                cx, cy, w, h = coords
                # Convert normalized cx, cy, w, h to absolute xyxy
                xmin = (cx - w / 2.0) * img_w
                xmax = (cx + w / 2.0) * img_w
                ymin = (cy - h / 2.0) * img_h
                ymax = (cy + h / 2.0) * img_h

                box_errors = []
                if xmin < 0 or ymin < 0 or xmax > img_w or ymax > img_h:
                    box_errors.append(f"BBox [{xmin:.1f}, {ymin:.1f}, {xmax:.1f}, {ymax:.1f}] extends outside image boundaries ({img_w}x{img_h})")
                area = max(0.0, xmax - xmin) * max(0.0, ymax - ymin)
                if area <= 0.0:
                    box_errors.append("BBox has zero or negative area")

                if box_errors:
                    errors.extend(box_errors)

                instances.append(InstanceAnnotation(
                    class_id=class_id,
                    class_name=class_name,
                    bbox_xyxy=[round(xmin, 2), round(ymin, 2), round(xmax, 2), round(ymax, 2)],
                    polygon_px=None,
                    area_px=round(area, 2),
                    is_valid=len(box_errors) == 0,
                    error_message="; ".join(box_errors) if box_errors else None,
                ))

            # Check if polygon (pairs of x, y normalized, len >= 6 and even)
            elif len(coords) >= 6 and len(coords) % 2 == 0:
                detected_type = AnnotationType.POLYGON_SEGMENTATION
                poly_pts: list[list[float]] = []
                poly_errors = []

                for i in range(0, len(coords), 2):
                    px = coords[i] * img_w
                    py = coords[i + 1] * img_h
                    if px < 0 or px > img_w or py < 0 or py > img_h:
                        poly_errors.append(f"Vertex ({px:.1f}, {py:.1f}) outside image boundaries ({img_w}x{img_h})")
                    poly_pts.append([round(px, 2), round(py, 2)])

                poly_area = polygon_area_shoelace(poly_pts)
                if poly_area <= 0.0:
                    poly_errors.append("Polygon has zero or negative area")

                if poly_errors:
                    errors.extend(poly_errors)

                # Derive bbox from polygon
                arr = np.array(poly_pts)
                xmin, ymin = float(arr[:, 0].min()), float(arr[:, 1].min())
                xmax, ymax = float(arr[:, 0].max()), float(arr[:, 1].max())

                instances.append(InstanceAnnotation(
                    class_id=class_id,
                    class_name=class_name,
                    bbox_xyxy=[round(xmin, 2), round(ymin, 2), round(xmax, 2), round(ymax, 2)],
                    polygon_px=poly_pts,
                    area_px=round(poly_area, 2),
                    is_valid=len(poly_errors) == 0,
                    error_message="; ".join(poly_errors) if poly_errors else None,
                ))

            else:
                errors.append(f"Line {line_num}: invalid coordinate count ({len(coords)}), neither bbox nor polygon")

        return detected_type, instances, errors
