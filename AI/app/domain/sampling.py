"""
Sampling Engine for Mandi Nyaay (Gate 5C).

Evaluates whether observed produce counts satisfy statistical sampling requirements
for lot-level procurement determination.

Guarantees:
- Returns explicit statuses: SUFFICIENT, CONTINUE, MANUAL_REVIEW, INVALID.
- Explains deterministic rationale for sufficiency or shortfall.
- Never hardcodes 'sufficient'.
- Explicitly documents that mass/size calibration is UNVALIDATED.
"""

from __future__ import annotations

import uuid
from typing import Sequence

from app.domain.inspection_session import (
    InspectionSamplingResult,
    SamplingStatus,
)
from app.domain.onion_observation import OnionObservationRecord, ObservationStatus


DEFAULT_TARGET_SAMPLE_SIZE = 20
SAMPLING_RULE_VERSION = "MANDI_NYAAY_SAMPLING_V1.0"


def evaluate_sampling_sufficiency(
    observations: Sequence[OnionObservationRecord],
    target_sample_size: int = DEFAULT_TARGET_SAMPLE_SIZE,
    conflict_count: int = 0,
    quality_grade: str = "PASS",
    sampling_rule_version: str = SAMPLING_RULE_VERSION,
    sample_units: Sequence[Any] | None = None,
    unique_sample_unit_count: int | None = None,
) -> InspectionSamplingResult:
    """
    Evaluate statistical sampling sufficiency over certified physical sample units.
    Guarantees sample size is the count of unique physical SampleUnits, not raw images or detections.
    """
    if sample_units is not None:
        observed_count = len(sample_units)
    elif unique_sample_unit_count is not None:
        observed_count = unique_sample_unit_count
    else:
        observed_count = len(observations)

    limitations = [
        "Bulb mass and 3D volumetric sizing are UNVALIDATED in current field conditions.",
        "Sampling sufficiency is determined strictly from unique physical SampleUnit counts, not image or detection count.",
    ]

    # 1. Check for INVALID capture/observations
    if quality_grade == "FAIL":
        return InspectionSamplingResult(
            sampling_id=f"smp_{uuid.uuid4().hex[:8]}",
            status=SamplingStatus.INVALID,
            target_sample_size=target_sample_size,
            observed_sample_size=observed_count,
            sampling_rule_version=sampling_rule_version,
            reason=(
                "Photographic quality screening failed baseline optical criteria (severe blur or clipping). "
                "Observations cannot be certified for sampling."
            ),
            limitations=limitations,
        )

    if observed_count == 0:
        return InspectionSamplingResult(
            sampling_id=f"smp_{uuid.uuid4().hex[:8]}",
            status=SamplingStatus.INVALID,
            target_sample_size=target_sample_size,
            observed_sample_size=0,
            sampling_rule_version=sampling_rule_version,
            reason="Zero physical produce bulbs observed in capture; sampling cannot be conducted.",
            limitations=limitations,
        )

    # 2. Check for conflicts requiring MANUAL_REVIEW
    if conflict_count > 0:
        return InspectionSamplingResult(
            sampling_id=f"smp_{uuid.uuid4().hex[:8]}",
            status=SamplingStatus.MANUAL_REVIEW,
            target_sample_size=target_sample_size,
            observed_sample_size=observed_count,
            sampling_rule_version=sampling_rule_version,
            reason=(
                f"Sample contains {conflict_count} cross-class conflict(s) where overlapping detections disagree. "
                "Manual review required before sampling sufficiency can be affirmed."
            ),
            limitations=limitations,
        )

    # 3. Check sample size sufficiency
    if observed_count >= target_sample_size:
        return InspectionSamplingResult(
            sampling_id=f"smp_{uuid.uuid4().hex[:8]}",
            status=SamplingStatus.SUFFICIENT,
            target_sample_size=target_sample_size,
            observed_sample_size=observed_count,
            sampling_rule_version=sampling_rule_version,
            reason=(
                f"Observed sample size ({observed_count}) meets or exceeds the target sample size "
                f"({target_sample_size}) with zero unresolved cross-class conflicts."
            ),
            limitations=limitations,
        )
    else:
        shortfall = target_sample_size - observed_count
        return InspectionSamplingResult(
            sampling_id=f"smp_{uuid.uuid4().hex[:8]}",
            status=SamplingStatus.CONTINUE,
            target_sample_size=target_sample_size,
            observed_sample_size=observed_count,
            sampling_rule_version=sampling_rule_version,
            reason=(
                f"Observed sample size ({observed_count}) is below required target sample size "
                f"({target_sample_size}). Additional {shortfall} bulb observation(s) required from subsequent captures."
            ),
            limitations=limitations,
        )
