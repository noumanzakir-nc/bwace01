# Domain Entities — Unit 1 `assessment-engine`

**Phase**: 🟢 CONSTRUCTION — Functional Design
**Technology-agnostic**: no library, framework, or storage concern appears here.

---

## 1. Entity Overview

| Group | Entities |
|---|---|
| Input records | `BwObject`, `UsageRecord`, `AreaCriticality`, `VolumeMetrics`, `ComplexityMetrics`, `DependencyNode`, `DependencyEdge` |
| Aggregate input | `Landscape` |
| Configuration | `ScoringConfig`, `WaveConfig`, `Scenario` |
| Computed | `DimensionScore`, `AxisScore`, `Classification`, `ObjectAssessment`, `LandscapeKpis`, `AssessmentResult` |
| Graph | `DependencyGraph` |
| Planning | `Wave`, `WaveRisk`, `DependencyViolation`, `WavePlan` |
| Validation | `ValidationIssue`, `ValidationReport`, `LoadOutcome` |
| Comparison | `ClassificationChange`, `ScenarioDiff` |
| Enumerations | `Category`, `Determinant`, `RiskBand`, `Severity`, `EdgeType`, `NodeType` |

**Universal rules**

- Every entity is **immutable** once constructed. Nothing mutates after creation.
- Collection fields are **ordered, fixed sequences**, never mutable lists. Immutability is what makes a computed result safe to cache and safe to share across several consumers in one pass.
- Every entity is comparable by value, not identity.

---

## 2. Input Entities

### BwObject

One BW object in the landscape.

| Field | Type | Constraint |
|---|---|---|
| `object_id` | text | Required, unique across the inventory. Identity field. |
| `object_type` | text | Required. Observed values: `Query`, `Custom Table`. Displayed only, never scored (assumption A-6). |
| `solution_area` | text | Required. Either a known area name or a composite of two, separated by `/`. |
| `description` | text | Required, non-empty. |
| `data_volume_label` | text | Required. Observed: `Low`, `Medium`, `High`, `Very High`. Displayed only — the Volume dimension uses `VolumeMetrics`, not this label. |
| `hana_cv_count` | integer | ≥ 0 |
| `adso_count` | integer | ≥ 0. Not scored (Q2=A retained the documented complexity attributes only). |
| `custom_table_count` | integer | ≥ 0. Not scored. |

**Count**: 22 in the bundled dataset, across 12 solution areas. `ZMD1` is one of the 22 and is the only composite-area object.

### UsageRecord

| Field | Type | Constraint |
|---|---|---|
| `object_id` | text | Required, must match a `BwObject` |
| `last_run_date` | date | Required, must parse as ISO-8601 |
| `monthly_executions` | integer | ≥ 0 |
| `distinct_users` | integer | ≥ 0 |
| `business_owner` | text | Required. Displayed only, never scored (assumption A-5). |

### AreaCriticality

| Field | Type | Constraint |
|---|---|---|
| `solution_area` | text | Required, unique. Identity field. |
| `criticality` | integer | 0–100. Used directly as a dimension score, no normalisation. |
| `migration_priority` | integer | 1–5. Wave planning only, never classification (assumption A-7). |
| `downtime_tolerance_hours` | integer | > 0. Wave risk only, never classification. |

**Count**: 12 records.

### VolumeMetrics

| Field | Type | Constraint |
|---|---|---|
| `object_id` | text | Required, must match a `BwObject` |
| `record_count` | integer | ≥ 0 |
| `storage_gb` | integer | ≥ 0 |
| `load_frequency` | text | One of `Monthly`, `Weekly`, `Daily`, `Hourly` |

### ComplexityMetrics

| Field | Type | Constraint |
|---|---|---|
| `object_id` | text | Required, must match a `BwObject` |
| `hana_cv_count` | integer | ≥ 0 |
| `transformation_count` | integer | ≥ 0 |
| `custom_logic_present` | boolean | Required |
| `interface_count` | integer | ≥ 0 |

**Note**: `hana_cv_count` appears in both `BwObject` and `ComplexityMetrics`. The complexity dimension uses the `ComplexityMetrics` value. Where they disagree, validation raises a warning naming both.

### DependencyNode

| Field | Type | Constraint |
|---|---|---|
| `node_id` | text | Required, unique. Identity field. |
| `label` | text | Required |
| `node_type` | `NodeType` | Required |

**Count**: 16 nodes — 12 solution areas plus `FF`, `DMK`, `ZMD1`, `SAPPS1`.

### DependencyEdge

| Field | Type | Constraint |
|---|---|---|
| `source` | text | Required. A `node_id`, or the literal `ALL`. |
| `target` | text | Required. A `node_id`. |
| `edge_type` | `EdgeType` | Required |
| `description` | text or absent | Optional |

**Count**: 21 declared edges. After `ALL` expansion, 32 — the single `ALL → DMK` edge becomes 12.

---

## 3. Aggregate Input

### Landscape

The complete validated input set. Constructing one is proof that validation passed.

| Field | Type | Purpose |
|---|---|---|
| `objects` | sequence of `BwObject` | Ordered as loaded |
| `usage` | lookup by `object_id` → `UsageRecord` | |
| `criticality` | lookup by `solution_area` → `AreaCriticality` | |
| `volume` | lookup by `object_id` → `VolumeMetrics` | |
| `complexity` | lookup by `object_id` → `ComplexityMetrics` | |
| `nodes` | sequence of `DependencyNode` | |
| `edges` | sequence of `DependencyEdge` | As declared, before `ALL` expansion |
| `fingerprint` | text | Content hash of the source bytes. Cache key. |
| `sources` | lookup by dataset name → `bundled` or `uploaded` | Satisfies S1.2 AC2 |

**Invariant**: a `Landscape` cannot be constructed while any fatal validation issue exists.

---

## 4. Configuration Entities

### ScoringConfig

Runtime-adjustable. Passed in, never read from global state.

| Field | Type | Default | Constraint |
|---|---|---|---|
| `value_threshold` | number | 33 | 0–100 |
| `effort_threshold` | number | 67 | 0–100 |
| `dormancy_days` | integer | 180 | > 0 |
| `dormancy_executions` | integer | 5 | ≥ 0 |
| `activity_days` | integer | 90 | > 0 |
| `activity_executions` | integer | 25 | ≥ 0 |

**Invariant**: `activity_days` < `dormancy_days`. This is what guarantees the two guard rules cannot both fire — see business rule BR-6.4.

### WaveConfig

| Field | Type | Default | Constraint |
|---|---|---|---|
| `wave_count` | integer | 5 | 1–10 |
| `wave_months` | integer | 3 | 1–12 |
| `start_date` | date | 2027-01-01 | any |

### Scenario

| Field | Type |
|---|---|
| `name` | text, non-empty |
| `scoring_config` | `ScoringConfig` |
| `wave_config` | `WaveConfig` |

---

## 5. Computed Entities

### DimensionScore

One scoring dimension for one object, carrying its full derivation so the UI can display it without recomputation.

| Field | Type | Purpose |
|---|---|---|
| `dimension` | text | Stable identifier, e.g. `usage_frequency` |
| `raw_display` | text | The raw input in human-readable form, e.g. `280 executions, last run 2026-08-13` |
| `normalised` | number | 0–100 |
| `weight` | number | The axis weight applied |
| `contribution` | number | `normalised × weight` |
| `inherited_from` | text or absent | Solution area name when the value was inherited, otherwise absent |

**Invariant**: `contribution` equals `normalised × weight` to within floating-point tolerance.

### AxisScore

| Field | Type | Constraint |
|---|---|---|
| `axis` | text | `business_value` or `technical_effort` |
| `total` | number | 0–100 |
| `dimensions` | sequence of `DimensionScore` | 5 for value, 2 for effort |

**Invariant**: `total` equals the sum of its dimensions' contributions.

### Classification

| Field | Type | Purpose |
|---|---|---|
| `category` | `Category` | The recommendation |
| `determinant` | `Determinant` | What actually decided it |
| `is_dormant` | boolean | Dormancy predicate result, independent of whether it changed the outcome |
| `is_active` | boolean | Activity predicate result, independent of whether it changed the outcome |
| `rationale` | text | Plain-language explanation |

**Design note on `determinant` versus the predicate flags.** This separation exists because validation showed the two differ. In the bundled dataset the dormancy predicate is true for `IN200`, `TR200` and `TM100`, but only `IN200` has its category *changed* by it — `TR200` and `TM100` are already below the Value threshold, so the ceiling merely agrees with the score.

`determinant` therefore records the **effective cause**: a guard rule only where that rule changed the outcome relative to pure score classification, otherwise `SCORE`. The predicate flags are recorded separately so that dormancy remains visible on `TR200` and `TM100` without falsely implying an override.

This makes the guard-rule badge meaningful — it marks the two genuinely overridden objects — while a dormancy note can still appear on all three dormant objects.

### ObjectAssessment

| Field | Type |
|---|---|
| `object_id` | text |
| `bw_object` | `BwObject` |
| `usage` | `UsageRecord` |
| `business_value` | `AxisScore` |
| `technical_effort` | `AxisScore` |
| `classification` | `Classification` |
| `incoming` | sequence of `DependencyEdge` |
| `outgoing` | sequence of `DependencyEdge` |

### LandscapeKpis

| Field | Type | Derivation |
|---|---|---|
| `total_objects` | integer | Count of assessments |
| `total_storage_gb` | integer | Sum of `storage_gb` across all objects |
| `decommission_pct` | number | Decommission count ÷ total × 100 |
| `reclaimable_storage_gb` | integer | Sum of `storage_gb` across Decommission objects only |

Bundled dataset at defaults: 22 objects, 604 GB, 18.2%, 21 GB. (Corrected 2026-08-18 during Code Generation: the storage total was mis-summed by hand as 596; the exact sum of `storage_gb` across all 22 records in source §3.5 is 604. Reclaimable storage and decommission percentage were unaffected.)

### AssessmentResult

| Field | Type |
|---|---|
| `assessments` | sequence of `ObjectAssessment` |
| `distribution` | lookup by `Category` → count |
| `graph` | `DependencyGraph` |
| `wave_plan` | `WavePlan` |
| `kpis` | `LandscapeKpis` |
| `scoring_config` | `ScoringConfig` |
| `wave_config` | `WaveConfig` |
| `fingerprint` | text |

**Invariants**: one assessment per object in the landscape; `distribution` values sum to the assessment count; carrying both configurations makes the result self-describing for export (FR-10.3).

---

## 6. Graph Entity

### DependencyGraph

| Field | Type | Purpose |
|---|---|---|
| `nodes` | sequence of `DependencyNode` | All 16 |
| `edges` | sequence of `DependencyEdge` | After `ALL` expansion: 32 |
| `out_degree` | lookup by `node_id` → integer | |
| `in_degree` | lookup by `node_id` → integer | |
| `area_order` | sequence of area codes | Fixed order for matrix rows and columns |
| `area_matrix` | square grid of integers | Cell (i, j) is 1 where area i has an edge to area j |
| `layout` | lookup by `node_id` → coordinate pair | Deterministic positions for the network view |

**Invariant**: `layout` must be deterministic for a given graph, so the network view does not shift between reruns.

---

## 7. Planning Entities

### WaveRisk

| Field | Type | Range |
|---|---|---|
| `score` | number | 0–100 |
| `band` | `RiskBand` | |
| `complexity_contribution` | number | 0–100 before weighting |
| `dependency_contribution` | number | 0–100 before weighting |
| `downtime_contribution` | number | 0–100 before weighting |
| `dmk_contribution` | number | 0 or 100 before weighting |

Contributions are stored **unweighted** so the UI can show both the raw factor and its weighted effect, which S6.4 AC2 requires.

### Wave

| Field | Type | Constraint |
|---|---|---|
| `number` | integer | 1 to `wave_count` |
| `start_date` | date | |
| `end_date` | date | After `start_date` |
| `object_ids` | sequence of text | May be empty when `wave_count` > 5 |
| `areas` | sequence of area codes | |
| `risk` | `WaveRisk` | |

### DependencyViolation

| Field | Type |
|---|---|
| `dependent_area` | text |
| `depends_on_area` | text |
| `dependent_wave` | integer |
| `depends_on_wave` | integer |
| `description` | text |

**Invariant**: only constructed when `dependent_wave` < `depends_on_wave`.

### WavePlan

| Field | Type |
|---|---|
| `waves` | sequence of `Wave` |
| `violations` | sequence of `DependencyViolation` |

**Invariant**: every object appears in exactly one wave.

Bundled dataset at defaults: 5 waves holding 5, 4, 5, 3, 5 objects; one violation.

---

## 8. Validation Entities

### ValidationIssue

| Field | Type | Purpose |
|---|---|---|
| `dataset` | text | Which of the six datasets |
| `field` | text or absent | The offending field |
| `record` | text or absent | Identifier or row number |
| `message` | text | Human-readable, names the problem |
| `severity` | `Severity` | `ERROR` or `WARNING` |

### ValidationReport

| Field | Type |
|---|---|
| `issues` | sequence of `ValidationIssue` |
| `is_fatal` | boolean — true when any issue has severity `ERROR` |

### LoadOutcome

| Field | Type |
|---|---|
| `landscape` | `Landscape` or absent |
| `report` | `ValidationReport` |

**Invariant**: `landscape` is present if and only if `report.is_fatal` is false.

---

## 9. Comparison Entities

### ClassificationChange

| Field | Type |
|---|---|
| `object_id` | text |
| `left_category` | `Category` |
| `right_category` | `Category` |

**Invariant**: only constructed when the two categories differ.

### ScenarioDiff

| Field | Type |
|---|---|
| `left_name` | text |
| `right_name` | text |
| `changed` | sequence of `ClassificationChange` |
| `left_distribution` | lookup by `Category` → count |
| `right_distribution` | lookup by `Category` → count |

---

## 10. Enumerations

| Enumeration | Values | Notes |
|---|---|---|
| `Category` | `DECOMMISSION`, `REPLICATE_AS_IS`, `REBUILD_AS_DATA_PRODUCT` | Exactly three. No fourth value. |
| `Determinant` | `SCORE`, `DORMANCY_CEILING`, `ACTIVITY_FLOOR` | Guard values used only where the guard changed the outcome |
| `RiskBand` | `LOW`, `MEDIUM`, `HIGH` | Boundaries in BR-9.3 |
| `Severity` | `ERROR`, `WARNING` | |
| `EdgeType` | `LOGICAL`, `OPERATIONAL`, `CONSTRAINT` | All count equally in dependency scoring (FR-4.2) |
| `NodeType` | `SOLUTION_AREA`, `EXTERNAL`, `CONSTRAINT`, `SHARED_OBJECT`, `SOURCE` | Only `SOLUTION_AREA` nodes receive waves (BR-8.4) |

---

## 11. Relationships

```
AreaCriticality  1 ────< N  BwObject                  by solution_area
                              (composite areas link to 2 AreaCriticality)

BwObject         1 ──── 1  UsageRecord                by object_id
BwObject         1 ──── 1  VolumeMetrics              by object_id
BwObject         1 ──── 1  ComplexityMetrics          by object_id
BwObject         1 ──── 1  ObjectAssessment           by object_id

DependencyNode   N >──< N  DependencyNode             via DependencyEdge

ObjectAssessment 1 ──── 2  AxisScore                  value and effort
AxisScore        1 ────< N  DimensionScore            5 for value, 2 for effort
ObjectAssessment 1 ──── 1  Classification

Wave             1 ────< N  BwObject                  by object_id, exactly one wave each
Wave             1 ──── 1  WaveRisk
WavePlan         1 ────< N  Wave
WavePlan         1 ────< N  DependencyViolation

Landscape        1 ──── 1  AssessmentResult           per configuration
AssessmentResult 1 ────< N  ObjectAssessment
```

### Cardinality notes

- `ZMD1` is the only object whose `solution_area` resolves to two `AreaCriticality` records. Its criticality and dependency counts are their average (BR-4.3).
- `DependencyEdge` may reference nodes that are not solution areas, so not every edge participates in wave violation detection (BR-8.4).
- A `Wave` may hold zero objects when `wave_count` exceeds 5 (BR-8.2).

---

## 12. Identity and Equality

| Entity | Identity |
|---|---|
| `BwObject`, `UsageRecord`, `VolumeMetrics`, `ComplexityMetrics`, `ObjectAssessment` | `object_id` |
| `AreaCriticality` | `solution_area` |
| `DependencyNode` | `node_id` |
| `DependencyEdge` | `source` + `target` + `edge_type` |
| `Wave` | `number` |
| `Scenario` | `name` |
| All others | Value equality across all fields |

---

## 13. Derived Versus Stored

Distinguishing these matters because only stored values are inputs to caching.

| Entity | Stored from input | Derived by computation |
|---|---|---|
| `BwObject` and other input records | all fields | none |
| `Landscape` | all record fields | `fingerprint`, `sources` |
| `DimensionScore` | `raw_display` source values | `normalised`, `weight`, `contribution`, `inherited_from` |
| `AxisScore` | none | `total`, `dimensions` |
| `Classification` | none | all fields |
| `LandscapeKpis` | none | all fields |
| `DependencyGraph` | `nodes`, declared `edges` | expanded edges, degrees, matrix, layout |
| `Wave`, `WaveRisk`, `WavePlan` | none | all fields |

Everything derived from the dataset alone belongs to the cached phase. Everything derived from a configuration does not. This split is specified in BR-10.
