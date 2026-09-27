"""
Unit and Integration Tests for Mandi Nyaay Inspection Session (Gate 5).

Covers:
1. Session creation & lifecycle states
2. CV result integration into canonical capture
3. Observation reconciliation integration
4. Sampling integration (SUFFICIENT, CONTINUE, MANUAL_REVIEW, INVALID)
5. Count vs mass aggregation separation
6. Deterministic procurement decision routing (GRADE_A, URS, REJECT)
7. MANUAL_REVIEW blocking conditions (conflicts, sample shortfall, quality fail)
8. Review signal generation & strict legal policy verification
9. Evidence summary & tamper-evident root hash
10. Deterministic decisioning & JSON serialization round-trip
11. Prevention of double counting in inspection session
"""

import json
from pathlib import Path
import pytest

from app.cv.label_mapping import CanonicalLabel, MappingStatus
from app.cv.model_adapter import Detection
from app.cv.quality import ImageQualityMetrics, QualityGrade
from app.domain.aggregation import aggregate_observations
from app.domain.decision_engine import (
    DECISION_RULE_VERSION,
    evaluate_procurement_decision,
)
from app.domain.inspection_session import (
    InspectionAggregation,
    InspectionCapture,
    InspectionDecision,
    InspectionEvidenceSummary,
    InspectionObservationSet,
    InspectionReviewSignal,
    InspectionSamplingResult,
    InspectionSession,
    InspectionSessionStatus,
    ProcurementGrade,
    ReviewSignalCode,
    ReviewSignalSeverity,
    SamplingStatus,
    compute_evidence_root_hash,
)
from app.domain.onion_observation import (
    ObservationProvenance,
    ObservationStatus,
    OnionObservationRecord,
)
from app.domain.review_signals import generate_review_signals
from app.domain.sampling import evaluate_sampling_sufficiency
from app.domain.status import MeasurementStatus
from app.pipeline.cv_pipeline import CVPipelineResult


def _make_observation(
    obs_id: str,
    semantic: CanonicalLabel = CanonicalLabel.HEALTHY,
    status: ObservationStatus = ObservationStatus.OBSERVED,
    confidence: float = 0.85,
    candidates: list[CanonicalLabel] | None = None,
    candidate_confs: list[float] | None = None,
) -> OnionObservationRecord:
    return OnionObservationRecord(
        observation_id=obs_id,
        capture_id="cap_test",
        bbox=(10.0, 10.0, 100.0, 100.0),
        class_semantic=semantic,
        confidence=confidence,
        observation_status=status,
        visibility_status=status,
        measurement_status=MeasurementStatus.CALIBRATION_NOT_AVAILABLE,
        provenance=ObservationProvenance(
            model_checkpoint="test_checkpoint.pt",
            raw_class_id=0,
            raw_class_name=semantic.value.lower(),
        ),
        candidate_classes=candidates or [semantic],
        candidate_confidences=candidate_confs or [confidence],
        source_detection_ids=[f"det_{obs_id}"],
    )


# 1. Test session creation and model validity
def test_inspection_session_creation():
    obs = _make_observation("obs_1", CanonicalLabel.HEALTHY)
    sampling = evaluate_sampling_sufficiency([obs], target_sample_size=1)
    aggregation = aggregate_observations([obs])
    signals = generate_review_signals(conflict_count=0, quality_grade="PASS")
    decision = evaluate_procurement_decision([obs], sampling, aggregation, signals)

    evidence_hash = compute_evidence_root_hash(
        session_id="ses_1",
        lot_id="lot_1",
        capture_ids=["cap_1"],
        image_hashes=["hash123"],
        observation_ids=["obs_1"],
        procurement_grade=decision.procurement_grade.value,
        rule_version=decision.decision_rule_version,
    )

    evidence = InspectionEvidenceSummary(
        evidence_id="evi_1",
        lot_id="lot_1",
        session_id="ses_1",
        model_version="yolov7",
        mapping_version="VERIFIED",
        sampling_version=sampling.sampling_rule_version,
        rule_version=decision.decision_rule_version,
        measurement_status="CALIBRATION_NOT_AVAILABLE",
        calibration_status="CALIBRATION_NOT_AVAILABLE",
        review_signals=signals,
        decision=decision,
        evidence_root_hash=evidence_hash,
    )

    capture = InspectionCapture(
        capture_id="cap_1",
        image_path="test.jpg",
        raw_detection_count=1,
        reconciled_observation_count=1,
        conflict_count=0,
        visible_condition_counts={"HEALTHY": 1},
        quality_status="PASS",
        mapping_status="VERIFIED",
        measurement_status="CALIBRATION_NOT_AVAILABLE",
        calibration_status="CALIBRATION_NOT_AVAILABLE",
    )

    obs_set = InspectionObservationSet(
        observation_set_id="obs_set_1",
        capture_ids=["cap_1"],
        total_raw_detections=1,
        total_reconciled_observations=1,
        conflict_count=0,
        observations=[obs],
        visible_condition_counts={"HEALTHY": 1},
    )

    session = InspectionSession(
        session_id="ses_1",
        lot_id="lot_1",
        status=InspectionSessionStatus.COMPLETED,
        captures=[capture],
        observation_set=obs_set,
        sampling_result=sampling,
        aggregation=aggregation,
        review_signals=signals,
        decision=decision,
        evidence_summary=evidence,
    )

    assert session.session_id == "ses_1"
    assert session.status == InspectionSessionStatus.COMPLETED
    assert session.decision.procurement_grade == ProcurementGrade.GRADE_A


# 2. Test Sampling Sufficiency Integration (SUFFICIENT, CONTINUE, MANUAL_REVIEW, INVALID)
def test_sampling_sufficiency_statuses():
    # A. Sufficient: count >= target, 0 conflicts
    obs_list = [_make_observation(f"o_{i}") for i in range(20)]
    res = evaluate_sampling_sufficiency(obs_list, target_sample_size=20, conflict_count=0)
    assert res.status == SamplingStatus.SUFFICIENT
    assert res.observed_sample_size == 20
    assert "meets or exceeds" in res.reason

    # B. Continue: count < target, 0 conflicts
    res_continue = evaluate_sampling_sufficiency(obs_list[:5], target_sample_size=20, conflict_count=0)
    assert res_continue.status == SamplingStatus.CONTINUE
    assert res_continue.observed_sample_size == 5
    assert "Additional 15 bulb observation(s) required" in res_continue.reason

    # C. Manual Review: conflict_count > 0
    res_review = evaluate_sampling_sufficiency(obs_list, target_sample_size=20, conflict_count=2)
    assert res_review.status == SamplingStatus.MANUAL_REVIEW
    assert "2 cross-class conflict(s)" in res_review.reason

    # D. Invalid: 0 observations
    res_empty = evaluate_sampling_sufficiency([], target_sample_size=20)
    assert res_empty.status == SamplingStatus.INVALID

    # E. Invalid: Quality FAIL
    res_quality_fail = evaluate_sampling_sufficiency(obs_list, target_sample_size=20, quality_grade="FAIL")
    assert res_quality_fail.status == SamplingStatus.INVALID
    assert "quality screening failed" in res_quality_fail.reason.lower()


# 3. Test Count vs Mass Aggregation Separation
def test_aggregation_count_and_mass_separation():
    obs = [
        _make_observation("o1", CanonicalLabel.HEALTHY),
        _make_observation("o2", CanonicalLabel.HEALTHY),
        _make_observation("o3", CanonicalLabel.DAMAGED),
        _make_observation("o4", CanonicalLabel.ROTTEN),
    ]
    agg = aggregate_observations(obs)

    assert agg.total_count == 4
    assert agg.aggregation_mode == "COUNT_BASED"
    assert agg.count_distribution["HEALTHY"]["count"] == 2
    assert agg.count_distribution["HEALTHY"]["percentage"] == 50.0
    assert agg.count_distribution["DAMAGED"]["count"] == 1
    assert agg.count_distribution["DAMAGED"]["percentage"] == 25.0
    assert agg.count_distribution["ROTTEN"]["count"] == 1
    assert agg.count_distribution["ROTTEN"]["percentage"] == 25.0

    # Strict mass guardrails
    assert agg.mass_status == "UNVALIDATED"
    assert agg.mass_distribution is None
    assert "UNVALIDATED" in agg.disclaimer


# 4. Test Deterministic Decision Routing (GRADE_A, URS, REJECT)
def test_decision_routing_grade_a():
    # 20 observations, 19 healthy, 1 damaged (5% defects, 0% rot)
    obs = [_make_observation(f"h_{i}", CanonicalLabel.HEALTHY) for i in range(19)]
    obs.append(_make_observation("d_1", CanonicalLabel.DAMAGED))

    sampling = evaluate_sampling_sufficiency(obs, target_sample_size=20)
    agg = aggregate_observations(obs)
    signals = generate_review_signals(conflict_count=0, quality_grade="PASS")

    decision = evaluate_procurement_decision(obs, sampling, agg, signals)
    assert decision.procurement_grade == ProcurementGrade.GRADE_A
    assert decision.status == "DECIDED"
    assert len(decision.blocking_reasons) == 0


def test_decision_routing_urs():
    # 20 observations: 17 healthy, 3 damaged (15% defects <= 20%, 0% rot)
    obs = [_make_observation(f"h_{i}", CanonicalLabel.HEALTHY) for i in range(17)]
    obs.extend([_make_observation(f"d_{i}", CanonicalLabel.DAMAGED) for i in range(3)])

    sampling = evaluate_sampling_sufficiency(obs, target_sample_size=20)
    agg = aggregate_observations(obs)
    signals = generate_review_signals(conflict_count=0, quality_grade="PASS")

    decision = evaluate_procurement_decision(obs, sampling, agg, signals)
    assert decision.procurement_grade == ProcurementGrade.URS
    assert decision.status == "DECIDED"


def test_decision_routing_reject():
    # 20 observations: 19 healthy, 1 rotten (5% rotten > 2.0% allowable limit)
    obs = [_make_observation(f"h_{i}", CanonicalLabel.HEALTHY) for i in range(19)]
    obs.append(_make_observation("r_1", CanonicalLabel.ROTTEN))

    sampling = evaluate_sampling_sufficiency(obs, target_sample_size=20)
    agg = aggregate_observations(obs)
    signals = generate_review_signals(conflict_count=0, quality_grade="PASS")

    decision = evaluate_procurement_decision(obs, sampling, agg, signals)
    assert decision.procurement_grade == ProcurementGrade.REJECT
    assert decision.status == "DECIDED"
    assert any("Rotten proportion" in r for r in decision.decision_reasons)


# 5. Test MANUAL_REVIEW Blocking Conditions
def test_manual_review_on_class_conflict():
    obs = [_make_observation("conf_1", CanonicalLabel.CLASS_CONFLICT, ObservationStatus.CLASS_CONFLICT)]
    sampling = evaluate_sampling_sufficiency(obs, target_sample_size=1, conflict_count=1)
    agg = aggregate_observations(obs)
    signals = generate_review_signals(conflict_count=1, quality_grade="PASS")

    decision = evaluate_procurement_decision(obs, sampling, agg, signals)
    assert decision.procurement_grade == ProcurementGrade.MANUAL_REVIEW
    assert decision.status == "REFERRED_TO_MANUAL_REVIEW"
    assert any("Cross-class detection conflict" in b for b in decision.blocking_reasons)


def test_manual_review_on_insufficient_sample():
    obs = [_make_observation("h_1", CanonicalLabel.HEALTHY)]
    sampling = evaluate_sampling_sufficiency(obs, target_sample_size=20, conflict_count=0)
    assert sampling.status == SamplingStatus.CONTINUE

    agg = aggregate_observations(obs)
    signals = generate_review_signals(conflict_count=0, quality_grade="PASS", sampling_status=sampling.status, observed_sample_size=1, target_sample_size=20)

    decision = evaluate_procurement_decision(obs, sampling, agg, signals)
    assert decision.procurement_grade == ProcurementGrade.MANUAL_REVIEW
    assert any("Sampling status is CONTINUE" in b for b in decision.blocking_reasons)


def test_manual_review_on_quality_fail():
    obs = [_make_observation("h_1", CanonicalLabel.HEALTHY)]
    sampling = evaluate_sampling_sufficiency(obs, target_sample_size=1, quality_grade="FAIL")
    agg = aggregate_observations(obs)
    signals = generate_review_signals(conflict_count=0, quality_grade="FAIL")

    decision = evaluate_procurement_decision(obs, sampling, agg, signals)
    assert decision.procurement_grade == ProcurementGrade.MANUAL_REVIEW
    assert any("LOW_IMAGE_QUALITY" in b or "Sampling status is INVALID" in b for b in decision.blocking_reasons)


# 6. Test Review Signal Policy & Safe Terminology
def test_review_signals_legal_policy():
    signals = generate_review_signals(
        conflict_count=2,
        quality_grade="FAIL",
        sampling_status=SamplingStatus.CONTINUE,
        observed_sample_size=5,
        target_sample_size=20,
        calibration_status="CALIBRATION_NOT_AVAILABLE",
        count_mass_divergence_pct=25.0,
        manual_override={"reason": "Adjudicated by committee"},
    )

    codes = [s.code for s in signals]
    assert ReviewSignalCode.CLASS_CONFLICT in codes
    assert ReviewSignalCode.LOW_IMAGE_QUALITY in codes
    assert ReviewSignalCode.INSUFFICIENT_SAMPLE in codes
    assert ReviewSignalCode.CALIBRATION_UNAVAILABLE in codes
    assert ReviewSignalCode.ONION_DIAMETER_UNVALIDATED in codes
    assert ReviewSignalCode.MASS_UNVALIDATED in codes
    assert ReviewSignalCode.COUNT_MASS_DIVERGENCE in codes
    assert ReviewSignalCode.MANUAL_OVERRIDE in codes

    for s in signals:
        # Strict Legal Policy Requirement
        assert "This is a review signal, not proof of fraud." in s.message
        assert "FRAUD DETECTED" not in s.message
        assert "theft" not in s.message.lower()
        assert "tampering" not in s.message.lower()


# 7. Test Evidence Tamper-Evident Root Hash
def test_evidence_root_hash_integrity():
    hash1 = compute_evidence_root_hash(
        session_id="ses_A",
        lot_id="lot_A",
        capture_ids=["cap_1"],
        image_hashes=["sha_img_1"],
        observation_ids=["obs_1", "obs_2"],
        procurement_grade="GRADE_A",
        rule_version="RULES_V1",
    )
    # Same inputs must produce exact same hash
    hash2 = compute_evidence_root_hash(
        session_id="ses_A",
        lot_id="lot_A",
        capture_ids=["cap_1"],
        image_hashes=["sha_img_1"],
        observation_ids=["obs_1", "obs_2"],
        procurement_grade="GRADE_A",
        rule_version="RULES_V1",
    )
    assert hash1 == hash2

    # Different grade changes hash
    hash3 = compute_evidence_root_hash(
        session_id="ses_A",
        lot_id="lot_A",
        capture_ids=["cap_1"],
        image_hashes=["sha_img_1"],
        observation_ids=["obs_1", "obs_2"],
        procurement_grade="REJECT",
        rule_version="RULES_V1",
    )
    assert hash1 != hash3


# 8. Test Deterministic Decisioning
def test_deterministic_decisioning():
    obs = [_make_observation(f"h_{i}", CanonicalLabel.HEALTHY) for i in range(20)]
    sampling = evaluate_sampling_sufficiency(obs, target_sample_size=20)
    agg = aggregate_observations(obs)
    signals = generate_review_signals(conflict_count=0, quality_grade="PASS")

    d1 = evaluate_procurement_decision(obs, sampling, agg, signals)
    d2 = evaluate_procurement_decision(obs, sampling, agg, signals)

    assert d1.procurement_grade == d2.procurement_grade
    assert d1.decision_reasons == d2.decision_reasons
    assert d1.blocking_reasons == d2.blocking_reasons
    assert d1.decision_rule_version == d2.decision_rule_version


# 9. Test JSON Serialization Round-Trip
def test_json_serialization_roundtrip():
    obs = _make_observation("obs_1", CanonicalLabel.HEALTHY)
    sampling = evaluate_sampling_sufficiency([obs], target_sample_size=1)
    agg = aggregate_observations([obs])
    signals = generate_review_signals(conflict_count=0, quality_grade="PASS")
    decision = evaluate_procurement_decision([obs], sampling, agg, signals)
    evidence = InspectionEvidenceSummary(
        evidence_id="evi_1",
        lot_id="lot_1",
        session_id="ses_1",
        model_version="yolov7",
        mapping_version="VERIFIED",
        sampling_version="SAMPLING_V1",
        rule_version="RULES_V1",
        measurement_status="CALIBRATION_NOT_AVAILABLE",
        calibration_status="CALIBRATION_NOT_AVAILABLE",
        review_signals=signals,
        decision=decision,
        evidence_root_hash="aabbcc112233",
    )
    session = InspectionSession(
        session_id="ses_1",
        lot_id="lot_1",
        status=InspectionSessionStatus.COMPLETED,
        captures=[
            InspectionCapture(
                capture_id="cap_1",
                image_path="test.jpg",
                quality_status="PASS",
                mapping_status="VERIFIED",
                measurement_status="CALIBRATION_NOT_AVAILABLE",
                calibration_status="CALIBRATION_NOT_AVAILABLE",
            )
        ],
        observation_set=InspectionObservationSet(
            observation_set_id="obs_set_1",
            observations=[obs],
        ),
        sampling_result=sampling,
        aggregation=agg,
        review_signals=signals,
        decision=decision,
        evidence_summary=evidence,
    )

    json_str = session.model_dump_json(indent=2)
    parsed = json.loads(json_str)
    assert parsed["session_id"] == "ses_1"
    assert parsed["decision"]["procurement_grade"] == "GRADE_A"

    # Validate back to Pydantic
    reconstructed = InspectionSession.model_validate_json(json_str)
    assert reconstructed.session_id == session.session_id
    assert reconstructed.decision.procurement_grade == session.decision.procurement_grade


# 10. Test Prevention of Double Counting in Inspection Service
def test_no_double_counting_in_session():
    from unittest.mock import MagicMock
    from app.pipeline.inspection_service import MandiNyaayInspectionService

    mock_pipeline = MagicMock()
    collapsed_obs = _make_observation("collapsed_1", CanonicalLabel.HEALTHY)
    collapsed_obs.source_detection_ids = ["det_1", "det_2"]

    cv_res = CVPipelineResult(
        capture_id="cap_mock",
        image_path="mock.jpg",
        image_metadata={"sha256": "abcdef"},
        raw_detection_count=2,
        reconciled_observation_count=1,
        conflict_count=0,
        observations=[collapsed_obs],
        mapping_status=MappingStatus.VERIFIED,
        pipeline_status="SUCCESS",
    )
    mock_pipeline.process_image.return_value = cv_res

    service = MandiNyaayInspectionService(pipeline=mock_pipeline)
    session = service.run_inspection(image_input="mock.jpg", target_sample_size=1)

    assert session.captures[0].raw_detection_count == 2
    assert session.captures[0].reconciled_observation_count == 1
    assert len(session.observation_set.observations) == 1
    assert session.aggregation.total_count == 1
    assert session.decision.procurement_grade == ProcurementGrade.GRADE_A

