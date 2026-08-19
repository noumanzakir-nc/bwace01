# Code Generation Summary — Unit 2 `presentation-app`

**Phase**: 🟢 CONSTRUCTION — Code Generation (Part 2)
**Plan executed**: `aidlc-docs/construction/plans/presentation-app-code-generation-plan.md`

Documentation summary only. Application code is in `src/bwace/app/`.

---

## 1. Modules Generated

| File | Component | Design source |
|---|---|---|
| `src/bwace/app/theme.py` | C11 `theme` | `business-rules.md` BR-P1, BR-P2 |
| `src/bwace/app/frames.py` | C12 `frames` | `domain-entities.md` §4 |
| `src/bwace/app/charts.py` | C13 `charts` | `business-rules.md` BR-P6 |
| `src/bwace/app/widgets.py` | C14 `widgets` | `business-rules.md` BR-P4, BR-P9, BR-P10 |
| `src/bwace/app/views/{dashboard,object_detail,dependency_view,wave_planner,scenario_compare}.py` | C15 `views` | `business-logic-model.md` §3 |
| `src/bwace/app/main.py` | C16 `app` | `business-logic-model.md` §1–2 |

No Unit 2 module imports anything from `bwace.engine` beyond types and the `service`/`loader`/`export`/`config` functions — no scoring, classification, dependency, or wave arithmetic appears anywhere in this unit (NFR-8.1, verified by inspection).

## 2. Tests Generated

17 tests across 3 files, all passing.

| File | Focus |
|---|---|
| `test_frames.py` | Row counts and column contracts for all five frames against a real `AssessmentResult`; storage totals cross-checked (604 GB all objects, 21 GB decommission set) |
| `test_theme_contrast.py` | Contrast checker validated against 3 known WCAG anchors, then every palette role recomputed; asserts the Decommission colour `#9c4f1f` passes AA on all three backgrounds; asserts no role is falsely marked `text_on_light` |
| `test_smoke_views.py` | Using `streamlit.testing.v1.AppTest`: initial render, all five views via the actual sidebar radio widget, KPI values, threshold interaction, object selector count, full scenario save/compare flow |

## 3. Verification Performed

1. `pip install -e .[dev]` — no new dependencies needed (Unit 1 already pinned `streamlit`, `plotly`, `pandas`)
2. `streamlit run src/bwace/app/main.py` started successfully in the background (HTTP 200), then stopped
3. `streamlit.testing.v1.AppTest` exercised every view via the real radio widget, the real threshold sliders, the real object selector, and the full scenario save-and-compare flow — all clean, zero error boxes, zero exceptions
4. `pytest tests/app` — 17/17 passed
5. `pytest tests` (full suite) — **73/73 passed**, confirming Unit 1's 56 tests are unaffected by Unit 2's addition
6. `run.bat`'s version-detection, venv-exists, and provisioned-marker branches each verified in isolation on this Windows machine
7. `run.sh` written to the identical specification but **not executable on this Windows machine** — flagged as unverified on Linux/macOS

## 4. Defects Found and Fixed During Generation

Four real defects were caught by testing before this stage was presented, not after:

1. **`st.cache_data` on `compute_base`'s return value.** `BaseScores` contains `MappingProxyType` fields that pickle cannot serialize, and `cache_data` requires pickling. Switched to `st.cache_resource`, which does not serialize. Caught immediately by `AppTest` — every view showed an error box on first run.
2. **Gantt chart date arithmetic.** `wave_gantt` mixed a plain `int` day-count with `datetime.date` values as Plotly `Bar` arguments, which Plotly's date axis cannot combine. Fixed by converting to `pandas.Timestamp` and `pandas.Timedelta` before passing to `go.Bar`. Caught by `AppTest` navigating to Wave Planner.
3. **Sidebar controls rendering in the main body.** `widgets.scoring_controls` and the upload/revert controls were called from `_render_sidebar` without an active `with st.sidebar:` context, so despite the function's name they rendered in the page body. Caught because the very first `AppTest` interaction (`at.sidebar.slider(key=...)`) raised `KeyError` — the widget genuinely was not in the sidebar. Fixed by wrapping the whole sidebar body in `with st.sidebar:`.
4. **`card` palette role incorrectly permitted for `text_on_light`.** `#ffffff` (the card background) was tagged as a valid text colour, which is nonsensical for a *background* fill and would fail AA regardless (1.09:1 against the app background). My own `test_no_role_used_for_text_on_light_lacks_permission` caught this the first time it ran. Removed the incorrect permission.

All four were found by executing the code and its tests, not by re-reading the design — consistent with the project's established pattern of verifying rather than asserting.

## 5. Known Deviation from the Functional Design Documents

`domain-entities.md` §4 specifies `storage_gb` as a column in `assessments_frame` and `candidates_frame`, but `AssessmentResult` does not carry per-object storage — that field lives on `Landscape.volume`. Both frame functions were implemented taking an additional `landscape: Landscape` parameter beyond the plan's original single-argument signature, so the column contract could be honoured without Unit 1 needing a design change. `main.py` and both call sites (`dashboard.py`) pass `landscape` through. This is recorded here rather than silently accepted because it is a real signature change from `frontend-components.md` §3's stated `(AssessmentResult) -> DataFrame`.

## 6. Deferred to Build & Test

- Cross-platform verification of `run.sh` (Linux/macOS only)
- Full end-to-end manual walkthrough with a real browser (only headless/AppTest verification performed here)
