"""
Statutory RulePack Validation Engine for Mandi Nyaay (Gate 6B Part 8).

Guarantees:
- Every RulePack governing procurement grading is strictly validated prior to decisioning.
- Validates:
  1. rule_pack_id exists and is non-empty.
  2. authority exists and is non-empty.
  3. source_reference exists and is non-empty.
  4. version exists and is non-empty.
  5. effective period is coherent (effective_from is valid, effective_to >= effective_from).
  6. criteria are complete (valid thresholds, operators, parameter names).
  7. sampling method is defined and valid.
  8. decision logic is deterministic (rules are unambiguous, target grades valid, all referenced criteria exist).
- An invalid RulePack MUST block procurement decisioning and divert to MANUAL_REVIEW.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.domain.inspection_session import ProcurementGrade
from app.domain.rule_pack import DecisionRule, RuleCriterion, RulePack, SamplingRule


class RulePackValidationResult(BaseModel):
    """
    Certified validation outcome for a statutory RulePack.
    """
    model_config = ConfigDict(extra="forbid")

    is_valid: bool = Field(..., description="Whether the RulePack is validated and certified for decisioning")
    errors: list[str] = Field(default_factory=list, description="List of blocking validation errors")
    warnings: list[str] = Field(default_factory=list, description="Non-blocking informational advisories")


def _parse_iso_date(date_str: str) -> date | None:
    """Attempt to parse an ISO date string (YYYY-MM-DD or full ISO datetime)."""
    if not date_str:
        return None
    try:
        if "T" in date_str:
            return datetime.fromisoformat(date_str).date()
        return date.fromisoformat(date_str)
    except (ValueError, TypeError):
        return None


def validate_rule_pack(rule_pack: Any) -> RulePackValidationResult:
    """
    Validate a RulePack against Gate 6B statutory integrity requirements.
    An invalid RulePack must block procurement decisioning.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # 1. Null check
    if rule_pack is None:
        return RulePackValidationResult(
            is_valid=False,
            errors=["NO_RULE_PACK: RulePack is None or missing."],
            warnings=[],
        )

    if not isinstance(rule_pack, RulePack):
        return RulePackValidationResult(
            is_valid=False,
            errors=[f"TYPE_ERROR: Expected RulePack instance, got {type(rule_pack).__name__}."],
            warnings=[],
        )

    # 2. rule_pack_id exists
    if not rule_pack.rule_pack_id or not str(rule_pack.rule_pack_id).strip():
        errors.append("MISSING_RULE_PACK_ID: rule_pack_id is required and cannot be empty.")

    # 3. authority exists
    if not rule_pack.authority or not str(rule_pack.authority).strip():
        errors.append("MISSING_AUTHORITY: Statutory authority is required and cannot be empty.")

    # 4. source reference exists
    source_ref = (
        getattr(rule_pack, "source_reference", None)
        or getattr(rule_pack, "source_uri_or_reference", None)
    )
    if not source_ref or not str(source_ref).strip():
        errors.append("MISSING_SOURCE_REFERENCE: source_reference is required and cannot be empty.")

    if not rule_pack.source_document or not str(rule_pack.source_document).strip():
        errors.append("MISSING_SOURCE_DOCUMENT: source_document is required and cannot be empty.")

    # 5. version exists
    if not rule_pack.version or not str(rule_pack.version).strip():
        errors.append("MISSING_VERSION: RulePack version is required and cannot be empty.")

    # 6. effective period is coherent
    if not rule_pack.effective_from or not str(rule_pack.effective_from).strip():
        errors.append("MISSING_EFFECTIVE_FROM: effective_from date is required.")
    else:
        dt_from = _parse_iso_date(str(rule_pack.effective_from).strip())
        if dt_from is None:
            errors.append(f"INVALID_EFFECTIVE_FROM: effective_from '{rule_pack.effective_from}' is not a valid ISO date.")
        else:
            if rule_pack.effective_to and str(rule_pack.effective_to).strip():
                dt_to = _parse_iso_date(str(rule_pack.effective_to).strip())
                if dt_to is None:
                    errors.append(f"INVALID_EFFECTIVE_TO: effective_to '{rule_pack.effective_to}' is not a valid ISO date.")
                elif dt_to < dt_from:
                    errors.append(
                        f"INCOHERENT_PERIOD: effective_to ({rule_pack.effective_to}) precedes "
                        f"effective_from ({rule_pack.effective_from})."
                    )

    # 7. criteria are complete
    if not rule_pack.criteria or len(rule_pack.criteria) == 0:
        errors.append("EMPTY_CRITERIA: RulePack contains zero criteria; cannot evaluate quality specifications.")
    else:
        valid_operators = {"<=", "<", ">=", ">", "==", "!="}
        seen_crit_ids: set[str] = set()

        for idx, crit in enumerate(rule_pack.criteria):
            if not crit.criterion_id or not str(crit.criterion_id).strip():
                errors.append(f"CRITERION_ID_MISSING: Criterion at index {idx} has an empty criterion_id.")
            elif crit.criterion_id in seen_crit_ids:
                errors.append(f"DUPLICATE_CRITERION_ID: Duplicate criterion_id '{crit.criterion_id}'.")
            else:
                seen_crit_ids.add(crit.criterion_id)

            if not crit.parameter_name or not str(crit.parameter_name).strip():
                errors.append(f"PARAMETER_NAME_MISSING: Criterion '{crit.criterion_id}' has an empty parameter_name.")

            if crit.comparison_operator not in valid_operators:
                errors.append(
                    f"INVALID_OPERATOR: Criterion '{crit.criterion_id}' has invalid operator '{crit.comparison_operator}'."
                )

            if not isinstance(crit.threshold_value, (int, float)):
                errors.append(
                    f"INVALID_THRESHOLD: Criterion '{crit.criterion_id}' threshold_value must be numeric, got {type(crit.threshold_value).__name__}."
                )

    # 8. sampling method is defined
    sampling_method_val = getattr(rule_pack, "sampling_method", None)
    if not sampling_method_val and rule_pack.sampling_rule:
        sampling_method_val = getattr(rule_pack.sampling_rule, "sampling_method", None)

    if not sampling_method_val or not str(sampling_method_val).strip():
        errors.append("UNDEFINED_SAMPLING_METHOD: sampling_method must be explicitly defined.")

    if not rule_pack.sampling_rule:
        errors.append("MISSING_SAMPLING_RULE: sampling_rule specification is missing.")
    else:
        if rule_pack.sampling_rule.min_sample_units < 1:
            errors.append(
                f"INVALID_MIN_SAMPLE: min_sample_units ({rule_pack.sampling_rule.min_sample_units}) must be at least 1."
            )

    # 9. decision logic is deterministic
    if not rule_pack.decision_logic or not str(rule_pack.decision_logic).strip():
        errors.append("EMPTY_DECISION_LOGIC: Human-readable decision_logic description is required.")

    if not rule_pack.decision_rules or len(rule_pack.decision_rules) == 0:
        errors.append("EMPTY_DECISION_RULES: RulePack must specify at least one DecisionRule.")
    else:
        known_criteria_ids = {c.criterion_id for c in rule_pack.criteria if c.criterion_id}
        seen_rule_ids: set[str] = set()

        for idx, dr in enumerate(rule_pack.decision_rules):
            if not dr.rule_id or not str(dr.rule_id).strip():
                errors.append(f"DECISION_RULE_ID_MISSING: DecisionRule at index {idx} has an empty rule_id.")
            elif dr.rule_id in seen_rule_ids:
                errors.append(f"DUPLICATE_DECISION_RULE_ID: Duplicate decision rule_id '{dr.rule_id}'.")
            else:
                seen_rule_ids.add(dr.rule_id)

            if not isinstance(dr.target_grade, ProcurementGrade):
                errors.append(
                    f"INVALID_TARGET_GRADE: DecisionRule '{dr.rule_id}' has invalid target_grade '{dr.target_grade}'."
                )

            # Check that all referenced criteria exist
            for req_crit_id in dr.required_criteria_ids:
                if req_crit_id not in known_criteria_ids:
                    errors.append(
                        f"UNDEFINED_CRITERION_REFERENCE: DecisionRule '{dr.rule_id}' references undefined criterion '{req_crit_id}'."
                    )

    return RulePackValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )
