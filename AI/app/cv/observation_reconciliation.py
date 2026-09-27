"""
Cross-Class Observation Reconciliation Module for Mandi Nyaay (Gate 4B).

Prevents one physical onion from becoming multiple observations when the detector
produces overlapping bounding boxes.

Guarantees:
1. Same-class overlapping detections collapse to the highest-confidence detection.
2. Cross-class overlapping detections collapse to ONE physical observation with
   observation_status = CLASS_CONFLICT and preserve candidate classes, confidences,
   and source detection IDs.
3. No double-counting of produce items.
4. Strict rejection of malformed bounding boxes.
5. Deterministic clustering and reconciliation.
"""

from __future__ import annotations

import math
from typing import Sequence
from pydantic import BaseModel, ConfigDict, Field

from app.cv.label_mapping import CanonicalLabel
from app.cv.model_adapter import Detection
from app.domain.onion_observation import (
    ObservationProvenance,
    ObservationStatus,
    OnionObservationRecord,
    resolve_annotation_ui,
)
from app.domain.status import MeasurementStatus
from app.version import get_processing_version

DEFAULT_RECONCILIATION_IOU_THRESHOLD: float = 0.70
RECONCILIATION_RULE_VERSION: str = "gate4b.reconcile.v1"


def compute_box_iou(
    boxA: tuple[float, float, float, float] | list[float],
    boxB: tuple[float, float, float, float] | list[float],
) -> float:
    """
    Compute Intersection over Union (IoU) of two bounding boxes in (x1, y1, x2, y2) format.
    """
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    inter_w = max(0.0, xB - xA)
    inter_h = max(0.0, yB - yA)
    inter_area = inter_w * inter_h

    boxA_area = max(0.0, boxA[2] - boxA[0]) * max(0.0, boxA[3] - boxA[1])
    boxB_area = max(0.0, boxB[2] - boxB[0]) * max(0.0, boxB[3] - boxB[1])

    union_area = boxA_area + boxB_area - inter_area
    if union_area <= 0.0:
        return 0.0

    return inter_area / union_area


def validate_detection_box(det: Detection) -> None:
    """
    Strictly validate detection box coordinates.
    Raises ValueError on NaN, infinite, inverted, or degenerate boxes.
    """
    coords = [det.x1, det.y1, det.x2, det.y2]
    for c in coords:
        if not math.isfinite(c):
            raise ValueError(f"Malformed bounding box with non-finite coordinate: {coords} in detection {det.detection_id}")

    if det.x2 <= det.x1:
        raise ValueError(f"Malformed bounding box with width <= 0 (x1={det.x1}, x2={det.x2}) in detection {det.detection_id}")

    if det.y2 <= det.y1:
        raise ValueError(f"Malformed bounding box with height <= 0 (y1={det.y1}, y2={det.y2}) in detection {det.detection_id}")

    if det.x1 < 0.0 or det.y1 < 0.0:
        raise ValueError(f"Malformed bounding box with negative coordinates (x1={det.x1}, y1={det.y1}) in detection {det.detection_id}")


class ReconciliationSummary(BaseModel):
    """Execution summary of the observation reconciliation stage."""
    model_config = ConfigDict(extra="forbid")

    raw_detection_count: int = Field(..., ge=0)
    reconciled_observation_count: int = Field(..., ge=0)
    conflict_count: int = Field(..., ge=0)
    same_class_collapsed_count: int = Field(..., ge=0)
    reconciliation_rule_version: str = Field(default=RECONCILIATION_RULE_VERSION)


def reconcile_detections_to_observations(
    detections: Sequence[Detection],
    capture_id: str,
    iou_threshold: float = DEFAULT_RECONCILIATION_IOU_THRESHOLD,
    min_reliable_confidence: float = 0.40,
    model_checkpoint: str = "onion-grading-v7.pt",
    measurement_status: MeasurementStatus = MeasurementStatus.CALIBRATION_NOT_AVAILABLE,
) -> tuple[list[OnionObservationRecord], ReconciliationSummary]:
    """
    Reconcile raw model detections into trustworthy, non-duplicated physical onion observations.

    Rules:
    - If IoU <= iou_threshold: distinct physical items, retain both.
    - If IoU > iou_threshold and classes are identical: retain highest-confidence detection.
    - If IoU > iou_threshold and classes differ: retain ONE physical observation with
      observation_status = CLASS_CONFLICT, preserving candidate classes, confidences,
      source detection IDs, and IoU.

    Returns:
        (observations, summary)
    """
    if not detections:
        return [], ReconciliationSummary(
            raw_detection_count=0,
            reconciled_observation_count=0,
            conflict_count=0,
            same_class_collapsed_count=0,
        )

    # 1. Validate all bounding boxes
    for det in detections:
        validate_detection_box(det)

    # 2. Sort deterministically by confidence descending, tie-break by detection_id
    sorted_dets = sorted(detections, key=lambda d: (-d.confidence, d.detection_id))

    unassigned = list(sorted_dets)
    reconciled_records: list[OnionObservationRecord] = []
    conflict_count = 0
    same_class_collapsed_count = 0
    obs_index = 0

    while unassigned:
        seed = unassigned.pop(0)
        seed_bbox = (seed.x1, seed.y1, seed.x2, seed.y2)

        # Find all overlapping detections with seed
        overlapping_matches: list[tuple[Detection, float]] = []
        remaining_unassigned: list[Detection] = []

        for candidate in unassigned:
            cand_bbox = (candidate.x1, candidate.y1, candidate.x2, candidate.y2)
            iou = compute_box_iou(seed_bbox, cand_bbox)
            if iou > iou_threshold:
                overlapping_matches.append((candidate, iou))
            else:
                remaining_unassigned.append(candidate)

        unassigned = remaining_unassigned

        cluster = [seed] + [m[0] for m in overlapping_matches]
        source_detection_ids = [d.detection_id for d in cluster]
        candidate_classes = [d.canonical_label for d in cluster]
        candidate_confidences = [d.confidence for d in cluster]

        # Calculate max IoU in cluster
        max_iou = max([m[1] for m in overlapping_matches]) if overlapping_matches else None

        # Check semantic consistency in cluster
        # Distinct meaningful classes (excluding unknown/conflict)
        unique_classes = sorted(list({c for c in candidate_classes if c not in (CanonicalLabel.UNKNOWN_MAPPING, CanonicalLabel.CLASS_CONFLICT)}))

        obs_id = f"obs_{capture_id}_{obs_index}"
        obs_index += 1

        if len(unique_classes) > 1:
            # CROSS-CLASS CONFLICT
            conflict_count += 1
            title, explanation, req_review = resolve_annotation_ui(
                CanonicalLabel.CLASS_CONFLICT, ObservationStatus.CLASS_CONFLICT
            )
            record = OnionObservationRecord(
                observation_id=obs_id,
                capture_id=capture_id,
                bbox=seed_bbox,
                class_semantic=CanonicalLabel.CLASS_CONFLICT,
                confidence=round(seed.confidence, 4),
                observation_status=ObservationStatus.CLASS_CONFLICT,
                visibility_status=ObservationStatus.CLASS_CONFLICT,
                measurement_status=measurement_status,
                provenance=ObservationProvenance(
                    model_checkpoint=model_checkpoint,
                    model_version=get_processing_version(),
                    raw_class_id=seed.class_id_external,
                    raw_class_name=seed.class_name_external,
                ),
                candidate_classes=candidate_classes,
                candidate_confidences=candidate_confidences,
                source_detection_ids=source_detection_ids,
                source_observation=seed.detection_id,
                title=title,
                explanation=explanation,
                review_required=req_review,
                reconciliation_iou=round(max_iou, 4) if max_iou is not None else None,
                reconciliation_rule=f"{RECONCILIATION_RULE_VERSION}.cross_class_conflict",
            )
        else:
            # SAME CLASS (or single detection)
            if overlapping_matches:
                same_class_collapsed_count += len(overlapping_matches)
                rule = f"{RECONCILIATION_RULE_VERSION}.same_class_collapsed"
            else:
                rule = f"{RECONCILIATION_RULE_VERSION}.single_detection_retained"

            # Determine observation status
            if seed.confidence < min_reliable_confidence:
                status = ObservationStatus.LOW_CONFIDENCE
            elif seed.canonical_label == CanonicalLabel.UNKNOWN_MAPPING:
                status = ObservationStatus.UNKNOWN_MAPPING
            else:
                status = ObservationStatus.OBSERVED

            title, explanation, req_review = resolve_annotation_ui(
                seed.canonical_label, status
            )

            record = OnionObservationRecord(
                observation_id=obs_id,
                capture_id=capture_id,
                bbox=seed_bbox,
                class_semantic=seed.canonical_label,
                confidence=round(seed.confidence, 4),
                observation_status=status,
                visibility_status=status,
                measurement_status=measurement_status,
                provenance=ObservationProvenance(
                    model_checkpoint=model_checkpoint,
                    model_version=get_processing_version(),
                    raw_class_id=seed.class_id_external,
                    raw_class_name=seed.class_name_external,
                ),
                candidate_classes=candidate_classes,
                candidate_confidences=candidate_confidences,
                source_detection_ids=source_detection_ids,
                source_observation=seed.detection_id,
                title=title,
                explanation=explanation,
                review_required=req_review,
                reconciliation_iou=round(max_iou, 4) if max_iou is not None else None,
                reconciliation_rule=rule,
            )

        reconciled_records.append(record)

    summary = ReconciliationSummary(
        raw_detection_count=len(detections),
        reconciled_observation_count=len(reconciled_records),
        conflict_count=conflict_count,
        same_class_collapsed_count=same_class_collapsed_count,
        reconciliation_rule_version=RECONCILIATION_RULE_VERSION,
    )

    return reconciled_records, summary
