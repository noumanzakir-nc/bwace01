"""The only pandas-touching module. Domain objects to DataFrames. See domain-entities.md #4."""
from __future__ import annotations

import pandas as pd

from bwace.engine.models import (
    AssessmentResult,
    Category,
    DependencyGraph,
    Landscape,
    ObjectAssessment,
    WavePlan,
)


def assessments_frame(result: AssessmentResult, landscape: Landscape) -> pd.DataFrame:
    rows = []
    for a in result.assessments:
        volume = landscape.volume.get(a.object_id)
        rows.append({
            "object_id": a.object_id,
            "object_type": a.bw_object.object_type,
            "solution_area": a.bw_object.solution_area,
            "description": a.bw_object.description,
            "business_value": a.business_value.total,
            "technical_effort": a.technical_effort.total,
            "category": a.classification.category,
            "category_label": a.classification.category.value.replace("_", " ").title(),
            "determinant": a.classification.determinant,
            "is_dormant": a.classification.is_dormant,
            "is_active": a.classification.is_active,
            "monthly_executions": a.usage.monthly_executions,
            "distinct_users": a.usage.distinct_users,
            "last_run_date": a.usage.last_run_date,
            "business_owner": a.usage.business_owner,
            "storage_gb": volume.storage_gb if volume else 0,
        })
    frame = pd.DataFrame(rows)
    return frame


def derivation_frame(assessment: ObjectAssessment) -> pd.DataFrame:
    rows = []
    for dim in assessment.business_value.dimensions:
        rows.append({
            "axis": "business_value", "dimension": dim.dimension,
            "dimension_label": dim.dimension.replace("_", " ").title(),
            "raw_display": dim.raw_display, "normalised": dim.normalised,
            "weight": dim.weight, "contribution": dim.contribution,
            "inherited_from": dim.inherited_from,
        })
    for dim in assessment.technical_effort.dimensions:
        rows.append({
            "axis": "technical_effort", "dimension": dim.dimension,
            "dimension_label": dim.dimension.replace("_", " ").title(),
            "raw_display": dim.raw_display, "normalised": dim.normalised,
            "weight": dim.weight, "contribution": dim.contribution,
            "inherited_from": dim.inherited_from,
        })
    return pd.DataFrame(rows)


def gantt_frame(plan: WavePlan) -> pd.DataFrame:
    rows = []
    for wave in plan.waves:
        rows.append({
            "wave": wave.number, "wave_label": f"Wave {wave.number}",
            "start_date": wave.start_date, "end_date": wave.end_date,
            "object_count": len(wave.object_ids), "areas": ", ".join(wave.areas),
            "risk_score": wave.risk.score, "risk_band": wave.risk.band,
        })
    return pd.DataFrame(rows)


def heatmap_frame(graph: DependencyGraph) -> pd.DataFrame:
    label_by_id = {n.node_id: n.label for n in graph.nodes}
    rows = []
    for i, row_id in enumerate(graph.area_order):
        for j, col_id in enumerate(graph.area_order):
            rows.append({
                "source_area": label_by_id[row_id],
                "target_area": label_by_id[col_id],
                "value": graph.area_matrix[i][j],
            })
    return pd.DataFrame(rows)


def candidates_frame(result: AssessmentResult, landscape: Landscape) -> pd.DataFrame:
    rows = []
    for a in result.assessments:
        if a.classification.category is not Category.DECOMMISSION:
            continue
        volume = landscape.volume.get(a.object_id)
        rows.append({
            "object_id": a.object_id,
            "description": a.bw_object.description,
            "solution_area": a.bw_object.solution_area,
            "business_owner": a.usage.business_owner,
            "last_run_date": a.usage.last_run_date,
            "monthly_executions": a.usage.monthly_executions,
            "distinct_users": a.usage.distinct_users,
            "storage_gb": volume.storage_gb if volume else 0,
            "determinant": a.classification.determinant,
            "rationale": a.classification.rationale,
        })
    return pd.DataFrame(rows)
