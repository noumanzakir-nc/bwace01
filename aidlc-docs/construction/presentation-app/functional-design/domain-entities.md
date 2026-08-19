# Domain Entities — Unit 2 `presentation-app`

**Phase**: 🟢 CONSTRUCTION — Functional Design
**Technology-agnostic** in intent; where a Streamlit concept is unavoidable (session state) it is described structurally rather than by API.

---

## 1. Why This Document Is Short

Unit 2 introduces almost no domain entities. That is the intended consequence of the Application Design decision that `AssessmentResult` is the entire contract between the units (`services.md` §3) — Unit 2 receives fully computed, immutable values and has nothing left to model.

Everything Unit 2 renders is defined in Unit 1's `domain-entities.md`: `AssessmentResult`, `ObjectAssessment`, `AxisScore`, `DimensionScore`, `Classification`, `DependencyGraph`, `WavePlan`, `Wave`, `WaveRisk`, `DependencyViolation`, `LandscapeKpis`, `ValidationReport`, `ValidationIssue`, `ScenarioDiff`, `ClassificationChange`, and the six enumerations.

This document defines only what Unit 2 adds: the shape of session state, the upload slot record, and the presentation-only value types.

---

## 2. Session State

Owned solely by C16 `main`, per `services.md` §6. No other component reads or writes it — this is what keeps C12–C15 pure or render-only and independently testable.

| Key | Type | Initial value | Purpose |
|---|---|---|---|
| `landscape` | `Landscape` | bundled load result | Currently active dataset |
| `scoring_config` | `ScoringConfig` | `DEFAULT_SCORING` | Live thresholds and guard parameters |
| `wave_config` | `WaveConfig` | `DEFAULT_WAVES` | Live wave settings |
| `scenarios` | ordered sequence of `Scenario` | empty | Saved scenarios (Q5=A — no enforced cap) |
| `uploads` | lookup: dataset name → bytes | empty | Uploaded payloads, retained so revert is possible and so a second upload of a *different* dataset does not discard the first |
| `active_view` | text | `"Dashboard"` | Sidebar selection |
| `last_report` | `ValidationReport` or absent | absent | Most recent validation outcome, so warnings persist across a rerun until superseded |

### 2.1 Invariants

| ID | Invariant |
|---|---|
| SS-1 | `landscape` is never absent after first successful load. A failed upload leaves the previous value in place (BR-11.13). |
| SS-2 | `uploads` keys are drawn from the six known dataset names only. |
| SS-3 | `scoring_config` and `wave_config` are always valid instances — the controls that write them cannot express an invalid value (see `frontend-components.md` §6), so `ScoringConfig`'s `activity_days < dormancy_days` invariant cannot be violated through the UI. |
| SS-4 | `active_view` is always one of the five known view names. |

### 2.2 What is deliberately *not* in session state

| Not stored | Why |
|---|---|
| `AssessmentResult` | Recomputed each run from `landscape` + the two configs. Cheap because `compute_base` is cached on fingerprint; storing it would risk serving a result that no longer matches the live controls. |
| `BaseScores` | Held by the cache keyed on `landscape.fingerprint`, not by session state. |
| Any DataFrame or Plotly figure | Rebuilt per render. `services.md` §5 explicitly declines to cache figures to avoid stale rendering. |

---

## 3. Presentation-Only Entities

### UploadSlot

Describes one of the six dataset upload positions. Exists so the "bundled / uploaded" indicator required by S1.2 AC2 has a defined shape rather than being assembled ad hoc in the view.

| Field | Type | Constraint |
|---|---|---|
| `dataset_name` | text | One of the six known dataset names |
| `display_label` | text | Human-readable, e.g. `Usage Logs` |
| `source` | `bundled` or `uploaded` | Derived from `landscape.sources` |
| `accepted_formats` | sequence of text | `("csv", "json")` for all six |

**Derived, not stored**: constructed on each render from `landscape.sources`.

### PaletteRole

Binds a semantic role to a colour, so that no view refers to a hex value directly (NFR-8.2).

| Field | Type | Purpose |
|---|---|---|
| `role` | text | e.g. `app_background`, `card`, `header`, `heading`, `accent`, `warm_neutral`, `category_rebuild`, `category_replicate`, `category_decommission` |
| `hex` | text | The colour |
| `permitted_uses` | sequence of text | e.g. `("fill", "border")` — `#82ce71` excludes `text_on_light` per NFR-4.3 |

**Design note**: `permitted_uses` makes NFR-4.3 a property of the data rather than a rule someone has to remember. A test can assert that no role used for text on a light background carries a colour whose `permitted_uses` excludes it.

### CategoryStyle

Everything needed to render one classification consistently, in one place.

| Field | Type | Purpose |
|---|---|---|
| `category` | `Category` | The classification |
| `label` | text | Display text, e.g. `Rebuild as Data Product` |
| `colour` | text | Hex from the corresponding `PaletteRole` |
| `text_colour_on_fill` | text | What colour text must be when drawn on `colour` |
| `icon` | text | Short glyph or symbol accompanying the label (NFR-4.5) |

**Invariant**: `label` is always non-empty. This is the mechanism by which NFR-4.5 ("never colour alone") holds structurally — a renderer that draws a `CategoryStyle` always has a label available and the widget contract requires it be drawn.

### BadgeKind

Distinguishes the two indicator types required by BR-6.6c and Q3=A.

| Value | Shown when | Visual treatment |
|---|---|---|
| `GUARD_DETERMINANT` | `classification.determinant` is not `SCORE` | Coloured chip with icon and rule name |
| `DORMANCY_NOTE` | `classification.is_dormant` is true | Plain italic text, no chip, no icon |
| `ACTIVITY_NOTE` | `classification.is_active` is true | Plain italic text, no chip, no icon |

The three are not mutually exclusive — `IN200` carries both a `GUARD_DETERMINANT` badge and a `DORMANCY_NOTE`; `TR200` carries only a `DORMANCY_NOTE`. See `business-rules.md` BR-P4 for the exact display matrix.

---

## 4. Frame Shapes

C12 `frames` is the only component touching pandas. Five functions, five shapes, per `component-methods.md` §11. Columns are specified here so charts and tables have a contract to code against.

| Frame | One row per | Columns |
|---|---|---|
| `assessments_frame` | object (22) | `object_id`, `object_type`, `solution_area`, `description`, `business_value`, `technical_effort`, `category`, `category_label`, `determinant`, `is_dormant`, `is_active`, `monthly_executions`, `distinct_users`, `last_run_date`, `business_owner`, `storage_gb` |
| `derivation_frame` | dimension (7 for one object) | `axis`, `dimension`, `dimension_label`, `raw_display`, `normalised`, `weight`, `contribution`, `inherited_from` |
| `gantt_frame` | wave | `wave`, `wave_label`, `start_date`, `end_date`, `object_count`, `areas`, `risk_score`, `risk_band` |
| `heatmap_frame` | area pair (12×12 = 144) | `source_area`, `target_area`, `value` |
| `candidates_frame` | Decommission object (4 at defaults) | `object_id`, `description`, `solution_area`, `business_owner`, `last_run_date`, `monthly_executions`, `distinct_users`, `storage_gb`, `determinant`, `rationale` |

**Invariant**: every frame is built by reading `AssessmentResult` only. No frame function computes a score, applies a threshold, or re-derives a classification.

---

## 5. Relationships

```
AssessmentResult (from Unit 1)
  │
  ├──> frames.assessments_frame   ──> charts.classification_donut
  │                                ──> charts.top_value_bar
  │                                ──> charts.quadrant_scatter
  │
  ├──> frames.candidates_frame    ──> views.dashboard candidate table
  │
  ├──> frames.derivation_frame    ──> widgets.derivation_table
  │      (per selected object)
  │
  ├── .graph ──> frames.heatmap_frame ──> charts.dependency_heatmap
  │           ──> charts.dependency_network  (reads graph.layout directly,
  │                                           no frame needed — it is
  │                                           coordinate data, not tabular)
  │
  ├── .wave_plan ──> frames.gantt_frame ──> charts.wave_gantt
  │               ──> views.wave_planner risk table and violation list
  │
  ├── .kpis ──> widgets.kpi_strip
  │
  └── .scoring_config / .wave_config ──> widgets.scoring_controls / wave_controls
                                          (as *current values*, not as state —
                                           the controls write back to session state)

Landscape (from Unit 1) ──> UploadSlot construction (via .sources)
ScenarioDiff (from Unit 1) ──> views.scenario_compare
ValidationReport (from Unit 1) ──> widgets.validation_panel
```

---

## 6. Identity and Equality

Unit 2 introduces no entity with an identity concern. `UploadSlot` is keyed by `dataset_name`, `PaletteRole` by `role`, `CategoryStyle` by `category` — all three are lookup tables rebuilt per render, never persisted or compared.

`Scenario` identity is `name`, defined in Unit 1. Saving a scenario under an existing name replaces it (see `business-rules.md` BR-P7).

---

## 7. Derived Versus Stored

| Entity | Stored in session state | Derived per render |
|---|---|---|
| `landscape`, `scoring_config`, `wave_config`, `scenarios`, `uploads`, `active_view`, `last_report` | all | none |
| `AssessmentResult` and everything inside it | none | all (via cached `compute_base` + fresh `apply_config`) |
| `UploadSlot`, `PaletteRole`, `CategoryStyle`, `BadgeKind` decisions | none | all |
| All five frames, all Plotly figures | none | all |

The rule: **session state holds inputs, never outputs.** This is the structural reason a threshold change cannot leave a stale figure on screen.
