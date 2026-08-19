# Frontend Components — Unit 2 `presentation-app`

**Phase**: 🟢 CONSTRUCTION — Functional Design
**Companion documents**: `domain-entities.md`, `business-rules.md`, `business-logic-model.md`

---

## 1. Component Tree

```
main.py  (C16)  — entry point, sole owner of session state
│
.streamlit/config.toml  — native widget theme (BR-P1.7)
│     ├── [theme]          primary, backgrounds, text, link, borders, radius
│     └── [theme.sidebar]  sidebar background, text, primary, border
│
main.py  (C16)  — entry point, sole owner of session state
│
├── theme.apply()                          (C11)
│     ├── Streamlit page config
│     ├── CSS injection (menu rows, cards, headings, sidebar captions)
│     └── font link with fallback stack
│
├── SIDEBAR — three labelled blocks (BR-P3.8)
│   ├── "Navigation" caption               (C16)
│   ├── navigation radio                   (C16)   6 options -> active_view, styled as a menu (BR-P3.6)
│   ├── widgets.sidebar_section("Scoring") (C14)   divider + caption
│   ├── widgets.scoring_controls()         (C14)   -> ScoringConfig
│   │     ├── value threshold slider
│   │     ├── effort threshold slider
│   │     └── guard parameters expander (4 controls)
│   ├── reset to defaults button           (C14)
│   ├── widgets.sidebar_section("Data")    (C14)   divider + caption
│   └── data source expander               (C16)
│         ├── 6 x file_uploader
│         ├── 6 x bundled/uploaded indicator
│         └── revert to demo data button
│
├── widgets.validation_panel(report)       (C14)   inline, top of body, when issues exist
│
└── BODY — dispatch on active_view          (C15)
    │
    │   Every view opens with widgets.page_header(title, subtitle) (BR-P14.1)
    │
    ├── views/dashboard.py
    │     ├── widgets.page_header("Dashboard", ...)         (C14)
    │     ├── widgets.kpi_strip(kpis)                       (C14)
    │     ├── export buttons (CSV + JSON)                   (C15)  raised above content (BR-P14.5)
    │     ├── "Classification Summary"    + charts.classification_donut(frame)          (C13)
    │     ├── "Top 10 by Business Value"  + charts.top_value_bar(frame, limit=10)       (C13)
    │     ├── "Business Value vs Technical Effort" + charts.quadrant_scatter(...)       (C13)
    │     ├── "Decommission Candidates"   + candidates table                            (C14)
    │     └── "Dependency Matrix"         + charts.dependency_heatmap(graph)            (C13)
    │
    ├── views/object_detail.py
    │     ├── widgets.page_header("Object Detail", ...)     (C14)
    │     ├── object selectbox
    │     ├── metadata block
    │     ├── widgets.classification_badge(classification) (C14)
    │     ├── widgets.guard_rule_badge(classification)     (C14)
    │     ├── widgets.dormancy_note(classification, usage)  (C14)
    │     ├── "Usage Metrics"
    │     ├── "Dependencies" -> Incoming / Outgoing columns
    │     ├── "Score Derivation" + widgets.derivation_table(assessment)  (C14)
    │     └── "Rationale"
    │
    ├── views/dependency_view.py
    │     ├── widgets.page_header("Dependencies", ...)      (C14)
    │     ├── "Dependency Matrix"  + charts.dependency_heatmap(graph)   (C13)
    │     ├── "Dependency Network" + charts.dependency_network(graph)   (C13)
    │     └── ZMD1 scoring note
    │
    ├── views/wave_planner.py
    │     ├── widgets.page_header("Wave Planner", ...)      (C14)
    │     ├── "Wave Configuration"      + widgets.wave_controls(current)   (C14) -> WaveConfig
    │     ├── "Migration Wave Timeline" + charts.wave_gantt(plan, freeze)  (C13)
    │     ├── "Wave Assignments"        + per-wave assignment table
    │     ├── "Risk Breakdown"          + per-wave risk breakdown table
    │     └── "Dependency Violations (n)" + violation list (count first)
    │
    ├── views/scenario_compare.py
    │     ├── widgets.page_header("Scenario Compare", ...)  (C14)
    │     ├── "Save Current Configuration"
    │     ├── two scenario selectboxes
    │     ├── "Scenario Configuration" + frames.scenario_config_frame(left, right)
    │     ├── "Distribution"           + frames.distribution_frame(diff)
    │     └── "Changed Objects (n)"    + changed-object table
    │
    └── views/source_data.py
          ├── widgets.page_header("Source Data", ...)       (C14)
          ├── dataset selectbox (6 datasets)
          ├── source indicator (bundled/uploaded)
          ├── per-dataset st.dataframe (dependencies split into Nodes/Edges tabs)
          └── per-table "Download as CSV" button
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

**CSS scope, revised 2026-08-19 (BR-P1.7)**. Anything Streamlit exposes as a theme config option now lives in `.streamlit/config.toml`, because injected CSS cannot reach native widget accents. C11's CSS is limited to what config cannot express:

| Concern | Owner |
|---|---|
| Widget accents (radio dot, slider handle/track, focus ring), body/link colour, widget borders, corner radius, dataframe chrome, sidebar fill and text | `.streamlit/config.toml` |
| Navigation rows styled as a menu (hover, selected fill, hidden radio circle, left border) | C11 CSS |
| Card treatment for metrics, dataframes, and Plotly charts | C11 CSS |
| Heading colour and letter spacing | C11 CSS |
| Sidebar section captions (uppercase, tracked) | C11 CSS |
| Sidebar button hover pairing and expander summary legibility | C11 CSS |
| Font family with the NFR-3.2 fallback stack | C11 CSS (`theme.font` cannot express a stack) |

`_css()` is a separate function from `apply()` so the stylesheet can be built and inspected without a Streamlit runtime.

**Palette roles**: 14, listed in `business-rules.md` BR-P1.7a. `header`, `header_text`, and `heading` were retired this round; `ink` and `text_on_accent` replace them.

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
| `object_inventory_frame` | `Landscape` | 22 |
| `usage_logs_frame` | `Landscape` | 22 |
| `criticality_frame` | `Landscape` | 12 |
| `data_volume_frame` | `Landscape` | 22 |
| `complexity_frame` | `Landscape` | 22 |
| `dependency_nodes_frame` | `Landscape` | 16 |
| `dependency_edges_frame` | `Landscape` | 21 |
| `distribution_frame` | `ScenarioDiff` | one per category present |
| `scenario_config_frame` | `Scenario`, `Scenario` | 9 (6 scoring + 3 wave parameters) |

**Correction made during Code Generation (2026-08-18)**: `assessments_frame` and `candidates_frame` take an additional `landscape: Landscape` parameter beyond what this table originally specified. `storage_gb` (required by `domain-entities.md` §4's column contract) is a `Landscape.volume` field, not part of `AssessmentResult` — Unit 1 correctly keeps per-object volume data out of the scoring-and-classification result object. Passing `landscape` through was the smaller change; changing Unit 1's `AssessmentResult` shape would have re-opened an approved and tested unit for a presentation-layer need. Recorded in `construction/presentation-app/code/summary.md` §5.

**Addition (2026-08-19, post-approval enhancement — Source Data view)**: seven new frame functions added, one per raw dataset: `object_inventory_frame`, `usage_logs_frame`, `criticality_frame`, `data_volume_frame`, `complexity_frame`, `dependency_nodes_frame`, `dependency_edges_frame`. Each takes only `landscape: Landscape` and returns the dataset's records exactly as loaded (post-validation, pre-scoring), with no derived columns. This preserves the "no frame recomputes a classification" constraint below — these frames don't even touch `AssessmentResult`.

**Constraint**: no frame function accepts a `ScoringConfig`, `WaveConfig`, or `Landscape`. Each takes only already-computed output. This makes it structurally impossible for a frame to recompute a classification (BR-P12.2).

---

## 4. C13 `charts`

All return a Plotly figure. All pure. None reads session state.

| Function | Signature | Key requirements |
|---|---|---|
| `classification_donut` | `(frame) -> Figure` | Segment labels with category name and count (BR-P5.2); inside labels, wide margins (BR-P6.12) |
| `top_value_bar` | `(frame, limit: int) -> Figure` | Descending by Business Value (BR-P6.3) |
| `quadrant_scatter` | `(frame, cfg: ScoringConfig) -> Figure` | Live boundary lines; guard-override markers outlined (BR-P6.2, BR-P4.6) |
| `dependency_heatmap` | `(graph, heatmap_df) -> Figure` | 12×12, both axes labelled with area names (BR-P6.4); `card` → `accent` scale (BR-P6.15) |
| `dependency_network` | `(graph) -> Figure` | Shape by node type, arrows, legend, layout from Unit 1 (BR-P6.5–BR-P6.8) |
| `wave_gantt` | `(frame, freeze_until: date) -> Figure` | One bar per wave, DMK line from the `freeze_until` argument (BR-P6.9–BR-P6.11, BR-P6.16) |
| `_style_axes` | `(fig) -> Figure` | Internal. Applies palette gridlines, axis lines, tick and title colours (BR-P6.14) |

`quadrant_scatter` takes the `ScoringConfig` **only to draw boundary lines**, never to classify — the categories it colours by are already in the frame.

**No chart sets a Plotly `title` (BR-P6.13).** Titles are `st.subheader` calls in the calling view, so chart titles and table titles look the same. `_LAYOUT_TEMPLATE` therefore uses a small top margin; `classification_donut` overrides it for radial label clearance.

`_style_axes` is applied by every builder except `classification_donut` (a pie has no axes) and `dependency_network` (axes deliberately invisible).

---

## 5. C14 `widgets`

| Function | Signature | Renders / returns |
|---|---|---|
| `page_header` | `(title: str, subtitle: str) -> None` | `st.header` (must be first, must equal the view name — BR-P14.2), caption, divider |
| `sidebar_section` | `(label: str) -> None` | Divider plus uppercase caption, for the sidebar's three blocks (BR-P3.8) |
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
| Source data dataset selector | `source-data-dataset-selector` |
| Source data table (per dataset/table) | `source-data-table-{dataset_name}` |
| Source data download (per dataset/table) | `source-data-download-{dataset_name}` |
| Scenario compare configuration table | `scenario-compare-config-table` |
| Scenario compare distribution table | `scenario-compare-distribution-table` |

`sidebar-upload-{dataset_name}` is the one templated key; `dataset_name` is drawn from the six fixed dataset names, so the resulting keys are still a closed, stable set.

**Unchanged by the 2026-08-19 design refresh.** No key was added, removed, or renamed. `sidebar-view-nav` still identifies the navigation control despite it now looking like a menu (BR-P3.7), and `export-classification-csv` / `export-wave-json` kept their keys when they moved from `main.py` into `dashboard.render` (BR-P14.6). This is why the refresh required no changes to `test_smoke_views.py`.

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
| S9.1 (post-approval addition) | C12 seven raw-dataset frames, `views/source_data.py` |
| S8.2 (revised 2026-08-19, design refresh) | `.streamlit/config.toml` `[theme]`, C11 palette and `_css`, C13 `_style_axes`, C14 `page_header` / `sidebar_section`, all six C15 views |

Every Unit 2 story has at least one owning component. Every component serves at least one story.

---

## 11. Smoke Test Targets

NFR-7.3 requires each view to render without error. The testable surface:

| Test | Asserts |
|---|---|
| `test_frames.py` | Every frame builds from a real `AssessmentResult`; row counts and columns match `domain-entities.md` §4 |
| `test_theme_contrast.py` | Every text colour pair recomputed and passing after the checker is re-validated against five WCAG anchors; `#82ce71` never in a text-on-light role; palette hygiene invariants (BR-P1.8) |
| `test_smoke_views.py` | Each of the six views renders without raising, and its first header equals its navigation name (BR-P14.2) |

C12 is fully unit-testable without Streamlit. C11's palette and contrast logic is testable as pure data. C13's figure construction is testable by asserting figure properties. C14 and C15 require Streamlit's test harness and are limited to smoke coverage, as NFR-7.3 anticipated.

**Explicitly outside the automated surface.** `AppTest` runs the Python render path; it does not evaluate CSS or expose rendered HTML, and it does not apply `.streamlit/config.toml`'s `[theme]` block. So the menu row styling (BR-P3.6), the card treatment (BR-P14.4), and the native widget accent colour (BR-P1.7) cannot be asserted by these tests. What *was* verified mechanically for the theme block: Streamlit's own `_populate_theme_msg` was called and the resulting `CustomThemeConfig` protobuf — the exact object delivered to the browser — reports `primary_color: "#0050e6"` for both the main and sidebar namespaces. The CSS selectors still need a human eye in a browser.
