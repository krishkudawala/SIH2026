"""
Review Signal Engine for Mandi Nyaay (Gate 5F).

Generates explicit, standardized operational review signals.

Guarantees:
- Strictly adheres to the legal policy:
  "This is a review signal, not proof of fraud."
- NEVER emits accusatory terms such as "FRAUD DETECTED", "theft", or "tampering".
- Flags uncertainty, physical limitations, calibration gaps, and sampling deficiencies.
"""

from __future__ import annotations

import uuid
from typing import Any, Sequence
from pydantic import BaseModel, ConfigDict, Field

from app.domain.inspection_session import (
    InspectionReviewSignal,
    ReviewSignalCode,
    ReviewSignalSeverity,
    SamplingStatus,
)


LEGAL_REVIEW_SIGNAL_SUFFIX = " This is a review signal, not proof of fraud."


def generate_review_signals(
    conflict_count: int = 0,
    quality_grade: str = "PASS",
    sampling_status: SamplingStatus = SamplingStatus.SUFFICIENT,
    observed_sample_size: int = 0,
    target_sample_size: int = 20,
    calibration_status: str = "CALIBRATION_NOT_AVAILABLE",
    measurement_status: str = "CALIBRATION_NOT_AVAILABLE",
    mass_status: str = "UNVALIDATED",
    count_mass_divergence_pct: float | None = None,
    divergence_threshold_pct: float = 15.0,
    manual_override: dict[str, Any] | None = None,
    calibration_required: bool = False,
) -> list[InspectionReviewSignal]:
    """
    Evaluate all operational inspection parameters and return standardized review signals.
    """
    signals: list[InspectionReviewSignal] = []

    # 1. CLASS_CONFLICT
    if conflict_count > 0:
        signals.append(
            InspectionReviewSignal(
                signal_id=f"sig_{uuid.uuid4().hex[:8]}",
                code=ReviewSignalCode.CLASS_CONFLICT,
                severity=ReviewSignalSeverity.CRITICAL,
                message=(
                    f"{conflict_count} cross-class detection conflict(s) detected during physical bulb reconciliation."
                    f"{LEGAL_REVIEW_SIGNAL_SUFFIX}"
                ),
                source="observation_reconciliation",
                requires_action=True,
            )
        )

    # 2. LOW_IMAGE_QUALITY
    if quality_grade == "FAIL":
        signals.append(
            InspectionReviewSignal(
                signal_id=f"sig_{uuid.uuid4().hex[:8]}",
                code=ReviewSignalCode.LOW_IMAGE_QUALITY,
                severity=ReviewSignalSeverity.CRITICAL,
                message=(
                    "Image quality screening failed baseline optical sharpness or exposure thresholds."
                    f"{LEGAL_REVIEW_SIGNAL_SUFFIX}"
                ),
                source="quality_screening",
                requires_action=True,
            )
        )
    elif quality_grade == "WARN":
        signals.append(
            InspectionReviewSignal(
                signal_id=f"sig_{uuid.uuid4().hex[:8]}",
                code=ReviewSignalCode.LOW_IMAGE_QUALITY,
                severity=ReviewSignalSeverity.WARNING,
                message=(
                    "Image quality screening emitted warning (borderline sharpness or illumination)."
                    f"{LEGAL_REVIEW_SIGNAL_SUFFIX}"
                ),
                source="quality_screening",
                requires_action=False,
            )
        )

    # 3. INSUFFICIENT_SAMPLE
    if sampling_status in (SamplingStatus.CONTINUE, SamplingStatus.INVALID):
        severity = ReviewSignalSeverity.CRITICAL if sampling_status == SamplingStatus.INVALID else ReviewSignalSeverity.WARNING
        signals.append(
            InspectionReviewSignal(
                signal_id=f"sig_{uuid.uuid4().hex[:8]}",
                code=ReviewSignalCode.INSUFFICIENT_SAMPLE,
                severity=severity,
                message=(
                    f"Observed sample size ({observed_sample_size}) does not satisfy target sample size ({target_sample_size})."
                    f"{LEGAL_REVIEW_SIGNAL_SUFFIX}"
                ),
                source="sampling_engine",
                requires_action=True,
            )
        )

    # 4. CALIBRATION_UNAVAILABLE / CALIBRATION_INVALID
    if calibration_status == "CALIBRATION_INVALID":
        severity = ReviewSignalSeverity.CRITICAL if calibration_required else ReviewSignalSeverity.WARNING
        signals.append(
            InspectionReviewSignal(
                signal_id=f"sig_{uuid.uuid4().hex[:8]}",
                code=ReviewSignalCode.CALIBRATION_INVALID,
                severity=severity,
                message=(
                    "Reference marker geometry or reprojection error is invalid. Metric measurement blocked."
                    f"{LEGAL_REVIEW_SIGNAL_SUFFIX}"
                ),
                source="marker_calibration",
                requires_action=calibration_required,
            )
        )
    elif calibration_status == "CALIBRATION_NOT_AVAILABLE":
        severity = ReviewSignalSeverity.CRITICAL if calibration_required else ReviewSignalSeverity.INFO
        signals.append(
            InspectionReviewSignal(
                signal_id=f"sig_{uuid.uuid4().hex[:8]}",
                code=ReviewSignalCode.CALIBRATION_UNAVAILABLE,
                severity=severity,
                message=(
                    "Planar calibration marker state is 'CALIBRATION_NOT_AVAILABLE'. Metric millimeter scaling is unavailable."
                    f"{LEGAL_REVIEW_SIGNAL_SUFFIX}"
                ),
                source="marker_calibration",
                requires_action=calibration_required,
            )
        )

    # 5. SIZE_UNVALIDATED / ONION_DIAMETER_UNVALIDATED
    signals.append(
        InspectionReviewSignal(
            signal_id=f"sig_{uuid.uuid4().hex[:8]}",
            code=ReviewSignalCode.ONION_DIAMETER_UNVALIDATED,
            severity=ReviewSignalSeverity.INFO,
            message=(
                "3D bulb equatorial diameter estimation from 2D bounding boxes is unvalidated in field conditions."
                f"{LEGAL_REVIEW_SIGNAL_SUFFIX}"
            ),
            source="measurement_engine",
            requires_action=False,
        )
    )

    # 6. MASS_UNVALIDATED
    if mass_status == "UNVALIDATED":
        signals.append(
            InspectionReviewSignal(
                signal_id=f"sig_{uuid.uuid4().hex[:8]}",
                code=ReviewSignalCode.MASS_UNVALIDATED,
                severity=ReviewSignalSeverity.INFO,
                message=(
                    "Volumetric mass estimation is unvalidated. Grading must remain count-based and not mass-based."
                    f"{LEGAL_REVIEW_SIGNAL_SUFFIX}"
                ),
                source="aggregation_engine",
                requires_action=False,
            )
        )

    # 7. COUNT_MASS_DIVERGENCE
    if count_mass_divergence_pct is not None and count_mass_divergence_pct > divergence_threshold_pct:
        signals.append(
            InspectionReviewSignal(
                signal_id=f"sig_{uuid.uuid4().hex[:8]}",
                code=ReviewSignalCode.COUNT_MASS_DIVERGENCE,
                severity=ReviewSignalSeverity.WARNING,
                message=(
                    f"Count-derived sample distribution diverges from weighbridge weight by {count_mass_divergence_pct:.1f}%."
                    f"{LEGAL_REVIEW_SIGNAL_SUFFIX}"
                ),
                source="aggregation_engine",
                requires_action=True,
            )
        )

    # 8. WEIGHBRIDGE_REVIEW
    if count_mass_divergence_pct is not None and count_mass_divergence_pct > divergence_threshold_pct:
        signals.append(
            InspectionReviewSignal(
                signal_id=f"sig_{uuid.uuid4().hex[:8]}",
                code=ReviewSignalCode.WEIGHBRIDGE_REVIEW,
                severity=ReviewSignalSeverity.WARNING,
                message=(
                    f"Weighbridge cross-check divergence ({count_mass_divergence_pct:.1f}%) exceeds allowable threshold."
                    f"{LEGAL_REVIEW_SIGNAL_SUFFIX}"
                ),
                source="weighbridge_cross_check",
                requires_action=True,
            )
        )

    # 9. MANUAL_OVERRIDE
    if manual_override is not None:
        reason = manual_override.get("reason", "Operator manual adjudication")
        signals.append(
            InspectionReviewSignal(
                signal_id=f"sig_{uuid.uuid4().hex[:8]}",
                code=ReviewSignalCode.MANUAL_OVERRIDE,
                severity=ReviewSignalSeverity.WARNING,
                message=(
                    f"Manual inspector override logged: {reason}."
                    f"{LEGAL_REVIEW_SIGNAL_SUFFIX}"
                ),
                source="operator_override",
                requires_action=False,
            )
        )

    return signals


class ReviewCenterQueue(BaseModel):
    """
    Unified operator review queue for Mandi Nyaay inspection sessions (Phase 16).
    Aggregates all active review signals, prioritizes by severity, and surfaces required actions.
    """
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(..., description="Inspection session identifier")
    signals: list[InspectionReviewSignal] = Field(default_factory=list, description="Ordered review signals")
    blocking_signals_count: int = Field(default=0, ge=0, description="Count of signals that block automated grading")
    has_critical: bool = Field(default=False, description="Whether any critical signals exist")
    total_signals: int = Field(default=0, ge=0, description="Total active review signals")


def build_review_center_queue(
    session_id: str,
    signals: Sequence[InspectionReviewSignal],
) -> ReviewCenterQueue:
    """
    Build a prioritized review queue: CRITICAL first, then WARNING, then INFO.
    """
    severity_order = {
        ReviewSignalSeverity.CRITICAL: 0,
        ReviewSignalSeverity.WARNING: 1,
        ReviewSignalSeverity.INFO: 2,
    }
    sorted_signals = sorted(signals, key=lambda s: (severity_order.get(s.severity, 99), s.code.value))
    blocking_count = sum(1 for s in sorted_signals if s.requires_action)
    has_crit = any(s.severity == ReviewSignalSeverity.CRITICAL for s in sorted_signals)

    return ReviewCenterQueue(
        session_id=session_id,
        signals=sorted_signals,
        blocking_signals_count=blocking_count,
        has_critical=has_crit,
        total_signals=len(sorted_signals),
    )

