"""
Physical Sample Identity Engine for Mandi Nyaay (Gate 6B).

Establishes strict physical sample identity boundaries to prevent repeated views
of the same physical onion from silently inflating the sampling denominator.

Guarantees:
- Every observation must belong to an explicit physical SampleUnit.
- Capture roles: PRIMARY_SAMPLE_CAPTURE vs. DETAIL_RECAPTURE.
- PRIMARY_SAMPLE_CAPTURE may instantiate new physical SampleUnits.
- DETAIL_RECAPTURE augments existing SampleUnits with additional evidence (TOP, SIDE, DETAIL).
- DETAIL_RECAPTURE MUST NEVER increment the physical sample size denominator.
- Without explicit correspondence, observations are marked CROSS_VIEW_IDENTITY_UNRESOLVED
  and cannot be silently merged.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Sequence
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.cv.label_mapping import CanonicalLabel
from app.domain.onion_observation import OnionObservationRecord, ObservationStatus


class ViewPerspective(str, Enum):
    """
    Standard camera perspectives for produce inspection.
    """
    PRIMARY = "PRIMARY"
    TOP = "TOP"
    SIDE = "SIDE"
    DETAIL = "DETAIL"
    UNDERSIDE = "UNDERSIDE"
    OPTIONAL_UNDERSIDE = "OPTIONAL_UNDERSIDE"


VALID_INSPECTION_MAT_CELLS_20: tuple[str, ...] = tuple(
    f"{r}{c}" for r in ["A", "B", "C", "D"] for c in range(1, 6)
)


def validate_mat_cell_id(cell_id: str | None) -> bool:
    """Check if a cell_id conforms to the standard 20-cell inspection mat (A1-D5)."""
    if not cell_id:
        return False
    return cell_id.strip().upper() in VALID_INSPECTION_MAT_CELLS_20


class CaptureRole(str, Enum):
    """
    Operational role of a photographic capture.
    PRIMARY_SAMPLE_CAPTURE: Establishes new physical sample units in a tray/lot.
    DETAIL_RECAPTURE: Re-photographs existing sample units from top/side/close-up angles.
    """
    PRIMARY_SAMPLE_CAPTURE = "PRIMARY_SAMPLE_CAPTURE"
    DETAIL_RECAPTURE = "DETAIL_RECAPTURE"


class ObservationReference(BaseModel):
    """
    Linkage binding a specific detector/pipeline observation to a physical sample unit.
    """
    model_config = ConfigDict(extra="forbid")

    observation_id: str = Field(..., description="Unique identifier of produce observation record")
    capture_id: str = Field(..., description="Source capture identifier")
    capture_role: CaptureRole = Field(..., description="Role of source capture (PRIMARY vs DETAIL)")
    view_angle: str = Field(default="UNSPECIFIED", description="Camera perspective: PRIMARY, TOP, SIDE, DETAIL, UNDERSIDE")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detector confidence score")
    class_semantic: CanonicalLabel = Field(..., description="Classified canonical semantic label")
    bbox: tuple[float, float, float, float] | None = Field(default=None, description="Bounding box in image coordinates")


class SampleCell(BaseModel):
    """
    Optional spatial coordinate on a physical inspection mat or grid tray.
    """
    model_config = ConfigDict(extra="forbid")

    cell_id: str = Field(..., description="Grid cell identifier (e.g. A1, B2, 01, 12)")
    grid_row: int | None = Field(default=None, description="0-indexed grid row")
    grid_col: int | None = Field(default=None, description="0-indexed grid column")
    description: str | None = Field(default=None, description="Human readable description of tray position")


class SampleUnit(BaseModel):
    """
    Represents exactly ONE physical produce specimen (e.g., one physical onion).

    Guarantees:
    - Multiple captures of the same onion (TOP + SIDE + DETAIL) belong to this single unit.
    - Physical sample size is counted by number of SampleUnits, NOT number of images or detections.
    """
    model_config = ConfigDict(extra="forbid")

    sample_unit_id: str = Field(..., description="Unique physical sample unit identifier")
    lot_id: str = Field(..., description="Agricultural lot identifier")
    source_reference: str = Field(default="TRAY_PRIMARY", description="Physical source tag (e.g. bag_id, tray_id, mat_id)")
    cell_id: str | None = Field(default=None, description="Physical mat grid cell ID (e.g. A1-D5)")
    primary_capture_id: str | None = Field(default=None, description="Capture ID that established this unit")
    detail_capture_ids: list[str] = Field(default_factory=list, description="Capture IDs of detail views of this unit")
    observation_ids: list[str] = Field(default_factory=list, description="IDs of all observations of this physical unit")
    capture_ids: list[str] = Field(default_factory=list, description="IDs of all captures containing views of this unit")
    observation_references: list[ObservationReference] = Field(
        default_factory=list,
        description="Chronological observation evidence referencing this physical unit"
    )
    primary_observation_id: str | None = Field(default=None, description="Initial primary observation establishing unit")
    resolved_class_semantic: CanonicalLabel = Field(
        default=CanonicalLabel.UNKNOWN_MAPPING,
        description="Current authoritative physical condition classification"
    )
    unit_status: str = Field(default="RECORDED", description="Status: RECORDED, DETAIL_AUGMENTED, CONFLICT")
    size_mm: float | None = Field(default=None, description="Estimated equatorial diameter in mm")
    size_status: str = Field(default="ONION_DIAMETER_UNVALIDATED", description="Status of size measurement")
    weight_estimate_g: float | None = Field(default=None, description="Estimated mass in grams")
    weight_status: str = Field(default="UNVALIDATED", description="Status of mass estimation")
    title: str = Field(default="Healthy", description="Canonical UI condition title")
    explanation: str = Field(default="No modeled visible defect detected.", description="Canonical UI explanation")
    review_required: bool = Field(default=False, description="Whether manual review is required")
    protocol_status: str = Field(default="FIELD_VALIDATION_PENDING", description="Mat protocol status")
    created_at_iso: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Timestamp when physical sample unit was established"
    )

    def add_observation(self, obs_ref: ObservationReference) -> None:
        """
        Associate an additional observation view to this physical unit.
        Never duplicates the physical unit denominator.
        """
        if obs_ref.observation_id not in self.observation_ids:
            self.observation_ids.append(obs_ref.observation_id)
        if obs_ref.capture_id not in self.capture_ids:
            self.capture_ids.append(obs_ref.capture_id)
        self.observation_references.append(obs_ref)

        if obs_ref.capture_role == CaptureRole.DETAIL_RECAPTURE:
            self.unit_status = "DETAIL_AUGMENTED"
            if obs_ref.capture_id not in self.detail_capture_ids:
                self.detail_capture_ids.append(obs_ref.capture_id)

        # Check for cross-view semantic conflict
        all_semantics = {ref.class_semantic for ref in self.observation_references if ref.class_semantic != CanonicalLabel.CLASS_CONFLICT}
        if len(all_semantics) > 1 or any(ref.class_semantic == CanonicalLabel.CLASS_CONFLICT for ref in self.observation_references):
            self.unit_status = "CONFLICT"
            self.resolved_class_semantic = CanonicalLabel.CLASS_CONFLICT
            self.title = "Review required"
            self.explanation = "Overlapping detections disagree on the visible condition. The system did not select one class automatically."
            self.review_required = True
        elif len(all_semantics) == 1:
            self.resolved_class_semantic = next(iter(all_semantics))

    @property
    def is_detail_augmented(self) -> bool:
        """Whether this unit contains detail recapture evidence."""
        return any(ref.capture_role == CaptureRole.DETAIL_RECAPTURE for ref in self.observation_references)

    @property
    def has_conflict(self) -> bool:
        """Whether any views of this unit disagree or contain conflicts."""
        return self.resolved_class_semantic == CanonicalLabel.CLASS_CONFLICT or self.unit_status == "CONFLICT"


class SampleUnitRegistry(BaseModel):
    """
    Lot-level collection of physical sample units.
    Guarantees physical sample size is computed strictly from unique SampleUnits.
    """
    model_config = ConfigDict(extra="forbid")

    lot_id: str = Field(..., description="Lot identifier")
    units: dict[str, SampleUnit] = Field(default_factory=dict, description="Registry mapping sample_unit_id to SampleUnit")
    unresolved_observation_ids: list[str] = Field(
        default_factory=list,
        description="Observations whose physical cross-view identity could not be established"
    )

    @property
    def unique_sample_count(self) -> int:
        """The certified physical sample size denominator."""
        return len(self.units)

    def register_primary_observation(
        self,
        obs: OnionObservationRecord,
        capture_id: str,
        cell_id: str | None = None,
        source_reference: str = "TRAY_PRIMARY",
        view_angle: str = "TOP",
    ) -> SampleUnit:
        """
        Register a new physical SampleUnit from a PRIMARY_SAMPLE_CAPTURE observation.
        """
        unit_id = f"su_{uuid.uuid4().hex[:8]}"
        obs_ref = ObservationReference(
            observation_id=obs.observation_id,
            capture_id=capture_id,
            capture_role=CaptureRole.PRIMARY_SAMPLE_CAPTURE,
            view_angle=view_angle,
            confidence=obs.confidence,
            class_semantic=obs.class_semantic,
            bbox=obs.bbox,
        )

        unit = SampleUnit(
            sample_unit_id=unit_id,
            lot_id=self.lot_id,
            source_reference=source_reference,
            cell_id=cell_id,
            primary_capture_id=capture_id,
            observation_ids=[obs.observation_id],
            capture_ids=[capture_id],
            observation_references=[obs_ref],
            primary_observation_id=obs.observation_id,
            resolved_class_semantic=obs.class_semantic,
            unit_status="CONFLICT" if obs.class_semantic == CanonicalLabel.CLASS_CONFLICT else "RECORDED",
            title=getattr(obs, "title", "Healthy"),
            explanation=getattr(obs, "explanation", "No modeled visible defect detected."),
            review_required=getattr(obs, "review_required", False),
        )
        self.units[unit_id] = unit
        return unit

    def associate_detail_observation(
        self,
        obs: OnionObservationRecord,
        capture_id: str,
        target_sample_unit_id: str | None = None,
        target_observation_id: str | None = None,
        view_angle: str = "DETAIL",
    ) -> bool:
        """
        Associate a DETAIL_RECAPTURE observation to an existing physical SampleUnit.
        Guarantees physical sample size is NOT incremented.
        If target unit cannot be found or is not provided, marks observation as
        CROSS_VIEW_IDENTITY_UNRESOLVED and refuses to silently merge.
        """
        matched_unit: SampleUnit | None = None

        if target_sample_unit_id is not None and target_sample_unit_id in self.units:
            matched_unit = self.units[target_sample_unit_id]
        elif target_observation_id is not None:
            for unit in self.units.values():
                if target_observation_id in unit.observation_ids:
                    matched_unit = unit
                    break

        if matched_unit is None:
            # Identity cannot be established -> DO NOT MERGE, DO NOT INCREMENT
            if obs.observation_id not in self.unresolved_observation_ids:
                self.unresolved_observation_ids.append(obs.observation_id)
            return False

        obs_ref = ObservationReference(
            observation_id=obs.observation_id,
            capture_id=capture_id,
            capture_role=CaptureRole.DETAIL_RECAPTURE,
            view_angle=view_angle,
            confidence=obs.confidence,
            class_semantic=obs.class_semantic,
            bbox=obs.bbox,
        )
        matched_unit.add_observation(obs_ref)
        return True

    def get_unit_for_observation(self, observation_id: str) -> SampleUnit | None:
        """Lookup physical unit owning an observation."""
        for unit in self.units.values():
            if observation_id in unit.observation_ids:
                return unit
        return None
