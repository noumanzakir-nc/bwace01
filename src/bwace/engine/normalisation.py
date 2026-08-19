"""Raw values to 0-100 scores via fixed absolute bands; area inheritance. See BR-1 to BR-5."""
from __future__ import annotations

from datetime import date

from bwace.engine.config import (
    BANDS,
    COMPLEXITY_SUBWEIGHTS,
    LOAD_FREQUENCY_SCORES,
    RECENCY_TIERS,
    VOLUME_SUBWEIGHTS,
    Band,
)
from bwace.engine.models import (
    AreaCriticality,
    ComplexityMetrics,
    DependencyGraph,
    DimensionScore,
    UsageRecord,
    VolumeMetrics,
)


def apply_band(value: float, bands: tuple[Band, ...]) -> float:
    for band in bands:
        if value <= band.upper:
            return band.score
    return bands[-1].score


def recency_factor(last_run: date, reference: date) -> float:
    elapsed_days = (reference - last_run).days
    for tier in RECENCY_TIERS:
        if elapsed_days <= tier.upper_days:
            return tier.factor
    return RECENCY_TIERS[-1].factor


def _constituent_areas(solution_area: str) -> tuple[str, ...]:
    return tuple(solution_area.split("/"))


class AreaMetrics:
    def __init__(self, criticality: float, outgoing: float, incoming: float, inherited_from: str) -> None:
        self.criticality = criticality
        self.outgoing = outgoing
        self.incoming = incoming
        self.inherited_from = inherited_from


def resolve_area_metrics(
    solution_area: str,
    criticality: dict[str, AreaCriticality],
    graph: DependencyGraph,
) -> AreaMetrics:
    areas = _constituent_areas(solution_area)
    crit_values = [criticality[a].criticality for a in areas]
    out_values = [graph.out_degree.get(_area_to_node_id(a, graph), 0) for a in areas]
    in_values = [graph.in_degree.get(_area_to_node_id(a, graph), 0) for a in areas]
    return AreaMetrics(
        criticality=sum(crit_values) / len(crit_values),
        outgoing=sum(out_values) / len(out_values),
        incoming=sum(in_values) / len(in_values),
        inherited_from=" / ".join(areas),
    )


def _area_to_node_id(area_label: str, graph: DependencyGraph) -> str:
    for node in graph.nodes:
        if node.label == area_label:
            return node.node_id
    return area_label


def score_usage_frequency(usage: UsageRecord, reference: date) -> DimensionScore:
    elapsed_days = (reference - usage.last_run_date).days
    base = apply_band(usage.monthly_executions, BANDS["usage_frequency"])
    factor = recency_factor(usage.last_run_date, reference)
    normalised = base * factor
    raw_display = f"{usage.monthly_executions} executions, last run {elapsed_days} days ago"
    return DimensionScore(
        dimension="usage_frequency", raw_display=raw_display,
        normalised=normalised, weight=0.0, contribution=0.0,
    )


def score_distinct_users(usage: UsageRecord) -> DimensionScore:
    normalised = apply_band(usage.distinct_users, BANDS["distinct_users"])
    return DimensionScore(
        dimension="distinct_users", raw_display=f"{usage.distinct_users} users",
        normalised=normalised, weight=0.0, contribution=0.0,
    )


def score_criticality(area: str, criticality: dict[str, AreaCriticality], graph: DependencyGraph) -> DimensionScore:
    metrics = resolve_area_metrics(area, criticality, graph)
    return DimensionScore(
        dimension="criticality", raw_display=f"{metrics.criticality:.1f} (inherited)",
        normalised=metrics.criticality, weight=0.0, contribution=0.0,
        inherited_from=metrics.inherited_from,
    )


def score_outgoing_dependencies(area: str, criticality: dict[str, AreaCriticality], graph: DependencyGraph) -> DimensionScore:
    metrics = resolve_area_metrics(area, criticality, graph)
    normalised = apply_band(metrics.outgoing, BANDS["outgoing_dependencies"])
    return DimensionScore(
        dimension="outgoing_dependencies", raw_display=f"{metrics.outgoing:.1f} (inherited)",
        normalised=normalised, weight=0.0, contribution=0.0,
        inherited_from=metrics.inherited_from,
    )


def score_incoming_dependencies(area: str, criticality: dict[str, AreaCriticality], graph: DependencyGraph) -> DimensionScore:
    metrics = resolve_area_metrics(area, criticality, graph)
    normalised = apply_band(metrics.incoming, BANDS["incoming_dependencies"])
    return DimensionScore(
        dimension="incoming_dependencies", raw_display=f"{metrics.incoming:.1f} (inherited)",
        normalised=normalised, weight=0.0, contribution=0.0,
        inherited_from=metrics.inherited_from,
    )


def score_complexity(metrics: ComplexityMetrics) -> DimensionScore:
    hana = apply_band(metrics.hana_cv_count, BANDS["hana_cv_count"])
    transform = apply_band(metrics.transformation_count, BANDS["transformation_count"])
    interface = apply_band(metrics.interface_count, BANDS["interface_count"])
    custom_logic = 100.0 if metrics.custom_logic_present else 0.0
    normalised = (
        hana * COMPLEXITY_SUBWEIGHTS["hana_cv_count"]
        + transform * COMPLEXITY_SUBWEIGHTS["transformation_count"]
        + interface * COMPLEXITY_SUBWEIGHTS["interface_count"]
        + custom_logic * COMPLEXITY_SUBWEIGHTS["custom_logic_present"]
    )
    raw_display = (
        f"HANA CVs {metrics.hana_cv_count}, transformations {metrics.transformation_count}, "
        f"interfaces {metrics.interface_count}, custom logic {metrics.custom_logic_present}"
    )
    return DimensionScore(
        dimension="technical_complexity", raw_display=raw_display,
        normalised=normalised, weight=0.0, contribution=0.0,
    )


def score_volume(metrics: VolumeMetrics) -> DimensionScore:
    records = apply_band(metrics.record_count, BANDS["record_count"])
    storage = apply_band(metrics.storage_gb, BANDS["storage_gb"])
    load = LOAD_FREQUENCY_SCORES.get(metrics.load_frequency, 0.0)
    normalised = (
        records * VOLUME_SUBWEIGHTS["record_count"]
        + storage * VOLUME_SUBWEIGHTS["storage_gb"]
        + load * VOLUME_SUBWEIGHTS["load_frequency"]
    )
    raw_display = (
        f"{metrics.record_count:,} records, {metrics.storage_gb} GB, {metrics.load_frequency}"
    )
    return DimensionScore(
        dimension="data_volume", raw_display=raw_display,
        normalised=normalised, weight=0.0, contribution=0.0,
    )
