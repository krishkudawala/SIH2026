"""
Unit & Integration Tests for Mandi Nyaay Gate 6B:
Physical Sample Identity + Versioned Rule-Pack Engine.

=============================================================================
SYNTHETIC STRUCTURAL TEST FIXTURE:
TEST FIXTURE — NOT FIELD DATA.
DO NOT PRESENT AS FIELD VALIDATION.
Designed strictly to verify mathematical identity invariants and RulePack provenance.
=============================================================================

Required Gate 6B Tests:
1. same onion across multiple captures counts once
2. detail recapture does not increase sample size
3. 3 views x 10 onions = 10 sampled units
4. unresolved cross-view identity prevents automatic merge
5. SampleUnit provenance preserved
6. missing RulePack blocks automatic decision
7. RulePack version preserved in decision
8. RulePack source preserved
9. deterministic decision with same RulePack
10. different RulePack versions preserve historical provenance
11. invalid RulePack blocks decision
12. replay preserves RulePack version
13. sampling uses unique SampleUnits
14. no hidden threshold remains in decision engine
"""

from __future__ import annotations

import copy
import pytest

from app.cv.label_mapping import CanonicalLabel
from app.domain.aggregation import aggregate_observations
from app.domain.decision_engine import (
    DECISION_RULE_VERSION,
    DecisionEngine,
    evaluate_procurement_decision,
)
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
from app.domain.review_signals import generate_review_signals
from app.domain.rule_pack import (
    AGMARK_ONION_STANDARD_V1,
    DEFAULT_RULE_PACK,
    DecisionRule,
    RuleCriterion,
    RulePack,
    SamplingRule,
)
from app.domain.rule_pack_validation import validate_rule_pack
from app.domain.sample_unit import (
    CaptureRole,
    ObservationReference,
    SampleCell,
    SampleUnit,
    SampleUnitRegistry,
)
from app.domain.sampling import evaluate_sampling_sufficiency
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
# GATE 6B TEST CASES (1 to 14)
# =============================================================================

# 1. Same onion across multiple captures counts once
def test_same_onion_across_multiple_captures_counts_once():
    acc = InspectionSessionAccumulator(lot_id="lot_g6b_01", target_sample_size=10)

    # Primary capture of 1 onion
    cap1 = _create_mock_capture("cap_p1", raw_count=1, reconciled_count=1, capture_role=CaptureRole.PRIMARY_SAMPLE_CAPTURE)
    obs1 = [_create_mock_observation("obs_onion_1", "cap_p1")]
    acc.append_capture(cap1, obs1)

    assert acc.sample_unit_registry.unique_sample_count == 1
    units = list(acc.sample_unit_registry.units.values())
    assert len(units) == 1
    unit = units[0]
    assert unit.primary_observation_id == "obs_onion_1"
    assert len(unit.observation_ids) == 1

    # Second capture: Detail recapture of the EXACT SAME onion
    cap2 = _create_mock_capture("cap_d1", raw_count=1, reconciled_count=1, capture_role=CaptureRole.DETAIL_RECAPTURE)
    obs2 = [_create_mock_observation("obs_onion_1_detail", "cap_d1")]
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


# 2. Detail recapture does not increase sample size
def test_detail_recapture_does_not_increase_sample_size():
    acc = InspectionSessionAccumulator(lot_id="lot_g6b_02", target_sample_size=10)

    # Primary capture of 5 onions
    cap1 = _create_mock_capture("cap_1", raw_count=5, reconciled_count=5, capture_role=CaptureRole.PRIMARY_SAMPLE_CAPTURE)
    obs1 = [_create_mock_observation(f"obs_p_{i}", "cap_1") for i in range(5)]
    s1 = acc.append_capture(cap1, obs1)

    assert s1.sampling_result.observed_sample_size == 5
    assert acc.sample_unit_registry.unique_sample_count == 5

    # Detail recapture of all 5 onions
    cap2 = _create_mock_capture("cap_2", raw_count=5, reconciled_count=5, capture_role=CaptureRole.DETAIL_RECAPTURE)
    obs2 = [_create_mock_observation(f"obs_d_{i}", "cap_2") for i in range(5)]
    associations = {f"obs_d_{i}": f"obs_p_{i}" for i in range(5)}
    s2 = acc.append_capture(cap2, obs2, identity_associations=associations)

    # Sample size MUST NOT increment to 10
    assert s2.sampling_result.observed_sample_size == 5
    assert acc.sample_unit_registry.unique_sample_count == 5


# 3. 3 views x 10 onions = 10 sampled units
def test_three_views_times_ten_onions_equals_ten_sampled_units():
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

    # SUCCESS INVARIANT: 3 captures, 30 observations -> sample_size = 10 (NOT 30!)
    assert len(s3.captures) == 3
    assert len(s3.observation_set.observations) == 30
    assert s3.sampling_result.observed_sample_size == 10
    assert s3.aggregation.total_count == 10
    assert acc.sample_unit_registry.unique_sample_count == 10
    assert s3.sampling_result.status == SamplingStatus.SUFFICIENT


# 4. Unresolved cross-view identity prevents automatic merge
def test_unresolved_cross_view_identity_prevents_automatic_merge():
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
    for unit in acc.sample_unit_registry.units.values():
        assert "obs_mysterious" not in unit.observation_ids
        assert unit.is_detail_augmented is False

    # Sample size remains 5 (not guessed, not silently merged)
    assert acc.sample_unit_registry.unique_sample_count == 5
    assert s2.sampling_result.observed_sample_size == 5

    # Safe observation must be tagged CROSS_VIEW_IDENTITY_UNRESOLVED
    unresolved_obs = [o for o in s2.observation_set.observations if o.observation_id == "obs_mysterious"][0]
    assert unresolved_obs.cross_view_identity_status == "CROSS_VIEW_IDENTITY_UNRESOLVED"


# 5. SampleUnit provenance preserved
def test_sample_unit_provenance_preserved():
    registry = SampleUnitRegistry(lot_id="lot_prov_test")
    obs = _create_mock_observation("obs_primary_1", "cap_1", CanonicalLabel.HEALTHY)

    unit = registry.register_primary_observation(
        obs=obs,
        capture_id="cap_1",
        cell_id="B3",
        source_reference="TRAY_ALPHA",
        view_angle="TOP",
    )

    assert unit.sample_unit_id.startswith("su_")
    assert unit.lot_id == "lot_prov_test"
    assert unit.source_reference == "TRAY_ALPHA"
    assert unit.cell_id == "B3"
    assert unit.observation_ids == ["obs_primary_1"]
    assert unit.capture_ids == ["cap_1"]
    assert unit.primary_observation_id == "obs_primary_1"
    assert len(unit.observation_references) == 1

    ref0 = unit.observation_references[0]
    assert ref0.observation_id == "obs_primary_1"
    assert ref0.capture_id == "cap_1"
    assert ref0.capture_role == CaptureRole.PRIMARY_SAMPLE_CAPTURE
    assert ref0.view_angle == "TOP"
    assert ref0.class_semantic == CanonicalLabel.HEALTHY

    # Augment with detail observation
    obs_detail = _create_mock_observation("obs_detail_1", "cap_2", CanonicalLabel.HEALTHY)
    success = registry.associate_detail_observation(
        obs=obs_detail,
        capture_id="cap_2",
        target_sample_unit_id=unit.sample_unit_id,
        view_angle="DETAIL",
    )
    assert success is True
    assert len(unit.observation_ids) == 2
    assert len(unit.capture_ids) == 2
    assert unit.capture_ids == ["cap_1", "cap_2"]
    assert len(unit.observation_references) == 2
    assert unit.is_detail_augmented is True


# 6. Missing RulePack blocks automatic decision
def test_missing_rule_pack_blocks_automatic_decision():
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
    assert any("NO_APPLICABLE_RULE_PACK" in b for b in session.decision.blocking_reasons)
    assert session.decision.rule_pack_id is None
    assert session.decision.rule_pack_version is None


# 7. RulePack version preserved in decision
def test_rule_pack_version_preserved_in_decision():
    engine = DecisionEngine(rule_pack=AGMARK_ONION_STANDARD_V1)
    obs = [_create_mock_observation(f"o_{i}", "c1", CanonicalLabel.HEALTHY) for i in range(20)]
    sampling = evaluate_sampling_sufficiency(obs, target_sample_size=20)
    agg = aggregate_observations(obs)
    signals = generate_review_signals(conflict_count=0, quality_grade="PASS")

    decision = engine.evaluate(
        observations=obs,
        sampling_result=sampling,
        aggregation=agg,
        review_signals=signals,
    )

    assert decision.rule_pack_id == "AGMARK_ONION_2024_V1"
    assert decision.rule_pack_version == "1.0.0"
    assert decision.decision_rule_version == "AGMARK_ONION_2024_V1_1.0.0"
    assert decision.procurement_grade == ProcurementGrade.GRADE_A


# 8. RulePack source preserved
def test_rule_pack_source_preserved():
    pack = AGMARK_ONION_STANDARD_V1
    assert "Directorate of Marketing & Inspection" in pack.authority
    assert "Agricultural Produce (Grading and Marking) Act, 1937" in pack.source_document
    assert pack.source_reference == "https://agmarknet.gov.in/Standards/onion.pdf"
    assert pack.source_uri_or_reference == "https://agmarknet.gov.in/Standards/onion.pdf"
    assert pack.sampling_method == "RANDOM_STRATIFIED_BAG_EXTRACTION"
    assert pack.version == "1.0.0"


# 9. Deterministic decision with same RulePack
def test_deterministic_decision_with_same_rule_pack():
    obs = [_create_mock_observation(f"o_{i}", "c1", CanonicalLabel.HEALTHY) for i in range(20)]
    sampling = evaluate_sampling_sufficiency(obs, target_sample_size=20)
    agg = aggregate_observations(obs)
    signals = generate_review_signals(conflict_count=0, quality_grade="PASS")

    engine = DecisionEngine(rule_pack=DEFAULT_RULE_PACK)
    d1 = engine.evaluate(obs, sampling, agg, signals)
    d2 = engine.evaluate(obs, sampling, agg, signals)

    assert d1.procurement_grade == d2.procurement_grade
    assert d1.rule_pack_id == d2.rule_pack_id
    assert d1.rule_pack_version == d2.rule_pack_version
    assert d1.decision_rule_version == d2.decision_rule_version
    assert d1.decision_reasons == d2.decision_reasons
    assert d1.blocking_reasons == d2.blocking_reasons


# 10. Different RulePack versions preserve historical provenance
def test_different_rule_pack_versions_preserve_historical_provenance():
    pack_v1 = AGMARK_ONION_STANDARD_V1
    pack_v2 = AGMARK_ONION_STANDARD_V1.model_copy(
        update={
            "rule_pack_id": "AGMARK_ONION_REVISED_2025",
            "version": "2.0.0",
        },
        deep=True,
    )

    acc1 = InspectionSessionAccumulator(lot_id="lot_hist_comp", target_sample_size=5, rule_pack=pack_v1)
    acc2 = InspectionSessionAccumulator(lot_id="lot_hist_comp", target_sample_size=5, rule_pack=pack_v2)

    cap = _create_mock_capture("c1", raw_count=5, reconciled_count=5)
    obs = [_create_mock_observation(f"o_{i}", "c1") for i in range(5)]

    s1 = acc1.append_capture(cap, obs)
    s2 = acc2.append_capture(cap, obs)

    assert s1.decision.rule_pack_version == "1.0.0"
    assert s2.decision.rule_pack_version == "2.0.0"
    assert s1.decision.decision_rule_version != s2.decision.decision_rule_version
    assert s1.evidence_summary.evidence_root_hash != s2.evidence_summary.evidence_root_hash


# 11. Invalid RulePack blocks decision
def test_invalid_rule_pack_blocks_decision():
    # Construct invalid pack: effective_to precedes effective_from, and negative min_sample_units
    invalid_pack = AGMARK_ONION_STANDARD_V1.model_copy(
        update={
            "effective_from": "2025-01-01",
            "effective_to": "2024-01-01",  # Incoherent period!
        },
        deep=True,
    )

    val = validate_rule_pack(invalid_pack)
    assert val.is_valid is False
    assert any("INCOHERENT_PERIOD" in err for err in val.errors)

    engine = DecisionEngine(rule_pack=invalid_pack)
    obs = [_create_mock_observation(f"o_{i}", "c1") for i in range(20)]
    sampling = evaluate_sampling_sufficiency(obs, target_sample_size=20)
    agg = aggregate_observations(obs)
    signals = generate_review_signals(conflict_count=0, quality_grade="PASS")

    decision = engine.evaluate(obs, sampling, agg, signals)
    assert decision.procurement_grade == ProcurementGrade.MANUAL_REVIEW
    assert decision.status == "REFERRED_TO_MANUAL_REVIEW"
    assert any("INVALID_RULE_PACK" in b for b in decision.blocking_reasons)


# 12. Replay preserves RulePack version
def test_replay_preserves_rule_pack_version():
    pack = AGMARK_ONION_STANDARD_V1
    acc = InspectionSessionAccumulator(lot_id="lot_replay_v_test", target_sample_size=5, rule_pack=pack)
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


# 13. Sampling uses unique SampleUnits
def test_sampling_uses_unique_sample_units():
    # Scenario A: 10 primary onions + 4 unlinked detail views = sample size 10
    reg = SampleUnitRegistry(lot_id="lot_sampling_test")
    for i in range(10):
        obs = _create_mock_observation(f"onion_p_{i}", "cap_1")
        reg.register_primary_observation(obs=obs, capture_id="cap_1", cell_id=f"A{i+1}")

    assert reg.unique_sample_count == 10

    # 4 unlinked detail views arrive
    for i in range(4):
        obs_detail = _create_mock_observation(f"onion_unlinked_{i}", "cap_2")
        reg.associate_detail_observation(obs=obs_detail, capture_id="cap_2")

    # Sample size must remain 10
    assert reg.unique_sample_count == 10
    assert len(reg.unresolved_observation_ids) == 4

    sampling_res_a = evaluate_sampling_sufficiency(
        observations=[],
        target_sample_size=14,
        unique_sample_unit_count=reg.unique_sample_count,
    )
    assert sampling_res_a.observed_sample_size == 10
    assert sampling_res_a.status == SamplingStatus.CONTINUE

    # Scenario B: 10 primary onions + 4 distinct primary onions = sample size 14
    for i in range(4):
        obs_distinct = _create_mock_observation(f"onion_distinct_{i}", "cap_3")
        reg.register_primary_observation(obs=obs_distinct, capture_id="cap_3", cell_id=f"B{i+1}")

    assert reg.unique_sample_count == 14
    sampling_res_b = evaluate_sampling_sufficiency(
        observations=[],
        target_sample_size=14,
        unique_sample_unit_count=reg.unique_sample_count,
    )
    assert sampling_res_b.observed_sample_size == 14
    assert sampling_res_b.status == SamplingStatus.SUFFICIENT


# 14. No hidden threshold remains in decision engine
def test_no_hidden_threshold_remains_in_decision_engine():
    # Pack with missing criteria
    incomplete_pack = RulePack(
        rule_pack_id="INCOMPLETE_PACK",
        authority="Test Authority",
        source_document="Test Standard",
        source_reference="https://test.gov.in/test.pdf",
        effective_from="2024-01-01",
        version="1.0.0",
        criteria=[],  # Stripped! No criteria!
        sampling_rule=SamplingRule(
            rule_id="samp_test",
            min_sample_units=20,
            sampling_method="RANDOM",
        ),
        decision_rules=[],
        decision_logic="Empty test logic",
    )

    engine = DecisionEngine(rule_pack=incomplete_pack)
    obs = [_create_mock_observation(f"o_{i}", "c1", CanonicalLabel.HEALTHY) for i in range(20)]
    sampling = evaluate_sampling_sufficiency(obs, target_sample_size=20)
    agg = aggregate_observations(obs)
    signals = generate_review_signals(conflict_count=0, quality_grade="PASS")

    # The engine must REFUSE to decide and divert to MANUAL_REVIEW rather than falling back to hidden constants
    decision = engine.evaluate(obs, sampling, agg, signals)
    assert decision.procurement_grade == ProcurementGrade.MANUAL_REVIEW
    assert decision.status == "REFERRED_TO_MANUAL_REVIEW"
    assert any("INVALID_RULE_PACK" in b or "MISSING_RULE_PACK_CRITERION" in b for b in decision.blocking_reasons)
