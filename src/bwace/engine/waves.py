"""Wave assignment, violation detection, risk scoring. See BR-8, BR-9."""
from __future__ import annotations

import math
from datetime import date

from bwace.engine.config import (
    CROSS_WAVE_DEPENDENCY_BANDS,
    DMK_FREEZE_UNTIL,
    DOWNTIME_BANDS,
    RISK_BANDS,
    RISK_WEIGHTS,
)
from bwace.engine.dependencies import constituent_areas
from bwace.engine.models import (
    DependencyGraph,
    DependencyViolation,
    Landscape,
    NodeType,
    ObjectAssessment,
    RiskBand,
    Wave,
    WaveConfig,
    WavePlan,
    WaveRisk,
)
from bwace.engine.normalisation import apply_band


def _priority_to_wave(priority: int, wave_count: int) -> int:
    if wave_count >= 5:
        return priority
    wave = math.floor((priority - 1) * wave_count / 5) + 1
    return max(1, min(wave, wave_count))


def assign_waves(
    assessments: tuple[ObjectAssessment, ...],
    landscape: Landscape,
    cfg: WaveConfig,
) -> dict[int, tuple[str, ...]]:
    area_priority = {a.solution_area: a.migration_priority for a in landscape.criticality.values()}
    membership: dict[int, list[str]] = {n: [] for n in range(1, cfg.wave_count + 1)}
    for assessment in assessments:
        areas = constituent_areas(assessment.bw_object.solution_area, ())
        wave_numbers = [_priority_to_wave(area_priority[a], cfg.wave_count) for a in areas]
        wave = max(wave_numbers)
        membership[wave].append(assessment.object_id)
    return {n: tuple(ids) for n, ids in membership.items()}


def wave_dates(number: int, cfg: WaveConfig) -> tuple[date, date]:
    start_month_offset = (number - 1) * cfg.wave_months
    end_month_offset = number * cfg.wave_months

    def add_months(d: date, months: int) -> date:
        total_month = d.month - 1 + months
        year = d.year + total_month // 12
        month = total_month % 12 + 1
        return date(year, month, 1)

    start = add_months(cfg.start_date, start_month_offset)
    next_start = add_months(cfg.start_date, end_month_offset)
    from datetime import timedelta
    end = next_start - timedelta(days=1)
    return start, end


def _area_wave_map(
    assignment: dict[int, tuple[str, ...]],
    landscape: Landscape,
) -> dict[str, int]:
    object_to_area = {obj.object_id: obj.solution_area for obj in landscape.objects}
    area_wave: dict[str, int] = {}
    for wave_number, object_ids in assignment.items():
        for object_id in object_ids:
            for area in constituent_areas(object_to_area[object_id], ()):
                area_wave[area] = wave_number
    return area_wave


def _area_edges(graph: DependencyGraph) -> tuple[tuple[str, str], ...]:
    """Unique (source_area_label, target_area_label) pairs where both endpoints are solution areas."""
    label_by_node_id = {n.node_id: n.label for n in graph.nodes}
    area_node_ids = {n.node_id for n in graph.nodes if n.node_type is NodeType.SOLUTION_AREA}
    seen: set[tuple[str, str]] = set()
    for edge in graph.edges:
        if edge.source not in area_node_ids or edge.target not in area_node_ids:
            continue
        pair = (label_by_node_id[edge.source], label_by_node_id[edge.target])
        seen.add(pair)
    return tuple(seen)


def detect_violations(
    assignment: dict[int, tuple[str, ...]],
    landscape: Landscape,
    graph: DependencyGraph,
) -> tuple[DependencyViolation, ...]:
    area_wave = _area_wave_map(assignment, landscape)
    violations: list[DependencyViolation] = []
    for source_area, target_area in _area_edges(graph):
        dependent_wave = area_wave.get(source_area)
        depends_on_wave = area_wave.get(target_area)
        if dependent_wave is None or depends_on_wave is None:
            continue
        if dependent_wave < depends_on_wave:
            violations.append(DependencyViolation(
                dependent_area=source_area, depends_on_area=target_area,
                dependent_wave=dependent_wave, depends_on_wave=depends_on_wave,
                description=f"{source_area} (wave {dependent_wave}) depends on {target_area} (wave {depends_on_wave})",
            ))
    return tuple(violations)


def cross_wave_dependency_count(
    wave_number: int,
    areas_in_wave: set[str],
    graph: DependencyGraph,
    area_wave: dict[str, int],
) -> int:
    count = 0
    for source_area, target_area in _area_edges(graph):
        if source_area not in areas_in_wave:
            continue
        target_wave = area_wave.get(target_area)
        if target_wave is None or target_wave == wave_number:
            continue
        count += 2 if wave_number < target_wave else 1
    return count


def risk_band(score: float) -> RiskBand:
    for boundary in RISK_BANDS:
        if score <= boundary.upper:
            return RiskBand(boundary.band)
    return RiskBand(RISK_BANDS[-1].band)


def wave_risk(
    object_ids: tuple[str, ...],
    landscape: Landscape,
    assessments_by_id: dict[str, ObjectAssessment],
    graph: DependencyGraph,
    area_wave: dict[str, int],
    wave_number: int,
    end_date: date,
) -> WaveRisk:
    if not object_ids:
        return WaveRisk(score=0.0, band=RiskBand.LOW, complexity_contribution=0.0,
                         dependency_contribution=0.0, downtime_contribution=0.0, dmk_contribution=0.0)

    complexities = [
        assessments_by_id[oid].technical_effort.dimensions[0].normalised for oid in object_ids
    ]
    complexity_contribution = sum(complexities) / len(complexities)

    areas_in_wave = {landscape_area for oid in object_ids for landscape_area in constituent_areas(
        next(o.solution_area for o in landscape.objects if o.object_id == oid), ())}

    cross_wave_edges = cross_wave_dependency_count(wave_number, areas_in_wave, graph, area_wave)
    dependency_contribution = apply_band(cross_wave_edges, CROSS_WAVE_DEPENDENCY_BANDS)

    downtime_values = [landscape.criticality[a].downtime_tolerance_hours for a in areas_in_wave]
    min_downtime = min(downtime_values) if downtime_values else 0
    downtime_contribution = apply_band(min_downtime, DOWNTIME_BANDS)

    dmk_contribution = 100.0 if end_date < DMK_FREEZE_UNTIL else 0.0

    score = (
        complexity_contribution * RISK_WEIGHTS["complexity"]
        + dependency_contribution * RISK_WEIGHTS["dependency"]
        + downtime_contribution * RISK_WEIGHTS["downtime"]
        + dmk_contribution * RISK_WEIGHTS["dmk"]
    )
    return WaveRisk(
        score=score, band=risk_band(score),
        complexity_contribution=complexity_contribution,
        dependency_contribution=dependency_contribution,
        downtime_contribution=downtime_contribution,
        dmk_contribution=dmk_contribution,
    )


def plan_waves(
    assessments: tuple[ObjectAssessment, ...],
    landscape: Landscape,
    graph: DependencyGraph,
    cfg: WaveConfig,
) -> WavePlan:
    assignment = assign_waves(assessments, landscape, cfg)
    violations = detect_violations(assignment, landscape, graph)
    area_wave = _area_wave_map(assignment, landscape)
    assessments_by_id = {a.object_id: a for a in assessments}
    object_to_area = {obj.object_id: obj.solution_area for obj in landscape.objects}

    waves: list[Wave] = []
    for number in sorted(assignment):
        object_ids = assignment[number]
        start, end = wave_dates(number, cfg)
        areas = tuple(sorted({area for oid in object_ids for area in constituent_areas(object_to_area[oid], ())}))
        risk = wave_risk(object_ids, landscape, assessments_by_id, graph, area_wave, number, end)
        waves.append(Wave(number=number, start_date=start, end_date=end,
                           object_ids=object_ids, areas=areas, risk=risk))

    return WavePlan(waves=tuple(waves), violations=violations)
