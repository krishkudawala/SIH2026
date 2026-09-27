"""
Domain Onion Observation Contract for Mandi Nyaay.

Represents an individual produce observation directly grounded in real sensor/model evidence.
Enforces:
- Explicit uncertainty (confidence thresholds, visibility state)
- Semantic classification (CanonicalLabel)
- Traceable provenance (checkpoint, raw class, model version)
- Zero procurement grade fabrication
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.cv.label_mapping import CanonicalLabel
from app.domain.status import MeasurementStatus
from app.version import get_processing_version


class ObservationStatus(str, Enum):
    """Observable physical state and detection quality of an individual bulb."""
    OBSERVED = "OBSERVED"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    CLASS_CONFLICT = "CLASS_CONFLICT"
    UNKNOWN_MAPPING = "UNKNOWN_MAPPING"
    INVALID_CAPTURE = "INVALID_CAPTURE"
    CROSS_VIEW_IDENTITY_UNRESOLVED = "CROSS_VIEW_IDENTITY_UNRESOLVED"
    # Backwards compatibility alias
    VISIBLE = "OBSERVED"


# Backwards compatibility alias
VisibilityStatus = ObservationStatus


class ObservationProvenance(BaseModel):
    """Cryptographic and operational lineage of this specific observation."""
    model_config = ConfigDict(extra="forbid")

    model_checkpoint: str = Field(..., description="Path or identifier of model checkpoint")
    model_version: str = Field(
        default_factory=get_processing_version,
        description="Software processing version"
    )
    raw_class_id: int = Field(..., description="Original integer class predicted by detector")
    raw_class_name: str = Field(..., description="Original class label string from model")
    created_at_iso: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp when observation was formed"
    )


class OnionObservationRecord(BaseModel):
    """
    Standard domain model for an observed onion instance in a capture.
    Guarantees no double-counting and reviewable conflict handling.
    """
    model_config = ConfigDict(extra="forbid")

    observation_id: str = Field(..., description="Unique deterministic identifier for this observation")
    capture_id: str = Field(..., description="Associated capture session identifier")
    bbox: tuple[float, float, float, float] = Field(
        ...,
        description="Bounding box in image coordinates (x1, y1, x2, y2)"
    )
    class_semantic: CanonicalLabel = Field(
        ...,
        description="Canonical semantic classification (e.g. HEALTHY, DAMAGED, ROTTEN, SPROUTED, CLASS_CONFLICT)"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Detector confidence score"
    )
    observation_status: ObservationStatus = Field(
        default=ObservationStatus.OBSERVED,
        description="Observation classification integrity (OBSERVED, LOW_CONFIDENCE, CLASS_CONFLICT, UNKNOWN_MAPPING, INVALID_CAPTURE)"
    )
    visibility_status: ObservationStatus = Field(
        default=ObservationStatus.OBSERVED,
        description="Observation classification state (retained for backward compatibility)"
    )
    measurement_status: MeasurementStatus = Field(
        default=MeasurementStatus.NOT_IMPLEMENTED,
        description="Physical metric measurement readiness (planar homography / calibrated)"
    )
    cross_view_identity_status: str = Field(
        default="CROSS_VIEW_IDENTITY_UNRESOLVED",
        description="Cross-capture physical identity status (CROSS_VIEW_IDENTITY_UNRESOLVED until validated correspondence)"
    )
    provenance: ObservationProvenance = Field(
        ...,
        description="Lineage and model metadata that produced this observation"
    )
    candidate_classes: list[CanonicalLabel] = Field(
        default_factory=list,
        description="Candidate classes when status is CLASS_CONFLICT, or single class when resolved"
    )
    candidate_confidences: list[float] = Field(
        default_factory=list,
        description="Candidate confidences corresponding to candidate classes"
    )
    source_detection_ids: list[str] = Field(
        default_factory=list,
        description="IDs of source detections that collapsed into this physical observation"
    )
    reconciliation_iou: float | None = Field(
        default=None,
        description="IoU between conflicting or duplicate bounding boxes during reconciliation"
    )
    reconciliation_rule: str | None = Field(
        default=None,
        description="Identifier of reconciliation rule applied"
    )
    title: str = Field(
        default="Healthy",
        description="Canonical human-readable observation title"
    )
    explanation: str = Field(
        default="No modeled visible defect detected.",
        description="Canonical observation explanation"
    )
    review_required: bool = Field(
        default=False,
        description="Whether this observation requires manual inspector review"
    )
    source_observation: str | None = Field(
        default=None,
        description="Primary source detection or reference identifier"
    )
    defect_disclaimer: str = Field(
        default="Externally visible condition only.",
        description="Explicit limitation disclaimer"
    )


def resolve_annotation_ui(
    class_semantic: CanonicalLabel,
    observation_status: ObservationStatus,
) -> tuple[str, str, bool]:
    """
    Resolve canonical human-readable title, explanation, and review requirement.
    Guarantees:
    - Never implies internal quality (always externally visible condition only).
    - CLASS_CONFLICT produces 'Review required'.
    """
    if observation_status == ObservationStatus.CLASS_CONFLICT or class_semantic == CanonicalLabel.CLASS_CONFLICT:
        return (
            "Review required",
            "Overlapping detections disagree on the visible condition. The system did not select one class automatically.",
            True,
        )

    if observation_status == ObservationStatus.LOW_CONFIDENCE:
        return (
            "Review required",
            "Detection confidence is below reliable operational threshold. Externally visible condition only.",
            True,
        )

    if class_semantic == CanonicalLabel.HEALTHY:
        return (
            "Healthy",
            "No modeled visible defect detected.",
            False,
        )
    elif class_semantic == CanonicalLabel.DAMAGED:
        return (
            "Visible damage",
            "Visible damaged condition detected. Externally visible condition only.",
            False,
        )
    elif class_semantic == CanonicalLabel.SPROUTED:
        return (
            "Visible sprouting",
            "Visible sprouting detected. Externally visible condition only.",
            False,
        )
    elif class_semantic == CanonicalLabel.ROTTEN:
        return (
            "Visible rotten condition",
            "Visible rotten-condition pattern detected. Externally visible condition only.",
            False,
        )
    else:
        return (
            "Review required",
            "Unrecognized or unverified condition mapping. Externally visible condition only.",
            True,
        )

