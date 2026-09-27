"""
Frozen Flutter / Mobile Client Contracts for Mandi Nyaay (Gate 6B / Phase 27).

These schemas define the exact contract exposed across the Flutter <-> Native Kotlin/Pigeon bridge.
Guarantees:
- Flutter NEVER computes or recreates decision rules or grade thresholds.
- Every state and status is typed and explicit.
- Unvalidated measurements return explicit UNVALIDATED states.
- 100% JSON-serializable.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.domain.inspection_session import (
    ProcurementGrade,
    ReviewSignalCode,
    ReviewSignalSeverity,
    SamplingStatus,
)


class FlutterCaptureContract(BaseModel):
    """Camera capture metadata sent from Flutter."""
    model_config = ConfigDict(extra="forbid")

    capture_id: str
    image_path: str
    capture_role: str = "PRIMARY_SAMPLE_CAPTURE"  # PRIMARY_SAMPLE_CAPTURE or DETAIL_RECAPTURE
    view_angle: str = "TOP"  # PRIMARY, TOP, SIDE, DETAIL, UNDERSIDE
    target_sample_unit_id: str | None = None
    target_cell_id: str | None = None
    captured_at_iso: str


class FlutterImageQualityContract(BaseModel):
    """Quality screening outcome rendered in Flutter viewfinder."""
    model_config = ConfigDict(extra="forbid")

    grade: str  # PASS, WARN, FAIL
    blur_score: float
    mean_luminance: float
    clipped_ratio: float
    reasons: list[str]


class FlutterAnnotationItemContract(BaseModel):
    """Single onion detection box overlay for Flutter camera screen."""
    model_config = ConfigDict(extra="forbid")

    observation_id: str
    sample_unit_id: str | None
    cell_id: str | None
    bbox: list[float]  # [x1, y1, x2, y2]
    class_semantic: str  # HEALTHY, DAMAGED, SPROUTED, ROTTEN, CLASS_CONFLICT
    confidence: float
    title: str  # "Healthy", "Visible damage", "Review required"
    explanation: str
    defect_disclaimer: str = "Externally visible condition only."
    review_required: bool
    size_mm: float | None = None
    size_status: str = "ONION_DIAMETER_UNVALIDATED"
    weight_g: float | None = None
    weight_status: str = "UNVALIDATED"


class FlutterSampleUnitContract(BaseModel):
    """Atomic physical onion model for multi-view navigation in Flutter."""
    model_config = ConfigDict(extra="forbid")

    sample_unit_id: str
    cell_id: str | None
    primary_capture_id: str | None
    detail_capture_ids: list[str]
    resolved_class_semantic: str
    unit_status: str  # RECORDED, DETAIL_AUGMENTED, CONFLICT
    title: str
    explanation: str
    review_required: bool
    size_mm: float | None
    size_status: str
    weight_g: float | None
    weight_status: str
    observation_count: int


class FlutterSamplingContract(BaseModel):
    """Sampling progress card for Flutter inspection screen."""
    model_config = ConfigDict(extra="forbid")

    observed_sample_size: int
    target_sample_size: int
    remaining_sample_size: int
    status: str  # SUFFICIENT, CONTINUE, MANUAL_REVIEW, INVALID
    reason: str
    source_selection_note: str = (
        "Source selected by inspector. Physical bag identity is not independently verified."
    )


class FlutterReviewSignalContract(BaseModel):
    """Review Center item rendered in Flutter review drawer."""
    model_config = ConfigDict(extra="forbid")

    signal_id: str
    code: str
    severity: str  # CRITICAL, WARNING, INFO
    message: str
    source: str
    requires_action: bool


class FlutterProcurementDecisionContract(BaseModel):
    """Final decision banner and grade award in Flutter."""
    model_config = ConfigDict(extra="forbid")

    decision_id: str
    procurement_grade: str  # GRADE_A, URS, REJECT, MANUAL_REVIEW
    status: str  # DECIDED, REFERRED_TO_MANUAL_REVIEW
    rule_pack_id: str | None
    rule_pack_version: str | None
    decision_reasons: list[str]
    blocking_reasons: list[str]
    override_applied: bool = False


class FlutterSessionContract(BaseModel):
    """
    Root inspection contract consumed by Flutter application.
    Freezes all state transitions into a single auditable package.
    """
    model_config = ConfigDict(extra="forbid")

    session_id: str
    lot_id: str
    status: str
    source_reference: str
    sampling: FlutterSamplingContract
    quality: FlutterImageQualityContract | None
    annotations: list[FlutterAnnotationItemContract]
    sample_units: list[FlutterSampleUnitContract]
    condition_counts: dict[str, int]
    condition_percentages: dict[str, float]
    size_status: str
    mass_status: str
    review_signals: list[FlutterReviewSignalContract]
    decision: FlutterProcurementDecisionContract
    evidence_root_hash: str
    offline_ref_code: str
    updated_at_iso: str
