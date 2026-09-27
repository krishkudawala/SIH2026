"""
Procurement Decision Engine for Mandi Nyaay (Gate 6B Part 7).

Evaluates produce observations, sampling status, physical measurements,
and review signals using deterministic, versioned procurement rules.

Guarantees:
- Validated procurement grades: GRADE_A, URS, REJECT, MANUAL_REVIEW.
- Never silently guesses or fabricates a procurement grade.
- Strict diversion to MANUAL_REVIEW upon detection conflicts, sampling shortfalls,
  quality/calibration failures, missing RulePack, or invalid RulePack.
- ZERO hidden global procurement thresholds. All thresholds must be explicitly
  specified in the provided RulePack.
- Decision output MUST include:
  rule_pack_id, rule_pack_version, decision_rule_version, decision_reasons, blocking_reasons.
"""

from __future__ import annotations

import uuid
from typing import Any, Sequence

from app.domain.inspection_session import (
    InspectionAggregation,
    InspectionDecision,
    InspectionReviewSignal,
    InspectionSamplingResult,
    ProcurementGrade,
    ReviewSignalCode,
    ReviewSignalSeverity,
    SamplingStatus,
)
from app.domain.onion_observation import OnionObservationRecord
from app.domain.status import MeasurementStatus
from app.domain.rule_pack import RulePack, DEFAULT_RULE_PACK
from app.domain.rule_pack_validation import validate_rule_pack


DECISION_RULE_VERSION = "MANDI_NYAAY_PROCUREMENT_RULES_V1.0"


class DecisionEngine:
    """
    Deterministic procurement decision engine for Mandi Nyaay (Gate 6B).

    Configured with an explicit, validated RulePack to enforce versioned,
    auditable grading without hidden global thresholds.
    """

    def __init__(self, rule_pack: RulePack | None = None):
        self.rule_pack = rule_pack

    def evaluate(
        self,
        observations: Sequence[OnionObservationRecord],
        sampling_result: InspectionSamplingResult,
        aggregation: InspectionAggregation,
        review_signals: Sequence[InspectionReviewSignal],
        measurement_status: MeasurementStatus | str = MeasurementStatus.CALIBRATION_NOT_AVAILABLE,
        decision_rule_version: str = DECISION_RULE_VERSION,
        measurement_required: bool = False,
        override_info: dict[str, Any] | None = None,
        input_capture_ids: list[str] | None = None,
    ) -> InspectionDecision:
        """
        Evaluate produce observations against the configured RulePack.
        """
        return evaluate_procurement_decision(
            observations=observations,
            sampling_result=sampling_result,
            aggregation=aggregation,
            review_signals=review_signals,
            measurement_status=measurement_status,
            decision_rule_version=decision_rule_version,
            measurement_required=measurement_required,
            override_info=override_info,
            input_capture_ids=input_capture_ids,
            rule_pack=self.rule_pack,
        )


def evaluate_procurement_decision(
    observations: Sequence[OnionObservationRecord],
    sampling_result: InspectionSamplingResult,
    aggregation: InspectionAggregation,
    review_signals: Sequence[InspectionReviewSignal],
    measurement_status: MeasurementStatus | str = MeasurementStatus.CALIBRATION_NOT_AVAILABLE,
    decision_rule_version: str = DECISION_RULE_VERSION,
    measurement_required: bool = False,
    override_info: dict[str, Any] | None = None,
    input_capture_ids: list[str] | None = None,
    rule_pack: RulePack | None = DEFAULT_RULE_PACK,
) -> InspectionDecision:
    """
    Apply deterministic Mandi Nyaay procurement rules to produce an auditable decision.
    Extracts criteria dynamically from an authoritative RulePack.
    If no applicable RulePack is provided or if the RulePack is invalid, diverts automatically to MANUAL_REVIEW.
    Contains ZERO hidden global procurement thresholds.
    """
    decision_id = f"dec_{uuid.uuid4().hex[:8]}"
    blocking_reasons: list[str] = []
    decision_reasons: list[str] = []

    # Derive input capture and observation IDs
    in_obs_ids = [obs.observation_id for obs in observations]
    in_cap_ids = input_capture_ids or sorted(list({obs.capture_id for obs in observations if obs.capture_id}))

    # 1. RulePack Presence & Validity Verification
    if rule_pack is None:
        blocking_reasons.append("NO_APPLICABLE_RULE_PACK: No applicable RulePack provided or verified for lot evaluation.")
        rule_pack_id = None
        rule_pack_version = None
        effective_rule_version = decision_rule_version
    else:
        rule_pack_id = rule_pack.rule_pack_id
        rule_pack_version = rule_pack.version
        effective_rule_version = (
            f"{rule_pack.rule_pack_id}_{rule_pack.version}"
            if decision_rule_version == DECISION_RULE_VERSION
            else decision_rule_version
        )

        validation = validate_rule_pack(rule_pack)
        if not validation.is_valid:
            blocking_reasons.append(
                f"INVALID_RULE_PACK: RulePack validation failed ({'; '.join(validation.errors)})"
            )

    meas_status_str = (
        measurement_status.value
        if isinstance(measurement_status, MeasurementStatus)
        else str(measurement_status)
    )

    # 2. Identify all operational blocking conditions that divert to MANUAL_REVIEW
    # A. Check for class conflicts
    has_conflict = any(sig.code == ReviewSignalCode.CLASS_CONFLICT for sig in review_signals)
    if has_conflict:
        blocking_reasons.append(
            "Cross-class detection conflict detected on 1 or more physical bulbs; manual adjudication required."
        )

    # B. Check sampling status
    if sampling_result.status != SamplingStatus.SUFFICIENT:
        blocking_reasons.append(
            f"Sampling status is {sampling_result.status.value}: {sampling_result.reason}"
        )

    # C. Check critical review signals (e.g. LOW_IMAGE_QUALITY FAIL)
    critical_signals = [
        sig for sig in review_signals
        if sig.severity == ReviewSignalSeverity.CRITICAL and sig.code != ReviewSignalCode.CLASS_CONFLICT
    ]
    for cs in critical_signals:
        blocking_reasons.append(f"Critical review signal [{cs.code.value}]: {cs.message}")

    # D. Check measurement/calibration if required
    if measurement_required and meas_status_str in (
        MeasurementStatus.CALIBRATION_NOT_AVAILABLE.value,
        MeasurementStatus.CALIBRATION_INVALID.value,
    ):
        blocking_reasons.append(
            f"Physical metric measurement is required but status is '{meas_status_str}'."
        )

    # E. Check for count/mass divergence review signal
    divergence_signals = [
        sig for sig in review_signals
        if sig.code == ReviewSignalCode.COUNT_MASS_DIVERGENCE and sig.requires_action
    ]
    for ds in divergence_signals:
        blocking_reasons.append(f"Weighbridge divergence requires review: {ds.message}")

    # If any blocking conditions exist, check if manual override resolves it
    if blocking_reasons:
        if override_info is not None and "override_grade" in override_info:
            override_grade_str = override_info["override_grade"]
            if override_grade_str in ProcurementGrade.__members__:
                grade = ProcurementGrade[override_grade_str]
                decision_reasons.append(
                    f"Manual inspector override applied: Grade adjusted to {grade.value}. Reason: {override_info.get('reason', 'N/A')}"
                )
                return InspectionDecision(
                    decision_id=decision_id,
                    status="DECIDED_WITH_OVERRIDE",
                    procurement_grade=grade,
                    decision_rule_version=effective_rule_version,
                    rule_pack_id=rule_pack_id,
                    rule_pack_version=rule_pack_version,
                    decision_reasons=decision_reasons,
                    blocking_reasons=blocking_reasons,
                    input_capture_ids=in_cap_ids,
                    input_observation_ids=in_obs_ids,
                    review_signals=list(review_signals),
                    override_info=override_info,
                )

        decision_reasons.append(
            "Automated procurement grading halted and diverted to MANUAL_REVIEW due to active blocking conditions."
        )
        return InspectionDecision(
            decision_id=decision_id,
            status="REFERRED_TO_MANUAL_REVIEW",
            procurement_grade=ProcurementGrade.MANUAL_REVIEW,
            decision_rule_version=effective_rule_version,
            rule_pack_id=rule_pack_id,
            rule_pack_version=rule_pack_version,
            decision_reasons=decision_reasons,
            blocking_reasons=blocking_reasons,
            input_capture_ids=in_cap_ids,
            input_observation_ids=in_obs_ids,
            review_signals=list(review_signals),
            override_info=override_info,
        )

    # 3. Extract dynamic threshold criteria from RulePack (ZERO hidden fallbacks)
    assert rule_pack is not None

    rot_reject_crit = rule_pack.get_criterion("crit_rot_reject") or rule_pack.get_criterion_by_param("rotten_percentage")
    rot_grade_a_crit = rule_pack.get_criterion("crit_rot_grade_a")
    tot_grade_a_crit = rule_pack.get_criterion("crit_total_defects_grade_a") or rule_pack.get_criterion_by_param("total_defect_percentage")
    tot_urs_crit = rule_pack.get_criterion("crit_total_defects_urs")

    # If any required criteria are missing from RulePack, REFUSE to use hidden constants
    missing_crit_reasons: list[str] = []
    if rot_reject_crit is None:
        missing_crit_reasons.append("Missing criterion for maximum rotten reject limit ('crit_rot_reject').")
    if rot_grade_a_crit is None:
        missing_crit_reasons.append("Missing criterion for Grade A rotten limit ('crit_rot_grade_a').")
    if tot_grade_a_crit is None:
        missing_crit_reasons.append("Missing criterion for Grade A total defect limit ('crit_total_defects_grade_a').")
    if tot_urs_crit is None:
        missing_crit_reasons.append("Missing criterion for URS total defect limit ('crit_total_defects_urs').")

    if missing_crit_reasons:
        blocking_reasons.extend(missing_crit_reasons)
        decision_reasons.append(
            "Automated procurement grading halted: RulePack lacks required threshold criteria. "
            "System strictly refuses to fall back to hidden default thresholds."
        )
        return InspectionDecision(
            decision_id=decision_id,
            status="REFERRED_TO_MANUAL_REVIEW",
            procurement_grade=ProcurementGrade.MANUAL_REVIEW,
            decision_rule_version=effective_rule_version,
            rule_pack_id=rule_pack_id,
            rule_pack_version=rule_pack_version,
            decision_reasons=decision_reasons,
            blocking_reasons=blocking_reasons,
            input_capture_ids=in_cap_ids,
            input_observation_ids=in_obs_ids,
            review_signals=list(review_signals),
            override_info=override_info,
        )

    # Strictly extract values from verified RulePack
    reject_min_rot = rot_reject_crit.threshold_value
    grade_a_max_rot = rot_grade_a_crit.threshold_value
    grade_a_max_defects = tot_grade_a_crit.threshold_value
    urs_max_defects = tot_urs_crit.threshold_value

    # 4. Deterministic Grading Rules (Executed only when sampling is SUFFICIENT and all criteria are verified)
    counts = aggregation.count_distribution
    rotten_pct = counts.get("ROTTEN", {}).get("percentage", 0.0)
    damaged_pct = counts.get("DAMAGED", {}).get("percentage", 0.0)
    sprouted_pct = counts.get("SPROUTED", {}).get("percentage", 0.0)
    total_defect_pct = rotten_pct + damaged_pct + sprouted_pct

    # Rule 1: Immediate Reject on excessive rotten proportion
    if rotten_pct > reject_min_rot:
        decision_reasons.append(
            f"Rotten proportion ({rotten_pct:.1f}%) exceeds maximum allowable limit ({reject_min_rot:.1f}%)."
        )
        grade = ProcurementGrade.REJECT

    # Rule 2: Grade A eligibility
    elif total_defect_pct <= grade_a_max_defects and rotten_pct <= grade_a_max_rot:
        decision_reasons.append(
            f"Produce meets Grade A specifications: total defects ({total_defect_pct:.1f}%) <= {grade_a_max_defects:.1f}% "
            f"and rotten ({rotten_pct:.1f}%) <= {grade_a_max_rot:.1f}%."
        )
        grade = ProcurementGrade.GRADE_A

    # Rule 3: URS (Under-grade Re-sort / Utility) eligibility
    elif total_defect_pct <= urs_max_defects:
        decision_reasons.append(
            f"Produce meets URS (Under-grade Re-sort) specifications: total defects ({total_defect_pct:.1f}%) <= {urs_max_defects:.1f}%. "
            "Commercial re-sorting or utility pricing required."
        )
        grade = ProcurementGrade.URS

    # Rule 4: Reject on excessive defects
    else:
        decision_reasons.append(
            f"Produce rejected: Total defects ({total_defect_pct:.1f}%) exceeds maximum allowable limit ({urs_max_defects:.1f}%)."
        )
        grade = ProcurementGrade.REJECT

    # Check if manual override modifies final grade
    if override_info is not None and "override_grade" in override_info:
        override_grade_str = override_info["override_grade"]
        if override_grade_str in ProcurementGrade.__members__:
            grade = ProcurementGrade[override_grade_str]
            decision_reasons.append(
                f"Manual inspector override applied: Grade adjusted to {grade.value}. Reason: {override_info.get('reason', 'N/A')}"
            )

    return InspectionDecision(
        decision_id=decision_id,
        status="DECIDED",
        procurement_grade=grade,
        decision_rule_version=effective_rule_version,
        rule_pack_id=rule_pack_id,
        rule_pack_version=rule_pack_version,
        decision_reasons=decision_reasons,
        blocking_reasons=[],
        input_capture_ids=in_cap_ids,
        input_observation_ids=in_obs_ids,
        review_signals=list(review_signals),
        override_info=override_info,
    )
