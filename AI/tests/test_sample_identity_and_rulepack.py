"""
Unit & Integration Tests for Gate 6B: Physical Sample Identity + Rule Pack Engine.

=============================================================================
SYNTHETIC STRUCTURAL TEST FIXTURE:
TEST FIXTURE — NOT FIELD DATA.
DO NOT PRESENT AS FIELD VALIDATION.
Designed strictly to verify mathematical identity invariants and RulePack provenance.
=============================================================================

Covered Test Cases:
1. Same onion captured twice remains one sample unit
2. Detail recapture does not increment sample size
3. Three views of ten onions = ten sampled onions
4. Unresolved identity blocks automatic merge
5. Rule pack version is preserved
6. Missing rule pack blocks automatic procurement decision (MANUAL_REVIEW)
7. Decision is deterministic for same RulePack
8. Changing RulePack version changes provenance
9. Historical session retains original RulePack
10. Replay preserves RulePack provenance
"""

import copy
import pytest

from app.cv.label_mapping import CanonicalLabel
from app.domain.inspection_session import (
    InspectionCapture,
    ProcurementGrade,
    SamplingStatus,
)
from app.domain.onion_observation import (
    ObservationProvenance,
    ObservationStatus,
    OnionObservationRecord,
)
from app.domain.rule_pack import (
    AGMARK_ONION_STANDARD_V1,
    DEFAULT_RULE_PACK,
    RulePack,
)
from app.domain.sample_unit import CaptureRole
from app.domain.session_accumulator import (
    InspectionSessionAccumulator,
    replay_session,
)
from app.domain.status import MeasurementStatus


# =============================================================================
# SYNTHETIC TEST FIXTURES — NOT FIELD DATA
# =============================================================================

def _create_mock_capture(
    capture_id: str,
    raw_count: int = 1,
    reconciled_count: int = 1,
    conflict_count: int = 0,
    quality_status: str = "PASS",
    capture_role: CaptureRole = CaptureRole.PRIMARY_SAMPLE_CAPTURE,
) -> InspectionCapture:
    """Synthetic capture fixture strictly for structural logic verification."""
    return InspectionCapture(
        capture_id=capture_id,
        capture_role=capture_role,
        image_path=f"data/synthetic_fixtures/{capture_id}.jpg",
        image_sha256=f"sha256_synthetic_{capture_id}",
        raw_detection_count=raw_count,
        reconciled_observation_count=reconciled_count,
        conflict_count=conflict_count,
        visible_condition_counts={"HEALTHY": reconciled_count},
        quality_status=quality_status,
        mapping_status="VERIFIED",
        measurement_status="CALIBRATION_NOT_AVAILABLE",
        calibration_status="CALIBRATION_NOT_AVAILABLE",
        provenance={"checkpoint_path": "onion-grading-v7.pt", "fixture_type": "TEST FIXTURE — NOT FIELD DATA"},
    )


def _create_mock_observation(
    obs_id: str,
    capture_id: str,
    semantic: CanonicalLabel = CanonicalLabel.HEALTHY,
    status: ObservationStatus = ObservationStatus.OBSERVED,
) -> OnionObservationRecord:
    """Synthetic observation record strictly for structural logic verification."""
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


# =============================================================================
# GATE 6B TEST CASES
# =============================================================================

# 1. Same onion captured twice remains one sample unit
def test_same_onion_captured_twice_remains_one_sample_unit():
    acc = InspectionSessionAccumulator(lot_id="lot_g6b_01", target_sample_size=10)

    # Primary capture of 1 onion
    cap1 = _create_mock_capture("cap_primary_1", raw_count=1, reconciled_count=1, capture_role=CaptureRole.PRIMARY_SAMPLE_CAPTURE)
    obs1 = [_create_mock_observation("obs_onion_1", "cap_primary_1")]
    acc.append_capture(cap1, obs1)

    assert acc.sample_unit_registry.unique_sample_count == 1
    units = list(acc.sample_unit_registry.units.values())
    assert len(units) == 1
    unit = units[0]
    assert unit.primary_observation_id == "obs_onion_1"
    assert len(unit.observation_ids) == 1

    # Detail recapture of the EXACT SAME onion
    cap2 = _create_mock_capture("cap_detail_1", raw_count=1, reconciled_count=1, capture_role=CaptureRole.DETAIL_RECAPTURE)
    obs2 = [_create_mock_observation("obs_onion_1_detail", "cap_detail_1")]
    acc.append_capture(
        cap2,
        obs2,
        identity_associations={"obs_onion_1_detail": "obs_onion_1"},
        view_angles={"obs_onion_1_detail": "DETAIL"},
    )

    # MATHEMATICAL INVARIANT: sample size must remain exactly 1
    assert acc.sample_unit_registry.unique_sample_count == 1
    assert len(unit.observation_ids) == 2
    assert "obs_onion_1_detail" in unit.observation_ids
    assert unit.is_detail_augmented is True
    session = acc.get_session()
    assert session.sampling_result.observed_sample_size == 1


# 2. Detail recapture does not increment sample size
def test_detail_recapture_does_not_increment_sample_size():
    acc = InspectionSessionAccumulator(lot_id="lot_g6b_02", target_sample_size=10)

    # Capture 1: Primary capture of 5 onions
    cap1 = _create_mock_capture("cap_1", raw_count=5, reconciled_count=5, capture_role=CaptureRole.PRIMARY_SAMPLE_CAPTURE)
    obs1 = [_create_mock_observation(f"obs_p_{i}", "cap_1") for i in range(5)]
    s1 = acc.append_capture(cap1, obs1)

    assert s1.sampling_result.observed_sample_size == 5
    assert s1.sampling_result.status == SamplingStatus.CONTINUE

    # Capture 2: Detail recapture of all 5 onions
    cap2 = _create_mock_capture("cap_2", raw_count=5, reconciled_count=5, capture_role=CaptureRole.DETAIL_RECAPTURE)
    obs2 = [_create_mock_observation(f"obs_d_{i}", "cap_2") for i in range(5)]
    associations = {f"obs_d_{i}": f"obs_p_{i}" for i in range(5)}
    s2 = acc.append_capture(cap2, obs2, identity_associations=associations)

    # Must NOT increment sample size to 10
    assert s2.sampling_result.observed_sample_size == 5
    assert acc.sample_unit_registry.unique_sample_count == 5
    assert s2.sampling_result.status == SamplingStatus.CONTINUE


# 3. Three views of ten onions = ten sampled onions
def test_three_views_of_ten_onions_equals_ten_sampled_onions():
    acc = InspectionSessionAccumulator(lot_id="lot_g6b_03", target_sample_size=10)

    # View 1: TOP view (Primary capture of 10 onions)
    cap_top = _create_mock_capture("cap_top", raw_count=10, reconciled_count=10, capture_role=CaptureRole.PRIMARY_SAMPLE_CAPTURE)
    obs_top = [_create_mock_observation(f"onion_{i}_top", "cap_top") for i in range(10)]
    cell_mapping = {f"onion_{i}_top": f"A{i+1}" for i in range(10)}
    s1 = acc.append_capture(cap_top, obs_top, cell_ids=cell_mapping, view_angles={f"onion_{i}_top": "TOP" for i in range(10)})
    assert s1.sampling_result.observed_sample_size == 10

    # View 2: SIDE view (Detail recapture of same 10 onions)
    cap_side = _create_mock_capture("cap_side", raw_count=10, reconciled_count=10, capture_role=CaptureRole.DETAIL_RECAPTURE)
    obs_side = [_create_mock_observation(f"onion_{i}_side", "cap_side") for i in range(10)]
    assoc_side = {f"onion_{i}_side": f"onion_{i}_top" for i in range(10)}
    s2 = acc.append_capture(cap_side, obs_side, identity_associations=assoc_side, view_angles={f"onion_{i}_side": "SIDE" for i in range(10)})

    # View 3: DETAIL / CLOSE-UP view (Detail recapture of same 10 onions)
    cap_detail = _create_mock_capture("cap_detail", raw_count=10, reconciled_count=10, capture_role=CaptureRole.DETAIL_RECAPTURE)
    obs_detail = [_create_mock_observation(f"onion_{i}_detail", "cap_detail") for i in range(10)]
    assoc_detail = {f"onion_{i}_detail": f"onion_{i}_top" for i in range(10)}
    s3 = acc.append_capture(cap_detail, obs_detail, identity_associations=assoc_detail, view_angles={f"onion_{i}_detail": "DETAIL" for i in range(10)})

    # SUCCESS INVARIANT:
    # 3 captures, 30 observations -> sample_size = 10 (NOT 30!)
    assert len(s3.captures) == 3
    assert len(s3.observation_set.observations) == 30
    assert s3.sampling_result.observed_sample_size == 10
    assert s3.aggregation.total_count == 10
    assert acc.sample_unit_registry.unique_sample_count == 10
    assert s3.sampling_result.status == SamplingStatus.SUFFICIENT


# 4. Unresolved identity blocks automatic merge
def test_unresolved_identity_blocks_automatic_merge():
    acc = InspectionSessionAccumulator(lot_id="lot_g6b_04", target_sample_size=10)

    # Primary capture of 5 onions
    cap1 = _create_mock_capture("cap_1", raw_count=5, reconciled_count=5, capture_role=CaptureRole.PRIMARY_SAMPLE_CAPTURE)
    obs1 = [_create_mock_observation(f"onion_{i}", "cap_1") for i in range(5)]
    acc.append_capture(cap1, obs1)

    # Detail recapture with unresolvable/unknown target
    cap2 = _create_mock_capture("cap_2", raw_count=1, reconciled_count=1, capture_role=CaptureRole.DETAIL_RECAPTURE)
    obs_unresolved = [_create_mock_observation("obs_mysterious", "cap_2")]
    s2 = acc.append_capture(
        cap2,
        obs_unresolved,
        identity_associations={"obs_mysterious": "unknown_ghost_onion_id"},
    )

    # Automatic merge must be blocked
    assert "obs_mysterious" in acc.sample_unit_registry.unresolved_observation_ids
    # Existing 5 units must not have been merged into
    for unit in acc.sample_unit_registry.units.values():
        assert "obs_mysterious" not in unit.observation_ids
        assert unit.is_detail_augmented is False

    # Sample size must remain 5 (not incremented, not guessed)
    assert acc.sample_unit_registry.unique_sample_count == 5
    assert s2.sampling_result.observed_sample_size == 5

    # Safe observation must be tagged CROSS_VIEW_IDENTITY_UNRESOLVED
    unresolved_obs = [o for o in s2.observation_set.observations if o.observation_id == "obs_mysterious"][0]
    assert unresolved_obs.cross_view_identity_status == "CROSS_VIEW_IDENTITY_UNRESOLVED"


# 5. Rule pack version is preserved
def test_rule_pack_version_is_preserved():
    custom_pack = AGMARK_ONION_STANDARD_V1
    acc = InspectionSessionAccumulator(
        lot_id="lot_g6b_05",
        target_sample_size=5,
        rule_pack=custom_pack,
    )

    cap = _create_mock_capture("cap_1", raw_count=5, reconciled_count=5)
    obs = [_create_mock_observation(f"o_{i}", "cap_1") for i in range(5)]
    session = acc.append_capture(cap, obs)

    assert session.decision.rule_pack_id == "AGMARK_ONION_2024_V1"
    assert session.decision.rule_pack_version == "1.0.0"
    assert session.decision.decision_rule_version == "AGMARK_ONION_2024_V1_1.0.0"
    assert session.evidence_summary.rule_version == "AGMARK_ONION_2024_V1_1.0.0"


# 6. Missing rule pack blocks automatic procurement decision
def test_missing_rule_pack_blocks_automatic_procurement_decision():
    # Pass rule_pack=None
    acc = InspectionSessionAccumulator(
        lot_id="lot_g6b_06",
        target_sample_size=5,
        rule_pack=None,
    )

    cap = _create_mock_capture("cap_1", raw_count=5, reconciled_count=5)
    obs = [_create_mock_observation(f"o_{i}", "cap_1") for i in range(5)]
    session = acc.append_capture(cap, obs)

    # Must divert to MANUAL_REVIEW
    assert session.decision.procurement_grade == ProcurementGrade.MANUAL_REVIEW
    assert session.decision.status == "REFERRED_TO_MANUAL_REVIEW"
    assert any("No applicable RulePack" in b for b in session.decision.blocking_reasons)
    assert session.decision.rule_pack_id is None
    assert session.decision.rule_pack_version is None


# 7. Decision is deterministic for same RulePack
def test_decision_is_deterministic_for_same_rule_pack():
    def _run_session():
        acc = InspectionSessionAccumulator(
            lot_id="lot_det",
            target_sample_size=5,
            rule_pack=DEFAULT_RULE_PACK,
        )
        cap = _create_mock_capture("c1", raw_count=5, reconciled_count=5)
        obs = [_create_mock_observation(f"o_{i}", "c1") for i in range(5)]
        return acc.append_capture(cap, obs)

    s1 = _run_session()
    s2 = _run_session()

    assert s1.decision.procurement_grade == s2.decision.procurement_grade
    assert s1.decision.rule_pack_id == s2.decision.rule_pack_id
    assert s1.decision.rule_pack_version == s2.decision.rule_pack_version
    assert s1.decision.decision_reasons == s2.decision.decision_reasons
    assert s1.decision.blocking_reasons == s2.decision.blocking_reasons


# 8. Changing RulePack version changes provenance
def test_changing_rule_pack_version_changes_provenance():
    pack_v1 = AGMARK_ONION_STANDARD_V1
    pack_v2 = AGMARK_ONION_STANDARD_V1.model_copy(
        update={
            "rule_pack_id": "AGMARK_ONION_SPECIAL_V2",
            "version": "2.0.0",
        },
        deep=True,
    )

    acc1 = InspectionSessionAccumulator(lot_id="lot_comp", target_sample_size=5, rule_pack=pack_v1)
    acc2 = InspectionSessionAccumulator(lot_id="lot_comp", target_sample_size=5, rule_pack=pack_v2)

    cap1 = _create_mock_capture("c1", raw_count=5, reconciled_count=5)
    obs1 = [_create_mock_observation(f"o_{i}", "c1") for i in range(5)]
    s1 = acc1.append_capture(cap1, obs1)

    cap2 = _create_mock_capture("c1", raw_count=5, reconciled_count=5)
    obs2 = [_create_mock_observation(f"o_{i}", "c1") for i in range(5)]
    s2 = acc2.append_capture(cap2, obs2)

    assert s1.decision.rule_pack_version == "1.0.0"
    assert s2.decision.rule_pack_version == "2.0.0"
    assert s1.decision.decision_rule_version != s2.decision.decision_rule_version
    assert s1.evidence_summary.evidence_root_hash != s2.evidence_summary.evidence_root_hash


# 9. Historical session retains original RulePack
def test_historical_session_retains_original_rule_pack():
    pack_v1 = AGMARK_ONION_STANDARD_V1
    acc = InspectionSessionAccumulator(lot_id="lot_hist", target_sample_size=5, rule_pack=pack_v1)
    cap = _create_mock_capture("c1", raw_count=5, reconciled_count=5)
    obs = [_create_mock_observation(f"o_{i}", "c1") for i in range(5)]
    historical_session = acc.append_capture(cap, obs)

    # Verify original session provenance
    assert historical_session.decision.rule_pack_id == "AGMARK_ONION_2024_V1"
    assert historical_session.decision.rule_pack_version == "1.0.0"

    # Even if default or global environment modifies later, historical session object and events are immutable
    start_event = acc.timeline.events[0]
    assert start_event.payload["rule_pack_id"] == "AGMARK_ONION_2024_V1"
    assert start_event.payload["rule_pack_version"] == "1.0.0"


# 10. Replay preserves RulePack provenance
def test_replay_preserves_rule_pack_provenance():
    pack_v1 = AGMARK_ONION_STANDARD_V1
    acc = InspectionSessionAccumulator(lot_id="lot_replay", target_sample_size=5, rule_pack=pack_v1)
    cap = _create_mock_capture("c1", raw_count=5, reconciled_count=5)
    obs = [_create_mock_observation(f"o_{i}", "c1") for i in range(5)]
    acc.append_capture(cap, obs)

    orig = acc.complete_session()
    replayed = replay_session(acc.timeline.events)

    assert replayed.decision.rule_pack_id == orig.decision.rule_pack_id
    assert replayed.decision.rule_pack_version == orig.decision.rule_pack_version
    assert replayed.decision.decision_rule_version == orig.decision.decision_rule_version
    assert replayed.evidence_summary.rule_version == orig.evidence_summary.rule_version
    assert replayed.evidence_summary.evidence_root_hash == orig.evidence_summary.evidence_root_hash
