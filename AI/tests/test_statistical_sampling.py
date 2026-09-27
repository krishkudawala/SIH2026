"""
Unit and integration tests for Wilson Score Intervals, Finite Population Sampling, and Sequential Sampling.
"""

import pytest

from app.domain.inspection_session import ProcurementGrade
from app.domain.rule_pack import DecisionRule, RuleCriterion, RulePack, SamplingRule
from app.domain.statistical_sampling import (
    SequentialSamplingController,
    WilsonIntervalCalculator,
)


def test_wilson_score_interval_formula():
    # Test 12 / 100 example from prompt
    ci = WilsonIntervalCalculator.build_defect_ci(
        defect_class="ROTTEN",
        defect_count=12,
        sample_n=100,
        confidence_level=0.95,
    )
    assert ci.sample_proportion == 0.12
    assert ci.sample_percentage_str == "12.0%"
    # 95% Wilson CI for 12/100 is approx [0.070, 0.198]
    assert 0.06 < ci.ci_lower < 0.08
    assert 0.18 < ci.ci_upper < 0.21
    assert "12 / 100 (12.0%), 95% Wilson CI:" in ci.ui_display_string
    assert "Not certified true lot percentage." in ci.disclaimer


def test_finite_population_sampling():
    # Lot of 500 bulbs, sampled 100
    ci_fpc = WilsonIntervalCalculator.build_defect_ci(
        defect_class="ROTTEN",
        defect_count=12,
        sample_n=100,
        confidence_level=0.95,
        lot_population_n=500,
    )
    assert ci_fpc.fpc_applied is True
    assert "FPC N=500" in ci_fpc.ui_display_string
    # FPC narrows interval compared to infinite population
    ci_inf = WilsonIntervalCalculator.build_defect_ci(
        defect_class="ROTTEN",
        defect_count=12,
        sample_n=100,
        confidence_level=0.95,
        lot_population_n=None,
    )
    width_fpc = ci_fpc.ci_upper - ci_fpc.ci_lower
    width_inf = ci_inf.ci_upper - ci_inf.ci_lower
    assert width_fpc < width_inf


def test_sequential_sampling_continue_and_sufficient():
    rule_pack = RulePack(
        rule_pack_id="RP_TEST_V1",
        authority="APMC_TEST",
        source_document="Test Standard",
        effective_from="2026-01-01",
        version="1.0.0",
        criteria=[
            RuleCriterion(
                criterion_id="crit_rot",
                name="Max Rot",
                description="Max 5% rot",
                parameter_name="ROTTEN",
                threshold_value=5.0,
                comparison_operator="<=",
                severity_if_exceeded="REJECT",
            )
        ],
        sampling_rule=SamplingRule(rule_id="smp_20", min_sample_units=20),
        decision_rules=[
            DecisionRule(
                rule_id="dec_a",
                target_grade=ProcurementGrade.GRADE_A,
                description="Grade A",
                required_criteria_ids=["crit_rot"],
            )
        ],
        decision_logic="Test logic",
    )

    # Sample size 8 < 20 -> CONTINUE
    res_continue = SequentialSamplingController.evaluate_step(
        sample_units_count=8,
        defect_counts={"ROTTEN": 0},
        rule_pack=rule_pack,
    )
    assert res_continue.state == "CONTINUE"
    assert "Need 12 more bulb(s)" in res_continue.reason

    # Sample size 20 >= 20 -> SUFFICIENT
    res_suff = SequentialSamplingController.evaluate_step(
        sample_units_count=20,
        defect_counts={"ROTTEN": 0},
        rule_pack=rule_pack,
    )
    assert res_suff.state == "SUFFICIENT"


def test_sequential_sampling_conflict_and_reject_boundary():
    rule_pack = RulePack(
        rule_pack_id="RP_TEST_V2",
        authority="APMC_TEST",
        source_document="Test Standard",
        effective_from="2026-01-01",
        version="1.0.0",
        criteria=[
            RuleCriterion(
                criterion_id="crit_rot",
                name="Max Rot",
                description="Max 5% rot",
                parameter_name="ROTTEN",
                threshold_value=5.0,
                comparison_operator="<=",
                severity_if_exceeded="REJECT",
            )
        ],
        sampling_rule=SamplingRule(rule_id="smp_20", min_sample_units=20),
        decision_rules=[],
        decision_logic="Test logic",
    )

    # Conflict -> MANUAL_REVIEW
    res_conflict = SequentialSamplingController.evaluate_step(
        sample_units_count=10,
        defect_counts={"ROTTEN": 0},
        rule_pack=rule_pack,
        conflict_count=2,
    )
    assert res_conflict.state == "MANUAL_REVIEW"

    # Early stopping permitted and lower bound exceeds 5% limit -> REJECT_BOUNDARY
    res_boundary = SequentialSamplingController.evaluate_step(
        sample_units_count=15,
        defect_counts={"ROTTEN": 5},
        rule_pack=rule_pack,
        early_stopping_permitted=True,
    )
    assert res_boundary.state == "REJECT_BOUNDARY"
