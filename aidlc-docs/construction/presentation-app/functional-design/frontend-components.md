# Frontend Components — Unit 2 `presentation-app`

**Phase**: 🟢 CONSTRUCTION — Functional Design
**Companion documents**: `domain-entities.md`, `business-rules.md`, `business-logic-model.md`

---

## 1. Component Tree

```
main.py  (C16)  — entry point, sole owner of session state
│
├── theme.apply()                          (C11)
│     ├── Streamlit page config
│     ├── CSS injection (palette, cards, header, sidebar)
│     └── font link with fallback stack
│
├── SIDEBAR
│   ├── navigation radio                   (C16)   5 options -> active_view
│   ├── widgets.scoring_controls()         (C14)   -> ScoringConfig
│   │     ├── value threshold slider
│   │     ├── effort threshold slider
│   │     └── guard parameters expander (4 controls)
│   ├── reset to defaults button           (C14)
│   └── data source expander               (C16)
│         ├── 6 x file_uploader
│         ├── 6 x bundled/uploaded indicator
│         └── revert to demo data button
│
├── widgets.validation_panel(report)       (C14)   inline, top of body, when issues exist
│
└── BODY — dispatch on active_view          (C15)
    │
    ├── views/dashboard.py
    │     ├── widgets.kpi_strip(kpis)                      (C14)
    │     ├── charts.classification_donut(frame)           (C13)
    │     ├── charts.top_value_bar(frame, limit=10)        (C13)
    │     ├── charts.quadrant_scatter(frame, scoring_cfg)  (C13)
    │     ├── candidates table + widgets badges            (C14)
    │     └── charts.dependency_heatmap(graph)             (C13)
    │
    ├── views/object_detail.py
    │     ├── object selectbox
    │     ├── metadata block
    │     ├── widgets.classification_badge(classification) (C14)
    │     ├── widgets.guard_rule_badge(classification)     (C14)
    │     ├── widgets.dormancy_note(classification, usage)  (C14)
    │     ├── usage metrics block
    │     ├── incoming / outgoing dependency lists
    │     ├── widgets.derivation_table(assessment)         (C14)
    │     └── rationale block
    │
    ├── views/dependency_view.py
    │     ├── charts.dependency_heatmap(graph)             (C13)
    │     ├── charts.dependency_network(graph)             (C13)
    │     └── ZMD1 scoring note
    │
    ├── views/wave_planner.py
    │     ├── widgets.wave_controls(current)               (C14) -> WaveConfig
    │     ├── charts.wave_gantt(plan, freeze_until)        (C13)
    │     ├── per-wave assignment table
    │     ├── per-wave risk breakdown table
    │     └── violation list (count first)
    │
    └── views/scenario_compare.py
          ├── save current as named scenario
          ├── two scenario selectboxes
          ├── distribution side-by-side
          └── changed-object table
```

**Dependency direction**: strictly downward. `views` may call `frames`, `charts`, `widgets`, `theme`. None of those may call `views`. No component below `main` touches session state (BR-P12.1).

---

## 2. C11 `theme`

| Function | Signature | Behaviour |
|---|---|---|
| `apply` | `() -> None` | Sets page config, injects CSS, adds font link |
| `palette` | `() -> Mapping[str, PaletteRole]` | Role-name lookup, resolved from C2 `config.PALETTE` |
| `category_style` | `(category: Category) -> CategoryStyle` | Colour, label, icon, on-fill text colour |
| `risk_style` | `(band: RiskBand) -> tuple[str, str]` | Colour and label for a risk band |

**State**: none. **Interactions**: none. Called once per run before anything renders.

**CSS scope**: application background, card containers, header bar, sidebar background and text, heading colours, warning/callout blocks. Exact declarations are written at Code Generation; this stage fixes which roles apply where (BR-P1.1).

---

## 3. C12 `frames`

Five functions, shapes fixed in `domain-entities.md` §4. All pure. The only pandas-touching component.

| Function | Input | Output rows |
|---|---|---|
| `assessments_frame` | `AssessmentResult`, `Landscape` | 22 |
| `derivation_frame` | `ObjectAssessment` | 7 |
| `gantt_frame` | `WavePlan` | one per wave |
| `heatmap_frame` | `DependencyGraph` | 144 (12×12) |
| `candidates_frame` | `AssessmentResult`, `Landscape` | one per Decommission object |

**Correction made during Code Generation (2026-08-18)**: `assessments_frame` and `candidates_frame` take an additional `landscape: Landscape` parameter beyond what this table originally specified. `storage_gb` (required by `domain-entities.md` §4's column contract) is a `Landscape.volume` field, not part of `AssessmentResult` — Unit 1 correctly keeps per-object volume data out of the scoring-and-classification result object. Passing `landscape` through was the smaller change; changing Unit 1's `AssessmentResult` shape would have re-opened an approved and tested unit for a presentation-layer need. Recorded in `construction/presentation-app/code/summary.md` §5.

**Constraint**: no frame function accepts a `ScoringConfig`, `WaveConfig`, or `Landscape`. Each takes only already-computed output. This makes it structurally impossible for a frame to recompute a classification (BR-P12.2).

---

## 4. C13 `charts`

All return a Plotly figure. All pure. None reads session state.

| Function | Signature | Key requirements |
|---|---|---|
| `classification_donut` | `(frame) -> Figure` | Segment labels with category name and count (BR-P5.2) |
| `top_value_bar` | `(frame, limit: int) -> Figure` | Descending by Business Value (BR-P6.3) |
| `quadrant_scatter` | `(frame, cfg: ScoringConfig) -> Figure` | Live boundary lines; guard-override markers outlined (BR-P6.2, BR-P4.6) |
| `dependency_heatmap` | `(graph) -> Figure` | 12×12, both axes labelled with area names (BR-P6.4) |
| `dependency_network` | `(graph) -> Figure` | Shape by node type, arrows, legend, layout from Unit 1 (BR-P6.5–BR-P6.8) |
| `wave_gantt` | `(frame, freeze_until: date) -> Figure` | One bar per wave, DMK line anchored to 2028-01-01 (BR-P6.9–BR-P6.11) |

`quadrant_scatter` takes the `ScoringConfig` **only to draw boundary lines**, never to classify — the categories it colours by are already in the frame.

---

## 5. C14 `widgets`

| Function | Signature | Renders / returns |
|---|---|---|
| `kpi_strip` | `(kpis: LandscapeKpis) -> None` | Four metric tiles |
| `classification_badge` | `(classification) -> None` | Colour + icon + text label |
| `guard_rule_badge` | `(classification) -> None` | Chip when determinant is not `SCORE`, else nothing |
| `dormancy_note` | `(classification, usage, reference) -> None` | Italic note when `is_dormant` or `is_active` |
| `derivation_table` | `(assessment) -> None` | Two grouped tables, one per axis |
| `scoring_controls` | `(current: ScoringConfig) -> ScoringConfig` | Sliders; returns the new config |
| `wave_controls` | `(current: WaveConfig) -> WaveConfig` | Controls; returns the new config |
| `validation_panel` | `(report: ValidationReport) -> None` | Grouped errors and warnings |

The two control functions **return** a config rather than writing session state — keeping C14 free of state access (BR-P12.1). C16 writes what they return.

---

## 6. Control Validation

| Control | Bounds enforced by the widget | Rule |
|---|---|---|
| Value threshold | slider 0–100, step 1 | BR-P10.1 |
| Effort threshold | slider 0–100, step 1 | BR-P10.2 |
| Dormancy days | 1–730 | BR-P10.3 |
| Dormancy executions | 0–100 | BR-P10.4 |
| Activity days | 1 to `dormancy_days - 1`, **max clamped dynamically** | BR-P10.5, BR-P10.11 |
| Activity executions | 0–500 | BR-P10.6 |
| Wave count | 1–10 | BR-P10.7 |
| Wave months | 1–12 | BR-P10.8 |
| Start date | date picker, any date | BR-P10.9 |
| Scenario name | non-empty; rejected inline if blank | BR-P7.3 |
| Upload | `.csv` / `.json` only, enforced by the uploader's type filter | BR-P8.1 |

**Design note**: every bound is expressed as a widget constraint rather than as post-hoc validation. A user cannot construct an invalid `ScoringConfig` through the UI, so the dataclass's `activity_days < dormancy_days` check becomes a defence against programming error rather than a user-facing error path.

---

## 7. Interaction Map

| Interaction | Triggers | Recomputes | Rule |
|---|---|---|---|
| Change view in sidebar | rerun | nothing (cache hit, same configs) | BR-P3.3 |
| Move a threshold slider | rerun | `apply_config` only | BR-P10.13 |
| Change a guard parameter | rerun | `apply_config` only | BR-P10.13 |
| Reset to defaults | rerun | `apply_config` only | BR-P10.12 |
| Upload a dataset | rerun | full reload + `compute_base` (new fingerprint) | BR-P8.2 |
| Revert to demo data | rerun | reload; `compute_base` usually a cache hit | BR-P8.4 |
| Change wave count / months / start date | rerun | `apply_config` only | §2.5 of logic model |
| Select a different object | rerun | nothing | — |
| Save a scenario | rerun | nothing | BR-P7.1 |
| Compare two scenarios | rerun | two `apply_config` passes over one cached base | BR-P7.6 |
| Download an export | no rerun | nothing — serialised from the current result | FR-10.1, FR-10.2 |

---

## 8. Launch Scripts — Deferred to Code Generation

S8.1 is the one Unit 2 story whose substance is not rendering. Recorded here so it is not lost between stages.

| Criterion | What Code Generation must produce |
|---|---|
| S8.1 AC1 | `run.bat` — create venv, install pinned deps, launch Streamlit |
| S8.1 AC2 | `run.sh` — same on Linux/macOS |
| S8.1 AC3 | Python as the only prerequisite |
| S8.1 AC4 | Skip install when the venv already exists |
| S8.1 AC5 | Detect Python below 3.11 and stop with a message naming found and required versions |
| S8.1 AC6 | Versions already pinned in `pyproject.toml` (done in Unit 1) |
| S8.1 AC7 | README covering both platforms plus troubleshooting |

---

## 9. Test Identifier Convention

Per the Code Generation automation-friendly rules, every interactive element carries an explicit stable `key`. Streamlit uses `key=` rather than `data-testid`, and keys must be unique per run.

**Pattern**: `{view}-{element-role}`, lowercase, hyphen-separated, no dynamic content in the key.

| Element | Key |
|---|---|
| Navigation radio | `sidebar-view-nav` |
| Value threshold slider | `sidebar-value-threshold` |
| Effort threshold slider | `sidebar-effort-threshold` |
| Dormancy days | `sidebar-dormancy-days` |
| Dormancy executions | `sidebar-dormancy-executions` |
| Activity days | `sidebar-activity-days` |
| Activity executions | `sidebar-activity-executions` |
| Reset button | `sidebar-reset-defaults` |
| Uploader per dataset | `sidebar-upload-{dataset_name}` |
| Revert button | `sidebar-revert-demo` |
| Object selector | `object-detail-selector` |
| Wave count | `wave-planner-count` |
| Wave months | `wave-planner-months` |
| Wave start date | `wave-planner-start-date` |
| Scenario name input | `scenario-name-input` |
| Scenario save button | `scenario-save-button` |
| Left scenario selector | `scenario-compare-left` |
| Right scenario selector | `scenario-compare-right` |
| CSV download | `export-classification-csv` |
| JSON download | `export-wave-json` |

`sidebar-upload-{dataset_name}` is the one templated key; `dataset_name` is drawn from the six fixed dataset names, so the resulting keys are still a closed, stable set.

---

## 10. Story Coverage

| Story | Components |
|---|---|
| S1.3b | C14 `validation_panel`, C16 upload handling |
| S2.4b | C14 `scoring_controls`, reset button, C16 state write |
| S3.1 | C14 `kpi_strip` |
| S3.2 | C12 `assessments_frame`, C13 `classification_donut`, `top_value_bar` |
| S3.3 | C13 `quadrant_scatter` |
| S3.4 | C12 `candidates_frame`, C14 badges, dashboard table |
| S4.1 | C15 `object_detail` |
| S4.2 | C12 `derivation_frame`, C14 `derivation_table` |
| S6.3 | C12 `gantt_frame`, C13 `wave_gantt` |
| S8.1 | Launch scripts (§8, Code Generation) |
| S8.2 | C11 `theme`, C13 all charts, C14 all badges |
| S8.3b | C11 font handling |

Every Unit 2 story has at least one owning component. Every component serves at least one story.

---

## 11. Smoke Test Targets

NFR-7.3 requires each view to render without error. The testable surface:

| Test | Asserts |
|---|---|
| `test_frames.py` | All five frames build from a real `AssessmentResult`; row counts and columns match `domain-entities.md` §4 |
| `test_theme_contrast.py` | Every text colour pair in BR-P1.3 recomputed and passing; `#82ce71` never in a text-on-light role |
| `test_smoke_views.py` | Each of the five views renders without raising, given a real `AssessmentResult` |

C12 is fully unit-testable without Streamlit. C11's palette and contrast logic is testable as pure data. C13's figure construction is testable by asserting figure properties. C14 and C15 require Streamlit's test harness and are limited to smoke coverage, as NFR-7.3 anticipated.
