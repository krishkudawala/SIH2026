"""
Produce Observation Aggregation Engine for Mandi Nyaay (Gate 5D).

Aggregates individual physical bulb observations into statistical distributions.

Guarantees:
- Maintains strict, immutable boundary between COUNT DISTRIBUTION and MASS DISTRIBUTION.
- Never silently substitutes count proportions for mass proportions.
- Sets mass_status = 'UNVALIDATED' and mass_distribution = None until calibrated mass is verified.
- Produces a clear COUNT-BASED OBSERVATION SUMMARY.
"""

from __future__ import annotations

import uuid
from typing import Any, Sequence

from app.domain.inspection_session import InspectionAggregation
from app.domain.onion_observation import OnionObservationRecord
from app.version import get_processing_version


def aggregate_observations(
    observations: Sequence[OnionObservationRecord],
    aggregation_id: str | None = None,
    sample_units: Sequence[Any] | None = None,
    unresolved_identity_count: int | None = None,
) -> InspectionAggregation:
    """
    Compute count distribution across physical produce observations or sample units.
    Explicitly refuses to simulate mass distribution without validated physical calibration.
    """
    if sample_units is not None and len(sample_units) > 0:
        total_count = len(sample_units)
        condition_counts: dict[str, int] = {}
        for unit in sample_units:
            semantic = unit.resolved_class_semantic
            label = semantic.value if hasattr(semantic, "value") else str(semantic)
            condition_counts[label] = condition_counts.get(label, 0) + 1
    else:
        total_count = len(observations)
        condition_counts: dict[str, int] = {}
        for obs in observations:
            semantic = obs.class_semantic
            label = semantic.value if hasattr(semantic, "value") else str(semantic)
            condition_counts[label] = condition_counts.get(label, 0) + 1

    count_distribution: dict[str, dict[str, Any]] = {}
    for label, count in condition_counts.items():
        percentage = round((count / total_count) * 100.0, 2) if total_count > 0 else 0.0
        count_distribution[label] = {
            "count": count,
            "percentage": percentage,
        }

    agg_id = aggregation_id or f"agg_{uuid.uuid4().hex[:8]}"

    healthy_count = condition_counts.get("HEALTHY", 0)
    damaged_count = condition_counts.get("DAMAGED", 0)
    sprouted_count = condition_counts.get("SPROUTED", 0)
    rotten_count = condition_counts.get("ROTTEN", 0)
    class_conflict_count = condition_counts.get("CLASS_CONFLICT", 0)

    # In the absence of multi-camera stereo tracking / verified visual re-identification,
    # cross-capture produce identity without explicit linkage remains unresolved.
    effective_unresolved_count = (
        unresolved_identity_count if unresolved_identity_count is not None else total_count
    )

    total_obs = len(observations) if len(observations) > 0 else total_count

    return InspectionAggregation(
        aggregation_id=agg_id,
        status="VALID" if total_count > 0 else "EMPTY",
        aggregation_mode="COUNT_BASED",
        total_count=total_count,
        total_observations=total_obs,
        healthy_count=healthy_count,
        damaged_count=damaged_count,
        sprouted_count=sprouted_count,
        rotten_count=rotten_count,
        class_conflict_count=class_conflict_count,
        unresolved_identity_count=effective_unresolved_count,
        count_distribution=count_distribution,
        mass_status="UNVALIDATED",
        mass_distribution=None,
        disclaimer=(
            "Aggregation is based strictly on physical bulb count. "
            "Calibrated individual bulb mass is UNVALIDATED and cannot be used for procurement settlement."
        ),
        version=get_processing_version(),
    )


