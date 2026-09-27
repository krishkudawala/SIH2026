"""
Statistical Sampling, Wilson Score Confidence Intervals & Sequential Sampling Engine
for Mandi Nyaay (Gate 6B / Components J, K, L).

Implements:
1. Wilson Score Confidence Intervals for defect proportions:
   - For each defect class: count, sample_n, proportion, lower, upper, confidence_level
   - UI format: "12 / 100, 12%, 95% Wilson CI: [lower, upper]"
   - Never calls raw sample percentage "true lot percentage".
2. Finite-Population Sampling (Component K):
   - When lot population N is known: applies Finite Population Correction (FPC) or exact hypergeometric logic.
3. Sequential Sampling State Machine (Component L):
   - Recalculates after every primary SampleUnit.
   - States: CONTINUE, SUFFICIENT, REJECT_BOUNDARY, ACCEPT_BOUNDARY, MANUAL_REVIEW.
   - Strict rule: ONLY uses early stopping where the active RulePack permits it.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Sequence
from scipy import stats
from pydantic import BaseModel, ConfigDict, Field

from app.cv.label_mapping import CanonicalLabel
from app.domain.rule_pack import RulePack

logger = logging.getLogger(__name__)


class DefectClassWilsonCI(BaseModel):
    """
    Wilson score confidence interval for a single produce defect class.
    """
    model_config = ConfigDict(extra="forbid")

    defect_class: str = Field(..., description="Canonical defect class label")
    defect_count: int = Field(..., ge=0, description="Observed defective bulb count")
    sample_n: int = Field(..., ge=1, description="Total certified physical SampleUnits")
    sample_proportion: float = Field(..., ge=0.0, le=1.0, description="Raw sample proportion count / n")
    sample_percentage_str: str = Field(..., description="e.g. '12.0%'")
    ci_lower: float = Field(..., ge=0.0, le=1.0, description="Lower bound of Wilson CI")
    ci_upper: float = Field(..., ge=0.0, le=1.0, description="Upper bound of Wilson CI")
    ci_lower_pct_str: str = Field(..., description="e.g. '6.9%'")
    ci_upper_pct_str: str = Field(..., description="e.g. '19.9%'")
    confidence_level: float = Field(default=0.95, description="Nominal confidence coefficient (e.g. 0.95)")
    lot_population_n: int | None = Field(default=None, description="Total lot bulb population N if known")
    fpc_applied: bool = Field(default=False, description="Whether finite population correction was applied")
    ui_display_string: str = Field(..., description="Certified UI display string")
    disclaimer: str = Field(
        default="Sample proportion with Wilson score interval. Not certified true lot percentage.",
        description="Mandatory statistical disclaimer"
    )


class SequentialSamplingDecision(BaseModel):
    """
    Real-time sequential sampling state updated after every primary SampleUnit.
    """
    model_config = ConfigDict(extra="forbid")

    state: str = Field(
        ...,
        description="CONTINUE, SUFFICIENT, REJECT_BOUNDARY, ACCEPT_BOUNDARY, or MANUAL_REVIEW"
    )
    current_sample_size: int = Field(..., description="Certified unique physical SampleUnits so far")
    target_sample_size: int = Field(..., description="Statutory target sample size from RulePack")
    defect_intervals: list[DefectClassWilsonCI] = Field(
        default_factory=list,
        description="Wilson intervals for all observed defect classes"
    )
    conflicts_count: int = Field(default=0, description="Count of unresolved cross-view conflicts")
    reason: str = Field(..., description="Deterministic explanation of sampling state")
    early_stopping_permitted: bool = Field(
        default=False,
        description="Whether active RulePack explicitly permits early boundary stopping"
    )
    boundary_hit: str | None = Field(
        default=None,
        description="Name of boundary hit (e.g. 'Rotten > 5% statutory limit')"
    )
    rule_pack_id: str = Field(..., description="Authoritative RulePack identifier")
    disclaimer: str = Field(
        default="Sequential sampling state evaluates physical SampleUnits against statutory thresholds.",
        description="Dispute and audit disclaimer"
    )


class WilsonIntervalCalculator:
    """
    Calculates Wilson score confidence intervals with optional Finite Population Correction.
    """

    @classmethod
    def compute_wilson_ci(
        cls,
        count: int,
        sample_n: int,
        confidence_level: float = 0.95,
        lot_population_n: int | None = None,
    ) -> tuple[float, float, bool]:
        """
        Compute Wilson score interval [lower, upper] for binomial proportion.
        Applies Finite Population Correction (FPC) when lot_population_N is provided and valid.
        """
        if sample_n <= 0:
            return 0.0, 1.0, False

        count = max(0, min(count, sample_n))
        p = count / sample_n

        # Critical z value from normal distribution
        alpha = 1.0 - confidence_level
        z = float(stats.norm.ppf(1.0 - alpha / 2.0))

        # Use battle-tested statsmodels reference implementation
        try:
            from statsmodels.stats.proportion import proportion_confint
            ci_low, ci_high = proportion_confint(count, sample_n, alpha=alpha, method="wilson")
            center = float((ci_low + ci_high) / 2.0)
            margin = float((ci_high - ci_low) / 2.0)
        except Exception:
            # Fallback to exact Wilson score formula
            denom = 1.0 + (z**2) / sample_n
            center = (p + (z**2) / (2.0 * sample_n)) / denom
            margin = (z / denom) * math.sqrt(
                (p * (1.0 - p) / sample_n) + ((z**2) / (4.0 * (sample_n**2)))
            )

        fpc_applied = False
        if lot_population_n is not None and lot_population_n > sample_n:
            # Finite Population Correction: sqrt((N - n) / (N - 1))
            fpc = math.sqrt((lot_population_n - sample_n) / max(1.0, lot_population_n - 1.0))
            margin *= fpc
            fpc_applied = True

        lower = max(0.0, center - margin)
        upper = min(1.0, center + margin)

        return round(lower, 4), round(upper, 4), fpc_applied

    @classmethod
    def build_defect_ci(
        cls,
        defect_class: str,
        defect_count: int,
        sample_n: int,
        confidence_level: float = 0.95,
        lot_population_n: int | None = None,
    ) -> DefectClassWilsonCI:
        """
        Construct a DefectClassWilsonCI with certified UI formatting.
        """
        lower, upper, fpc = cls.compute_wilson_ci(
            defect_count, sample_n, confidence_level, lot_population_n
        )
        prop = defect_count / max(1, sample_n)
        pct_str = f"{prop * 100:.1f}%"
        low_str = f"{lower * 100:.1f}%"
        high_str = f"{upper * 100:.1f}%"

        pop_tag = f" [FPC N={lot_population_n}]" if fpc else ""
        ui_str = f"{defect_count} / {sample_n} ({pct_str}), {int(confidence_level * 100)}% Wilson CI: [{low_str}, {high_str}]{pop_tag}"

        return DefectClassWilsonCI(
            defect_class=defect_class,
            defect_count=defect_count,
            sample_n=sample_n,
            sample_proportion=round(prop, 4),
            sample_percentage_str=pct_str,
            ci_lower=lower,
            ci_upper=upper,
            ci_lower_pct_str=low_str,
            ci_upper_pct_str=high_str,
            confidence_level=confidence_level,
            lot_population_n=lot_population_n,
            fpc_applied=fpc,
            ui_display_string=ui_str,
        )


class SequentialSamplingController:
    """
    Evaluates real-time sampling progression after every primary SampleUnit.
    Strictly prevents silent statutory bypass while enabling auditable early stopping
    when authorized by the active RulePack.
    """

    @classmethod
    def evaluate_step(
        cls,
        sample_units_count: int,
        defect_counts: dict[str, int],
        rule_pack: RulePack,
        conflict_count: int = 0,
        lot_population_n: int | None = None,
        confidence_level: float = 0.95,
        early_stopping_permitted: bool = False,
    ) -> SequentialSamplingDecision:
        """
        Recalculate sequential sampling state after an inspection step.
        """
        min_target = rule_pack.sampling_rule.min_sample_units

        # Compute Wilson intervals for each defect class
        intervals: list[DefectClassWilsonCI] = []
        for d_class in ["ROTTEN", "DAMAGED", "SPROUTED", "TOTAL_DEFECTS"]:
            cnt = defect_counts.get(d_class, 0)
            if sample_units_count > 0:
                ci = WilsonIntervalCalculator.build_defect_ci(
                    defect_class=d_class,
                    defect_count=cnt,
                    sample_n=sample_units_count,
                    confidence_level=confidence_level,
                    lot_population_n=lot_population_n,
                )
                intervals.append(ci)

        # 1. Check for manual review condition (conflicts)
        if conflict_count > 0:
            return SequentialSamplingDecision(
                state="MANUAL_REVIEW",
                current_sample_size=sample_units_count,
                target_sample_size=min_target,
                defect_intervals=intervals,
                conflicts_count=conflict_count,
                early_stopping_permitted=early_stopping_permitted,
                rule_pack_id=rule_pack.rule_pack_id,
                reason=(
                    f"Session contains {conflict_count} unresolved cross-view conflict(s). "
                    "Sequential sampling halted for human inspector review."
                ),
            )

        # 2. Check early stopping boundaries if explicitly permitted by RulePack
        if early_stopping_permitted and sample_units_count >= 10:
            for criterion in rule_pack.criteria:
                # Look for parameter match in intervals
                param = criterion.parameter_name.upper()
                matching_ci = next((ci for ci in intervals if ci.defect_class in param or param in ci.defect_class), None)
                if matching_ci is not None:
                    thresh_prop = criterion.threshold_value / 100.0 if criterion.threshold_value > 1.0 else criterion.threshold_value

                    # REJECT BOUNDARY: Lower bound already violates maximum limit
                    if criterion.comparison_operator in ["<=", "<"] and matching_ci.ci_lower > thresh_prop:
                        return SequentialSamplingDecision(
                            state="REJECT_BOUNDARY",
                            current_sample_size=sample_units_count,
                            target_sample_size=min_target,
                            defect_intervals=intervals,
                            conflicts_count=0,
                            early_stopping_permitted=True,
                            boundary_hit=f"{criterion.name} (Lower bound {matching_ci.ci_lower_pct_str} > limit {criterion.threshold_value}%)",
                            rule_pack_id=rule_pack.rule_pack_id,
                            reason=(
                                f"Statistical reject boundary hit: 95% Wilson lower bound ({matching_ci.ci_lower_pct_str}) "
                                f"exceeds allowable threshold ({criterion.threshold_value}%). Early rejection permitted."
                            ),
                        )

                    # ACCEPT BOUNDARY: Upper bound safely below limit and past half sample
                    if (
                        criterion.comparison_operator in ["<=", "<"]
                        and matching_ci.ci_upper < (thresh_prop * 0.5)
                        and sample_units_count >= int(min_target * 0.75)
                    ):
                        return SequentialSamplingDecision(
                            state="ACCEPT_BOUNDARY",
                            current_sample_size=sample_units_count,
                            target_sample_size=min_target,
                            defect_intervals=intervals,
                            conflicts_count=0,
                            early_stopping_permitted=True,
                            boundary_hit=f"{criterion.name} (Upper bound {matching_ci.ci_upper_pct_str} << limit {criterion.threshold_value}%)",
                            rule_pack_id=rule_pack.rule_pack_id,
                            reason=(
                                f"Statistical accept boundary hit: 95% Wilson upper bound ({matching_ci.ci_upper_pct_str}) "
                                f"is well below threshold ({criterion.threshold_value}%). Early acceptance permitted."
                            ),
                        )

        # 3. Standard sample sufficiency check
        if sample_units_count >= min_target:
            return SequentialSamplingDecision(
                state="SUFFICIENT",
                current_sample_size=sample_units_count,
                target_sample_size=min_target,
                defect_intervals=intervals,
                conflicts_count=0,
                early_stopping_permitted=early_stopping_permitted,
                rule_pack_id=rule_pack.rule_pack_id,
                reason=(
                    f"Sample size ({sample_units_count}) satisfies statutory minimum ({min_target}) "
                    f"defined by RulePack '{rule_pack.rule_pack_id}' with zero conflicts."
                ),
            )
        else:
            shortfall = min_target - sample_units_count
            return SequentialSamplingDecision(
                state="CONTINUE",
                current_sample_size=sample_units_count,
                target_sample_size=min_target,
                defect_intervals=intervals,
                conflicts_count=0,
                early_stopping_permitted=early_stopping_permitted,
                rule_pack_id=rule_pack.rule_pack_id,
                reason=(
                    f"Sampling in progress: {sample_units_count} / {min_target} SampleUnits. "
                    f"Need {shortfall} more bulb(s) to reach statutory minimum."
                ),
            )
