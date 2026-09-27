"""
Semantic Label Safety and Explicit Class Mapping for Mandi Nyaay.

Guarantees:
- Strict semantic labels (HEALTHY, DAMAGED, ROTTEN, SPROUTED)
- Explicit bidirectional mapping between integer class IDs and semantic labels
- Zero silent assumptions (e.g. checkpoint ID 2 vs canonical ID 2)
- Rejection of ambiguous, duplicate, or unverified class mappings
"""

from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class CanonicalLabel(str, Enum):
    """
    Canonical semantic produce labels for Mandi Nyaay inspection.
    Primary domain contracts must use these semantic labels, not integer IDs.
    """
    HEALTHY = "HEALTHY"
    DAMAGED = "DAMAGED"
    ROTTEN = "ROTTEN"
    SPROUTED = "SPROUTED"
    CLASS_CONFLICT = "CLASS_CONFLICT"
    UNKNOWN_MAPPING = "UNKNOWN_MAPPING"


class MappingStatus(str, Enum):
    """Status reflecting confidence and provenance of external class mapping."""
    VERIFIED = "VERIFIED"
    NEEDS_CONTROLLED_VALIDATION = "NEEDS_CONTROLLED_VALIDATION"
    AMBIGUOUS = "AMBIGUOUS"
    UNVERIFIED = "UNVERIFIED"
    INVALID = "INVALID"


# Canonical Ground Truth Dataset Mapping
# Dataset specifies:
# 0 = healthy, 1 = damaged, 2 = rotten, 3 = sprouted
CANONICAL_DATASET_ID_TO_LABEL: dict[int, CanonicalLabel] = {
    0: CanonicalLabel.HEALTHY,
    1: CanonicalLabel.DAMAGED,
    2: CanonicalLabel.ROTTEN,
    3: CanonicalLabel.SPROUTED,
}

CANONICAL_NAME_TO_LABEL: dict[str, CanonicalLabel] = {
    "healthy": CanonicalLabel.HEALTHY,
    "damaged": CanonicalLabel.DAMAGED,
    "rotten": CanonicalLabel.ROTTEN,
    "sprouted": CanonicalLabel.SPROUTED,
}


class ModelClassMapping(BaseModel):
    """
    Explicit specification of how a model's raw class IDs map to CanonicalLabels.
    """
    model_config = ConfigDict(extra="forbid")

    mapping_id: str = Field(..., description="Unique mapping profile identifier")
    model_name: str = Field(..., description="Model checkpoint identifier")
    id_to_canonical: dict[int, CanonicalLabel] = Field(
        ...,
        description="Explicit mapping from model class index to CanonicalLabel"
    )
    raw_class_names: dict[int, str] = Field(
        default_factory=dict,
        description="Original class string names stored in model metadata"
    )
    status: MappingStatus = Field(
        default=MappingStatus.UNVERIFIED,
        description="Verification state of this mapping profile"
    )
    notes: str = Field(
        default="",
        description="Audit notes explaining origin or ambiguities of this mapping"
    )


# Baseline known configurations for onion-grading-v7.pt
# Variant A: Assumes model raw IDs follow dataset canonical mapping (0: healthy, 1: damaged, 2: rotten, 3: sprouted)
V7_MAPPING_VARIANT_A = ModelClassMapping(
    mapping_id="v7_canonical_assumption",
    model_name="onion-grading-v7.pt",
    id_to_canonical={
        0: CanonicalLabel.HEALTHY,
        1: CanonicalLabel.DAMAGED,
        2: CanonicalLabel.ROTTEN,
        3: CanonicalLabel.SPROUTED,
    },
    raw_class_names={
        0: "healthy",
        1: "damaged",
        2: "sprouted",
        3: "rotten",
    },
    status=MappingStatus.NEEDS_CONTROLLED_VALIDATION,
    notes="Assumes model predictions match dataset IDs regardless of raw checkpoint strings",
)

# Variant B: Strictly maps raw string names stored inside the checkpoint (0: healthy, 1: damaged, 2: sprouted, 3: rotten)
V7_MAPPING_VARIANT_B = ModelClassMapping(
    mapping_id="v7_checkpoint_raw_names",
    model_name="onion-grading-v7.pt",
    id_to_canonical={
        0: CanonicalLabel.HEALTHY,
        1: CanonicalLabel.DAMAGED,
        2: CanonicalLabel.SPROUTED,
        3: CanonicalLabel.ROTTEN,
    },
    raw_class_names={
        0: "healthy",
        1: "damaged",
        2: "sprouted",
        3: "rotten",
    },
    status=MappingStatus.NEEDS_CONTROLLED_VALIDATION,
    notes="Directly honors checkpoint strings where ID 2 is sprouted and ID 3 is rotten",
)

# Formally Verified Adapter Mapping for onion-grading-v7.pt (Mandi Nyaay Gate 4A)
V7_MAPPING_VERIFIED = ModelClassMapping(
    mapping_id="v7_canonical_verified_adapter",
    model_name="onion-grading-v7.pt",
    id_to_canonical={
        0: CanonicalLabel.HEALTHY,
        1: CanonicalLabel.DAMAGED,
        2: CanonicalLabel.SPROUTED,
        3: CanonicalLabel.ROTTEN,
    },
    raw_class_names={
        0: "healthy",
        1: "damaged",
        2: "sprouted",
        3: "rotten",
    },
    status=MappingStatus.VERIFIED,
    notes="Formally verified in Gate 4A via source-code forensics (evaluate_model.py, finetune_from_photos.py) and visual semantic adjudication",
)

# Canonical external v7 adapter mapping configuration
V7_EXTERNAL_ADAPTER_MAPPING = V7_MAPPING_VERIFIED


def validate_mapping(mapping: ModelClassMapping) -> tuple[bool, list[str]]:
    """
    Validate that an external class mapping is non-ambiguous, bijective, and valid.
    """
    errors: list[str] = []

    # Check for empty mapping
    if not mapping.id_to_canonical:
        errors.append("Mapping dictionary is empty")
        return False, errors

    # Check for duplicate target assignments
    seen_labels: dict[CanonicalLabel, int] = {}
    for cid, label in mapping.id_to_canonical.items():
        if label == CanonicalLabel.UNKNOWN_MAPPING:
            continue
        if label in seen_labels:
            errors.append(f"Ambiguous mapping: multiple class IDs ({seen_labels[label]} and {cid}) map to {label.value}")
        else:
            seen_labels[label] = cid

    # Verify that all raw class names map to consistent labels if provided
    for cid, raw_name in mapping.raw_class_names.items():
        if cid in mapping.id_to_canonical:
            assigned_label = mapping.id_to_canonical[cid]
            expected_from_name = CANONICAL_NAME_TO_LABEL.get(raw_name.lower().strip())
            if expected_from_name and assigned_label != CanonicalLabel.UNKNOWN_MAPPING and assigned_label != expected_from_name:
                errors.append(
                    f"Class ID {cid} semantic discrepancy: raw name '{raw_name}' indicates {expected_from_name.value} "
                    f"but mapped to {assigned_label.value}"
                )

    is_valid = len(errors) == 0
    return is_valid, errors


def convert_model_class_id(
    class_id: int,
    mapping: ModelClassMapping | None,
    raw_class_name: str | None = None,
) -> tuple[CanonicalLabel, MappingStatus]:
    """
    Explicitly convert a raw model class ID to a CanonicalLabel.

    Guarantees:
    - If mapping is None or unverified, returns UNKNOWN_MAPPING.
    - Never silently reinterprets IDs.
    - If class_id is missing from mapping, returns UNKNOWN_MAPPING with AMBIGUOUS status.
    """
    if mapping is None:
        return CanonicalLabel.UNKNOWN_MAPPING, MappingStatus.UNVERIFIED

    if mapping.status not in (MappingStatus.VERIFIED, MappingStatus.NEEDS_CONTROLLED_VALIDATION):
        return CanonicalLabel.UNKNOWN_MAPPING, mapping.status

    if class_id not in mapping.id_to_canonical:
        return CanonicalLabel.UNKNOWN_MAPPING, MappingStatus.AMBIGUOUS

    canonical = mapping.id_to_canonical[class_id]
    return canonical, mapping.status
