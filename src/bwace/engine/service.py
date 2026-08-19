"""Single orchestrator. Landscape + configuration -> immutable AssessmentResult. See services.md."""
from __future__ import annotations

from bwace.engine.classification import classify, distribution
from bwace.engine.dependencies import build_graph, edges_for_object
from bwace.engine.models import (
    AssessmentResult,
    BaseScores,
    Category,
    ClassificationChange,
    Landscape,
    LandscapeKpis,
    ObjectAssessment,
    Scenario,
    ScenarioDiff,
    ScoringConfig,
    WaveConfig,
)
from bwace.engine.scoring import reference_date, score_all
from bwace.engine.waves import plan_waves


def compute_base(landscape: Landscape) -> BaseScores:
    graph = build_graph(landscape.nodes, landscape.edges)
    axis_scores = score_all(landscape, graph)
    ref = reference_date(landscape)
    return BaseScores(graph=graph, axis_scores=axis_scores, reference_date=ref)


def kpis(assessments: tuple[ObjectAssessment, ...], landscape: Landscape) -> LandscapeKpis:
    total_objects = len(assessments)
    total_storage = sum(v.storage_gb for v in landscape.volume.values())
    decommission = sum(1 for a in assessments if a.classification.category is Category.DECOMMISSION)
    decommission_pct = (decommission / total_objects * 100) if total_objects else 0.0
    reclaimable = sum(
        landscape.volume[a.object_id].storage_gb
        for a in assessments
        if a.classification.category is Category.DECOMMISSION and a.object_id in landscape.volume
    )
    return LandscapeKpis(
        total_objects=total_objects,
        total_storage_gb=total_storage,
        decommission_pct=decommission_pct,
        reclaimable_storage_gb=reclaimable,
    )


def apply_config(
    base: BaseScores,
    landscape: Landscape,
    scoring: ScoringConfig,
    waves: WaveConfig,
) -> AssessmentResult:
    assessments: list[ObjectAssessment] = []
    for obj in landscape.objects:
        value_score, effort_score = base.axis_scores[obj.object_id]
        usage = landscape.usage[obj.object_id]
        classification = classify(value_score, effort_score, usage, base.reference_date, scoring)
        incoming, outgoing = edges_for_object(obj, base.graph)
        assessments.append(ObjectAssessment(
            object_id=obj.object_id, bw_object=obj, usage=usage,
            business_value=value_score, technical_effort=effort_score,
            classification=classification, incoming=incoming, outgoing=outgoing,
        ))
    assessments_tuple = tuple(assessments)
    dist = distribution(assessments_tuple)
    kpi_values = kpis(assessments_tuple, landscape)
    wave_plan = plan_waves(assessments_tuple, landscape, base.graph, waves)

    return AssessmentResult(
        assessments=assessments_tuple, distribution=dist, graph=base.graph,
        wave_plan=wave_plan, kpis=kpi_values, scoring_config=scoring,
        wave_config=waves, fingerprint=landscape.fingerprint,
    )


def assess(landscape: Landscape, scoring: ScoringConfig, waves: WaveConfig) -> AssessmentResult:
    base = compute_base(landscape)
    return apply_config(base, landscape, scoring, waves)


def compare(landscape: Landscape, left: Scenario, right: Scenario) -> ScenarioDiff:
    base = compute_base(landscape)
    left_result = apply_config(base, landscape, left.scoring_config, left.wave_config)
    right_result = apply_config(base, landscape, right.scoring_config, right.wave_config)

    left_by_id = {a.object_id: a.classification.category for a in left_result.assessments}
    right_by_id = {a.object_id: a.classification.category for a in right_result.assessments}
    changed = tuple(
        ClassificationChange(object_id=oid, left_category=left_by_id[oid], right_category=right_by_id[oid])
        for oid in left_by_id
        if left_by_id[oid] != right_by_id[oid]
    )

    return ScenarioDiff(
        left_name=left.name, right_name=right.name, changed=changed,
        left_distribution=left_result.distribution, right_distribution=right_result.distribution,
    )
