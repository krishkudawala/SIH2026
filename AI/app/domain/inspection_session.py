"""
Canonical Mandi Nyaay Inspection Session Contracts (Gate 5).

Represents the complete vertical inspection slice:
OBSERVATION -> SAMPLING -> AGGREGATION -> REVIEW SIGNALS -> DECISION -> EVIDENCE

Enforces:
- Strict Pydantic models with explicit IDs, statuses, provenance, and timestamps.
- Explicit separation of count distribution and unvalidated mass distribution.
- Mandated procurement grade states: GRADE_A, URS, REJECT, MANUAL_REVIEW.
- Deterministic, tamper-evident, replayable evidence generation.
- Zero data fabrication.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.domain.onion_observation import OnionObservationRecord, ObservationStatus
from app.domain.status import MeasurementStatus
from app.version import get_processing_version


class ProcurementGrade(str, Enum):
    """
    Standardized procurement decision grades.
    Raw model output must never directly assign a procurement grade.
    """
    GRADE_A = "GRADE_A"
    URS = "URS"
    REJECT = "REJECT"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class SamplingStatus(str, Enum):
    """Statistical sample sufficiency states."""
    SUFFICIENT = "SUFFICIENT"
    CONTINUE = "CONTINUE"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    INVALID = "INVALID"


class ReviewSignalSeverity(str, Enum):
    """Severity classification of inspection review signals."""
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class ReviewSignalCode(str, Enum):
    """Standardized review signal identifiers."""
    CLASS_CONFLICT = "CLASS_CONFLICT"
    LOW_IMAGE_QUALITY = "LOW_IMAGE_QUALITY"
    INSUFFICIENT_SAMPLE = "INSUFFICIENT_SAMPLE"
    CALIBRATION_UNAVAILABLE = "CALIBRATION_UNAVAILABLE"
    CALIBRATION_INVALID = "CALIBRATION_INVALID"
    SIZE_UNVALIDATED = "SIZE_UNVALIDATED"
    ONION_DIAMETER_UNVALIDATED = "ONION_DIAMETER_UNVALIDATED"
    MASS_UNVALIDATED = "MASS_UNVALIDATED"
    COUNT_MASS_DIVERGENCE = "COUNT_MASS_DIVERGENCE"
    WEIGHBRIDGE_REVIEW = "WEIGHBRIDGE_REVIEW"
    RULE_UNAVAILABLE = "RULE_UNAVAILABLE"
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE"


class InspectionSessionStatus(str, Enum):
    """Session lifecycle state."""
    CREATED = "CREATED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    INVALID = "INVALID"


class InspectionReviewSignal(BaseModel):
    """
    Formal operational or quality review signal.

    Guarantees:
    - Never uses accusatory or legal fraud terminology.
    - Always framed as an objective review signal requiring action or recording.
    """
    model_config = ConfigDict(extra="forbid")

    signal_id: str = Field(..., description="Unique deterministic identifier for this signal")
    code: ReviewSignalCode = Field(..., description="Standardized review signal code")
    severity: ReviewSignalSeverity = Field(..., description="Severity classification")
    message: str = Field(..., description="Human-readable review explanation")
    source: str = Field(..., description="Subsystem or pipeline component that generated signal")
    requires_action: bool = Field(default=False, description="Whether this signal blocks automated finalization")
    created_at_iso: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp of signal generation"
    )


class InspectionCapture(BaseModel):
    """
    Standardized result of a single physical photographic capture in the session.
    Grounds all counts in real CV pipeline execution.
    """
    model_config = ConfigDict(extra="forbid")

    capture_id: str = Field(..., description="Unique capture identifier")
    status: str = Field(default="SUCCESS", description="Capture execution status (SUCCESS, QUALITY_FAIL, INVALID_CAPTURE)")
    image_path: str = Field(..., description="Path to input image file")
    image_sha256: str | None = Field(default=None, description="Cryptographic SHA256 digest of image content")
    captured_at_iso: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp of capture processing"
    )
    raw_detection_count: int = Field(default=0, ge=0, description="Raw bounding boxes detected before reconciliation")
    reconciled_observation_count: int = Field(default=0, ge=0, description="Deduplicated physical bulb count")
    conflict_count: int = Field(default=0, ge=0, description="Number of overlapping cross-class conflicts detected")
    visible_condition_counts: dict[str, int] = Field(
        default_factory=dict,
        description="Count of reconciled observations per canonical semantic condition"
    )
    quality_status: str = Field(..., description="Photometric quality assessment grade (PASS, WARN, FAIL)")
    mapping_status: str = Field(..., description="Semantic class mapping verification status")
    measurement_status: str = Field(..., description="Physical measurement readiness status")
    calibration_status: str = Field(..., description="Reference marker calibration status")
    observation_ids: list[str] = Field(
        default_factory=list,
        description="IDs of observations formed directly from this capture"
    )
    model_version: str | None = Field(
        default=None,
        description="Model checkpoint and version applied to this capture"
    )
    capture_role: str = Field(
        default="PRIMARY_SAMPLE_CAPTURE",
        description="Capture role: PRIMARY_SAMPLE_CAPTURE or DETAIL_RECAPTURE"
    )
    provenance: dict[str, Any] = Field(
        default_factory=dict,
        description="Model checkpoint name, version, and execution parameters"
    )


class InspectionObservationSet(BaseModel):
    """
    Aggregated collection of physical produce observations across captures.
    Guarantees no double-counting and full traceability.
    """
    model_config = ConfigDict(extra="forbid")

    observation_set_id: str = Field(..., description="Unique identifier for observation collection")
    status: str = Field(default="VALID", description="Aggregate observation set status (VALID, HAS_CONFLICTS, INVALID)")
    capture_ids: list[str] = Field(default_factory=list, description="IDs of captures contributing to this set")
    total_raw_detections: int = Field(default=0, ge=0, description="Cumulative raw bounding box detections")
    total_reconciled_observations: int = Field(default=0, ge=0, description="Cumulative deduplicated physical bulbs")
    conflict_count: int = Field(default=0, ge=0, description="Total cross-class conflicts across all captures")
    observations: list[OnionObservationRecord] = Field(
        default_factory=list,
        description="List of all deduplicated physical produce observation records"
    )
    visible_condition_counts: dict[str, int] = Field(
        default_factory=dict,
        description="Cumulative count per semantic condition"
    )
    version: str = Field(
        default_factory=get_processing_version,
        description="Software processing version"
    )
    created_at_iso: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp when observation set was formed"
    )


class InspectionSamplingResult(BaseModel):
    """
    Outcome of sampling sufficiency evaluation.
    Explains why sampling is sufficient or why more observations are required.
    """
    model_config = ConfigDict(extra="forbid")

    sampling_id: str = Field(..., description="Unique identifier for sampling determination")
    status: SamplingStatus = Field(..., description="Sufficiency status: SUFFICIENT, CONTINUE, MANUAL_REVIEW, INVALID")
    target_sample_size: int = Field(default=20, ge=1, description="Configured target sample count for lot determination")
    observed_sample_size: int = Field(..., ge=0, description="Actual count of valid produce bulbs observed")
    sampling_rule_version: str = Field(
        default="MANDI_NYAAY_SAMPLING_V1.0",
        description="Versioned sampling policy"
    )
    reason: str = Field(..., description="Clear explanation of why sampling is sufficient or why more are needed")
    limitations: list[str] = Field(
        default_factory=list,
        description="Explicit disclaimers regarding unvalidated mass/size dimensions"
    )
    created_at_iso: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp of sampling evaluation"
    )


class InspectionAggregation(BaseModel):
    """
    Distribution aggregation over canonical observations.

    Guarantees:
    - Clear distinction between Count Distribution and Mass Distribution.
    - Never substitutes count for mass.
    - When mass is unavailable or unvalidated, explicitly states UNVALIDATED.
    """
    model_config = ConfigDict(extra="forbid")

    aggregation_id: str = Field(..., description="Unique identifier for aggregation calculation")
    status: str = Field(default="VALID", description="Aggregation status")
    aggregation_mode: str = Field(default="COUNT_BASED", description="Mode: COUNT_BASED (mass-based unvalidated)")
    total_count: int = Field(default=0, ge=0, description="Total physical bulbs counted")
    total_observations: int = Field(default=0, ge=0, description="Cumulative produce observations across session")
    healthy_count: int = Field(default=0, ge=0, description="Count of healthy bulbs")
    damaged_count: int = Field(default=0, ge=0, description="Count of damaged bulbs")
    sprouted_count: int = Field(default=0, ge=0, description="Count of sprouted bulbs")
    rotten_count: int = Field(default=0, ge=0, description="Count of rotten bulbs")
    class_conflict_count: int = Field(default=0, ge=0, description="Count of class conflict bulbs")
    unresolved_identity_count: int = Field(default=0, ge=0, description="Count of bulbs with unresolved cross-view identity")
    count_distribution: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Count and percentage per condition: {'HEALTHY': {'count': 10, 'percentage': 80.0}, ...}"
    )
    mass_status: str = Field(
        default="UNVALIDATED",
        description="Status of physical mass estimation: UNVALIDATED"
    )
    mass_distribution: dict[str, Any] | None = Field(
        default=None,
        description="Mass per condition. MUST remain None until physical mass calibration is verified."
    )
    disclaimer: str = Field(
        default="Aggregation is based strictly on physical bulb count. Calibrated individual bulb mass is UNVALIDATED and cannot be used for procurement settlement.",
        description="Mandatory aggregation boundary disclaimer"
    )
    version: str = Field(
        default_factory=get_processing_version,
        description="Software processing version"
    )
    created_at_iso: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp of aggregation"
    )


class InspectionDecision(BaseModel):
    """
    Procurement decision resulting from deterministic rule evaluation.
    Never guesses; diverts to MANUAL_REVIEW when uncertainty or blocking conditions exist.
    """
    model_config = ConfigDict(extra="forbid")

    decision_id: str = Field(..., description="Unique identifier for this decision")
    status: str = Field(default="DECIDED", description="Status: DECIDED or REFERRED_TO_MANUAL_REVIEW")
    procurement_grade: ProcurementGrade = Field(
        ...,
        description="Deterministic grade outcome: GRADE_A, URS, REJECT, MANUAL_REVIEW"
    )
    decision_rule_version: str = Field(
        default="MANDI_NYAAY_PROCUREMENT_RULES_V1.0",
        description="Versioned rule pack identifier"
    )
    rule_pack_id: str | None = Field(
        default=None,
        description="Authoritative RulePack identifier (e.g. AGMARK_ONION_2024_V1)"
    )
    rule_pack_version: str | None = Field(
        default=None,
        description="Authoritative RulePack semantic version"
    )
    decision_reasons: list[str] = Field(
        default_factory=list,
        description="Deterministic rationale explaining the grade assignment"
    )
    blocking_reasons: list[str] = Field(
        default_factory=list,
        description="Explicit list of conditions that triggered or contributed to MANUAL_REVIEW"
    )
    input_capture_ids: list[str] = Field(
        default_factory=list,
        description="IDs of captures contributing to this decision"
    )
    input_observation_ids: list[str] = Field(
        default_factory=list,
        description="IDs of physical observations contributing to this decision"
    )
    review_signals: list[InspectionReviewSignal] = Field(
        default_factory=list,
        description="Review signals associated with this decision"
    )
    override_info: dict[str, Any] | None = Field(
        default=None,
        description="Inspector manual override metadata if an override was recorded"
    )
    decided_at_iso: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp of decision"
    )


class InspectionEvidenceSummary(BaseModel):
    """
    Replayable, tamper-evident evidence summary for auditing, dispute resolution,
    and ledger recording.

    Guarantees:
    - Never claims 'tamper-proof'. Explicitly uses 'tamper-evident/replayable'.
    - Contains all cryptographic digests, model versions, rule versions, and observations.
    """
    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(..., description="Unique deterministic evidence package ID")
    lot_id: str = Field(..., description="Identifier of the agricultural produce lot")
    session_id: str = Field(..., description="Associated inspection session ID")
    status: str = Field(default="RECORDED", description="Evidence record status")
    capture_ids: list[str] = Field(default_factory=list, description="IDs of all photographic captures")
    image_hashes: list[str] = Field(default_factory=list, description="SHA256 digests of source images")
    observation_ids: list[str] = Field(default_factory=list, description="IDs of canonical produce observations")
    model_version: str = Field(..., description="Detector model checkpoint and version")
    mapping_version: str = Field(..., description="Semantic mapping version")
    sampling_version: str = Field(..., description="Sampling rule version")
    rule_version: str = Field(..., description="Procurement rule engine version")
    measurement_status: str = Field(..., description="Physical measurement readiness status")
    calibration_status: str = Field(..., description="Calibration marker status")
    review_signals: list[InspectionReviewSignal] = Field(
        default_factory=list,
        description="All review signals emitted during inspection"
    )
    decision: InspectionDecision = Field(..., description="Final procurement decision object")
    override_information: dict[str, Any] | None = Field(
        default=None,
        description="Override details if manual inspector action was logged"
    )
    evidence_root_hash: str = Field(
        ...,
        description="Deterministic SHA256 digest over the canonical evidence content"
    )
    evidence_ledger_term: str = Field(
        default="tamper-evident/replayable",
        description="Audit integrity classification (tamper-evident/replayable)"
    )
    created_at_iso: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp of evidence summary creation"
    )


class InspectionSession(BaseModel):
    """
    Root Mandi Nyaay Inspection Session.
    Encapsulates the entire vertical slice from raw capture to audit evidence.
    """
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(..., description="Unique inspection session identifier")
    lot_id: str = Field(..., description="Associated agricultural lot identifier")
    status: InspectionSessionStatus = Field(..., description="Overall session status")
    captures: list[InspectionCapture] = Field(
        default_factory=list,
        description="Chronological captures taken in this session"
    )
    observation_set: InspectionObservationSet = Field(
        ...,
        description="Reconciled physical produce observations"
    )
    sampling_result: InspectionSamplingResult = Field(
        ...,
        description="Statistical sampling sufficiency assessment"
    )
    aggregation: InspectionAggregation = Field(
        ...,
        description="Count distribution aggregation"
    )
    review_signals: list[InspectionReviewSignal] = Field(
        default_factory=list,
        description="All operational review signals generated"
    )
    decision: InspectionDecision = Field(
        ...,
        description="Procurement grade decision"
    )
    evidence_summary: InspectionEvidenceSummary = Field(
        ...,
        description="Tamper-evident replayable evidence package"
    )
    created_at_iso: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Session start timestamp"
    )
    updated_at_iso: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Session completion timestamp"
    )
    pipeline_version: str = Field(
        default_factory=get_processing_version,
        description="Software pipeline version"
    )


def compute_evidence_root_hash(
    session_id: str,
    lot_id: str,
    capture_ids: list[str],
    image_hashes: list[str],
    observation_ids: list[str],
    procurement_grade: str,
    rule_version: str,
) -> str:
    """
    Compute a deterministic canonical SHA256 root hash over the essential evidence components.
    Provides tamper-evident verification.
    """
    payload = {
        "session_id": session_id,
        "lot_id": lot_id,
        "capture_ids": sorted(capture_ids),
        "image_hashes": sorted(image_hashes),
        "observation_ids": sorted(observation_ids),
        "procurement_grade": procurement_grade,
        "rule_version": rule_version,
    }
    canonical_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(canonical_bytes).hexdigest()


class LotInspectionResult(BaseModel):
    """
    Lot-level procurement and quality inspection result (Phase 17).
    Presents complete inspection outcome with all statuses, counts, and visible uncertainty.
    """
    model_config = ConfigDict(extra="forbid")

    lot_id: str = Field(..., description="Agricultural lot identifier")
    session_id: str = Field(..., description="Inspection session identifier")
    source_reference: str = Field(
        default="BAG_INSPECTOR_SELECTED",
        description="Physical bag or lot source identifier"
    )
    source_selection_note: str = Field(
        default="Source selected by inspector. Physical bag identity is not independently verified.",
        description="Statutory traceability limitation notice"
    )
    sample_size: int = Field(..., ge=0, description="Observed unique physical SampleUnits")
    target_sample_size: int = Field(..., ge=1, description="Target sample size required by rule")
    remaining_sample_size: int = Field(default=0, ge=0, description="Additional sample units required")
    sampling_status: str = Field(..., description="Sampling sufficiency status")
    sampling_reason: str = Field(default="", description="Sampling rationale")
    healthy_count: int = Field(default=0, ge=0)
    damaged_count: int = Field(default=0, ge=0)
    sprouted_count: int = Field(default=0, ge=0)
    rotten_count: int = Field(default=0, ge=0)
    class_conflict_count: int = Field(default=0, ge=0)
    healthy_pct: float = Field(default=0.0)
    damaged_pct: float = Field(default=0.0)
    sprouted_pct: float = Field(default=0.0)
    rotten_pct: float = Field(default=0.0)
    total_defect_pct: float = Field(default=0.0)
    undersized_count: int = Field(default=0, ge=0)
    undersized_pct: float = Field(default=0.0)
    size_status: str = Field(
        default="ONION_DIAMETER_UNVALIDATED",
        description="Status of size estimation: ONION_DIAMETER_UNVALIDATED, CALIBRATION_NOT_AVAILABLE, etc."
    )
    mass_status: str = Field(default="UNVALIDATED", description="Status of mass estimation: UNVALIDATED")
    estimated_lot_mass_kg: float | None = Field(default=None)
    review_signals: list[InspectionReviewSignal] = Field(default_factory=list)
    rule_pack_id: str | None = Field(default=None)
    rule_pack_version: str | None = Field(default=None)
    decision: ProcurementGrade = Field(..., description="Final procurement grade")
    decision_status: str = Field(
        default="DECIDED",
        description="Decision state: DECIDED or REFERRED_TO_MANUAL_REVIEW"
    )
    decision_reasons: list[str] = Field(default_factory=list)
    blocking_reasons: list[str] = Field(default_factory=list)
    evidence_available: bool = Field(default=True)
    evidence_root_hash: str | None = Field(default=None)
    inspection_timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


def build_lot_inspection_result(
    session: InspectionSession,
    source_reference: str = "BAG_INSPECTOR_SELECTED",
    source_selection_note: str = "Source selected by inspector. Physical bag identity is not independently verified.",
    undersized_count: int = 0,
    size_status: str = "ONION_DIAMETER_UNVALIDATED",
) -> LotInspectionResult:
    """
    Construct a canonical LotInspectionResult from an active InspectionSession.
    """
    agg = session.aggregation
    samp = session.sampling_result
    dec = session.decision

    total = agg.total_count
    remaining = max(0, samp.target_sample_size - samp.observed_sample_size)

    counts = agg.count_distribution
    h_pct = counts.get("HEALTHY", {}).get("percentage", 0.0)
    d_pct = counts.get("DAMAGED", {}).get("percentage", 0.0)
    s_pct = counts.get("SPROUTED", {}).get("percentage", 0.0)
    r_pct = counts.get("ROTTEN", {}).get("percentage", 0.0)
    tot_def = round(d_pct + s_pct + r_pct, 2)

    u_pct = round((undersized_count / total * 100.0), 2) if total > 0 else 0.0

    return LotInspectionResult(
        lot_id=session.lot_id,
        session_id=session.session_id,
        source_reference=source_reference,
        source_selection_note=source_selection_note,
        sample_size=samp.observed_sample_size,
        target_sample_size=samp.target_sample_size,
        remaining_sample_size=remaining,
        sampling_status=samp.status.value,
        sampling_reason=samp.reason,
        healthy_count=agg.healthy_count,
        damaged_count=agg.damaged_count,
        sprouted_count=agg.sprouted_count,
        rotten_count=agg.rotten_count,
        class_conflict_count=agg.class_conflict_count,
        healthy_pct=h_pct,
        damaged_pct=d_pct,
        sprouted_pct=s_pct,
        rotten_pct=r_pct,
        total_defect_pct=tot_def,
        undersized_count=undersized_count,
        undersized_pct=u_pct,
        size_status=size_status,
        mass_status=agg.mass_status,
        estimated_lot_mass_kg=None,
        review_signals=session.review_signals,
        rule_pack_id=dec.rule_pack_id,
        rule_pack_version=dec.rule_pack_version,
        decision=dec.procurement_grade,
        decision_status=dec.status,
        decision_reasons=dec.decision_reasons,
        blocking_reasons=dec.blocking_reasons,
        evidence_available=True,
        evidence_root_hash=session.evidence_summary.evidence_root_hash,
        inspection_timestamp=session.updated_at_iso,
    )

