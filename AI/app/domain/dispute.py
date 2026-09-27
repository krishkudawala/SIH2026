"""
Dispute Resolution & Blind Secondary Inspection Workflow for Mandi Nyaay (Gate 6B / Phase 18).

Workflow:
1. OPEN DISPUTE: Farmer, trader, or inspector formally challenges primary result.
2. CREATE BLIND SECONDARY INSPECTION: Generates secondary inspection session with
   primary counts, primary defects, and primary decision strictly hidden/redacted.
3. SECOND INSPECTION: Secondary inspector conducts independent evaluation.
4. COMPARE DISTRIBUTIONS: Deterministic comparison of primary vs secondary condition distributions.
5. HUMAN ARBITRATION: Mandi board/APMC arbitrator reviews discrepancies and evidence.
6. FINAL RESOLUTION: Certified binding decision with tamper-evident evidence package.

ANTI-FABRICATION RULE:
Do NOT claim statistical significance unless justified by physical sample size and tests.
Comparison is deterministic and reports absolute and percentage point differences.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid
from pydantic import BaseModel, ConfigDict, Field

from app.domain.inspection_session import (
    InspectionAggregation,
    InspectionDecision,
    InspectionSession,
    ProcurementGrade,
)


class DisputeStatus(str, Enum):
    """Lifecycle status of an inspection dispute."""
    OPENED = "OPENED"
    SECONDARY_INSPECTION_PENDING = "SECONDARY_INSPECTION_PENDING"
    SECONDARY_INSPECTION_COMPLETED = "SECONDARY_INSPECTION_COMPLETED"
    UNDER_ARBITRATION = "UNDER_ARBITRATION"
    RESOLVED = "RESOLVED"


class BlindSecondarySessionConfig(BaseModel):
    """
    Configuration for secondary inspection guaranteeing inspector blindness.
    Strictly omits primary counts, defects, and grading decisions.
    """
    model_config = ConfigDict(extra="forbid")

    dispute_id: str
    lot_id: str
    secondary_session_id: str
    target_sample_size: int
    rule_pack_id: str
    source_reference: str
    assigned_inspector_id: str
    blindness_notice: str = (
        "BLIND INSPECTION NOTICE: Previous inspection counts, condition breakdowns, "
        "and procurement grades have been redacted to ensure objective, independent re-grading."
    )


class DistributionComparison(BaseModel):
    """
    Deterministic comparison between primary and secondary inspection distributions.
    """
    model_config = ConfigDict(extra="forbid")

    primary_sample_size: int
    secondary_sample_size: int
    condition_differences: dict[str, dict[str, float]]
    total_defect_diff_pct: float
    max_condition_divergence_pct: float
    requires_arbitration: bool
    divergence_threshold_pct: float
    comparison_method: str = "DETERMINISTIC_ABSOLUTE_DIFFERENCE"
    statistical_significance_claimed: bool = False
    disclaimer: str = (
        "Comparison is deterministic. No statistical hypothesis significance is claimed "
        "due to finite non-parametric agricultural lot sample constraints."
    )


class DisputeRecord(BaseModel):
    """
    Permanent, auditable record of an inspection dispute and its resolution.
    """
    model_config = ConfigDict(extra="forbid")

    dispute_id: str = Field(..., description="Unique dispute identifier")
    lot_id: str = Field(..., description="Agricultural lot identifier")
    primary_session_id: str = Field(..., description="Original inspection session ID")
    primary_evidence_hash: str = Field(..., description="Evidence root hash of primary inspection")
    primary_decision_grade: ProcurementGrade = Field(..., description="Primary procurement grade (hidden from secondary inspector)")
    dispute_reason: str = Field(..., description="Statement of dispute reason submitted by challenger")
    opened_by: str = Field(..., description="Identifier of party opening dispute (farmer, trader, supervisor)")
    opened_at_iso: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp of dispute opening"
    )
    status: DisputeStatus = Field(default=DisputeStatus.OPENED, description="Dispute lifecycle status")
    secondary_session_id: str | None = Field(default=None, description="Session ID of blind secondary inspection")
    secondary_evidence_hash: str | None = Field(default=None, description="Evidence root hash of secondary inspection")
    secondary_decision_grade: ProcurementGrade | None = Field(default=None, description="Secondary inspection decision")
    comparison: DistributionComparison | None = Field(default=None, description="Comparative distribution analysis")
    arbitration_notes: str | None = Field(default=None, description="Findings of human arbitrator / committee")
    final_resolution_grade: ProcurementGrade | None = Field(default=None, description="Binding procurement grade awarded")
    resolved_by: str | None = Field(default=None, description="Arbitrator or committee chairperson ID")
    resolved_at_iso: str | None = Field(default=None, description="Timestamp of final dispute resolution")


def open_dispute(
    primary_session: InspectionSession,
    dispute_reason: str,
    opened_by: str = "LOT_OWNER",
) -> DisputeRecord:
    """
    Formally open an inspection dispute against a completed session.
    """
    dispute_id = f"dsp_{uuid.uuid4().hex[:8]}"
    return DisputeRecord(
        dispute_id=dispute_id,
        lot_id=primary_session.lot_id,
        primary_session_id=primary_session.session_id,
        primary_evidence_hash=primary_session.evidence_summary.evidence_root_hash,
        primary_decision_grade=primary_session.decision.procurement_grade,
        dispute_reason=dispute_reason,
        opened_by=opened_by,
        status=DisputeStatus.OPENED,
    )


def create_blind_secondary_config(
    dispute: DisputeRecord,
    target_sample_size: int,
    rule_pack_id: str,
    source_reference: str,
    secondary_inspector_id: str,
) -> BlindSecondarySessionConfig:
    """
    Generate session initialization configuration for the secondary inspector.
    Guarantees strict blindness: zero primary counts or grades are leaked.
    """
    sec_session_id = f"sec_sess_{uuid.uuid4().hex[:8]}"
    dispute.secondary_session_id = sec_session_id
    dispute.status = DisputeStatus.SECONDARY_INSPECTION_PENDING

    return BlindSecondarySessionConfig(
        dispute_id=dispute.dispute_id,
        lot_id=dispute.lot_id,
        secondary_session_id=sec_session_id,
        target_sample_size=target_sample_size,
        rule_pack_id=rule_pack_id,
        source_reference=source_reference,
        assigned_inspector_id=secondary_inspector_id,
    )


def compare_inspection_distributions(
    primary_agg: InspectionAggregation,
    secondary_agg: InspectionAggregation,
    divergence_threshold_pct: float = 5.0,
) -> DistributionComparison:
    """
    Deterministically compare condition distributions between primary and secondary inspections.

    ANTI-FABRICATION RULE:
    Explicitly declares statistical_significance_claimed = False.
    """
    p_counts = primary_agg.count_distribution
    s_counts = secondary_agg.count_distribution

    conditions = sorted(list(set(list(p_counts.keys()) + list(s_counts.keys()))))
    diffs: dict[str, dict[str, float]] = {}
    max_div = 0.0

    for cond in conditions:
        p_pct = p_counts.get(cond, {}).get("percentage", 0.0)
        s_pct = s_counts.get(cond, {}).get("percentage", 0.0)
        diff_pct = round(abs(s_pct - p_pct), 2)
        diffs[cond] = {
            "primary_pct": p_pct,
            "secondary_pct": s_pct,
            "absolute_diff_pct": diff_pct,
        }
        if diff_pct > max_div:
            max_div = diff_pct

    p_def = sum(p_counts.get(c, {}).get("percentage", 0.0) for c in ["DAMAGED", "SPROUTED", "ROTTEN"])
    s_def = sum(s_counts.get(c, {}).get("percentage", 0.0) for c in ["DAMAGED", "SPROUTED", "ROTTEN"])
    total_def_diff = round(abs(s_def - p_def), 2)

    req_arbitration = max_div > divergence_threshold_pct or total_def_diff > divergence_threshold_pct

    return DistributionComparison(
        primary_sample_size=primary_agg.total_count,
        secondary_sample_size=secondary_agg.total_count,
        condition_differences=diffs,
        total_defect_diff_pct=total_def_diff,
        max_condition_divergence_pct=max_div,
        requires_arbitration=req_arbitration,
        divergence_threshold_pct=divergence_threshold_pct,
        statistical_significance_claimed=False,
    )


def record_secondary_inspection(
    dispute: DisputeRecord,
    secondary_session: InspectionSession,
    divergence_threshold_pct: float = 5.0,
    primary_aggregation: InspectionAggregation | None = None,
) -> DisputeRecord:
    """
    Record secondary inspection completion and compute comparative analysis.
    """
    dispute.secondary_session_id = secondary_session.session_id
    dispute.secondary_evidence_hash = secondary_session.evidence_summary.evidence_root_hash
    dispute.secondary_decision_grade = secondary_session.decision.procurement_grade
    dispute.status = DisputeStatus.SECONDARY_INSPECTION_COMPLETED

    if primary_aggregation is not None:
        dispute.comparison = compare_inspection_distributions(
            primary_aggregation,
            secondary_session.aggregation,
            divergence_threshold_pct=divergence_threshold_pct,
        )
        if dispute.comparison.requires_arbitration or dispute.primary_decision_grade != dispute.secondary_decision_grade:
            dispute.status = DisputeStatus.UNDER_ARBITRATION

    return dispute


def resolve_dispute(
    dispute: DisputeRecord,
    final_grade: ProcurementGrade,
    arbitrator_id: str,
    arbitration_notes: str,
) -> DisputeRecord:
    """
    Formally conclude dispute with human arbitration ruling.
    """
    dispute.final_resolution_grade = final_grade
    dispute.resolved_by = arbitrator_id
    dispute.arbitration_notes = arbitration_notes
    dispute.resolved_at_iso = datetime.now(timezone.utc).isoformat()
    dispute.status = DisputeStatus.RESOLVED
    return dispute
