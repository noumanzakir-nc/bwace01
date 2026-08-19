# Component Methods — BW-ACE

**Stage**: INCEPTION — Application Design

Signatures and input/output types only. **Business rules, band boundaries, sub-weights, formulas, and evaluation order are deliberately absent** — they are defined in Unit 1 Functional Design (requirements §4.6).

Type names refer to the domain objects declared in C1 `models`, listed in §1.

---

## 1. C1 — `models` (type declarations)

All are frozen dataclasses. Collection fields are `tuple`, never `list`, so instances stay immutable and safe to share across Streamlit reruns.

### Input records

| Type | Fields |
|---|---|
| `BwObject` | `object_id: str`, `object_type: str`, `solution_area: str`, `description: str`, `data_volume_label: str`, `hana_cv_count: int`, `adso_count: int`, `custom_table_count: int` |
| `UsageRecord` | `object_id: str`, `last_run_date: date`, `monthly_executions: int`, `distinct_users: int`, `business_owner: str` |
| `AreaCriticality` | `solution_area: str`, `criticality: int`, `migration_priority: int`, `downtime_tolerance_hours: int` |
| `VolumeMetrics` | `object_id: str`, `record_count: int`, `storage_gb: int`, `load_frequency: str` |
| `ComplexityMetrics` | `object_id: str`, `hana_cv_count: int`, `transformation_count: int`, `custom_logic_present: bool`, `interface_count: int` |
| `DependencyNode` | `node_id: str`, `label: str`, `node_type: str` |
| `DependencyEdge` | `source: str`, `target: str`, `edge_type: str`, `description: str \| None` |

### Aggregate input

| Type | Fields |
|---|---|
| `Landscape` | `objects: tuple[BwObject, ...]`, `usage: Mapping[str, UsageRecord]`, `criticality: Mapping[str, AreaCriticality]`, `volume: Mapping[str, VolumeMetrics]`, `complexity: Mapping[str, ComplexityMetrics]`, `nodes: tuple[DependencyNode, ...]`, `edges: tuple[DependencyEdge, ...]`, `fingerprint: str`, `sources: Mapping[str, str]` |

`sources` records `bundled` or `uploaded` per dataset, for FR-1.3 AC2. `fingerprint` is the cache key described in `services.md`.

### Computed results

| Type | Fields |
|---|---|
| `DimensionScore` | `dimension: str`, `raw_display: str`, `normalised: float`, `weight: float`, `contribution: float`, `inherited_from: str \| None` |
| `AxisScore` | `axis: str`, `total: float`, `dimensions: tuple[DimensionScore, ...]` |
| `Classification` | `category: Category`, `set_by: Determinant`, `rationale: str` |
| `ObjectAssessment` | `object_id: str`, `bw_object: BwObject`, `usage: UsageRecord`, `business_value: AxisScore`, `technical_effort: AxisScore`, `classification: Classification`, `incoming: tuple[DependencyEdge, ...]`, `outgoing: tuple[DependencyEdge, ...]` |
| `LandscapeKpis` | `total_objects: int`, `total_storage_gb: int`, `decommission_pct: float`, `reclaimable_storage_gb: int` |
| `AssessmentResult` | `assessments: tuple[ObjectAssessment, ...]`, `distribution: Mapping[Category, int]`, `graph: DependencyGraph`, `wave_plan: WavePlan`, `kpis: LandscapeKpis`, `scoring_config: ScoringConfig`, `wave_config: WaveConfig`, `fingerprint: str` |

### Dependency and wave structures

| Type | Fields |
|---|---|
| `DependencyGraph` | `nodes: tuple[DependencyNode, ...]`, `edges: tuple[DependencyEdge, ...]`, `out_degree: Mapping[str, int]`, `in_degree: Mapping[str, int]`, `area_matrix: tuple[tuple[int, ...], ...]`, `area_order: tuple[str, ...]`, `layout: Mapping[str, tuple[float, float]]` |
| `WaveRisk` | `score: float`, `band: RiskBand`, `complexity_contribution: float`, `dependency_contribution: float`, `downtime_contribution: float`, `dmk_contribution: float` |
| `Wave` | `number: int`, `start_date: date`, `end_date: date`, `object_ids: tuple[str, ...]`, `risk: WaveRisk` |
| `DependencyViolation` | `dependent_area: str`, `depends_on_area: str`, `dependent_wave: int`, `depends_on_wave: int` |
| `WavePlan` | `waves: tuple[Wave, ...]`, `violations: tuple[DependencyViolation, ...]` |

### Validation and comparison

| Type | Fields |
|---|---|
| `ValidationIssue` | `dataset: str`, `field: str \| None`, `record: str \| None`, `message: str`, `severity: Severity` |
| `ValidationReport` | `issues: tuple[ValidationIssue, ...]`, `is_fatal: bool` |
| `LoadOutcome` | `landscape: Landscape \| None`, `report: ValidationReport` |
| `ScenarioDiff` | `changed: tuple[ClassificationChange, ...]`, `left_distribution: Mapping[Category, int]`, `right_distribution: Mapping[Category, int]` |
| `ClassificationChange` | `object_id: str`, `left_category: Category`, `right_category: Category` |
| `Scenario` | `name: str`, `scoring_config: ScoringConfig`, `wave_config: WaveConfig` |

### Enumerations

| Type | Members |
|---|---|
| `Category` | `DECOMMISSION`, `REPLICATE_AS_IS`, `REBUILD_AS_DATA_PRODUCT` |
| `Determinant` | `SCORE`, `DORMANCY_CEILING`, `ACTIVITY_FLOOR` |
| `RiskBand` | `LOW`, `MEDIUM`, `HIGH` |
| `Severity` | `ERROR`, `WARNING` |

---

## 2. C2 — `config` (constants)

Exposed as module-level frozen dataclass instances. No functions.

| Name | Type | Purpose |
|---|---|---|
| `VALUE_WEIGHTS` | `Mapping[str, float]` | Renormalised Business Value axis weights |
| `EFFORT_WEIGHTS` | `Mapping[str, float]` | Renormalised Technical Effort axis weights |
| `COMPLEXITY_SUBWEIGHTS` | `Mapping[str, float]` | Sub-weights within technical complexity |
| `VOLUME_SUBWEIGHTS` | `Mapping[str, float]` | Sub-weights within data volume |
| `BANDS` | `Mapping[str, tuple[Band, ...]]` | Fixed absolute normalisation bands per dimension |
| `RECENCY_TIERS` | `tuple[RecencyTier, ...]` | Day thresholds and multipliers |
| `DEFAULT_SCORING` | `ScoringConfig` | Threshold and guard rule defaults |
| `DEFAULT_WAVES` | `WaveConfig` | Wave count, duration, start date defaults |
| `RISK_BANDS` | `tuple[RiskBandBoundary, ...]` | Low/Medium/High boundaries |
| `PALETTE` | `Palette` | Brand colours and classification colour roles |
| `DMK_FREEZE_UNTIL` | `date` | The 2028 constraint boundary |

Runtime-adjustable configuration types:

| Type | Fields |
|---|---|
| `ScoringConfig` | `value_threshold: float`, `effort_threshold: float`, `dormancy_days: int`, `dormancy_executions: int`, `activity_days: int`, `activity_executions: int` |
| `WaveConfig` | `wave_count: int`, `wave_months: int`, `start_date: date` |

---

## 3. C3 — `loader`

| Method | Signature | Purpose |
|---|---|---|
| `load_bundled` | `() -> LoadOutcome` | Read all six bundled JSON datasets and validate |
| `load_with_overrides` | `(overrides: Mapping[str, bytes]) -> LoadOutcome` | Load bundled data, replacing named datasets from uploaded bytes |
| `parse_dataset` | `(name: str, payload: bytes) -> tuple[list[dict], ValidationReport]` | Detect CSV or JSON and parse to raw records |
| `validate_objects` | `(records: list[dict]) -> tuple[tuple[BwObject, ...], ValidationReport]` | Structural and type validation of the inventory |
| `validate_usage` | `(records: list[dict]) -> tuple[Mapping[str, UsageRecord], ValidationReport]` | Structural and type validation of usage logs |
| `validate_criticality` | `(records: list[dict]) -> tuple[Mapping[str, AreaCriticality], ValidationReport]` | Structural and type validation of the criticality matrix |
| `validate_volume` | `(records: list[dict]) -> tuple[Mapping[str, VolumeMetrics], ValidationReport]` | Structural and type validation of volume metrics |
| `validate_complexity` | `(records: list[dict]) -> tuple[Mapping[str, ComplexityMetrics], ValidationReport]` | Structural and type validation of complexity scores |
| `validate_dependencies` | `(payload: dict) -> tuple[tuple[DependencyNode, ...], tuple[DependencyEdge, ...], ValidationReport]` | Validate the graph payload |
| `check_referential_integrity` | `(landscape: Landscape) -> ValidationReport` | Cross-dataset checks, including objects lacking a usage record (S1.3 AC4) |
| `fingerprint` | `(datasets: Mapping[str, bytes]) -> str` | Content hash used as the cache key |

**Contract**: no function in this component raises on user-supplied data problems. Every failure is returned as a `ValidationReport`, satisfying NFR-6.4.

---

## 4. C4 — `normalisation`

| Method | Signature | Purpose |
|---|---|---|
| `score_usage_frequency` | `(usage: UsageRecord, reference: date) -> DimensionScore` | Banded executions with the recency factor applied |
| `score_distinct_users` | `(usage: UsageRecord) -> DimensionScore` | Banded distinct user count |
| `score_criticality` | `(area: str, criticality: Mapping[str, AreaCriticality]) -> DimensionScore` | Area criticality, averaged for cross-area objects |
| `score_outgoing_dependencies` | `(area: str, graph: DependencyGraph) -> DimensionScore` | Banded outgoing degree, inherited from the area |
| `score_incoming_dependencies` | `(area: str, graph: DependencyGraph) -> DimensionScore` | Banded incoming degree, inherited from the area |
| `score_complexity` | `(metrics: ComplexityMetrics) -> DimensionScore` | Composite of the four complexity attributes |
| `score_volume` | `(metrics: VolumeMetrics) -> DimensionScore` | Composite of record count, storage, and load frequency |
| `resolve_area_metrics` | `(solution_area: str, criticality: Mapping[str, AreaCriticality], graph: DependencyGraph) -> AreaMetrics` | Resolve inheritance, averaging across constituent areas |
| `apply_band` | `(value: float, bands: tuple[Band, ...]) -> float` | Map a raw value to 0–100 via fixed absolute bands |
| `recency_factor` | `(last_run: date, reference: date) -> float` | Multiplier from elapsed days |

All functions are pure. None takes a `ScoringConfig`, which is the property that makes them cacheable independently of threshold changes.

---

## 5. C5 — `scoring`

| Method | Signature | Purpose |
|---|---|---|
| `business_value` | `(object_id: str, landscape: Landscape, graph: DependencyGraph, reference: date) -> AxisScore` | Weight and sum the five value dimensions |
| `technical_effort` | `(object_id: str, landscape: Landscape) -> AxisScore` | Weight and sum the two effort dimensions |
| `score_all` | `(landscape: Landscape, graph: DependencyGraph) -> Mapping[str, tuple[AxisScore, AxisScore]]` | Both axes for every object |
| `reference_date` | `(landscape: Landscape) -> date` | Latest `last_run_date` in the dataset, for deterministic recency (assumption A-4) |

---

## 6. C6 — `classification`

| Method | Signature | Purpose |
|---|---|---|
| `classify` | `(value: AxisScore, effort: AxisScore, usage: UsageRecord, reference: date, cfg: ScoringConfig) -> Classification` | Full classification including guard rules |
| `classify_by_score` | `(value: AxisScore, effort: AxisScore, cfg: ScoringConfig) -> Category` | Quadrant mapping alone, without guard rules |
| `is_dormant` | `(usage: UsageRecord, reference: date, cfg: ScoringConfig) -> bool` | Dormancy ceiling predicate |
| `is_active` | `(usage: UsageRecord, reference: date, cfg: ScoringConfig) -> bool` | Activity floor predicate |
| `build_rationale` | `(value: AxisScore, effort: AxisScore, category: Category, determinant: Determinant, usage: UsageRecord) -> str` | Plain-language explanation naming dominant factors |
| `distribution` | `(assessments: tuple[ObjectAssessment, ...]) -> Mapping[Category, int]` | Counts per category |

`classify_by_score` is exposed separately so that story S2.3 AC6 — that guard rules change exactly two objects — is directly testable by comparing against `classify`.

---

## 7. C7 — `dependencies`

| Method | Signature | Purpose |
|---|---|---|
| `build_graph` | `(nodes: tuple[DependencyNode, ...], edges: tuple[DependencyEdge, ...], areas: tuple[str, ...]) -> DependencyGraph` | Construct the graph and expand the `ALL` wildcard |
| `expand_wildcards` | `(edges: tuple[DependencyEdge, ...], areas: tuple[str, ...]) -> tuple[DependencyEdge, ...]` | Replace `ALL` sources with one edge per area |
| `area_matrix` | `(graph: DependencyGraph) -> tuple[tuple[int, ...], ...]` | Area-by-area adjacency for the heatmap |
| `edges_for_object` | `(obj: BwObject, graph: DependencyGraph) -> tuple[tuple[DependencyEdge, ...], tuple[DependencyEdge, ...]]` | Incoming and outgoing edges resolved via solution area |
| `constituent_areas` | `(solution_area: str, known_areas: tuple[str, ...]) -> tuple[str, ...]` | Split a composite area label into its constituents |
| `compute_layout` | `(graph: DependencyGraph) -> Mapping[str, tuple[float, float]]` | Node coordinates for the network view |

---

## 8. C8 — `waves`

| Method | Signature | Purpose |
|---|---|---|
| `plan_waves` | `(assessments: tuple[ObjectAssessment, ...], landscape: Landscape, graph: DependencyGraph, cfg: WaveConfig) -> WavePlan` | Full wave plan with risk and violations |
| `assign_waves` | `(assessments: tuple[ObjectAssessment, ...], landscape: Landscape, cfg: WaveConfig) -> Mapping[int, tuple[str, ...]]` | Priority-led assignment |
| `wave_dates` | `(number: int, cfg: WaveConfig) -> tuple[date, date]` | Start and end for a wave |
| `detect_violations` | `(assignment: Mapping[int, tuple[str, ...]], landscape: Landscape, graph: DependencyGraph) -> tuple[DependencyViolation, ...]` | Dependency ordering breaches |
| `wave_risk` | `(object_ids: tuple[str, ...], landscape: Landscape, violations: tuple[DependencyViolation, ...], end_date: date) -> WaveRisk` | Composite risk with per-factor contributions |
| `risk_band` | `(score: float) -> RiskBand` | Band a risk score |

---

## 9. C9 — `export`

| Method | Signature | Purpose |
|---|---|---|
| `classification_csv` | `(result: AssessmentResult) -> str` | CSV text, one row per object, configuration embedded |
| `wave_recommendation_json` | `(result: AssessmentResult) -> dict` | JSON-serialisable wave plan with configuration embedded |
| `config_summary` | `(scoring: ScoringConfig, waves: WaveConfig) -> dict` | Configuration block shared by both exports |

---

## 10. C10 — `assessment_service`

| Method | Signature | Purpose |
|---|---|---|
| `assess` | `(landscape: Landscape, scoring: ScoringConfig, waves: WaveConfig) -> AssessmentResult` | Full orchestration |
| `compute_base` | `(landscape: Landscape) -> BaseScores` | Dataset-dependent stages only: graph, normalisation, axis scores. The cached seam. |
| `apply_config` | `(base: BaseScores, landscape: Landscape, scoring: ScoringConfig, waves: WaveConfig) -> AssessmentResult` | Threshold-dependent stages: classification, distribution, KPIs, wave plan |
| `compare` | `(landscape: Landscape, left: Scenario, right: Scenario) -> ScenarioDiff` | Diff two configurations |
| `kpis` | `(assessments: tuple[ObjectAssessment, ...], landscape: Landscape) -> LandscapeKpis` | Landscape headline figures |

`BaseScores` holds `graph: DependencyGraph`, `axis_scores: Mapping[str, tuple[AxisScore, AxisScore]]`, and `reference_date: date`. The split between `compute_base` and `apply_config` is the Q4=B caching strategy expressed as an interface.

---

## 11. Unit 2 — Presentation Method Sketches

Signatures here are indicative. Final shape is settled in Unit 2 Functional Design.

### C12 — `frames`

| Method | Signature |
|---|---|
| `assessments_frame` | `(result: AssessmentResult) -> DataFrame` |
| `derivation_frame` | `(assessment: ObjectAssessment) -> DataFrame` |
| `gantt_frame` | `(plan: WavePlan) -> DataFrame` |
| `heatmap_frame` | `(graph: DependencyGraph) -> DataFrame` |
| `candidates_frame` | `(result: AssessmentResult) -> DataFrame` |

### C13 — `charts`

| Method | Signature |
|---|---|
| `classification_donut` | `(result: AssessmentResult) -> Figure` |
| `top_value_bar` | `(result: AssessmentResult, limit: int) -> Figure` |
| `quadrant_scatter` | `(result: AssessmentResult) -> Figure` |
| `dependency_heatmap` | `(graph: DependencyGraph) -> Figure` |
| `dependency_network` | `(graph: DependencyGraph) -> Figure` |
| `wave_gantt` | `(plan: WavePlan, freeze_until: date) -> Figure` |

### C14 — `widgets`

| Method | Signature |
|---|---|
| `kpi_strip` | `(kpis: LandscapeKpis) -> None` |
| `classification_badge` | `(classification: Classification) -> None` |
| `guard_rule_badge` | `(determinant: Determinant) -> None` |
| `derivation_table` | `(assessment: ObjectAssessment) -> None` |
| `scoring_controls` | `(current: ScoringConfig) -> ScoringConfig` |
| `wave_controls` | `(current: WaveConfig) -> WaveConfig` |
| `validation_panel` | `(report: ValidationReport) -> None` |

### C15 — `views`

Each view exposes `render(result: AssessmentResult) -> None`. `scenario_compare` exposes `render(landscape: Landscape, scenarios: tuple[Scenario, ...]) -> None`.

### C16 — `app`

| Method | Signature |
|---|---|
| `main` | `() -> None` |
| `sidebar_navigation` | `() -> str` |
| `data_source_controls` | `() -> Mapping[str, bytes]` |

---

## 12. Testability Summary

Pure functions, directly unit-testable without any fixture beyond input data:

- All of C4 `normalisation`
- All of C5 `scoring`
- All of C6 `classification`
- All of C7 `dependencies`
- All of C8 `waves`
- All of C9 `export`
- C10 `compute_base`, `apply_config`, `compare`, `kpis`
- C3 validation functions, given byte payloads
- C12 `frames`, given a result object

This covers every requirement carrying a reference-data acceptance criterion, satisfying NFR-7.1 and NFR-7.2. Only C11, C13, C14, C15, and C16 require Streamlit and are therefore limited to the smoke tests of NFR-7.3.
