# Business Logic Model — Unit 2 `presentation-app`

**Phase**: 🟢 CONSTRUCTION — Functional Design
**Companion documents**: `domain-entities.md`, `business-rules.md`, `frontend-components.md`

---

## 1. Render Pipeline

```
STREAMLIT SCRIPT RUN (every interaction re-runs the whole script)
                    │
    ┌───────────────┴────────────────────────────────────────┐
    │  STAGE 1  BOOTSTRAP                          C16       │
    │  Page config, inject theme CSS, load font link          │
    │  Initialise session state on first run only             │
    └───────────────┬────────────────────────────────────────┘
                    │
    ┌───────────────┴────────────────────────────────────────┐
    │  STAGE 2  RESOLVE DATASET                    C16 + C3  │
    │  If uploads present: loader.load_with_overrides         │
    │  Else if no landscape yet: loader.load_bundled          │
    │  Else: reuse session-state landscape                    │
    │  Fatal report -> keep previous landscape (BR-P8.5)      │
    │  OUT: Landscape + ValidationReport                      │
    └───────────────┬────────────────────────────────────────┘
                    │  Landscape
    ╔═══════════════╧════════════════════════════════════════╗
    ║  STAGE 3  ENGINE PHASE A            CACHED, UNIT 1     ║
    ║  service.compute_base(landscape)                       ║
    ║  Cache key: landscape.fingerprint                      ║
    ║  OUT: BaseScores                                       ║
    ╚═══════════════╤════════════════════════════════════════╝
                    │  BaseScores
    ┌───────────────┴────────────────────────────────────────┐
    │  STAGE 4  READ CONTROLS                      C14       │
    │  Sidebar renders scoring + guard controls, returns      │
    │  the live ScoringConfig; writes it to session state     │
    │  Wave controls read in Stage 6 for the planner view     │
    └───────────────┬────────────────────────────────────────┘
                    │  ScoringConfig, WaveConfig
    ┌───────────────┴────────────────────────────────────────┐
    │  STAGE 5  ENGINE PHASE B          RECOMPUTED, UNIT 1   │
    │  service.apply_config(base, landscape, scoring, waves)  │
    │  OUT: AssessmentResult                                  │
    └───────────────┬────────────────────────────────────────┘
                    │  AssessmentResult
    ┌───────────────┴────────────────────────────────────────┐
    │  STAGE 6  RENDER SELECTED VIEW              C15        │
    │  Dispatch on session_state["active_view"]               │
    │    ├─ C12 frames.*    AssessmentResult -> DataFrames    │
    │    ├─ C13 charts.*    DataFrames/graph -> Figures       │
    │    └─ C14 widgets.*   render fragments                  │
    └───────────────┬────────────────────────────────────────┘
                    │
OUTPUT: rendered page
```

### 1.1 Why the expensive stage is skipped on the hot path

Stage 3 is the only costly step, and it is cached on `landscape.fingerprint`. Moving a threshold changes neither the landscape nor its fingerprint, so Stage 3 is a cache hit and only Stages 4–6 execute. This is the mechanism behind NFR-5.1's sub-500 ms target, and it is exact rather than approximate because `compute_base` accepts no `ScoringConfig` (Unit 1 BR-10.3).

### 1.2 Note on Streamlit's execution model

Streamlit re-runs the entire script on every interaction. This makes Stage 6 naturally consistent — there is no partial update path where one chart reflects a new threshold and another reflects the old one. Every visible element is rebuilt from one `AssessmentResult` computed once per run. BR-P12.4's prohibition on caching figures exists to preserve exactly this property.

---

## 2. Session State Lifecycle

### 2.1 Cold start

```
First script run
  ├─ session state empty -> initialise
  │    scoring_config = DEFAULT_SCORING
  │    wave_config    = DEFAULT_WAVES
  │    scenarios      = ()
  │    uploads        = {}
  │    active_view    = "Dashboard"
  ├─ loader.load_bundled()  ->  Landscape (22 objects), report with warnings only
  ├─ store landscape, store report as last_report
  ├─ compute_base (cache MISS, computed)
  ├─ apply_config with defaults
  └─ render Dashboard
```

Expected first-render figures: 22 objects, 604 GB total storage, 18.2% decommission, 21 GB reclaimable; donut reading 5 / 13 / 4.

### 2.2 Threshold change — the hot path

```
User moves the Value threshold slider
  ├─ Streamlit rerun
  ├─ landscape reused from session state, NOT reloaded
  ├─ compute_base  ->  CACHE HIT (fingerprint unchanged)
  ├─ control returns new ScoringConfig, written to session state
  ├─ apply_config  ->  recomputed, cheap
  └─ active view re-renders; every chart, count, table and badge updates
```

Nothing in this path touches disk or recomputes a dimension score. S2.4b AC2's "every classification, chart, count, and table across all views reflects the new threshold" holds because there is only one `AssessmentResult` and every element reads from it.

### 2.3 Upload

```
User uploads a replacement usage log
  ├─ bytes written to uploads["usage_logs"]
  ├─ loader.load_with_overrides(uploads)
  │    ├─ report NOT fatal ->  new landscape stored, new fingerprint
  │    │     └─ compute_base CACHE MISS -> full recompute
  │    └─ report IS fatal   ->  landscape unchanged (BR-P8.5)
  │          └─ offending entry removed from uploads (BR-P8.6)
  │          └─ validation panel rendered; previous results still on screen
  └─ render
```

The fingerprint does the cache invalidation. No explicit invalidation call exists, which is why there is no path where a stale base survives a dataset change.

### 2.4 Revert

```
User clicks "Revert to demo data"
  ├─ uploads cleared entirely
  ├─ loader.load_bundled()  ->  original fingerprint restored
  ├─ compute_base  ->  CACHE HIT on the original fingerprint (still warm)
  └─ reference distribution 5 / 13 / 4 restored
```

Reverting is fast for a non-obvious reason worth recording: the bundled fingerprint is usually still in the cache from cold start, so revert costs a classification pass rather than a full recompute.

### 2.5 Wave configuration change

```
User changes wave count from 5 to 3 in the Wave Planner
  ├─ wave_config written to session state
  ├─ compute_base  ->  CACHE HIT
  ├─ apply_config  ->  recomputed; classification unchanged but recomputed anyway,
  │                    keeping a single code path (services.md 4.4)
  └─ Wave Planner re-renders: 3 waves, all 22 objects still assigned,
     violations re-detected, risk recomputed per new grouping
```

### 2.6 Scenario save and compare

```
Save:
  └─ Scenario(name, current scoring_config, current wave_config)
     appended to session state scenarios (replacing any same-named entry)

Compare:
  ├─ two names selected from dropdown
  ├─ service.compare(landscape, left, right)
  │    ├─ compute_base  ->  CACHE HIT, shared by both sides
  │    ├─ apply_config with left  config
  │    ├─ apply_config with right config
  │    └─ diff  ->  ScenarioDiff
  └─ render distributions side by side + changed-object list
```

A comparison costs two cheap classification passes over one shared cached base, not two full pipelines.

---

## 3. Per-View Composition

### 3.1 Dashboard

| Region | Source | Component chain |
|---|---|---|
| KPI strip | `result.kpis` | C14 `kpi_strip` |
| Classification donut | `result.distribution` | C12 `assessments_frame` → C13 `classification_donut` |
| Top 10 by value | assessments | C12 `assessments_frame` → C13 `top_value_bar` |
| Value/Effort scatter | assessments + live thresholds | C12 `assessments_frame` → C13 `quadrant_scatter` |
| Decommission candidates | Decommission subset | C12 `candidates_frame` → table + C14 badges |
| Dependency heatmap | `result.graph` | C12 `heatmap_frame` → C13 `dependency_heatmap` |

### 3.2 Object Detail

| Region | Source | Component chain |
|---|---|---|
| Object selector | assessments | C15 dropdown |
| Metadata, classification, usage | selected `ObjectAssessment` | C14 `classification_badge`, guard badge, dormancy note |
| Dependencies both directions | `assessment.incoming` / `.outgoing` | C15 two lists |
| Derivation table | both `AxisScore`s | C12 `derivation_frame` → C14 `derivation_table` |
| Rationale | `classification.rationale` | rendered verbatim (BR-P11.6) |

### 3.3 Dependencies

| Region | Source | Component chain |
|---|---|---|
| Area matrix heatmap | `graph.area_matrix`, `graph.area_order` | C12 `heatmap_frame` → C13 `dependency_heatmap` |
| Network graph | `graph.nodes`, `.edges`, `.layout` | C13 `dependency_network` directly from the graph |
| `ZMD1` scoring note | static text | C15, satisfying S5.1 AC6 |

The network chart reads the graph directly rather than through a frame, because coordinates and edges are not tabular data and forcing them through pandas would add a conversion with no benefit.

### 3.4 Wave Planner

| Region | Source | Component chain |
|---|---|---|
| Wave configuration controls | session state | C14 `wave_controls` |
| Gantt timeline with DMK marker | `result.wave_plan` | C12 `gantt_frame` → C13 `wave_gantt` |
| Per-wave assignment table | `wave.object_ids`, `.areas` | C15 table |
| Risk breakdown | `wave.risk` unweighted contributions | C15 table, four named contributions |
| Violation list | `wave_plan.violations` | C15 list with count stated first |

### 3.5 Scenario Compare

| Region | Source | Component chain |
|---|---|---|
| Save control | current configs | C15 text input + button |
| Two-scenario selector | `scenarios` | C15 two dropdowns |
| Distribution comparison | `diff.left_distribution`, `.right_distribution` | C15 side-by-side |
| Changed object list | `diff.changed` | C15 table, count stated |

---

## 4. Worked Example — Threshold Change End to End

**Starting state**: Dashboard, defaults, donut showing 5 / 13 / 4.

**Action**: user drags the Effort threshold from 67 to 66.

1. Streamlit reruns the script.
2. Stage 2 reuses the session-state landscape. Fingerprint unchanged.
3. Stage 3 `compute_base` — cache hit. `FI100GC`'s Effort score is still 66.3; **the score did not change**, only the boundary it is compared against.
4. Stage 4 returns `ScoringConfig(effort_threshold=66)`.
5. Stage 5 `apply_config` reclassifies. `FI100GC` now has Effort 66.3 ≥ 66, and Value 60.6 ≥ 33, so it moves from `REPLICATE_AS_IS` to `REBUILD_AS_DATA_PRODUCT`.
6. Stage 6 re-renders: donut now 6 / 12 / 4; the scatter's vertical Effort boundary shifts left by one unit and `FI100GC`'s point changes colour; the top-10 bar chart is unchanged because Business Value did not change; KPI strip unchanged because the Decommission set did not change.

This is the demo moment requirements §4.5 anticipated: one control movement visibly reclassifies Acme's flagship P&L query, and the derivation table explains exactly why.

---

## 5. Worked Example — Guard Badge Rendering

**Object `IN200`**, Object Detail view, defaults.

Engine output: `category=DECOMMISSION`, `determinant=DORMANCY_CEILING`, `is_dormant=True`, `is_active=False`, Value 35.9, Effort 25.7.

Rendered:
- Classification badge: "Decommission" in `#9c4f1f` with icon and label (BR-P5.1)
- Chip badge: icon + "Dormancy Ceiling" (BR-P4.1a)
- Italic note: "Dormant — last run 375 days ago, 2 executions/month" (BR-P4.1d)
- Rationale verbatim from the engine, explaining that the computed value of 35.9 is inflated by inherited area attributes

**Object `TR200`**, same view.

Engine output: `category=DECOMMISSION`, `determinant=SCORE`, `is_dormant=True`, Value 18.8.

Rendered:
- Classification badge: "Decommission"
- **No chip badge** (BR-P4.1c) — the score alone already placed it here
- Italic note: "Dormant — last run 326 days ago, 3 executions/month" (BR-P4.1d)

The difference between these two renderings is the whole point of Unit 1's BR-6.6 determinant/predicate split. A viewer can see that `IN200` was overridden and `TR200` was not, without reading any explanatory text.

---

## 6. Edge Cases

| Case | Handling | Rule |
|---|---|---|
| Fatal upload | Previous landscape retained, panel shown, views still render | BR-P8.5 |
| Same upload retried automatically after failure | Prevented — offending entry removed from `uploads` | BR-P8.6 |
| Upload with warnings only | Applied, warnings shown alongside results | BR-P8.7 |
| Fewer than two saved scenarios | Comparison control disabled with explanation | BR-P7.5 |
| Two identical scenarios compared | Explicit "no differences" statement, not a blank area | BR-P7.7 |
| Duplicate scenario name | Replaces, and says so | BR-P7.4 |
| Empty scenario name | Rejected inline, no save | BR-P7.3 |
| `wave_count` > 5 producing empty waves | Empty bar rendered with zero-count label | BR-P6.11 |
| Activity days set at or above dormancy days | Unreachable — control max is clamped | BR-P10.11 |
| CDN unreachable | Fallback font stack applies, layout intact | BR-P2.2, BR-P2.3 |
| Unexpected exception in a view | Caught at C16 boundary, readable message | BR-P9.6 |
| `ZMD1` composite area | `inherited_from` names both areas; view states the 82.5 average | BR-P11.5 |
| Object with no usage record (uploaded data) | Engine scores those dimensions 0 and warns; view shows the warning and the 0 values | BR-P9.4 |

---

## 7. Determinism Guarantees

| Guarantee | Mechanism |
|---|---|
| Network graph does not shift between reruns | Layout coordinates come from Unit 1, computed with a fixed seed | BR-P6.8 |
| No stale visual after a configuration change | Figures and frames never cached; whole script reruns | BR-P12.4 |
| Same result renders identically | No randomness, no clock reads in any Unit 2 component | BR-P12.3 |
| A view cannot disagree with another view | All views read one `AssessmentResult` computed once per run | §1.2 |
| A view cannot compute a score | Views hold outputs, never the inputs scoring requires | BR-P12.2, `services.md` §1 |

---

## 8. Story Logic Coverage

| Story | Logic |
|---|---|
| S1.3b | Stage 2 fatal-report branch, §2.3, BR-P9 |
| S2.4b | Stages 4–6, §2.2, §4 |
| S3.1 | §3.1 KPI strip |
| S3.2 | §3.1 donut and bar |
| S3.3 | §3.1 scatter, §4 step 6 |
| S3.4 | §3.1 candidates region |
| S4.1 | §3.2 |
| S4.2 | §3.2 derivation table, §5 |
| S6.3 | §3.4 Gantt |
| S8.1 | Launch scripts — Code Generation |
| S8.2 | BR-P1, BR-P5, BR-P6.1 applied throughout every view |
| S8.3b | Stage 1 font handling, BR-P2 |

All 12 Unit 2 stories have their presentation logic specified.
