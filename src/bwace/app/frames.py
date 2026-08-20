"""The only pandas-touching module. Domain objects to DataFrames. See domain-entities.md #4."""
from __future__ import annotations

from typing import Sequence

import pandas as pd

from bwace.engine.config import ODATA_ENV_VARS, ODATA_LIVE_DATASETS
from bwace.engine.odata import EndpointResult, OdataSettings
from bwace.engine.models import (
    AssessmentResult,
    Category,
    DependencyGraph,
    Landscape,
    ObjectAssessment,
    Scenario,
    ScenarioDiff,
    WavePlan,
)

# Canonical dataset labels. Single definition so the sidebar, the Source Data
# view and the Connection Settings view cannot drift apart.
DATASET_LABELS: dict[str, str] = {
    "object_inventory": "Object Inventory",
    "usage_logs": "Usage Logs",
    "criticality": "Criticality Matrix",
    "dependencies": "Dependency Map",
    "data_volume": "Data Volume Metrics",
    "complexity": "Complexity Scores",
}


def object_inventory_frame(landscape: Landscape) -> pd.DataFrame:
    rows = [{
        "object_id": o.object_id, "object_type": o.object_type, "solution_area": o.solution_area,
        "description": o.description, "data_volume_label": o.data_volume_label,
        "hana_cv_count": o.hana_cv_count, "adso_count": o.adso_count,
        "custom_table_count": o.custom_table_count,
    } for o in landscape.objects]
    return pd.DataFrame(rows)


def usage_logs_frame(landscape: Landscape) -> pd.DataFrame:
    rows = [{
        "object_id": u.object_id, "last_run_date": u.last_run_date,
        "monthly_executions": u.monthly_executions, "distinct_users": u.distinct_users,
        "business_owner": u.business_owner,
    } for u in landscape.usage.values()]
    return pd.DataFrame(rows)


def criticality_frame(landscape: Landscape) -> pd.DataFrame:
    rows = [{
        "solution_area": c.solution_area, "criticality": c.criticality,
        "migration_priority": c.migration_priority,
        "downtime_tolerance_hours": c.downtime_tolerance_hours,
    } for c in landscape.criticality.values()]
    return pd.DataFrame(rows)


def data_volume_frame(landscape: Landscape) -> pd.DataFrame:
    rows = [{
        "object_id": v.object_id, "record_count": v.record_count, "storage_gb": v.storage_gb,
        "load_frequency": v.load_frequency,
    } for v in landscape.volume.values()]
    return pd.DataFrame(rows)


def complexity_frame(landscape: Landscape) -> pd.DataFrame:
    rows = [{
        "object_id": c.object_id, "hana_cv_count": c.hana_cv_count,
        "transformation_count": c.transformation_count,
        "custom_logic_present": c.custom_logic_present, "interface_count": c.interface_count,
    } for c in landscape.complexity.values()]
    return pd.DataFrame(rows)


def dependency_nodes_frame(landscape: Landscape) -> pd.DataFrame:
    rows = [{
        "node_id": n.node_id, "label": n.label, "node_type": n.node_type.value,
    } for n in landscape.nodes]
    return pd.DataFrame(rows)


def dependency_edges_frame(landscape: Landscape) -> pd.DataFrame:
    rows = [{
        "source": e.source, "target": e.target, "edge_type": e.edge_type.value,
        "description": e.description,
    } for e in landscape.edges]
    return pd.DataFrame(rows)


def distribution_frame(diff: ScenarioDiff) -> pd.DataFrame:
    categories = sorted(
        set(diff.left_distribution) | set(diff.right_distribution), key=lambda c: c.value,
    )
    rows = [{
        "category": c.value.replace("_", " ").title(),
        diff.left_name: diff.left_distribution.get(c, 0),
        diff.right_name: diff.right_distribution.get(c, 0),
    } for c in categories]
    return pd.DataFrame(rows)


def scenario_config_frame(left: Scenario, right: Scenario) -> pd.DataFrame:
    labels = {
        "value_threshold": "Value Threshold", "effort_threshold": "Effort Threshold",
        "dormancy_days": "Dormancy Days", "dormancy_executions": "Dormancy Executions",
        "activity_days": "Activity Days", "activity_executions": "Activity Executions",
        "wave_count": "Wave Count", "wave_months": "Wave Months", "start_date": "Wave Start Date",
    }
    rows = []
    for scoring_field, label in labels.items():
        if scoring_field in ("wave_count", "wave_months", "start_date"):
            l_value = getattr(left.wave_config, scoring_field)
            r_value = getattr(right.wave_config, scoring_field)
        else:
            l_value = getattr(left.scoring_config, scoring_field)
            r_value = getattr(right.scoring_config, scoring_field)
        # Values span int and date across rows within the same column (e.g. start_date
        # alongside wave_count); Arrow cannot infer one type for a mixed-type object
        # column, so every value is rendered as a display string (display-only table).
        rows.append({"parameter": label, left.name: str(l_value), right.name: str(r_value)})
    return pd.DataFrame(rows)


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
            "risk_band_label": wave.risk.band.value.title(),
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


# ---- Connection Settings frames (requirements §10, FR-15.2) ----------------


def endpoint_status_frame(endpoints: Sequence[EndpointResult]) -> pd.DataFrame:
    rows = [{
        "dataset": DATASET_LABELS.get(e.dataset, e.dataset),
        "status": e.status.value,
        "records": str(e.record_count) if e.record_count else "-",
        "detail": e.detail,
        "url": e.url,
    } for e in endpoints]
    return pd.DataFrame(rows, columns=["dataset", "status", "records", "detail", "url"])


def endpoint_config_frame(settings: OdataSettings) -> pd.DataFrame:
    rows = [{
        "dataset": DATASET_LABELS.get(dataset, dataset),
        "service path": settings.service_paths[dataset],
        "resolved collection URL": settings.collection_url(dataset) if settings.base_url else "(base URL not set)",
    } for dataset in ODATA_LIVE_DATASETS]
    rows.append({
        "dataset": DATASET_LABELS["criticality"],
        "service path": "(no live source)",
        "resolved collection URL": "bundled or uploaded file - business judgement matrix",
    })
    return pd.DataFrame(rows, columns=["dataset", "service path", "resolved collection URL"])


def environment_frame(settings: OdataSettings) -> pd.DataFrame:
    """Presence only. Values are never rendered (NFR-9.2)."""
    rows = [
        {"variable": ODATA_ENV_VARS["base_url"], "set": _yes_no(bool(settings.base_url)),
         "effective value": settings.base_url or "(not set)"},
        {"variable": ODATA_ENV_VARS["user"], "set": _yes_no(settings.user_set), "effective value": "(hidden)"},
        {"variable": ODATA_ENV_VARS["password"], "set": _yes_no(settings.password_set), "effective value": "(hidden)"},
        {"variable": ODATA_ENV_VARS["service_root"], "set": _yes_no(True),
         "effective value": settings.service_root},
        {"variable": ODATA_ENV_VARS["ca_bundle"], "set": _yes_no(bool(settings.ca_bundle)),
         "effective value": settings.ca_bundle or "(system trust store)"},
        {"variable": ODATA_ENV_VARS["timeout"], "set": _yes_no(True),
         "effective value": f"{settings.timeout_seconds:g} s"},
        {"variable": ODATA_ENV_VARS["max_records"], "set": _yes_no(True),
         "effective value": str(settings.max_records)},
    ]
    return pd.DataFrame(rows, columns=["variable", "set", "effective value"])


def provenance_frame(landscape: Landscape) -> pd.DataFrame:
    rows = [{
        "dataset": DATASET_LABELS.get(name, name),
        "provenance": landscape.sources.get(name, "bundled"),
    } for name in DATASET_LABELS]
    return pd.DataFrame(rows, columns=["dataset", "provenance"])


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"
