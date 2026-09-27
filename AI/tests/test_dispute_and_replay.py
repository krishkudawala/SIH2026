"""
Tests for Dispute Workflow and Deterministic Session Replay.
"""

from pathlib import Path
import pytest

from app.cv.label_mapping import CanonicalLabel
from app.domain.aggregation import aggregate_observations
from app.domain.decision_engine import evaluate_procurement_decision
from app.domain.dispute import (
    DisputeStatus,
    open_dispute,
    create_blind_secondary_config,
    compare_inspection_distributions,
    resolve_dispute,
)
from app.domain.inspection_session import (
    InspectionAggregation,
    InspectionCapture,
    InspectionEvidenceSummary,
    InspectionObservationSet,
    InspectionSamplingResult,
    InspectionSession,
    InspectionSessionStatus,
    ProcurementGrade,
    compute_evidence_root_hash,
)
from app.domain.onion_observation import (
    ObservationProvenance,
    ObservationStatus,
    OnionObservationRecord,
)
from app.domain.rule_pack import AGMARK_ONION_STANDARD_V1
from app.domain.sampling import SamplingStatus
from app.storage.replay import replay_inspection_session


@pytest.fixture
def sample_session():
    # Build a minimal valid completed session
    obs = [
        OnionObservationRecord(
            observation_id=f"obs_0_{i}",
            capture_id="cap_0",
            bbox=(10.0 + i, 10.0 + i, 50.0 + i, 50.0 + i),
            class_semantic=CanonicalLabel.HEALTHY if i < 19 else CanonicalLabel.ROTTEN,
            confidence=0.85,
            observation_status=ObservationStatus.OBSERVED,
            provenance=ObservationProvenance(
                model_checkpoint="test_model.onnx",
                model_version="v1",
                raw_class_id=0 if i < 19 else 3,
                raw_class_name="healthy" if i < 19 else "rotten",
            ),
        )
        for i in range(20)
    ]
    agg = aggregate_observations(obs)
    samp = InspectionSamplingResult(
        sampling_id="smp_001",
        status=SamplingStatus.SUFFICIENT,
        target_sample_size=20,
        observed_sample_size=20,
        reason="Target sample size met",
    )
    dec = evaluate_procurement_decision(
        observations=obs,
        sampling_result=samp,
        aggregation=agg,
        review_signals=[],
        rule_pack=AGMARK_ONION_STANDARD_V1,
    )
    root_hash = compute_evidence_root_hash(
        session_id="ses_test_01",
        lot_id="LOT_001",
        capture_ids=["cap_0"],
        image_hashes=["hash123"],
        observation_ids=[o.observation_id for o in obs],
        procurement_grade=dec.procurement_grade.value,
        rule_version=dec.decision_rule_version,
    )
    evid = InspectionEvidenceSummary(
        evidence_id="evi_001",
        lot_id="LOT_001",
        session_id="ses_test_01",
        capture_ids=["cap_0"],
        image_hashes=["hash123"],
        observation_ids=[o.observation_id for o in obs],
        model_version="v1",
        mapping_version="VERIFIED",
        sampling_version=samp.sampling_rule_version,
        rule_version=dec.decision_rule_version,
        measurement_status="CALIBRATION_NOT_AVAILABLE",
        calibration_status="CALIBRATION_NOT_AVAILABLE",
        decision=dec,
        evidence_root_hash=root_hash,
    )
    return InspectionSession(
        session_id="ses_test_01",
        lot_id="LOT_001",
        status=InspectionSessionStatus.COMPLETED,
        captures=[],
        observation_set=InspectionObservationSet(
            observation_set_id="os_001",
            status="VALID",
            capture_ids=["cap_0"],
            total_raw_detections=20,
            total_reconciled_observations=20,
            conflict_count=0,
            observations=obs,
        ),
        sampling_result=samp,
        aggregation=agg,
        review_signals=[],
        decision=dec,
        evidence_summary=evid,
    )


def test_dispute_workflow_blindness_and_resolution(sample_session):
    # 1. Open dispute
    disp = open_dispute(sample_session, dispute_reason="Contesting rot grading", opened_by="FARMER_01")
    assert disp.status == DisputeStatus.OPENED
    assert disp.primary_decision_grade == sample_session.decision.procurement_grade

    # 2. Secondary blind config
    sec_cfg = create_blind_secondary_config(
        dispute=disp,
        target_sample_size=20,
        rule_pack_id="AGMARK_ONION_2024_V1",
        source_reference="BAG_B",
        secondary_inspector_id="INSPECTOR_02",
    )
    assert disp.status == DisputeStatus.SECONDARY_INSPECTION_PENDING
    assert sec_cfg.assigned_inspector_id == "INSPECTOR_02"
    assert "redacted" in sec_cfg.blindness_notice.lower()

    # 3. Deterministic comparison
    primary_agg = sample_session.aggregation
    # Simulate secondary aggregation with 10% rotten
    sec_obs = [
        OnionObservationRecord(
            observation_id=f"obs_sec_{i}",
            capture_id="cap_sec",
            bbox=(10.0, 10.0, 50.0, 50.0),
            class_semantic=CanonicalLabel.HEALTHY if i < 18 else CanonicalLabel.ROTTEN,
            confidence=0.85,
            provenance=ObservationProvenance(
                model_checkpoint="test_model.onnx",
                model_version="v1",
                raw_class_id=0,
                raw_class_name="healthy",
            ),
        )
        for i in range(20)
    ]
    sec_agg = aggregate_observations(sec_obs)
    comp = compare_inspection_distributions(primary_agg, sec_agg)
    assert comp.statistical_significance_claimed is False
    assert "No statistical hypothesis significance is claimed" in comp.disclaimer

    # 4. Resolve dispute
    resolved = resolve_dispute(
        disp,
        final_grade=ProcurementGrade.GRADE_A,
        arbitrator_id="ARBITRATOR_LEGAL_CHAIR",
        arbitration_notes="Adjudicated under Grade A allowance criteria.",
    )
    assert resolved.status == DisputeStatus.RESOLVED
    assert resolved.final_resolution_grade == ProcurementGrade.GRADE_A
    assert resolved.resolved_by == "ARBITRATOR_LEGAL_CHAIR"


def test_deterministic_session_replay(sample_session):
    replay_res = replay_inspection_session(sample_session)
    assert replay_res.is_replay_successful is True
    assert replay_res.is_bit_for_bit_identical is True
    assert replay_res.stored_evidence_hash == sample_session.evidence_summary.evidence_root_hash
    assert replay_res.replayed_evidence_hash == sample_session.evidence_summary.evidence_root_hash
    assert replay_res.audit_classification == "TAMPER-EVIDENT/REPLAYABLE"
    assert len(replay_res.discrepancies) == 0
