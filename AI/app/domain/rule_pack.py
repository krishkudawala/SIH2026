"""
Versioned Procurement Rule Pack Engine for Mandi Nyaay (Gate 6B Part F).

Decouples agricultural decision rules from application code by defining
versioned, auditable RulePacks backed by legal and statutory standards.

Guarantees:
- Every procurement decision records rule_pack_id, rule_pack_version, and provenance.
- Zero global hidden thresholds.
- Full statutory attribution (authority, source document, reference URI, effective dates).
- If no applicable RulePack is provided, decisions route to MANUAL_REVIEW.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.inspection_session import ProcurementGrade


class RuleCriterion(BaseModel):
    """
    An explicit, auditable threshold criterion defined by a standards authority.
    """
    model_config = ConfigDict(extra="forbid")

    criterion_id: str = Field(..., description="Unique criterion identifier (e.g. crit_rot_max)")
    name: str = Field(..., description="Short name (e.g. Maximum Rotten Allowance)")
    description: str = Field(..., description="Statutory description of parameter")
    parameter_name: str = Field(..., description="Machine variable name (e.g. rotten_percentage, total_defect_percentage)")
    threshold_value: float = Field(..., description="Numerical threshold limit")
    comparison_operator: str = Field(..., description="Operator: <=, >=, <, >")
    severity_if_exceeded: str = Field(..., description="Outcome if violated: REJECT, URS, MANUAL_REVIEW")


class SamplingRule(BaseModel):
    """
    Statistical sampling criteria required by the standards authority.
    """
    model_config = ConfigDict(extra="forbid")

    rule_id: str = Field(..., description="Sampling rule identifier")
    min_sample_units: int = Field(default=20, ge=1, description="Minimum certified physical SampleUnits required")
    sampling_method: str = Field(
        default="RANDOM_STRATIFIED_BAG_EXTRACTION",
        description="Physical bag/tray sampling protocol specified by authority"
    )
    allow_detail_recaptures: bool = Field(
        default=True,
        description="Whether detail close-up recaptures are permitted to augment units"
    )
    unresolved_identity_policy: str = Field(
        default="BLOCK_AND_FLAG",
        description="Policy when cross-view correspondence is unresolved"
    )


class DecisionRule(BaseModel):
    """
    Target grade qualification rule binding criteria to a final procurement outcome.
    """
    model_config = ConfigDict(extra="forbid")

    rule_id: str = Field(..., description="Decision rule identifier")
    target_grade: ProcurementGrade = Field(..., description="Target outcome: GRADE_A, URS, REJECT")
    description: str = Field(..., description="Human readable rule intent")
    required_criteria_ids: list[str] = Field(
        default_factory=list,
        description="Criterion IDs that must all be satisfied for this grade"
    )


class RulePack(BaseModel):
    """
    Complete, authoritative versioned rule pack governing produce inspection.
    """
    model_config = ConfigDict(extra="forbid")

    rule_pack_id: str = Field(..., description="Canonical rule pack identifier")
    authority: str = Field(..., description="Standards authority (e.g. DMI, NAFED, NCCF, APMC)")
    source_document: str = Field(..., description="Official regulation or Gazette notification")
    source_reference: str = Field(default="", description="Official URL or circular reference")
    source_uri_or_reference: str = Field(default="", description="Official URL or circular reference (alias for source_reference)")
    effective_from: str = Field(..., description="ISO date when standard took legal effect")
    effective_to: str | None = Field(default=None, description="ISO date of sunset, or None if currently active")
    version: str = Field(..., description="Semantic version string (e.g. 1.0.0)")
    criteria: list[RuleCriterion] = Field(default_factory=list, description="All individual threshold criteria")
    sampling_rule: SamplingRule = Field(..., description="Sampling sufficiency specification")
    sampling_method: str | None = Field(default=None, description="Sampling protocol name")
    decision_rules: list[DecisionRule] = Field(default_factory=list, description="Grade assignment rules")
    decision_logic: str = Field(..., description="Human readable description of grading algorithm")

    @model_validator(mode="before")
    @classmethod
    def _sync_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Sync source_reference and source_uri_or_reference
            if not data.get("source_reference") and data.get("source_uri_or_reference"):
                data["source_reference"] = data["source_uri_or_reference"]
            elif not data.get("source_uri_or_reference") and data.get("source_reference"):
                data["source_uri_or_reference"] = data["source_reference"]
            # Sync sampling_method
            if not data.get("sampling_method") and data.get("sampling_rule"):
                sr = data["sampling_rule"]
                if isinstance(sr, dict) and sr.get("sampling_method"):
                    data["sampling_method"] = sr["sampling_method"]
                elif hasattr(sr, "sampling_method"):
                    data["sampling_method"] = sr.sampling_method
        return data

    def get_criterion(self, criterion_id: str) -> RuleCriterion | None:
        """Lookup criterion by ID."""
        for c in self.criteria:
            if c.criterion_id == criterion_id:
                return c
        return None

    def get_criterion_by_param(self, param_name: str) -> RuleCriterion | None:
        """Lookup first criterion matching parameter name."""
        for c in self.criteria:
            if c.parameter_name == param_name:
                return c
        return None


# Canonical Statutory Rule Packs

AGMARK_ONION_STANDARD_V1 = RulePack(
    rule_pack_id="AGMARK_ONION_2024_V1",
    authority="Directorate of Marketing & Inspection (DMI), Ministry of Agriculture & Farmers Welfare, Govt. of India",
    source_document="Agricultural Produce (Grading and Marking) Act, 1937 — Onion Grading and Marking Rules",
    source_reference="https://agmarknet.gov.in/Standards/onion.pdf",
    source_uri_or_reference="https://agmarknet.gov.in/Standards/onion.pdf",
    effective_from="2024-01-01",
    effective_to=None,
    version="1.0.0",
    criteria=[
        RuleCriterion(
            criterion_id="crit_rot_reject",
            name="Maximum Rotten Limit (Reject)",
            description="Rotten, decayed, or soft bulbs exceeding this threshold mandate lot rejection.",
            parameter_name="rotten_percentage",
            threshold_value=2.0,
            comparison_operator="<=",
            severity_if_exceeded="REJECT",
        ),
        RuleCriterion(
            criterion_id="crit_rot_grade_a",
            name="Maximum Rotten Limit (Grade A)",
            description="Grade A permits at most 1.0% minor superficial decay.",
            parameter_name="rotten_percentage",
            threshold_value=1.0,
            comparison_operator="<=",
            severity_if_exceeded="URS",
        ),
        RuleCriterion(
            criterion_id="crit_total_defects_grade_a",
            name="Maximum Total Defects (Grade A)",
            description="Cumulative sum of damaged, sprouted, and rotten bulbs must not exceed 5.0%.",
            parameter_name="total_defect_percentage",
            threshold_value=5.0,
            comparison_operator="<=",
            severity_if_exceeded="URS",
        ),
        RuleCriterion(
            criterion_id="crit_total_defects_urs",
            name="Maximum Total Defects (Under-grade Re-sort)",
            description="Cumulative defects up to 20.0% permit commercial utility re-sort.",
            parameter_name="total_defect_percentage",
            threshold_value=20.0,
            comparison_operator="<=",
            severity_if_exceeded="REJECT",
        ),
    ],
    sampling_rule=SamplingRule(
        rule_id="samp_agmark_std",
        min_sample_units=20,
        sampling_method="RANDOM_STRATIFIED_BAG_EXTRACTION",
        allow_detail_recaptures=True,
        unresolved_identity_policy="BLOCK_AND_FLAG",
    ),
    decision_rules=[
        DecisionRule(
            rule_id="dec_reject_excessive_rot",
            target_grade=ProcurementGrade.REJECT,
            description="Reject if rotten percentage exceeds 2.0%",
            required_criteria_ids=["crit_rot_reject"],
        ),
        DecisionRule(
            rule_id="dec_grade_a",
            target_grade=ProcurementGrade.GRADE_A,
            description="Award Grade A if total defects <= 5.0% and rotten <= 1.0%",
            required_criteria_ids=["crit_total_defects_grade_a", "crit_rot_grade_a"],
        ),
        DecisionRule(
            rule_id="dec_urs",
            target_grade=ProcurementGrade.URS,
            description="Award URS if total defects <= 20.0% and rotten <= 2.0%",
            required_criteria_ids=["crit_total_defects_urs"],
        ),
    ],
    decision_logic=(
        "1. If rotten_percentage > 2.0% -> REJECT. "
        "2. If total_defect_percentage <= 5.0% and rotten_percentage <= 1.0% -> GRADE_A. "
        "3. Else if total_defect_percentage <= 20.0% -> URS. "
        "4. Else -> REJECT."
    ),
)

DEFAULT_RULE_PACK = AGMARK_ONION_STANDARD_V1
