"""
Deterministic Session Replay Engine for Mandi Nyaay (Gate 6B / Phase 19).

Reconstructs an inspection session from stored inputs and verifies state parity.

CRITICAL TERMINOLOGY RULE:
Uses 'TAMPER-EVIDENT' and 'REPLAYABLE'.
NEVER calls records 'TAMPER-PROOF'.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.domain.aggregation import aggregate_observations
from app.domain.decision_engine import evaluate_procurement_decision
from app.domain.inspection_session import (
    InspectionSession,
    compute_evidence_root_hash,
)
from app.domain.rule_pack import DEFAULT_RULE_PACK, AGMARK_ONION_STANDARD_V1
from app.domain.sampling import evaluate_sampling_sufficiency


class ReplayResult(BaseModel):
    """
    Verification outcome of replaying an inspection session from historical records.
    """
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(..., description="Replayed session ID")
    lot_id: str = Field(..., description="Lot identifier")
    is_replay_successful: bool = Field(..., description="Whether recomputation completed without exception")
    is_bit_for_bit_identical: bool = Field(..., description="Whether replayed evidence root hash matches stored hash exactly")
    stored_evidence_hash: str = Field(..., description="Original evidence root hash")
    replayed_evidence_hash: str = Field(..., description="Re-computed evidence root hash")
    stored_grade: str = Field(..., description="Original procurement grade")
    replayed_grade: str = Field(..., description="Re-computed procurement grade")
    audit_classification: str = Field(
        default="TAMPER-EVIDENT/REPLAYABLE",
        description="Statutory terminology (never tamper-proof)"
    )
    discrepancies: list[str] = Field(
        default_factory=list,
        description="Detailed list of discrepancies if any differences were detected"
    )


def replay_inspection_session(session: InspectionSession) -> ReplayResult:
    """
    Deterministically recompute sampling, aggregation, decision, and evidence root hash
    from stored observations.
    """
    observations = session.observation_set.observations
    target_sample_size = session.sampling_result.target_sample_size
    conflict_count = session.observation_set.conflict_count
    quality_grade = "PASS" if not any("quality" in s.source for s in session.review_signals if s.requires_action) else "FAIL"

    discrepancies: list[str] = []

    # 1. Re-evaluate sampling sufficiency
    replayed_sampling = evaluate_sampling_sufficiency(
        observations=observations,
        target_sample_size=target_sample_size,
        conflict_count=conflict_count,
        quality_grade=quality_grade,
    )
    if replayed_sampling.status != session.sampling_result.status:
        discrepancies.append(
            f"Sampling status divergence: stored '{session.sampling_result.status.value}' vs replayed '{replayed_sampling.status.value}'"
        )

    # 2. Re-evaluate aggregation
    replayed_agg = aggregate_observations(observations=observations)
    if replayed_agg.total_count != session.aggregation.total_count:
        discrepancies.append(
            f"Total count divergence: stored {session.aggregation.total_count} vs replayed {replayed_agg.total_count}"
        )

    # 3. Re-evaluate procurement decision
    replayed_decision = evaluate_procurement_decision(
        observations=observations,
        sampling_result=replayed_sampling,
        aggregation=replayed_agg,
        review_signals=session.review_signals,
        measurement_status=session.evidence_summary.measurement_status,
        decision_rule_version=session.decision.decision_rule_version,
        rule_pack=DEFAULT_RULE_PACK,
    )
    if replayed_decision.procurement_grade != session.decision.procurement_grade:
        discrepancies.append(
            f"Procurement grade divergence: stored '{session.decision.procurement_grade.value}' vs replayed '{replayed_decision.procurement_grade.value}'"
        )

    # 4. Recompute evidence root hash
    replayed_hash = compute_evidence_root_hash(
        session_id=session.session_id,
        lot_id=session.lot_id,
        capture_ids=session.evidence_summary.capture_ids,
        image_hashes=session.evidence_summary.image_hashes,
        observation_ids=session.evidence_summary.observation_ids,
        procurement_grade=replayed_decision.procurement_grade.value,
        rule_version=session.evidence_summary.rule_version,
    )

    stored_hash = session.evidence_summary.evidence_root_hash
    hash_match = replayed_hash == stored_hash
    if not hash_match:
        discrepancies.append(f"Evidence root hash mismatch: stored '{stored_hash}' vs replayed '{replayed_hash}'")

    identical = len(discrepancies) == 0

    return ReplayResult(
        session_id=session.session_id,
        lot_id=session.lot_id,
        is_replay_successful=True,
        is_bit_for_bit_identical=identical,
        stored_evidence_hash=stored_hash,
        replayed_evidence_hash=replayed_hash,
        stored_grade=session.decision.procurement_grade.value,
        replayed_grade=replayed_decision.procurement_grade.value,
        audit_classification="TAMPER-EVIDENT/REPLAYABLE",
        discrepancies=discrepancies,
    )
