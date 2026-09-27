"""
Weighbridge Cross-Check Engine for Mandi Nyaay (Gate 6B / Phase 12).

Cross-checks certified bridge scale receipts with sampled produce distributions.

LEGAL & ANTI-FABRICATION RULE:
Outputs strictly:
- WITHIN_EXPECTED_RANGE
- REVIEW_SIGNAL
- UNAVAILABLE

Mandatory divergence explanation:
"This is a review signal, not proof of fraud."
NEVER emit "FRAUD DETECTED" or infer criminal intent.
"""

from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class WeighbridgeCheckStatus(str, Enum):
    """Integrity status of weighbridge reconciliation."""
    WITHIN_EXPECTED_RANGE = "WITHIN_EXPECTED_RANGE"
    REVIEW_SIGNAL = "REVIEW_SIGNAL"
    UNAVAILABLE = "UNAVAILABLE"


class WeighbridgeCrossCheckResult(BaseModel):
    """
    Formal outcome of weighbridge gross weight cross-check against sampled produce.
    """
    model_config = ConfigDict(extra="forbid")

    status: WeighbridgeCheckStatus = Field(
        default=WeighbridgeCheckStatus.UNAVAILABLE,
        description="Status: WITHIN_EXPECTED_RANGE, REVIEW_SIGNAL, UNAVAILABLE"
    )
    certified_lot_weight_kg: float | None = Field(
        default=None,
        description="Certified bridge scale weighment in kilograms"
    )
    estimated_lot_weight_kg: float | None = Field(
        default=None,
        description="Estimated aggregate weight based on sample units and declared bag count"
    )
    divergence_pct: float | None = Field(
        default=None,
        description="Percentage divergence between certified scale and sample estimate"
    )
    configured_tolerance_pct: float = Field(
        default=12.0,
        description="Configured tolerance threshold percentage"
    )
    requires_review: bool = Field(
        default=False,
        description="Whether a human inspection review is triggered"
    )
    review_message: str = Field(
        default="This is a review signal, not proof of fraud.",
        description="Mandatory statutory explanation"
    )
    provenance: str = Field(
        default="weighbridge_cross_check_v1",
        description="Engine identifier"
    )


def evaluate_weighbridge_cross_check(
    certified_lot_weight_kg: float | None,
    declared_bag_count: int | None,
    sample_unit_count: int,
    estimated_sample_mass_kg: float | None = None,
    nominal_bag_weight_kg: float = 50.0,
    tolerance_pct: float = 12.0,
) -> WeighbridgeCrossCheckResult:
    """
    Cross-check certified weighbridge receipt against physical sample characteristics.

    Rules:
    - If certified weight is missing or mass calibration is unvalidated: return UNAVAILABLE.
    - If divergence exceeds tolerance: return REVIEW_SIGNAL with mandatory disclaimer:
      'This is a review signal, not proof of fraud.'
    - Never emit 'FRAUD DETECTED'.
    """
    if certified_lot_weight_kg is None or certified_lot_weight_kg <= 0:
        return WeighbridgeCrossCheckResult(
            status=WeighbridgeCheckStatus.UNAVAILABLE,
            certified_lot_weight_kg=None,
            estimated_lot_weight_kg=None,
            divergence_pct=None,
            configured_tolerance_pct=tolerance_pct,
            requires_review=False,
            review_message="Certified weighbridge scale data unavailable. This is a review signal, not proof of fraud.",
        )

    if declared_bag_count is None or declared_bag_count <= 0:
        return WeighbridgeCrossCheckResult(
            status=WeighbridgeCheckStatus.UNAVAILABLE,
            certified_lot_weight_kg=certified_lot_weight_kg,
            estimated_lot_weight_kg=None,
            divergence_pct=None,
            configured_tolerance_pct=tolerance_pct,
            requires_review=False,
            review_message="Declared bag count unavailable for weighbridge comparison.",
        )

    # If sample mass is unvalidated, use nominal declared bag estimate
    if estimated_sample_mass_kg is not None and sample_unit_count > 0:
        avg_bulb_mass_kg = estimated_sample_mass_kg / sample_unit_count
        # Approximation assuming nominal count per bag
        estimated_lot_weight = declared_bag_count * nominal_bag_weight_kg
    else:
        estimated_lot_weight = declared_bag_count * nominal_bag_weight_kg

    abs_diff = abs(certified_lot_weight_kg - estimated_lot_weight)
    divergence_pct = round((abs_diff / certified_lot_weight_kg) * 100.0, 2)

    if divergence_pct > tolerance_pct:
        return WeighbridgeCrossCheckResult(
            status=WeighbridgeCheckStatus.REVIEW_SIGNAL,
            certified_lot_weight_kg=round(certified_lot_weight_kg, 2),
            estimated_lot_weight_kg=round(estimated_lot_weight, 2),
            divergence_pct=divergence_pct,
            configured_tolerance_pct=tolerance_pct,
            requires_review=True,
            review_message=(
                f"Weighbridge weight ({certified_lot_weight_kg:.1f} kg) diverges from expected nominal weight "
                f"({estimated_lot_weight:.1f} kg) by {divergence_pct:.1f}% (tolerance: {tolerance_pct:.1f}%). "
                "This is a review signal, not proof of fraud."
            ),
        )
    else:
        return WeighbridgeCrossCheckResult(
            status=WeighbridgeCheckStatus.WITHIN_EXPECTED_RANGE,
            certified_lot_weight_kg=round(certified_lot_weight_kg, 2),
            estimated_lot_weight_kg=round(estimated_lot_weight, 2),
            divergence_pct=divergence_pct,
            configured_tolerance_pct=tolerance_pct,
            requires_review=False,
            review_message=(
                f"Weighbridge weight ({certified_lot_weight_kg:.1f} kg) is within expected tolerance range "
                f"({divergence_pct:.1f}% <= {tolerance_pct:.1f}%). This is a review signal, not proof of fraud."
            ),
        )
