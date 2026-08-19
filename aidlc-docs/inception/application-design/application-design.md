# Application Design — BW-ACE

**Stage**: INCEPTION — Application Design
**Date**: 2026-08-18
**Status**: Awaiting approval

**Consolidates**: `components.md`, `component-methods.md`, `services.md`, `component-dependency.md`
**Inputs**: approved requirements, 22 user stories, 3 personas, execution plan

---

## 1. Design Decisions

Six decisions were taken at the planning gate. Each is recorded with the reasoning, so it can be revisited on substance.

| # | Decision | Chosen | Reasoning |
|---|---|---|---|
| 1 | Engine granularity | **7 computation modules** plus config and service | Each module has one reason to change, and the four most test-critical concerns — normalisation, scoring, classification, guard rules — become separately addressable. The alternative coarse split folded them into larger modules where isolating a scoring defect is harder. |
| 2 | Data representation | **Typed frozen dataclasses internally; DataFrames only at the presentation boundary** | Three approved requirements point the same way. NFR-8.3 asks for type hints, which are near-meaningless over DataFrame column access. NFR-7.1 wants an independently testable engine, far easier when a function takes a typed object and returns a typed result. And it confines the pandas 3.x behavioural risk flagged in the execution plan to one module rather than spreading it through the engine. At 22 objects there is no vectorisation argument to weigh against this. |
| 3 | Configuration | **Single Python module of typed frozen constants** | Satisfies NFR-8.2 with no parsing layer and no second source of truth that could drift from what the tests assert. Live-adjustable values travel as configuration objects, never by mutating the module. |
| 4 | Recomputation | **Cache dataset-dependent stages; recompute threshold-dependent stages** | Not merely an optimisation. It reflects a real property of the model: a threshold cannot change any dimension score, only which side of a boundary it falls on. Caching is therefore exact rather than approximate, and NFR-5.3's 1,000-object headroom is met by design. |
| 5 | Orchestration | **Single `AssessmentService` returning one immutable result** | This is the mechanism that *enforces* NFR-8.1 rather than leaving it as a rule to remember. A view cannot perform scoring arithmetic because it never holds the inputs. It also makes scenario comparison a diff of two value objects rather than a re-orchestration. |
| 6 | Upload validation | **Hand-rolled** | The requirement is not "validate a schema" but "produce a specific quality of error message naming field and record". Story S1.3 AC4 needs a cross-dataset referential check that neither pydantic nor pandera handles natively, so a library would cover the easy half and leave the half that matters. |

---

## 2. Architecture Overview

Sixteen components across two units, in six layers, with dependencies pointing strictly downward.

```
Layer 5   C16 app                          entry point, session state, navigation
Layer 4   C15 views                        four views plus scenario comparison
Layer 3   C13 charts    C14 widgets        figures and UI fragments
Layer 2   C11 theme     C12 frames         styling and the DataFrame boundary
========================================  UNIT BOUNDARY  =========================
Layer 1   C10 assessment_service           orchestration
Layer 0   C3 loader   C4 normalisation   C5 scoring   C6 classification
          C7 dependencies   C8 waves   C9 export     computation
Layer -1  C1 models    C2 config           types and constants
```

The unit boundary is crossed by exactly one type in the outward direction: `AssessmentResult`. Inward, C16 passes a `Landscape` and two configuration objects.

### 2.1 Why the boundary holds

| Check | Result |
|---|---|
| Any Unit 1 component importing a Unit 2 component? | No |
| Any Unit 1 component importing Streamlit or Plotly? | No |
| Unit 1 testable with Unit 2 absent? | Yes |
| Any Unit 2 component performing scoring arithmetic? | No |
| Enforced structurally or by convention? | **Structurally** — Unit 2 holds outputs, never the inputs required to score |

Eight of the ten engine components need nothing beyond the Python standard library. Only `networkx` reaches into the engine, and only into C7.

---

## 3. Components

Full definitions in `components.md`; signatures in `component-methods.md`.

### Unit 1 — Assessment Engine

| Component | Purpose | Pure |
|---|---|---|
| C1 `models` | Typed domain objects, all frozen, collections as tuples | types only |
| C2 `config` | Every static default in one place — weights, bands, thresholds, palette | constants only |
| C3 `loader` | Files or uploads to a validated `Landscape`, or a precise error report | No (I/O) |
| C4 `normalisation` | Raw values to 0–100 via fixed absolute bands; resolves area inheritance | Yes |
| C5 `scoring` | Weight and sum each axis, preserving per-dimension contributions | Yes |
| C6 `classification` | Quadrant mapping plus guard rules, plus rationale generation | Yes |
| C7 `dependencies` | Graph construction, wildcard expansion, degrees, matrix, layout | Yes |
| C8 `waves` | Assignment, violation detection, risk scoring | Yes |
| C9 `export` | CSV and JSON serialisation with configuration embedded | Yes |
| C10 `assessment_service` | Orchestration; the sole interface to Unit 2 | Yes |

### Unit 2 — Presentation App

| Component | Purpose |
|---|---|
| C11 `theme` | Palette, CSS, web font with system fallback |
| C12 `frames` | The only pandas-touching module; domain objects to DataFrames |
| C13 `charts` | Donut, bar, quadrant scatter, heatmap, network, Gantt |
| C14 `widgets` | KPI strip, classification and guard badges, derivation table, controls |
| C15 `views` | Dashboard, object detail, dependencies, wave planner, scenario compare |
| C16 `app` | Entry point, navigation, session state, upload and revert |

---

## 4. The Result Object

`AssessmentResult` is the entire contract between the units.

```
AssessmentResult
├── assessments      one per object: both axis scores with per-dimension
│                    derivation, classification, determinant, rationale,
│                    and resolved incoming/outgoing dependencies
├── distribution     counts per category
├── graph            nodes, edges, degrees, area matrix, layout coordinates
├── wave_plan        waves with risk breakdown, plus dependency violations
├── kpis             total objects, total storage, decommission %, reclaimable
├── scoring_config   the configuration that produced this result
├── wave_config      the wave settings that produced this result
└── fingerprint      identifies the source dataset
```

Immutable throughout, so it is safe to cache, to hold in session state, and to pass to several views in one render pass. Because it carries its own configuration, exports are self-describing and FR-10.3 needs no separate mechanism.

---

## 5. Execution Flow

### Cold start
`C16` loads via `C3` → fatal errors stop and display → `C10.compute_base` builds the graph, normalises, and scores **(cached on fingerprint)** → `C10.apply_config` classifies, aggregates, and plans waves → the selected view renders.

### Threshold change — the hot path
Loading is skipped, `compute_base` hits cache, only `apply_config` recomputes. Both expensive stages are avoided, which is why the 500 ms target in NFR-5.1 is met by design rather than by the dataset happening to be small.

### Correctness of the cache
`compute_base` takes no `ScoringConfig`. Dimension scores are a function of the dataset alone. Caching is exact, not approximate.

### Scenario comparison
Both scenarios share one cached base, so a comparison costs two cheap classification passes rather than two full pipelines.

Full sequences, caching table, session state ownership, and error propagation are in `services.md`.

---

## 6. Story to Component Map

| Story | Components |
|---|---|
| S1.1 Load bundled landscape | C3, C10, C16 |
| S1.2 Upload own extract | C3, C10, C16 |
| S1.3 Understand rejection | C3, C14, C16 |
| S2.1 Two-axis scoring | C4, C5 |
| S2.2 Three-way classification | C6 |
| S2.3 Usage overrides score | C6, C14 |
| S2.4 Threshold sensitivity | C6, C10, C14, C16 |
| S3.1 KPI strip | C10, C14, C15 |
| S3.2 Landscape shape | C12, C13, C15 |
| S3.3 Value/effort positioning | C12, C13, C15 |
| S3.4 Decommission candidates | C6, C12, C15 |
| S4.1 Object profile | C7, C12, C15 |
| S4.2 Derivation and rationale | C4, C5, C6, C14, C15 |
| S5.1 Dependency matrix and network | C7, C12, C13, C15 |
| S6.1 Wave sequence | C8, C15 |
| S6.2 Wave structure | C8, C14, C16 |
| S6.3 Timeline with DMK | C8, C13, C15 |
| S6.4 Wave risk | C8, C15 |
| S7.1 Scenario comparison | C10, C15 |
| S7.2 Export | C9, C15 |
| S8.1 Cross-platform launch | C16, launch scripts |
| S8.2 Readable screens | C11, C13, C14 |
| S8.3 Offline and responsive | C10, C11 |

Every story has an owning component. Every component serves at least one story.

---

## 7. Requirement Coverage

| Requirement group | Owning components |
|---|---|
| FR-1.x data ingestion | C3, C16 |
| FR-2.x scoring | C4, C5 |
| FR-3.x classification and guard rules | C6, C14 |
| FR-4.x dependency analysis | C7 |
| FR-5.x wave planning | C8 |
| FR-6.x dashboard | C10, C12, C13, C14, C15 |
| FR-7.x object detail | C7, C12, C14, C15 |
| FR-8.x wave planner view | C8, C13, C15 |
| FR-9.x scenario comparison | C10, C15 |
| FR-10.x exports | C9, C15 |
| NFR-2.x portability | C16, launch scripts |
| NFR-3.x offline | C10 caching, C11 font fallback |
| NFR-4.x accessibility | C11, C13, C14 |
| NFR-5.x performance | C10 two-phase caching |
| NFR-6.x usability | C14, C16 |
| NFR-7.x testability | C1–C10 purity |
| NFR-8.x maintainability | C2 single config, layering, C12 pandas containment |

---

## 8. Testability

Directly unit-testable with no fixture beyond input data: all of C4, C5, C6, C7, C8, C9; C10's four methods; C3's validation functions given byte payloads; C12 given a result object.

This covers every requirement carrying a reference-data acceptance criterion, satisfying NFR-7.1 and NFR-7.2. Only C11, C13, C14, C15, C16 need Streamlit and are therefore limited to the NFR-7.3 smoke tests.

The separation of `classify` from `classify_by_score` in C6 exists specifically so that story S2.3 AC6 — that guard rules change exactly two objects and no others — is testable by direct comparison.

---

## 9. Deliberately Deferred

| Deferred to | Items |
|---|---|
| **Unit 1 Functional Design** | Normalisation band boundaries; complexity and volume sub-weights; recency multiplier tiers; guard rule evaluation order; wave assignment algorithm; risk formula and band boundaries; rationale wording |
| **Unit 2 Functional Design** | Terracotta hex selection and contrast verification; palette role mapping; view layout; chart specifications; navigation structure |
| **Code Generation** | File and directory layout; dependency version pins; launch script implementation; README |

---

## 10. Design Risks

| Risk | Assessment | Mitigation |
|---|---|---|
| pandas 3.x behavioural change | Contained. Confined to C12 by decision 2. | Unit-test `frames` against known results |
| C12 as a single conversion chokepoint | Low. Concentrates risk but also concentrates review. | One reviewable module |
| `AssessmentResult` accumulating fields | Moderate. Aggregates tend to grow. | Grouped sub-objects rather than a flat structure |
| `networkx` API drift | Low. Only construction and degree counting used. | Pin version; avoid layout algorithms whose output varies across releases |
| Cache correctness | Low. Argued exact in §5, not merely plausible. | `compute_base` takes no `ScoringConfig`, enforced by signature |
