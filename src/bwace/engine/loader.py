"""Parse, validate, and assemble the Landscape from bundled or uploaded datasets. See BR-11."""
from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from bwace.engine.models import (
    AreaCriticality,
    BwObject,
    ComplexityMetrics,
    DependencyEdge,
    DependencyNode,
    EdgeType,
    Landscape,
    LoadOutcome,
    NodeType,
    Severity,
    UsageRecord,
    ValidationIssue,
    ValidationReport,
    VolumeMetrics,
)

DATA_DIR = Path(__file__).resolve().parents[3] / "data"

DATASET_FILES = {
    "object_inventory": "object_inventory.json",
    "usage_logs": "usage_logs.json",
    "criticality": "criticality.json",
    "dependencies": "dependencies.json",
    "data_volume": "data_volume.json",
    "complexity": "complexity.json",
}


def fingerprint(datasets: dict[str, bytes]) -> str:
    hasher = hashlib.sha256()
    for name in sorted(datasets):
        hasher.update(name.encode("utf-8"))
        hasher.update(datasets[name])
    return hasher.hexdigest()


def parse_dataset(name: str, payload: bytes) -> tuple[Any, ValidationReport]:
    try:
        return json.loads(payload.decode("utf-8")), ValidationReport()
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass
    try:
        import csv
        import io

        text = payload.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        return list(reader), ValidationReport()
    except (UnicodeDecodeError, csv.Error):
        issue = ValidationIssue(
            dataset=name, field=None, record=None,
            message=f"Dataset '{name}' is neither valid JSON nor valid CSV.",
            severity=Severity.ERROR,
        )
        return None, ValidationReport(issues=(issue,))


def _require(record: dict, field_name: str, dataset: str, record_id: str | None, issues: list[ValidationIssue]) -> Any:
    if field_name not in record or record[field_name] is None:
        issues.append(ValidationIssue(
            dataset=dataset, field=field_name, record=record_id,
            message=f"Missing required field '{field_name}' in dataset '{dataset}'.",
            severity=Severity.ERROR,
        ))
        return None
    return record[field_name]


def _parse_date(value: str, dataset: str, record_id: str, field_name: str, issues: list[ValidationIssue]) -> date | None:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        issues.append(ValidationIssue(
            dataset=dataset, field=field_name, record=record_id,
            message=f"Field '{field_name}' on record '{record_id}' is not a valid ISO-8601 date.",
            severity=Severity.ERROR,
        ))
        return None


def _require_non_negative(value: Any, dataset: str, record_id: str, field_name: str, issues: list[ValidationIssue]) -> None:
    if isinstance(value, (int, float)) and value < 0:
        issues.append(ValidationIssue(
            dataset=dataset, field=field_name, record=record_id,
            message=f"Field '{field_name}' on record '{record_id}' must not be negative.",
            severity=Severity.ERROR,
        ))


def validate_objects(records: list[dict]) -> tuple[tuple[BwObject, ...], ValidationReport]:
    issues: list[ValidationIssue] = []
    objects: list[BwObject] = []
    for rec in records:
        record_id = rec.get("object_id")
        fields = ["object_id", "object_type", "solution_area", "description",
                  "data_volume_label", "hana_cv_count", "adso_count", "custom_table_count"]
        values = {f: _require(rec, f, "object_inventory", record_id, issues) for f in fields}
        if any(v is None for v in values.values()):
            continue
        for f in ("hana_cv_count", "adso_count", "custom_table_count"):
            _require_non_negative(values[f], "object_inventory", record_id, f, issues)
        objects.append(BwObject(**values))
    return tuple(objects), ValidationReport(issues=tuple(issues))


def validate_usage(records: list[dict]) -> tuple[dict[str, UsageRecord], ValidationReport]:
    issues: list[ValidationIssue] = []
    usage: dict[str, UsageRecord] = {}
    for rec in records:
        record_id = rec.get("object_id")
        fields = ["object_id", "last_run_date", "monthly_executions", "distinct_users", "business_owner"]
        values = {f: _require(rec, f, "usage_logs", record_id, issues) for f in fields}
        if any(v is None for v in values.values()):
            continue
        parsed_date = _parse_date(values["last_run_date"], "usage_logs", record_id, "last_run_date", issues)
        if parsed_date is None:
            continue
        values["last_run_date"] = parsed_date
        _require_non_negative(values["monthly_executions"], "usage_logs", record_id, "monthly_executions", issues)
        _require_non_negative(values["distinct_users"], "usage_logs", record_id, "distinct_users", issues)
        usage[record_id] = UsageRecord(**values)
    return usage, ValidationReport(issues=tuple(issues))


def validate_criticality(records: list[dict]) -> tuple[dict[str, AreaCriticality], ValidationReport]:
    issues: list[ValidationIssue] = []
    criticality: dict[str, AreaCriticality] = {}
    for rec in records:
        record_id = rec.get("solution_area")
        fields = ["solution_area", "criticality", "migration_priority", "downtime_tolerance_hours"]
        values = {f: _require(rec, f, "criticality", record_id, issues) for f in fields}
        if any(v is None for v in values.values()):
            continue
        criticality[record_id] = AreaCriticality(**values)
    return criticality, ValidationReport(issues=tuple(issues))


def validate_volume(records: list[dict]) -> tuple[dict[str, VolumeMetrics], ValidationReport]:
    issues: list[ValidationIssue] = []
    volume: dict[str, VolumeMetrics] = {}
    for rec in records:
        record_id = rec.get("object_id")
        fields = ["object_id", "record_count", "storage_gb", "load_frequency"]
        values = {f: _require(rec, f, "data_volume", record_id, issues) for f in fields}
        if any(v is None for v in values.values()):
            continue
        if values["load_frequency"] not in ("Monthly", "Weekly", "Daily", "Hourly"):
            issues.append(ValidationIssue(
                dataset="data_volume", field="load_frequency", record=record_id,
                message=f"Unknown load_frequency '{values['load_frequency']}' on record '{record_id}'; scores 0.",
                severity=Severity.WARNING,
            ))
        _require_non_negative(values["record_count"], "data_volume", record_id, "record_count", issues)
        _require_non_negative(values["storage_gb"], "data_volume", record_id, "storage_gb", issues)
        volume[record_id] = VolumeMetrics(**values)
    return volume, ValidationReport(issues=tuple(issues))


def validate_complexity(records: list[dict]) -> tuple[dict[str, ComplexityMetrics], ValidationReport]:
    issues: list[ValidationIssue] = []
    complexity: dict[str, ComplexityMetrics] = {}
    for rec in records:
        record_id = rec.get("object_id")
        fields = ["object_id", "hana_cv_count", "transformation_count", "custom_logic_present", "interface_count"]
        values = {f: _require(rec, f, "complexity", record_id, issues) for f in fields}
        if any(v is None for v in values.values()):
            continue
        for f in ("hana_cv_count", "transformation_count", "interface_count"):
            _require_non_negative(values[f], "complexity", record_id, f, issues)
        complexity[record_id] = ComplexityMetrics(**values)
    return complexity, ValidationReport(issues=tuple(issues))


def validate_dependencies(payload: dict) -> tuple[tuple[DependencyNode, ...], tuple[DependencyEdge, ...], ValidationReport]:
    issues: list[ValidationIssue] = []
    nodes: list[DependencyNode] = []
    known_ids: set[str] = set()
    for rec in payload.get("nodes", []):
        node_id = rec.get("node_id")
        fields = ["node_id", "label", "node_type"]
        values = {f: _require(rec, f, "dependencies", node_id, issues) for f in fields}
        if any(v is None for v in values.values()):
            continue
        try:
            values["node_type"] = NodeType(values["node_type"])
        except ValueError:
            issues.append(ValidationIssue(
                dataset="dependencies", field="node_type", record=node_id,
                message=f"Unknown node_type '{values['node_type']}' on node '{node_id}'.",
                severity=Severity.ERROR,
            ))
            continue
        nodes.append(DependencyNode(**values))
        known_ids.add(values["node_id"])

    edges: list[DependencyEdge] = []
    for rec in payload.get("edges", []):
        source = rec.get("source")
        target = rec.get("target")
        edge_type_raw = rec.get("edge_type")
        if source is None or target is None or edge_type_raw is None:
            issues.append(ValidationIssue(
                dataset="dependencies", field=None, record=f"{source}->{target}",
                message="Edge missing source, target, or edge_type.",
                severity=Severity.ERROR,
            ))
            continue
        if target not in known_ids or (source != "ALL" and source not in known_ids):
            issues.append(ValidationIssue(
                dataset="dependencies", field=None, record=f"{source}->{target}",
                message=f"Edge references an unknown node ('{source}' -> '{target}'); dropped.",
                severity=Severity.WARNING,
            ))
            continue
        try:
            edge_type = EdgeType(edge_type_raw)
        except ValueError:
            issues.append(ValidationIssue(
                dataset="dependencies", field="edge_type", record=f"{source}->{target}",
                message=f"Unknown edge_type '{edge_type_raw}'; dropped.",
                severity=Severity.WARNING,
            ))
            continue
        edges.append(DependencyEdge(source=source, target=target, edge_type=edge_type,
                                     description=rec.get("description")))
    return tuple(nodes), tuple(edges), ValidationReport(issues=tuple(issues))


def check_referential_integrity(
    objects: tuple[BwObject, ...],
    usage: dict[str, UsageRecord],
    criticality: dict[str, AreaCriticality],
    volume: dict[str, VolumeMetrics],
    complexity: dict[str, ComplexityMetrics],
) -> ValidationReport:
    issues: list[ValidationIssue] = []
    for obj in objects:
        if obj.object_id not in usage:
            issues.append(ValidationIssue(
                dataset="usage_logs", field=None, record=obj.object_id,
                message=f"Object '{obj.object_id}' has no usage record; usage dimensions score 0.",
                severity=Severity.WARNING,
            ))
        if obj.object_id not in volume or obj.object_id not in complexity:
            issues.append(ValidationIssue(
                dataset="data_volume/complexity", field=None, record=obj.object_id,
                message=f"Object '{obj.object_id}' is missing volume or complexity data; those dimensions score 0.",
                severity=Severity.WARNING,
            ))
        for area in obj.solution_area.split("/"):
            if area not in criticality:
                issues.append(ValidationIssue(
                    dataset="criticality", field="solution_area", record=obj.object_id,
                    message=f"Solution area '{area}' referenced by '{obj.object_id}' is not in the criticality matrix.",
                    severity=Severity.ERROR,
                ))
        inv_hana = obj.hana_cv_count
        cmp = complexity.get(obj.object_id)
        if cmp is not None and cmp.hana_cv_count != inv_hana:
            issues.append(ValidationIssue(
                dataset="object_inventory/complexity", field="hana_cv_count", record=obj.object_id,
                message=(f"hana_cv_count differs between inventory ({inv_hana}) and complexity "
                         f"({cmp.hana_cv_count}) for '{obj.object_id}'; complexity value is used."),
                severity=Severity.WARNING,
            ))
    return ValidationReport(issues=tuple(issues))


def _load_all(read: dict[str, bytes], uploaded_names: frozenset[str] = frozenset()) -> LoadOutcome:
    all_issues: list[ValidationIssue] = []

    inv_raw, r = parse_dataset("object_inventory", read["object_inventory"])
    all_issues.extend(r.issues)
    objects, r = validate_objects(inv_raw or [])
    all_issues.extend(r.issues)

    usage_raw, r = parse_dataset("usage_logs", read["usage_logs"])
    all_issues.extend(r.issues)
    usage, r = validate_usage(usage_raw or [])
    all_issues.extend(r.issues)

    crit_raw, r = parse_dataset("criticality", read["criticality"])
    all_issues.extend(r.issues)
    criticality, r = validate_criticality(crit_raw or [])
    all_issues.extend(r.issues)

    vol_raw, r = parse_dataset("data_volume", read["data_volume"])
    all_issues.extend(r.issues)
    volume, r = validate_volume(vol_raw or [])
    all_issues.extend(r.issues)

    cmp_raw, r = parse_dataset("complexity", read["complexity"])
    all_issues.extend(r.issues)
    complexity, r = validate_complexity(cmp_raw or [])
    all_issues.extend(r.issues)

    dep_raw, r = parse_dataset("dependencies", read["dependencies"])
    all_issues.extend(r.issues)
    nodes, edges, r = validate_dependencies(dep_raw or {})
    all_issues.extend(r.issues)

    if not any(i.severity is Severity.ERROR for i in all_issues):
        r = check_referential_integrity(objects, usage, criticality, volume, complexity)
        all_issues.extend(r.issues)

    report = ValidationReport(issues=tuple(all_issues))
    if report.is_fatal:
        return LoadOutcome(landscape=None, report=report)

    landscape = Landscape(
        objects=objects,
        usage=usage,
        criticality=criticality,
        volume=volume,
        complexity=complexity,
        nodes=nodes,
        edges=edges,
        fingerprint=fingerprint(read),
        sources={name: ("uploaded" if name in uploaded_names else "bundled") for name in DATASET_FILES},
    )
    return LoadOutcome(landscape=landscape, report=report)


def load_bundled() -> LoadOutcome:
    read = {name: (DATA_DIR / filename).read_bytes() for name, filename in DATASET_FILES.items()}
    return _load_all(read)


def load_with_overrides(overrides: dict[str, bytes]) -> LoadOutcome:
    read = {name: (DATA_DIR / filename).read_bytes() for name, filename in DATASET_FILES.items()}
    read.update(overrides)
    return _load_all(read, uploaded_names=frozenset(overrides))
