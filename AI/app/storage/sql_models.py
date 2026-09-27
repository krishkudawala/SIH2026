"""
SQLModel Database Entities for Mandi Nyaay (Gate 8 & Feature 20).

Pure local offline relational models backed by SQLite.
Persists sessions, captures, observations, sample units, review signals,
procurement decisions, disputes, event timeline, and physical calibration samples.
"""

from __future__ import annotations

from typing import Optional
from sqlmodel import Field, SQLModel


class SessionModel(SQLModel, table=True):
    __tablename__ = "inspection_sessions"

    id: str = Field(primary_key=True, index=True)
    lot_id: str = Field(index=True)
    source_reference: str = Field(default="BAG_INSPECTOR_SELECTED")
    source_selected_by_inspector: bool = Field(default=True)
    physical_source_identity_verified: bool = Field(default=False)
    target_sample_size: int = Field(default=20)
    status: str = Field(default="CREATED")
    rule_pack_id: Optional[str] = Field(default="AGMARK_ONION_2024_V1")
    rule_pack_version: Optional[str] = Field(default="1.0.0")
    procurement_grade: Optional[str] = Field(default=None)
    quality_grade: Optional[str] = Field(default=None)
    size_status: str = Field(default="ONION_DIAMETER_UNVALIDATED")
    mass_status: str = Field(default="MASS_UNVALIDATED")
    evidence_root_hash: Optional[str] = Field(default=None)
    offline_ref_code: Optional[str] = Field(default=None)
    created_at: str
    updated_at: str
    data_json: str = Field(default="{}")


class CaptureModel(SQLModel, table=True):
    __tablename__ = "inspection_captures"

    id: str = Field(primary_key=True, index=True)
    session_id: str = Field(index=True)
    image_path: str
    capture_role: str = Field(default="PRIMARY_SAMPLE_CAPTURE")
    view_angle: str = Field(default="TOP")
    target_sample_unit_id: Optional[str] = Field(default=None)
    target_cell_id: Optional[str] = Field(default=None)
    quality_grade: str = Field(default="PASS")
    blur_score: float = Field(default=0.0)
    mean_luminance: float = Field(default=0.0)
    clipped_ratio: float = Field(default=0.0)
    captured_at: str


class SampleUnitModel(SQLModel, table=True):
    __tablename__ = "sample_units"

    id: str = Field(primary_key=True, index=True)
    session_id: str = Field(index=True)
    lot_id: str = Field(index=True)
    cell_id: Optional[str] = Field(default=None)
    primary_capture_id: Optional[str] = Field(default=None)
    resolved_class_semantic: str = Field(default="HEALTHY")
    unit_status: str = Field(default="RECORDED")
    size_mm: Optional[float] = Field(default=None)
    length_mm: Optional[float] = Field(default=None)
    width_mm: Optional[float] = Field(default=None)
    thickness_mm: Optional[float] = Field(default=None)
    geometric_diameter_mm: Optional[float] = Field(default=None)
    sphericity: Optional[float] = Field(default=None)
    volume_cm3: Optional[float] = Field(default=None)
    size_status: str = Field(default="ONION_DIAMETER_UNVALIDATED")
    weight_estimate_g: Optional[float] = Field(default=None)
    weight_interval_low_g: Optional[float] = Field(default=None)
    weight_interval_high_g: Optional[float] = Field(default=None)
    weight_status: str = Field(default="MASS_UNVALIDATED")
    weight_model_version: Optional[str] = Field(default="v1.0")
    weight_calibration_version: Optional[str] = Field(default="uncalibrated")
    review_required: bool = Field(default=False)
    title: str = Field(default="Healthy")
    explanation: str = Field(default="No modeled visible defect detected.")
    created_at: str


class ObservationModel(SQLModel, table=True):
    __tablename__ = "onion_observations"

    id: str = Field(primary_key=True, index=True)
    session_id: str = Field(index=True)
    capture_id: str = Field(index=True)
    sample_unit_id: Optional[str] = Field(default=None, index=True)
    bbox_x1: float
    bbox_y1: float
    bbox_x2: float
    bbox_y2: float
    class_semantic: str
    confidence: float
    classifier_class: Optional[str] = Field(default=None)
    classifier_confidence: Optional[float] = Field(default=None)
    visible_defect_area_px: float = Field(default=0.0)
    onion_silhouette_area_px: float = Field(default=0.0)
    visible_defect_fraction: float = Field(default=0.0)
    mask_quality: float = Field(default=0.0)
    observation_status: str = Field(default="OBSERVED")
    review_required: bool = Field(default=False)
    title: str = Field(default="Healthy")
    explanation: str = Field(default="")


class ReviewSignalModel(SQLModel, table=True):
    __tablename__ = "review_signals"

    id: str = Field(primary_key=True, index=True)
    session_id: str = Field(index=True)
    code: str
    severity: str
    message: str
    source: str
    requires_action: bool = Field(default=False)
    created_at: str


class DecisionModel(SQLModel, table=True):
    __tablename__ = "inspection_decisions"

    id: str = Field(primary_key=True, index=True)
    session_id: str = Field(unique=True, index=True)
    procurement_grade: str
    status: str
    rule_pack_id: Optional[str] = Field(default=None)
    rule_pack_version: Optional[str] = Field(default=None)
    decision_reasons_json: str = Field(default="[]")
    blocking_reasons_json: str = Field(default="[]")
    override_applied: bool = Field(default=False)
    override_grade: Optional[str] = Field(default=None)
    override_reason: Optional[str] = Field(default=None)
    decided_at: str


class DisputeModel(SQLModel, table=True):
    __tablename__ = "inspection_disputes"

    id: str = Field(primary_key=True, index=True)
    lot_id: str = Field(index=True)
    primary_session_id: str = Field(index=True)
    primary_evidence_hash: str
    primary_decision_grade: str
    dispute_reason: str
    opened_by: str
    opened_at: str
    status: str
    secondary_session_id: Optional[str] = Field(default=None)
    secondary_evidence_hash: Optional[str] = Field(default=None)
    secondary_decision_grade: Optional[str] = Field(default=None)
    comparison_json: Optional[str] = Field(default=None)
    arbitration_notes: Optional[str] = Field(default=None)
    final_resolution_grade: Optional[str] = Field(default=None)
    resolved_by: Optional[str] = Field(default=None)
    resolved_at: Optional[str] = Field(default=None)


class EventLedgerModel(SQLModel, table=True):
    __tablename__ = "event_ledger"

    id: str = Field(primary_key=True, index=True)
    session_id: str = Field(index=True)
    sequence_number: int
    event_type: str
    timestamp: str
    payload_json: str
    payload_hash: str
    previous_event_hash: str
    event_hash: str


class CalibrationSampleModel(SQLModel, table=True):
    __tablename__ = "calibration_samples"

    id: str = Field(primary_key=True, index=True)
    sample_unit_id: str = Field(index=True)
    lot_id: str
    length_mm: float
    width_mm: float
    thickness_mm: float
    geometric_diameter_mm: float
    volume_cm3: float
    aspect_ratio: float = Field(default=1.0)
    sphericity: float = Field(default=0.9)
    actual_scale_weight_g: float
    condition: str = Field(default="HEALTHY")
    defect_fraction: float = Field(default=0.0)
    variety: str = Field(default="Nashik Red")
    operator_id: str = Field(default="INSPECTOR_01")
    created_at: str
