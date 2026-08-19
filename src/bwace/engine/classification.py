"""Quadrant mapping, guard rules, rationale generation. See BR-6, BR-12."""
from __future__ import annotations

from datetime import date

from bwace.engine.models import (
    AxisScore,
    Category,
    Classification,
    Determinant,
    ObjectAssessment,
    ScoringConfig,
    UsageRecord,
)


def classify_by_score(value: AxisScore, effort: AxisScore, cfg: ScoringConfig) -> Category:
    if value.total < cfg.value_threshold:
        return Category.DECOMMISSION
    if effort.total >= cfg.effort_threshold:
        return Category.REBUILD_AS_DATA_PRODUCT
    return Category.REPLICATE_AS_IS


def is_dormant(usage: UsageRecord, reference: date, cfg: ScoringConfig) -> bool:
    elapsed_days = (reference - usage.last_run_date).days
    return elapsed_days > cfg.dormancy_days and usage.monthly_executions < cfg.dormancy_executions


def is_active(usage: UsageRecord, reference: date, cfg: ScoringConfig) -> bool:
    elapsed_days = (reference - usage.last_run_date).days
    return elapsed_days <= cfg.activity_days and usage.monthly_executions >= cfg.activity_executions


def _top_dimensions(axis: AxisScore, count: int) -> list[str]:
    ranked = sorted(axis.dimensions, key=lambda d: d.contribution, reverse=True)
    return [d.dimension.replace("_", " ") for d in ranked[:count]]


def build_rationale(
    value: AxisScore,
    effort: AxisScore,
    category: Category,
    determinant: Determinant,
    usage: UsageRecord,
    reference: date,
    cfg: ScoringConfig,
    is_dormant_flag: bool,
) -> str:
    elapsed_days = (reference - usage.last_run_date).days
    top_value = _top_dimensions(value, 2)
    factor1 = top_value[0] if len(top_value) > 0 else "usage"
    factor2 = top_value[1] if len(top_value) > 1 else "criticality"

    if determinant is Determinant.DORMANCY_CEILING:
        return (
            f"Last run {elapsed_days} days ago with only {usage.monthly_executions} executions per month. "
            f"The dormancy ceiling classifies this for decommission regardless of its computed value of "
            f"{value.total:.1f}, which is inflated by inherited solution-area attributes."
        )
    if determinant is Determinant.ACTIVITY_FLOOR:
        return (
            f"Computed value of {value.total:.1f} falls below the retention threshold, but "
            f"{usage.monthly_executions} executions per month across {usage.distinct_users} users within "
            f"the last {elapsed_days} days means this is in active use. The activity floor prevents decommission."
        )

    if category is Category.REBUILD_AS_DATA_PRODUCT:
        top_effort = _top_dimensions(effort, 1)
        effort_factor = top_effort[0] if top_effort else "technical complexity"
        return (
            f"High business value ({value.total:.1f}) driven by {factor1} and {factor2}, combined with "
            f"high technical effort ({effort.total:.1f}) from {effort_factor}. Modernising as a data product "
            f"is warranted."
        )
    if category is Category.REPLICATE_AS_IS:
        return (
            f"Business value of {value.total:.1f} justifies retention, driven by {factor1} and {factor2}. "
            f"Technical effort of {effort.total:.1f} is below the rebuild threshold, so a pragmatic lift is "
            f"appropriate."
        )

    base = (
        f"Business value of {value.total:.1f} falls below the retention threshold of "
        f"{cfg.value_threshold}. {factor1} and {factor2} are the weakest contributors."
    )
    if is_dormant_flag:
        base += (
            f" Last run {elapsed_days} days ago with {usage.monthly_executions} executions per month, "
            f"which corroborates the assessment."
        )
    return base


def classify(
    value: AxisScore,
    effort: AxisScore,
    usage: UsageRecord,
    reference: date,
    cfg: ScoringConfig,
) -> Classification:
    pure_category = classify_by_score(value, effort, cfg)
    dormant = is_dormant(usage, reference, cfg)
    active = is_active(usage, reference, cfg)

    category = pure_category
    determinant = Determinant.SCORE
    if dormant:
        category = Category.DECOMMISSION
        if category != pure_category:
            determinant = Determinant.DORMANCY_CEILING
    elif active:
        if pure_category is Category.DECOMMISSION:
            category = Category.REBUILD_AS_DATA_PRODUCT if effort.total >= cfg.effort_threshold else Category.REPLICATE_AS_IS
            determinant = Determinant.ACTIVITY_FLOOR
        else:
            category = pure_category

    rationale = build_rationale(value, effort, category, determinant, usage, reference, cfg, dormant)
    return Classification(
        category=category, determinant=determinant,
        is_dormant=dormant, is_active=active, rationale=rationale,
    )


def distribution(assessments: tuple[ObjectAssessment, ...]) -> dict[Category, int]:
    counts: dict[Category, int] = {c: 0 for c in Category}
    for a in assessments:
        counts[a.classification.category] += 1
    return counts
