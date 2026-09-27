"""
Comprehensive Unit & Integration Tests for Gate 6A Multi-Capture Lot Engine.

Tests:
1. Session creation
2. Capture append
3. Capture immutability
4. Deterministic ordering
5. Cumulative observations
6. Sampling progression tracking
7. CONTINUE -> SUFFICIENT state transition
8. Conflicts remain blocking across session
9. Unresolved cross-view identity remains explicit
10. Aggregation preserves provenance
11. No fabricated mass
12. Event hashing & cryptographic chain links
13. Tamper detection on modified payload or reordered events
14. Deterministic replay execution
15. Final state equals replayed state
"""

import copy
import json
from pathlib import Path
import pytest

from app.cv.label_mapping import CanonicalLabel, MappingStatus
from app.cv.quality import QualityGrade
from app.domain.event_ledger import (
    EventTimeline,
    InspectionEvent,
    InspectionEventType,
    compute_event_hash,
    compute_payload_hash,
)
from app.domain.inspection_session import (
    InspectionCapture,
    InspectionSessionStatus,
    ProcurementGrade,
    SamplingStatus,
)
from app.domain.onion_observation import (
    ObservationProvenance,
    ObservationStatus,
    OnionObservationRecord,
)
from app.domain.session_accumulator import (
    InspectionSessionAccumulator,
    replay_session,
)
from app.domain.status import MeasurementStatus


def _create_mock_capture(
    capture_id: str,
    raw_count: int = 1,
    reconciled_count: int = 1,
    conflict_count: int = 0,
    quality_status: str = "PASS",
) -> InspectionCapture:
    return InspectionCapture(
        capture_id=capture_id,
        image_path=f"data/raw/{capture_id}.jpg",
        image_sha256=f"hash_{capture_id}",
        raw_detection_count=raw_count,
        reconciled_observation_count=reconciled_count,
        conflict_count=conflict_count,
        visible_condition_counts={"HEALTHY": reconciled_count},
        quality_status=quality_status,
        mapping_status="VERIFIED",
        measurement_status="CALIBRATION_NOT_AVAILABLE",
        calibration_status="CALIBRATION_NOT_AVAILABLE",
        provenance={"checkpoint_path": "onion-grading-v7.pt"},
    )


def _create_mock_observation(
    obs_id: str,
    capture_id: str,
    semantic: CanonicalLabel = CanonicalLabel.HEALTHY,
    status: ObservationStatus = ObservationStatus.OBSERVED,
) -> OnionObservationRecord:
    return OnionObservationRecord(
        observation_id=obs_id,
        capture_id=capture_id,
        bbox=(10.0, 10.0, 50.0, 50.0),
        class_semantic=semantic,
        confidence=0.88,
        observation_status=status,
        visibility_status=status,
        measurement_status=MeasurementStatus.CALIBRATION_NOT_AVAILABLE,
        cross_view_identity_status="CROSS_VIEW_IDENTITY_UNRESOLVED",
        provenance=ObservationProvenance(
            model_checkpoint="onion-grading-v7.pt",
            raw_class_id=0,
            raw_class_name=semantic.value.lower(),
        ),
        candidate_classes=[semantic],
        candidate_confidences=[0.88],
        source_detection_ids=[f"det_{obs_id}"],
    )


# 1. Test Session Creation
def test_session_creation():
    acc = InspectionSessionAccumulator(lot_id="lot_test_01", target_sample_size=15)
    assert acc.lot_id == "lot_test_01"
    assert acc.target_sample_size == 15
    assert len(acc.captures) == 0
    assert len(acc.observations) == 0
    assert len(acc.timeline.events) == 1  # SESSION_STARTED event
    assert acc.timeline.events[0].event_type == InspectionEventType.SESSION_STARTED


# 2. Test Capture Append
def test_capture_append():
    acc = InspectionSessionAccumulator(lot_id="lot_test_02", target_sample_size=10)
    cap = _create_mock_capture("cap_001", raw_count=2, reconciled_count=2)
    obs = [
        _create_mock_observation("obs_001", "cap_001", CanonicalLabel.HEALTHY),
        _create_mock_observation("obs_002", "cap_001", CanonicalLabel.HEALTHY),
    ]
    session = acc.append_capture(cap, obs)

    assert len(acc.captures) == 1
    assert len(acc.observations) == 2
    assert session.session_id == acc.session_id
    assert session.aggregation.total_observations == 2


# 3. Test Capture Immutability
def test_capture_immutability():
    acc = InspectionSessionAccumulator(lot_id="lot_test_03", target_sample_size=20)
    cap1 = _create_mock_capture("cap_001", raw_count=3, reconciled_count=3)
    obs1 = [_create_mock_observation(f"obs_1_{i}", "cap_001") for i in range(3)]
    acc.append_capture(cap1, obs1)

    cap1_snapshot = acc.captures[0].model_dump()

    # Append second capture
    cap2 = _create_mock_capture("cap_002", raw_count=4, reconciled_count=4)
    obs2 = [_create_mock_observation(f"obs_2_{i}", "cap_002") for i in range(4)]
    acc.append_capture(cap2, obs2)

    # Prior capture record must be strictly identical
    assert acc.captures[0].model_dump() == cap1_snapshot


# 4. Test Deterministic Ordering
def test_deterministic_ordering():
    acc = InspectionSessionAccumulator(lot_id="lot_test_04", target_sample_size=20)
    for idx in range(1, 4):
        cap = _create_mock_capture(f"cap_{idx:03d}")
        obs = [_create_mock_observation(f"obs_{idx:03d}", f"cap_{idx:03d}")]
        acc.append_capture(cap, obs)

    cap_ids = [c.capture_id for c in acc.captures]
    assert cap_ids == ["cap_001", "cap_002", "cap_003"]

    event_types = [e.event_type for e in acc.timeline.events]
    assert event_types[0] == InspectionEventType.SESSION_STARTED
    assert event_types[1] == InspectionEventType.SOURCE_SELECTED


# 5. Test Cumulative Observations
def test_cumulative_observations():
    acc = InspectionSessionAccumulator(lot_id="lot_test_05", target_sample_size=20)
    cap1 = _create_mock_capture("cap_1", raw_count=5, reconciled_count=5)
    obs1 = [_create_mock_observation(f"obs_1_{i}", "cap_1") for i in range(5)]
    acc.append_capture(cap1, obs1)
    assert len(acc.observations) == 5

    cap2 = _create_mock_capture("cap_2", raw_count=7, reconciled_count=7)
    obs2 = [_create_mock_observation(f"obs_2_{i}", "cap_2") for i in range(7)]
    acc.append_capture(cap2, obs2)
    assert len(acc.observations) == 12
    assert acc.get_session().aggregation.total_observations == 12


# 6. Test Sampling Progression
def test_sampling_progression():
    acc = InspectionSessionAccumulator(lot_id="lot_test_06", target_sample_size=15)
    for i in range(3):
        cap = _create_mock_capture(f"c_{i}")
        obs = [_create_mock_observation(f"o_{i}_{j}", f"c_{i}") for j in range(4)]
        acc.append_capture(cap, obs)

    prog = acc.sampling_progression
    assert len(prog) == 3
    assert prog[0]["observed_sample_size"] == 4
    assert prog[1]["observed_sample_size"] == 8
    assert prog[2]["observed_sample_size"] == 12
    assert all(p["status"] == "CONTINUE" for p in prog)


# 7. Test CONTINUE -> SUFFICIENT Transition
def test_continue_to_sufficient_transition():
    acc = InspectionSessionAccumulator(lot_id="lot_test_07", target_sample_size=10)

    # Capture 1: 6 bulbs (shortfall: 4) -> CONTINUE
    cap1 = _create_mock_capture("cap_1", raw_count=6, reconciled_count=6)
    obs1 = [_create_mock_observation(f"o1_{i}", "cap_1") for i in range(6)]
    s1 = acc.append_capture(cap1, obs1)
    assert s1.sampling_result.status == SamplingStatus.CONTINUE
    assert s1.decision.procurement_grade == ProcurementGrade.MANUAL_REVIEW

    # Capture 2: 5 bulbs (cumulative: 11 >= 10) -> SUFFICIENT
    cap2 = _create_mock_capture("cap_2", raw_count=5, reconciled_count=5)
    obs2 = [_create_mock_observation(f"o2_{i}", "cap_2") for i in range(5)]
    s2 = acc.append_capture(cap2, obs2)
    assert s2.sampling_result.status == SamplingStatus.SUFFICIENT
    assert s2.decision.procurement_grade == ProcurementGrade.GRADE_A
    assert s2.decision.status == "DECIDED"


# 8. Test Conflicts Remain Blocking Across Session
def test_conflicts_remain_blocking():
    acc = InspectionSessionAccumulator(lot_id="lot_test_08", target_sample_size=5)

    # Capture 1 has a CLASS_CONFLICT
    cap1 = _create_mock_capture("cap_1", raw_count=2, reconciled_count=1, conflict_count=1)
    obs1 = [_create_mock_observation("obs_conf", "cap_1", CanonicalLabel.CLASS_CONFLICT, ObservationStatus.CLASS_CONFLICT)]
    s1 = acc.append_capture(cap1, obs1)
    assert s1.decision.procurement_grade == ProcurementGrade.MANUAL_REVIEW

    # Capture 2 adds 10 healthy bulbs; total 11 >= 5, but conflict remains!
    cap2 = _create_mock_capture("cap_2", raw_count=10, reconciled_count=10)
    obs2 = [_create_mock_observation(f"obs_h_{i}", "cap_2", CanonicalLabel.HEALTHY) for i in range(10)]
    s2 = acc.append_capture(cap2, obs2)

    # MUST NOT silently resolve conflict!
    assert s2.observation_set.conflict_count == 1
    assert s2.decision.procurement_grade == ProcurementGrade.MANUAL_REVIEW
    assert any("Cross-class detection conflict" in b for b in s2.decision.blocking_reasons)


# 9. Test Unresolved Cross-View Identity Remains Explicit
def test_unresolved_cross_view_identity():
    acc = InspectionSessionAccumulator(lot_id="lot_test_09", target_sample_size=10)
    cap1 = _create_mock_capture("c1")
    obs1 = [_create_mock_observation("o1", "c1")]
    acc.append_capture(cap1, obs1)

    cap2 = _create_mock_capture("c2")
    obs2 = [_create_mock_observation("o2", "c2")]
    session = acc.append_capture(cap2, obs2)

    assert session.aggregation.unresolved_identity_count == 2
    for o in acc.observations:
        assert o.cross_view_identity_status == "CROSS_VIEW_IDENTITY_UNRESOLVED"


# 10. Test Aggregation Preserves Provenance
def test_aggregation_preserves_provenance():
    acc = InspectionSessionAccumulator(lot_id="lot_test_10", target_sample_size=5)
    cap = _create_mock_capture("c1", raw_count=3, reconciled_count=3)
    obs = [
        _create_mock_observation("o1", "c1", CanonicalLabel.HEALTHY),
        _create_mock_observation("o2", "c1", CanonicalLabel.DAMAGED),
        _create_mock_observation("o3", "c1", CanonicalLabel.ROTTEN),
    ]
    session = acc.append_capture(cap, obs)

    assert session.aggregation.total_observations == 3
    assert session.aggregation.healthy_count == 1
    assert session.aggregation.damaged_count == 1
    assert session.aggregation.rotten_count == 1
    assert session.aggregation.count_distribution["HEALTHY"]["percentage"] == 33.33


# 11. Test No Fabricated Mass
def test_no_fabricated_mass():
    acc = InspectionSessionAccumulator(lot_id="lot_test_11", target_sample_size=5)
    cap = _create_mock_capture("c1")
    obs = [_create_mock_observation("o1", "c1")]
    session = acc.append_capture(cap, obs)

    assert session.aggregation.aggregation_mode == "COUNT_BASED"
    assert session.aggregation.mass_status == "UNVALIDATED"
    assert session.aggregation.mass_distribution is None
    assert "UNVALIDATED" in session.aggregation.disclaimer


# 12. Test Event Hashing & Chaining
def test_event_hashing_and_chaining():
    acc = InspectionSessionAccumulator(lot_id="lot_test_12", target_sample_size=5)
    cap = _create_mock_capture("c1")
    obs = [_create_mock_observation("o1", "c1")]
    acc.append_capture(cap, obs)

    valid, err = acc.timeline.verify_integrity()
    assert valid is True
    assert err is None

    # Check each event's previous_event_hash matches predecessor's event_hash
    events = acc.timeline.events
    assert len(events) >= 5
    for i in range(1, len(events)):
        assert events[i].previous_event_hash == events[i - 1].event_hash


# 13. Test Tamper Detection
def test_tamper_detection():
    acc = InspectionSessionAccumulator(lot_id="lot_test_13", target_sample_size=5)
    cap = _create_mock_capture("c1")
    obs = [_create_mock_observation("o1", "c1")]
    acc.append_capture(cap, obs)

    # Tamper with an event payload
    tampered_events = [e.model_copy(deep=True) for e in acc.timeline.events]
    tampered_events[1].payload["image_path"] = "fraudulent_path.jpg"

    timeline_tampered = EventTimeline(session_id=acc.session_id, events=tampered_events)
    valid, err = timeline_tampered.verify_integrity()
    assert valid is False
    assert "Payload tampering detected" in err


# 14. Test Deterministic Replay
def test_deterministic_replay():
    acc = InspectionSessionAccumulator(lot_id="lot_test_14", target_sample_size=5)
    cap1 = _create_mock_capture("c1", raw_count=3, reconciled_count=3)
    obs1 = [_create_mock_observation(f"o1_{i}", "c1") for i in range(3)]
    acc.append_capture(cap1, obs1)

    cap2 = _create_mock_capture("c2", raw_count=3, reconciled_count=3)
    obs2 = [_create_mock_observation(f"o2_{i}", "c2") for i in range(3)]
    acc.append_capture(cap2, obs2)

    orig_session = acc.complete_session()
    replayed_session = replay_session(acc.timeline.events)

    assert replayed_session.session_id == orig_session.session_id
    assert replayed_session.status == orig_session.status
    assert replayed_session.decision.procurement_grade == orig_session.decision.procurement_grade
    assert replayed_session.evidence_summary.evidence_root_hash == orig_session.evidence_summary.evidence_root_hash


# 15. Test Final State Equals Replayed State
def test_final_state_equals_replayed_state():
    acc = InspectionSessionAccumulator(lot_id="lot_test_15", target_sample_size=6)
    for i in range(2):
        cap = _create_mock_capture(f"cap_{i}", raw_count=3, reconciled_count=3)
        obs = [_create_mock_observation(f"o_{i}_{j}", f"cap_{i}") for j in range(3)]
        acc.append_capture(cap, obs)

    orig = acc.complete_session()
    replayed = replay_session(acc.timeline.events)

    orig_dict = orig.model_dump()
    replay_dict = replayed.model_dump()

    assert orig_dict["session_id"] == replay_dict["session_id"]
    assert orig_dict["status"] == replay_dict["status"]
    assert orig_dict["decision"] == replay_dict["decision"]
    assert orig_dict["aggregation"] == replay_dict["aggregation"]
    assert orig_dict["evidence_summary"]["evidence_root_hash"] == replay_dict["evidence_summary"]["evidence_root_hash"]
