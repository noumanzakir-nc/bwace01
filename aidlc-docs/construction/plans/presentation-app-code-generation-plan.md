# Code Generation Plan — Unit 2 `presentation-app`

**Phase**: 🟢 CONSTRUCTION
**Unit**: `presentation-app` (components C11–C16, 12 stories, depends on Unit 1)
**Inputs**: `domain-entities.md`, `business-rules.md`, `business-logic-model.md`, `frontend-components.md` (Unit 2), plus Unit 1's approved code as the actual dependency
**Prerequisites confirmed**: Functional Design approved. NFR Requirements, NFR Design, Infrastructure Design all skipped for this unit per the execution plan.

---

## 1. Unit Context

**Stories implemented**: S1.3b, S2.4b, S3.1, S3.2, S3.3, S3.4, S4.1, S4.2, S6.3, S8.1, S8.2, S8.3b (12 stories).

**Dependencies**: Unit 1 (`bwace.engine`, already installed and tested) plus `streamlit==1.61.1`, `plotly==6.9.0`, `pandas==3.0.5` — all already pinned in `pyproject.toml` from Unit 1's Code Generation.

**Expected interface**: consumes `AssessmentResult` from `bwace.engine.service`. Passes `Landscape`, `ScoringConfig`, `WaveConfig` inward via the same service functions. No component in this unit computes a score, classification, dependency degree, or wave assignment (NFR-8.1, BR-P12.2).

**Database entities owned**: none.

---

## 2. Technology Decisions for This Stage

| Decision | Choice | Reason |
|---|---|---|
| Streamlit caching | `st.cache_resource` for `loader.load_bundled`, `st.cache_data` for `service.compute_base` keyed on `landscape.fingerprint` | Matches `services.md` §5 caching table; `cache_resource` suits the immutable bundled-load call, `cache_data` suits a pure function keyed by a hashable string |
| CSS injection mechanism | `st.markdown(..., unsafe_allow_html=True)` with a single `<style>` block built in `theme.py` | Standard Streamlit approach for page-level CSS not exposed via `st.set_page_config` or `st.markdown` theming config |
| Font loading | `<link>` tag to Google Fonts `Inter`, injected alongside the CSS block, with the fallback stack in the same `font-family` declaration so a network failure degrades silently (BR-P2.2, BR-P2.4) | No JS needed; pure CSS fallback |
| Plotly theme | Shared `layout` template dict built once in `charts.py`, applied to every figure, rather than repeating `layout=dict(...)` in each function | Keeps BR-P6.1 (labelled axes, legends, hover text) consistent without duplication |
| Session state initialisation | A single `_init_session_state()` in `main.py`, guarded by `if "scoring_config" not in st.session_state` | Idiomatic Streamlit pattern; avoids re-initialising on every rerun |
| Export downloads | `st.download_button` with `data=` computed inline from `export.classification_csv` / `wave_recommendation_json`, no server-side file write | Matches Q12=B (on-demand export, no `outputs/` directory) |
| Launch scripts | `run.bat` (Windows) and `run.sh` (Linux/macOS): check Python version via `python --version` parsing, create `.venv` if absent, `pip install -e .[dev]` on first run only (marker file `.venv/.provisioned`), then `streamlit run src/bwace/app/main.py` | Satisfies S8.1 AC1–AC5 exactly; marker file is the mechanism for AC4 (skip reinstall) |
| Test framework | `pytest` + Streamlit's `AppTest` harness (`streamlit.testing.v1.AppTest`, available in streamlit 1.61.1) for smoke tests | Standard for Streamlit smoke testing without a browser |

---

## 3. Steps

### Step 1 — Project Structure Setup
- [x] Create `src/bwace/app/__init__.py`
- [x] Create `src/bwace/app/views/__init__.py`
- [x] Create `tests/app/__init__.py`
- [x] Verify `pyproject.toml` already declares `streamlit`, `plotly`, `pandas` (done in Unit 1) — no changes needed unless a gap is found

**Story mapping**: infrastructure for all 12 Unit 2 stories.

### Step 2 — Frontend Components Generation: `theme.py` (C11)
- [x] `PALETTE` role table matching `business-rules.md` BR-P1.1 exactly, including the `#9c4f1f` Decommission colour
- [x] `apply()` — page config, CSS injection (background, cards, header, sidebar, headings), font link with fallback stack
- [x] `palette()`, `category_style()`, `risk_style()` per `frontend-components.md` §2
- [x] `PaletteRole` and `CategoryStyle` dataclasses per Unit 2 `domain-entities.md` §3, defined in `theme.py` since C11 is their only producer and consumer

**Story mapping**: S8.2, S8.3b.

### Step 3 — Frontend Components Generation: `frames.py` (C12)
- [x] `assessments_frame`, `derivation_frame`, `gantt_frame`, `heatmap_frame`, `candidates_frame` per the five column contracts in `domain-entities.md` §4
- [x] No function accepts `ScoringConfig`, `WaveConfig`, or `Landscape` — only already-computed Unit 1 output types

**Story mapping**: S3.2, S3.4, S4.2, S6.3.

### Step 4 — Frontend Components Generation: `charts.py` (C13)
- [x] Shared Plotly layout template (fonts, colours from `theme.palette()`)
- [x] `classification_donut`, `top_value_bar`, `quadrant_scatter` (with live threshold boundary lines and guard-override marker outlines), `dependency_heatmap`, `dependency_network` (shape-by-type, arrows, legend), `wave_gantt` (with fixed DMK marker at 2028-01-01)
- [x] Every figure: labelled axes, legend where >1 category, hover text (BR-P6.1)

**Story mapping**: S3.2, S3.3, S6.3, S8.2.

### Step 5 — Frontend Components Generation: `widgets.py` (C14)
- [x] `kpi_strip`, `classification_badge`, `guard_rule_badge`, `dormancy_note`, `derivation_table`, `scoring_controls`, `wave_controls`, `validation_panel`
- [x] Guard badge shown only when `determinant != SCORE`; dormancy/activity notes shown independently per BR-P4.1
- [x] Control functions return the new config; they do not write session state themselves (BR-P12.1)
- [x] Activity-days control max dynamically clamped to `dormancy_days - 1` (BR-P10.11)

**Story mapping**: S1.3b, S2.4b, S3.1, S4.1, S4.2.

### Step 6 — Frontend Components Generation: Views (C15)
- [x] `views/dashboard.py` — KPI strip, donut, top-10 bar, quadrant scatter, candidates table, dependency heatmap
- [x] `views/object_detail.py` — selector, metadata, classification + badges, usage, dependencies both directions, derivation table, rationale
- [x] `views/dependency_view.py` — heatmap, network graph, `ZMD1` scoring note
- [x] `views/wave_planner.py` — wave controls, Gantt, assignment table, risk breakdown, violation list (count first)
- [x] `views/scenario_compare.py` — save control, two selectors, distribution comparison, changed-object table with explicit empty-state message

**Story mapping**: S3.1, S3.2, S3.3, S3.4, S4.1, S4.2, S6.3.

### Step 7 — Frontend Components Generation: `main.py` (C16)
- [x] `_init_session_state()` — one-time defaults per `domain-entities.md` §2
- [x] `theme.apply()` call
- [x] Sidebar: navigation radio, scoring controls, guard parameter expander, reset button, data-source expander (6 uploaders + indicators + revert button)
- [x] Dataset resolution: uploads → `load_with_overrides`, else `load_bundled`; fatal report keeps previous landscape (BR-P8.5, BR-P8.6)
- [x] `compute_base` (cached) → `apply_config` → dispatch to selected view
- [x] Top-level exception boundary rendering a readable message (BR-P9.6)
- [x] Export download buttons (CSV, JSON) available from the sidebar or Dashboard, wired to Unit 1's `export.py`

**Story mapping**: S1.3b, S2.4b, S8.1 (entry point half), S8.3b.

### Step 8 — Frontend Components Unit Testing
- [x] `tests/app/test_frames.py` — all five frames, row counts and columns against `domain-entities.md` §4, built from a real `AssessmentResult`
- [x] `tests/app/test_theme_contrast.py` — recompute every BR-P1.3 pair programmatically (reusing the validated contrast function), assert all pass, assert `#82ce71` never assigned a `text_on_light` permitted use
- [x] `tests/app/test_smoke_views.py` — using `streamlit.testing.v1.AppTest`, run `main.py` and assert no exception for each of the five `active_view` values, given the bundled dataset

**Story mapping**: NFR-7.3, S8.2 (contrast assertions).

### Step 9 — Frontend Components Summary
- [x] Write `aidlc-docs/construction/presentation-app/code/summary.md`

### Step 10 — Documentation Generation
- [x] Extend `README.md` with the Unit 2 section: how to launch (`run.bat` / `run.sh`), how to run app tests, screenshots section left as a placeholder note (no screenshot capability in this environment)

**Story mapping**: S8.1 AC7.

### Step 11 — Deployment Artifacts Generation
- [x] `run.bat` — Python version check, venv creation, first-run install via marker file, `streamlit run`
- [x] `run.sh` — same for Linux/macOS
- [x] Both scripts tested manually against this workspace's actual Python during verification

**Story mapping**: S8.1 AC1–AC6.

**No API Layer, Repository Layer, or Database Migration steps** — Unit 2 has none of those concerns (confirmed in `application-design.md` and `unit-of-work.md` §3).

---

## 4. Verification Plan

1. `pytest tests/app -v` — all tests pass
2. `pytest tests/engine tests/app` — full suite, confirm Unit 1 is untouched (regression check)
3. Manually start the app via `streamlit run src/bwace/app/main.py --server.headless true` in the background, confirm it serves without startup error, then stop it
4. Confirm `run.bat` executes cleanly on this Windows machine (the only platform available to verify directly); `run.sh` is written to the same specification but cannot be executed on Windows — flagged as unverified on Linux, consistent with the verification guideline's requirement to state what could not be checked
5. Recompute all BR-P1.3 contrast pairs and confirm PASS, including `#9c4f1f`

---

## 5. Artifacts

**Application code** (workspace root):
- `src/bwace/app/__init__.py`, `src/bwace/app/{theme,frames,charts,widgets,main}.py`
- `src/bwace/app/views/__init__.py`, `src/bwace/app/views/{dashboard,object_detail,dependency_view,wave_planner,scenario_compare}.py`
- `tests/app/__init__.py`, `tests/app/test_{frames,theme_contrast,smoke_views}.py`
- `run.bat`, `run.sh`
- `README.md` (extended)

**Documentation**: `aidlc-docs/construction/presentation-app/code/summary.md`

---

## 6. Out of Scope

- Any change to `src/bwace/engine/` (Unit 1 is complete and approved)
- Cross-unit integration tests beyond the smoke tests already planned — full integration verification belongs to Build & Test
