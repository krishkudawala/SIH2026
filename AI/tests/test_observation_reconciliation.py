"""
Unit tests for Cross-Class Observation Reconciliation (Gate 4B-C).

Test Cases:
1. Same-class overlapping detections collapse to one.
2. High-IoU cross-class detections become one CLASS_CONFLICT observation.
3. Low-IoU detections remain separate.
4. Source detections are preserved.
5. Candidate confidences are preserved.
6. No double counting.
7. Deterministic reconciliation.
8. Malformed boxes are rejected.
"""

import pytest
from app.cv.label_mapping import CanonicalLabel, MappingStatus
from app.cv.model_adapter import Detection
from app.cv.observation_reconciliation import (
    compute_box_iou,
    reconcile_detections_to_observations,
    validate_detection_box,
)
from app.domain.onion_observation import ObservationStatus


def _make_detection(
    det_id: str,
    cls_id: int,
    cls_name: str,
    canonical_label: CanonicalLabel,
    confidence: float,
    box: tuple[float, float, float, float],
) -> Detection:
    x1, y1, x2, y2 = box
    return Detection(
        detection_id=det_id,
        class_id_external=cls_id,
        class_name_external=cls_name,
        canonical_label=canonical_label,
        mapping_status=MappingStatus.VERIFIED,
        confidence=confidence,
        x1=x1,
        y1=y1,
        x2=x2,
        y2=y2,
        width_px=x2 - x1,
        height_px=y2 - y1,
    )


# 1. Same-class overlapping detections collapse to one
def test_same_class_overlapping_collapse():
    # Two detections of HEALTHY with IoU ~ 0.90
    d1 = _make_detection("d1", 0, "healthy", CanonicalLabel.HEALTHY, 0.85, (10.0, 10.0, 100.0, 100.0))
    d2 = _make_detection("d2", 0, "healthy", CanonicalLabel.HEALTHY, 0.60, (12.0, 12.0, 102.0, 102.0))

    obs, summary = reconcile_detections_to_observations(
        detections=[d1, d2],
        capture_id="test_cap",
        iou_threshold=0.70,
    )

    assert summary.raw_detection_count == 2
    assert summary.reconciled_observation_count == 1
    assert summary.conflict_count == 0
    assert summary.same_class_collapsed_count == 1

    assert len(obs) == 1
    record = obs[0]
    assert record.observation_status == ObservationStatus.OBSERVED
    assert record.class_semantic == CanonicalLabel.HEALTHY
    assert record.confidence == 0.85  # Retained strongest detection
    assert "d1" in record.source_detection_ids
    assert "d2" in record.source_detection_ids


# 2. High-IoU cross-class detections become one CLASS_CONFLICT observation
def test_high_iou_cross_class_becomes_conflict():
    # Example from prompt: damaged 0.49 vs sprouted 0.48, IoU > 0.95
    d1 = _make_detection("d_damaged", 1, "damaged", CanonicalLabel.DAMAGED, 0.49, (1.0, 1.0, 255.0, 250.0))
    d2 = _make_detection("d_sprouted", 2, "sprouted", CanonicalLabel.SPROUTED, 0.48, (2.0, 0.0, 256.0, 251.0))

    obs, summary = reconcile_detections_to_observations(
        detections=[d1, d2],
        capture_id="smoke_cap",
        iou_threshold=0.70,
    )

    assert summary.raw_detection_count == 2
    assert summary.reconciled_observation_count == 1
    assert summary.conflict_count == 1

    assert len(obs) == 1
    conflict_record = obs[0]
    assert conflict_record.observation_status == ObservationStatus.CLASS_CONFLICT
    assert conflict_record.class_semantic == CanonicalLabel.CLASS_CONFLICT

    # Preserves candidate classes
    assert CanonicalLabel.DAMAGED in conflict_record.candidate_classes
    assert CanonicalLabel.SPROUTED in conflict_record.candidate_classes

    # Preserves candidate confidences
    assert 0.49 in conflict_record.candidate_confidences
    assert 0.48 in conflict_record.candidate_confidences

    # Preserves source detection IDs
    assert "d_damaged" in conflict_record.source_detection_ids
    assert "d_sprouted" in conflict_record.source_detection_ids

    # Preserves IoU
    assert conflict_record.reconciliation_iou is not None
    assert conflict_record.reconciliation_iou > 0.90


# 3. Low-IoU detections remain separate
def test_low_iou_detections_remain_separate():
    # Two spatially separated onions
    d1 = _make_detection("d1", 0, "healthy", CanonicalLabel.HEALTHY, 0.90, (10.0, 10.0, 50.0, 50.0))
    d2 = _make_detection("d2", 1, "damaged", CanonicalLabel.DAMAGED, 0.88, (100.0, 100.0, 150.0, 150.0))

    obs, summary = reconcile_detections_to_observations(
        detections=[d1, d2],
        capture_id="sep_cap",
        iou_threshold=0.70,
    )

    assert summary.raw_detection_count == 2
    assert summary.reconciled_observation_count == 2
    assert summary.conflict_count == 0
    assert len(obs) == 2


# 4. Source detections are preserved
def test_source_detections_preserved():
    d1 = _make_detection("det_alpha", 0, "healthy", CanonicalLabel.HEALTHY, 0.80, (10.0, 10.0, 80.0, 80.0))
    d2 = _make_detection("det_beta", 1, "damaged", CanonicalLabel.DAMAGED, 0.75, (12.0, 12.0, 82.0, 82.0))

    obs, _ = reconcile_detections_to_observations(
        detections=[d1, d2],
        capture_id="trace_cap",
        iou_threshold=0.70,
    )

    assert len(obs) == 1
    assert obs[0].source_detection_ids == ["det_alpha", "det_beta"]


# 5. Candidate confidences are preserved
def test_candidate_confidences_preserved():
    d1 = _make_detection("det_1", 2, "sprouted", CanonicalLabel.SPROUTED, 0.72, (20.0, 20.0, 100.0, 100.0))
    d2 = _make_detection("det_2", 3, "rotten", CanonicalLabel.ROTTEN, 0.65, (22.0, 21.0, 101.0, 99.0))

    obs, _ = reconcile_detections_to_observations(
        detections=[d1, d2],
        capture_id="conf_cap",
        iou_threshold=0.70,
    )

    assert len(obs) == 1
    assert obs[0].candidate_confidences == [0.72, 0.65]


# 6. No double counting
def test_no_double_counting():
    # Cluster 1: 3 overlapping detections on onion 1 (2 healthy, 1 damaged)
    c1_a = _make_detection("c1_a", 0, "healthy", CanonicalLabel.HEALTHY, 0.80, (10.0, 10.0, 60.0, 60.0))
    c1_b = _make_detection("c1_b", 0, "healthy", CanonicalLabel.HEALTHY, 0.70, (11.0, 10.0, 59.0, 60.0))
    c1_c = _make_detection("c1_c", 1, "damaged", CanonicalLabel.DAMAGED, 0.65, (12.0, 11.0, 61.0, 59.0))

    # Cluster 2: 2 overlapping detections on onion 2 (both rotten)
    c2_a = _make_detection("c2_a", 3, "rotten", CanonicalLabel.ROTTEN, 0.90, (200.0, 200.0, 260.0, 260.0))
    c2_b = _make_detection("c2_b", 3, "rotten", CanonicalLabel.ROTTEN, 0.85, (202.0, 201.0, 258.0, 261.0))

    # Isolated onion 3 (healthy)
    c3_a = _make_detection("c3_a", 0, "healthy", CanonicalLabel.HEALTHY, 0.95, (400.0, 400.0, 450.0, 450.0))

    all_dets = [c1_a, c1_b, c1_c, c2_a, c2_b, c3_a]

    obs, summary = reconcile_detections_to_observations(
        detections=all_dets,
        capture_id="no_double_cap",
        iou_threshold=0.70,
    )

    # 6 raw detections -> strictly 3 physical onions
    assert summary.raw_detection_count == 6
    assert summary.reconciled_observation_count == 3
    assert len(obs) == 3

    # One conflict (Cluster 1), two clean observations (Cluster 2 and 3)
    assert summary.conflict_count == 1


# 7. Deterministic reconciliation
def test_deterministic_reconciliation():
    d1 = _make_detection("det_a", 0, "healthy", CanonicalLabel.HEALTHY, 0.80, (10.0, 10.0, 60.0, 60.0))
    d2 = _make_detection("det_b", 1, "damaged", CanonicalLabel.DAMAGED, 0.75, (12.0, 11.0, 59.0, 61.0))
    d3 = _make_detection("det_c", 0, "healthy", CanonicalLabel.HEALTHY, 0.90, (100.0, 100.0, 150.0, 150.0))

    # Pass in different permutations
    obs1, sum1 = reconcile_detections_to_observations([d1, d2, d3], "cap_det")
    obs2, sum2 = reconcile_detections_to_observations([d3, d2, d1], "cap_det")
    obs3, sum3 = reconcile_detections_to_observations([d2, d1, d3], "cap_det")

    assert sum1.reconciled_observation_count == sum2.reconciled_observation_count == sum3.reconciled_observation_count
    assert sum1.conflict_count == sum2.conflict_count == sum3.conflict_count

    # Verify identical observation attributes
    for o1, o2 in zip(obs1, obs2):
        assert o1.bbox == o2.bbox
        assert o1.class_semantic == o2.class_semantic
        assert o1.confidence == o2.confidence
        assert o1.observation_status == o2.observation_status


# 8. Malformed boxes are rejected
def test_malformed_boxes_rejected():
    # Inverted box (x2 < x1)
    bad_det_1 = _make_detection("bad_1", 0, "healthy", CanonicalLabel.HEALTHY, 0.8, (50.0, 10.0, 20.0, 80.0))
    with pytest.raises(ValueError, match="Malformed bounding box"):
        reconcile_detections_to_observations([bad_det_1], "malformed_cap")

    # Degenerate height (y2 == y1)
    bad_det_2 = _make_detection("bad_2", 0, "healthy", CanonicalLabel.HEALTHY, 0.8, (10.0, 50.0, 60.0, 50.0))
    with pytest.raises(ValueError, match="Malformed bounding box"):
        reconcile_detections_to_observations([bad_det_2], "malformed_cap")

    # Negative coordinates
    bad_det_3 = _make_detection("bad_3", 0, "healthy", CanonicalLabel.HEALTHY, 0.8, (-10.0, 10.0, 60.0, 60.0))
    with pytest.raises(ValueError, match="Malformed bounding box"):
        reconcile_detections_to_observations([bad_det_3], "malformed_cap")
