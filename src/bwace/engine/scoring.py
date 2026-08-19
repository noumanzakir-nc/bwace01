"""Weight and sum both axes from normalised dimensions. See BR-2, BR-5, BR-6.1."""
from __future__ import annotations

from datetime import date

from bwace.engine.config import EFFORT_WEIGHTS, VALUE_WEIGHTS
from bwace.engine.models import AxisScore, DependencyGraph, DimensionScore, Landscape
from bwace.engine.normalisation import (
    score_complexity,
    score_criticality,
    score_distinct_users,
    score_incoming_dependencies,
    score_outgoing_dependencies,
    score_usage_frequency,
    score_volume,
)


def reference_date(landscape: Landscape) -> date:
    return max(record.last_run_date for record in landscape.usage.values())


def _weighted(dim: DimensionScore, weight_pct: float) -> DimensionScore:
    weight = weight_pct / 100.0
    return DimensionScore(
        dimension=dim.dimension, raw_display=dim.raw_display,
        normalised=dim.normalised, weight=weight,
        contribution=dim.normalised * weight,
        inherited_from=dim.inherited_from,
    )


def business_value(object_id: str, landscape: Landscape, graph: DependencyGraph, reference: date) -> AxisScore:
    obj = next(o for o in landscape.objects if o.object_id == object_id)
    usage = landscape.usage[object_id]
    dims = (
        _weighted(score_usage_frequency(usage, reference), VALUE_WEIGHTS["usage_frequency"]),
        _weighted(score_distinct_users(usage), VALUE_WEIGHTS["distinct_users"]),
        _weighted(score_criticality(obj.solution_area, landscape.criticality, graph), VALUE_WEIGHTS["criticality"]),
        _weighted(score_outgoing_dependencies(obj.solution_area, landscape.criticality, graph), VALUE_WEIGHTS["outgoing_dependencies"]),
        _weighted(score_incoming_dependencies(obj.solution_area, landscape.criticality, graph), VALUE_WEIGHTS["incoming_dependencies"]),
    )
    total = sum(d.contribution for d in dims)
    return AxisScore(axis="business_value", total=total, dimensions=dims)


def technical_effort(object_id: str, landscape: Landscape) -> AxisScore:
    complexity = landscape.complexity[object_id]
    volume = landscape.volume[object_id]
    dims = (
        _weighted(score_complexity(complexity), EFFORT_WEIGHTS["technical_complexity"]),
        _weighted(score_volume(volume), EFFORT_WEIGHTS["data_volume"]),
    )
    total = sum(d.contribution for d in dims)
    return AxisScore(axis="technical_effort", total=total, dimensions=dims)


def score_all(landscape: Landscape, graph: DependencyGraph) -> dict[str, tuple[AxisScore, AxisScore]]:
    ref = reference_date(landscape)
    return {
        obj.object_id: (
            business_value(obj.object_id, landscape, graph, ref),
            technical_effort(obj.object_id, landscape),
        )
        for obj in landscape.objects
    }
