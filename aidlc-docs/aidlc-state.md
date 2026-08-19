# AI-DLC State Tracking

## Project Information
- **Project Name**: BW Object Assessment & Classification Engine (BW-ACE)
- **Project Type**: Greenfield
- **Start Date**: 2026-08-18T00:00:00Z
- **Current Phase**: INCEPTION
- **Current Stage**: Requirements Analysis

## Workspace State
- **Existing Code**: No
- **Programming Languages**: None detected
- **Build System**: None detected
- **Project Structure**: Empty (documentation/requirements only)
- **Reverse Engineering Needed**: No
- **Workspace Root**: `c:\git\rfp\arla-sap`

## Code Location Rules
- **Application Code**: Workspace root (NEVER in aidlc-docs/)
- **Documentation**: aidlc-docs/ only
- **Structure patterns**: See code-generation.md Critical Rules

## Extension Configuration
| Extension | Enabled | Decided At |
|---|---|---|
| Security Baseline | No | Requirements Analysis |
| Resiliency Baseline | No | Requirements Analysis |
| Property-Based Testing | No | Requirements Analysis |

Rationale: demo/PoC for customer presentation, not a production workload. User answers Q18=B, Q19=B, Q20=C. Full rule files not loaded (deferred loading — opted out).

## Stage Progress

### 🔵 INCEPTION PHASE
- [x] Workspace Detection
- [ ] Reverse Engineering — SKIPPED (greenfield)
- [x] Requirements Analysis
- [x] User Stories
- [x] Workflow Planning
- [x] Application Design — COMPLETE
- [x] Units Generation — COMPLETE (2 units)

### 🟢 CONSTRUCTION PHASE

**Unit 1 — assessment-engine** — ✅ COMPLETE
- [x] Functional Design — COMPLETE
- [ ] NFR Requirements — SKIP
- [ ] NFR Design — SKIP
- [ ] Infrastructure Design — SKIP
- [x] Code Generation Part 1 (Planning) — COMPLETE
- [x] Code Generation Part 2 (Generation) — COMPLETE, approved

**Unit 2 — presentation-app** — ✅ COMPLETE
- [x] Functional Design — COMPLETE, approved
- [ ] NFR Requirements — SKIP
- [ ] NFR Design — SKIP
- [ ] Infrastructure Design — SKIP
- [x] Code Generation Part 1 (Planning) — COMPLETE
- [x] Code Generation Part 2 (Generation) — COMPLETE, approved

**After both units**
- [x] Build and Test — COMPLETE, awaiting approval (GATE)

### 🟡 OPERATIONS PHASE
- [ ] Operations (placeholder)

## Decisions Log
- 22 verification questions answered: Q1=D, Q2=B, Q3=B, Q4=B, Q5=A, Q6=B, Q7=C, Q8=B, Q9=B, Q10=A, Q11=B, Q12=B, Q13=A, Q14=A, Q15=B, Q16=B, Q17=C, Q18=B, Q19=B, Q20=C, Q21=A, Q22=D
- Contradiction detected (Q1 two-axis model vs Q2 composite 33/67 bands) and resolved via 4 clarification questions: CQ1=A, CQ2=A, CQ3=A, CQ4=A
- Scoring model: two-axis (Business Value x Technical Effort), value-first quadrant mapping, fixed absolute normalisation bands, Value threshold 33 / Effort threshold 67 (both adjustable)
- Stack verified empirically on Python 3.14.0: streamlit 1.61.1, pandas 3.0.5, networkx 3.6.1, plotly 6.9.0

## Resolved Decisions
1. **Guard rules** — ADOPTED on requirements approval. Dormancy ceiling (>180 days idle AND <5 exec → Decommission) plus activity floor (≤90 days AND ≥25 exec → never Decommission). Added as FR-3.6 to FR-3.9. Supersedes CQ4=A.
2. **Python version** — ADOPTED target Python 3.11+, running on installed 3.14.0. Supersedes the "3.12" element of Q10=A.

## Applied User Preferences (from memory graph)
- Minimal code comments; rationale belongs in aidlc-docs, not source. Codified as NFR-8.4; NFR-8.3 reduced to type hints only.
- Project-specific detail stays in aidlc-docs, never the memory graph.
- Shell notes: `$` variables stripped from inline commands (use temp in-workspace `.ps1`); `&` is the background operator, use `;`; network intermittent — relevant to launch script design.

## Stage Assessments
- **User Stories**: EXECUTE. Rationale in `aidlc-docs/inception/plans/user-stories-assessment.md`.

## User Stories Decisions
- Story plan answers: Q1=B (three analytical personas, no Demo Presenter), Q2=D (capability epics with persona-phrased stories), Q3=B (15-22 stories), Q4=A (Given/When/Then), Q5=A (concrete data expectations incl. full reference distribution), Q6=A (dedicated non-functional stories)
- **Resolution applied**: Q1=B removed the Demo Presenter persona, but several operator-facing *functional* Must requirements (FR-1.3, FR-3.3, FR-9.1/9.2, FR-10.1/10.2) needed an owner. Each attributed to the analytical persona with genuine interest — documented in `personas.md` §5. No clarification round raised; the resolution follows from reading Q1 and Q6 together.
- Artifacts: 3 personas, 22 stories across 8 capability epics, full two-way traceability, INVEST verification

## Execution Plan Summary
- **Plan document**: `aidlc-docs/inception/plans/execution-plan.md`
- **Stages completed**: 4 (Workspace Detection, Requirements Analysis, User Stories, Workflow Planning)
- **Stages to execute**: 7 — Application Design, Units Generation, Functional Design x2, Code Generation x2, Build and Test
- **Stages skipped**: Reverse Engineering (greenfield), NFR Requirements x2, NFR Design x2, Infrastructure Design x2, Operations
- **Remaining approval gates**: 9 (Code Generation has separate plan and generation gates per unit)
- **Risk level**: Low-Medium. Easy rollback (greenfield). Raised above Low by customer-facing consequence, pandas 3.x novelty, and the numeric detail deferred to Unit 1 Functional Design.
- **Unit build order**: `assessment-engine` first (no dependencies, independently verifiable against the reference distribution), then `presentation-app` (consumes engine output).
- Mermaid workflow diagram validated programmatically before the document was presented: 21 nodes declared, 21 styled, balanced delimiters, all edge endpoints and style targets resolved.

## Application Design Decisions
Plan answers: Q1=B, Q2=B, Q3=A, Q4=B, Q5=A, Q6=A (all as recommended, mutually consistent, no clarification round needed).

1. **Engine granularity** — 7 computation modules plus config and service
2. **Data representation** — typed frozen dataclasses internally, DataFrames only at the presentation boundary. Confines the pandas 3.x risk to component C12.
3. **Configuration** — single Python module of typed frozen constants (NFR-8.2)
4. **Recomputation** — two-phase: `compute_base` (dataset-dependent, cached on fingerprint) then `apply_config` (threshold-dependent, recomputed). Cache is exact because `compute_base` takes no ScoringConfig.
5. **Orchestration** — single `AssessmentService` returning one immutable `AssessmentResult`. This structurally enforces NFR-8.1.
6. **Upload validation** — hand-rolled, because S1.3 AC4's cross-dataset referential check is not handled natively by pydantic or pandera.

**Architecture**: 16 components (C1-C10 engine, C11-C16 presentation) across 6 layers, dependencies strictly downward, no cycles. Unit boundary crossed by exactly one outward type (`AssessmentResult`). 8 of 10 engine components need only the stdlib; networkx reaches only C7; pandas reaches only C12.

**Artifacts**: `components.md`, `component-methods.md`, `services.md`, `component-dependency.md`, `application-design.md` (consolidation).

## Session Continuity Note
A turn was interrupted after Application Design approval, while the Units Generation rules were being loaded and before `unit-of-work-plan.md` was written. On resume, state was verified directly: all 5 Application Design artifacts present, no `unit-of-work-plan.md`, no `aidlc-docs/construction/` directory, no application code at workspace root. No partial work required cleanup. The missing approval entry and state update were reconciled.

## Units Generation Decisions
Plan answers: Q1=A, Q2=B, Q3=A, Q4=A, Q5=A, Q6=A, Q7=A. Q2 diverged from the recommendation (split rather than cross-reference).

1. **Two units** — `assessment-engine` (C1-C10, 14 stories), `presentation-app` (C11-C16, 12 stories). Sequential build.
2. **Boundary-straddling stories split** — S1.3, S2.4, S8.3 each become `a` (engine) + `b` (app) sub-stories with parent acceptance criteria allocated, not duplicated. 23 stories become 26.
3. **One project, two packages** — single `pyproject.toml`, editable install by the launcher.
4. **Single developer, sequential** — units create verification checkpoints, not parallelism.
5. **No CLI** — Streamlit is the only engine consumer.
6. **Wave planning stays in the engine unit** — the assessment/planning domain seam is real (assumption A-7) but expressed as a module boundary, since `waves` consumes classification output.
7. **AI-DLC monolith structure** — `src/bwace/engine/`, `src/bwace/app/`, `tests/engine/`, `tests/app/`, `data/` at root.

**Story count correction**: `stories.md` stated 22 stories in three places; the actual inventory is 23 (per-epic counts were correct and sum to 23). Corrected in the document before the story map was built.

**Deviations from source document §4.2 structure**, recorded in `unit-of-work.md` §4.3: `src/bwace/app/main.py` instead of root `app.py`; `app/` instead of `ui/`; `demo/` data generator omitted (datasets fixed and fully specified); `outputs/` omitted (Q12=B chose on-demand export).

**Artifacts**: `unit-of-work.md`, `unit-of-work-dependency.md`, `unit-of-work-story-map.md`.

## Corrections Made to Approved Artifacts
1. **Story count** (`stories.md`) — stated 22, actual 23. Per-epic counts were correct and sum to 23. Corrected in 3 places before the story map was built.
2. **Object count** (`unit-of-work.md`) — stated 23 objects in 3 places plus a fabricated source note. Actual is **22**; the 23 was the story count carried across in error. Verified by counting source §3.1 and corroborated by 5+13+4=22. `ZMD1` is one of the 22. Confirmed via grep that `stories.md` was unaffected (correctly states 22 in S1.1 AC2, S3.1 AC2, S7.2 AC5).
3. **Violation example** (`stories.md` S6.1 AC5) — cited Purchasing depending on Supply Chain as the illustrative violation. Not a violation: PO is priority 4 (wave 4), SC is priority 2 (wave 2), dependency already satisfied. Actual and only violation is `LC` → `TM` (waves 4 and 5). Found by executing the specified wave rules.
4. **Guard badge criterion** (`unit-of-work.md` Unit 2 criterion 6) — implied only `IN200` and `IM100` carry dormancy indication. Guard predicates fire on 4 objects (`IN200`, `TR200`, `TM100` dormant; `IM100` active) but change the outcome on only 2. Criterion rewritten to distinguish determinant badges from dormancy notes.

## Unit 1 Functional Design Decisions
Plan answers: Q1=A through Q8=A — all validated values retained, so no re-derivation was needed and the reference distribution holds unchanged.

- Normalisation bands, complexity sub-weights (40/30/20/10), volume sub-weights (40/40/20), recency tiers (1.0/0.75/0.5/0.25 at 90/180/365 days) — all as validated
- **Wave compression (Q5=A)**: if W>=5, wave = priority (waves 6..W empty); if W<5, wave = floor((priority-1)*W/5)+1
- **Violation semantics (Q6=A)**: both endpoints must be SOLUTION_AREA nodes with a wave; edges to FF/SAPPS1/DMK/ZMD1 excluded; same-wave not a violation
- **Risk formula (Q7=A)**: complexity 40% + cross-wave deps 25% (violations double-weighted) + downtime 25% (from the wave's tightest window) + DMK 10%; bands Low 0-39, Medium 40-69, High 70-100
- **Rationale (Q8=A)**: template-driven, deterministic, one template per category and per guard determinant
- **NEW design decision (BR-6.6)**: `determinant` records the *effective cause* — a guard value only where the guard changed the category versus pure score. `is_dormant`/`is_active` recorded separately. Needed because predicates fire on 4 objects but override only 2.

**Verified by execution before the design was written**: distribution 5/13/4 intact; Rebuild and Decommission sets exact; FI100GC flips at Effort 66; 22 objects; ALL expands to 12 edges; wave assignment correct at W=5/3/7; exactly 1 violation (LC→TM); risk spread 1 Low / 3 Medium / 1 High.

**Artifacts**: `domain-entities.md`, `business-rules.md` (BR-1 to BR-12 with verification record), `business-logic-model.md` (8-stage pipeline, 4 worked examples with real numbers, 18 edge cases).

## Last Completed
Build and Test — executed from a completely clean environment. 73/73 tests pass, all performance targets pass with large margins (threshold recompute avg 1.55ms vs 500ms target; startup 3.04s vs 10s target; 1,100-object headroom 94-98ms). 5 documents created in `aidlc-docs/construction/build-and-test/`.

## Next Step
User approval of Build and Test results. Both units and Construction phase then complete — proceed to Operations (currently a placeholder).

## Current Phase
🟢 **CONSTRUCTION** — Build and Test complete, awaiting approval (GATE) — final gate before Operations

## Unit 2 Functional Design Decisions
Plan answers: Q1=A through Q6=A — all as recommended, no contradictions, no clarification round needed.

1. **Decommission colour — SUBSTITUTION FORCED.** Answer A approved `#b5651d`, but the contrast figures I quoted in the option text were asserted rather than computed and were **wrong**. Programmatic verification (checker validated against 5 known WCAG anchors) measured `#b5651d` at 3.99:1 on `#f2f7f1` and 4.34:1 on `#ffffff` — both below the 4.5:1 AA minimum. **`#9c4f1f` used instead**: 5.45:1 / 5.91:1 / 5.18:1, passing on all three backgrounds with margin. Same terracotta family, one step deeper. NFR-4.2 is binding and outranks a hex value that was only a suggestion. Near-boundary alternative `#a85820` (exactly 4.50:1 on `#f6eeee`) rejected for having no margin.
2. **Navigation** — sidebar radio, 5 options, `active_view` in session state
3. **Badge vs note** — chip badge (icon + rule name) only where a guard *changed* the outcome; plain italic note wherever the predicate merely fired. Makes Unit 1's BR-6.6 split visible: badges on `IN200`/`IM100` only, notes also on `TR200`/`TM100`
4. **Network nodes** — shape by node type, deliberately *not* colour, so colour continues to mean classification everywhere and never means two things
5. **Scenarios** — no cap
6. **Upload** — six independent uploaders, one per dataset

**Correction to requirements §3.4.1**: all seven documented contrast ratios were hand-estimated and off by up to 0.5. Recomputed with the validated checker. **Every verdict unchanged**; `#0d6a4b` is in fact better than recorded (6.08 vs 5.8, 6.60 vs 6.2). Table corrected and extended with the four new Decommission-colour rows.

**Artifacts**: `domain-entities.md` (deliberately short — Unit 2 adds almost no entities, which is the intended consequence of `AssessmentResult` being the whole contract), `business-rules.md` (BR-P1 to BR-P12), `business-logic-model.md` (8-stage render pipeline, 6 session-state lifecycles, 2 worked examples), `frontend-components.md` (component tree, control bounds, interaction map, test-key convention).

## Post-Approval Change: Colour Theme Restyle (2026-08-19)
User requested a direct restyle of the chrome palette to match the IBM Cloud cost estimator (Carbon Design System g100 dark console over light content): `#161616`, `#ffffff`, `#e8e8e8`, `#0050e6`. Treated as a small, well-scoped implementation change to already-approved, already-built code — no new gate.

- `theme.py` PALETTE updated (`app_background`, `header`, `heading`, `accent`, `warm_neutral`); sidebar changed to a diagonal CSS gradient `#161616` → `#0050e6`. Classification category colours (NFR-4.4, semantic) left unchanged and re-verified against the new background.
- Opportunistic fix: `widgets.py guard_rule_badge` hardcoded hex replaced with `palette()` lookups (BR-P1.4a compliance).
- `charts.py` heatmap colourscale endpoint now tracks `palette()["heading"]` instead of a pinned literal.
- `test_theme_contrast.py` updated: old accent-fails-on-white test now applies to `category_replicate`; new test asserts the new accent passes AA on light backgrounds.
- `business-rules.md` BR-P1.1 marked superseded for chrome roles, new contrast table (BR-P1.1a) added.
- Verified: 74/74 tests pass.

## Post-Approval Change: Sidebar Colour + Donut Label Padding Fix (2026-08-19, same day)
User feedback on the restyle: (1) the near-black `#161616` sidebar clashed with the blue/light theme; (2) classification donut labels overflowed the chart.

- `theme.py` `header` role changed `#161616` → `#001d6c` (IBM Carbon "Blue 80" — dark blue, same family as the `#0050e6` accent instead of near-black). Sidebar gradient mechanism unchanged, only the dark endpoint moved. Re-verified AA: 15.08:1 (white text on header), 12.31:1/8.93:1 for header on the light backgrounds.
- `charts.py` `classification_donut` — labels moved to `textposition="inside"` with `insidetextorientation="radial"`, plus wider top/bottom margins (60px vs the shared 40px template), so labels stay within the chart card.
- `business-rules.md` BR-P1.1/BR-P1.1a revised with the new header hex and contrast figures; BR-P6.12 added for the donut fix.
- `test_theme_contrast.py` — renamed `test_dark_green_on_backgrounds_passes_aa` to `test_header_colour_on_backgrounds_passes_aa` (header is no longer green).
- Verified: 74/74 tests pass.
## Post-Approval Fix: Scenario Config Table Arrow Serialization Error (2026-08-19, sixth iteration)
User reported a runtime error in execution logs: `pyarrow.lib.ArrowInvalid: Could not convert datetime.date(2027, 1, 1) ... tried to convert to int64` when rendering the new "Scenario Configuration" table.

**Root cause**: `scenario_config_frame` (added in the fifth iteration) builds one row per *parameter*, so `left.name`/`right.name` columns hold a mix of `int` values (thresholds, day/execution counts) across most rows and a `datetime.date` value (`start_date`) in one row. Pandas keeps this as an `object`-dtype column; PyArrow, used internally by `st.dataframe`, cannot infer one Arrow column type spanning `int` and `date` and fails outright (Streamlit's automatic-fix fallback did not save it here because the column is genuinely heterogeneous, not just wrongly-typed).

**Fix**: every value in `scenario_config_frame` is now rendered as `str(value)` before being placed in the frame — this is a display-only comparison table (not an export), so string formatting has no functional cost, matching the existing pattern in `derivation_frame` (`raw_display: str`).

- `frames.py` `scenario_config_frame` — values wrapped in `str()`; inline comment explaining why.
- `test_frames.py` — updated `test_scenario_config_frame_shows_differing_effort_threshold` to assert on string values; added `test_scenario_config_frame_is_arrow_serialisable`, a direct regression test that calls `pyarrow.Table.from_pandas()` on the frame (fails with `ArrowInvalid` on the original code, passes now).
- Verified: 85/85 tests pass (was 84; +1 new regression test).

## Post-Approval Change: Scenario Compare — Distribution Table + Configuration Comparison (2026-08-19, fifth iteration)
User feedback: the distribution comparison rendered as a raw Python dict (shown by Streamlit as JSON-like text), and there was no way to see what scoring/wave parameters differed between two saved scenarios — only the resulting classification differences were visible.

- `frames.py` — 2 new pure functions: `distribution_frame(diff: ScenarioDiff)` (one row per category, one column per scenario name) and `scenario_config_frame(left: Scenario, right: Scenario)` (one row per of the 9 adjustable parameters — 6 `ScoringConfig` + 3 `WaveConfig` — one column per scenario).
- `views/scenario_compare.py` — replaced the `st.write({...})` dict dump with `st.dataframe(frames.distribution_frame(diff))`; added a new "Scenario Configuration" table above it via `frames.scenario_config_frame`.
- `business-rules.md` — BR-P7.9 (distribution must be a table, never JSON/dict) and BR-P7.10 (configuration comparison table, 9 parameters) added; story coverage row noted for S7.1 (revised).
- `frontend-components.md` — frame table, component tree, test-key table updated. New keys: `scenario-compare-config-table`, `scenario-compare-distribution-table`.
- Tests: 2 new frame tests in `test_frames.py` (`test_distribution_frame_shape_and_totals`, `test_scenario_config_frame_shows_differing_effort_threshold`), reusing the existing `Scenario`/`compare()` pattern from `test_service.py`. No new smoke test needed — `test_scenario_save_and_compare_flow` already exercises this render path.
- Verified: 84/84 tests pass (was 82; +2 new).

## Post-Approval Change: Source Data View Added (2026-08-19, fourth iteration)
User requested a new option to view raw source data. Ran a short Standard-depth clarification round (`aidlc-docs/inception/requirements/source-data-view-questions.md`, 5 questions) before implementing, since scope/placement/format were underspecified. Answers: Q1=A (all six datasets), Q2=A (new sidebar nav entry), Q3=A (plain per-dataset table), Q4=A (no search/filter), Q5=B (per-dataset CSV download). All as recommended except Q5; no contradictions found, so implemented directly without reopening Application Design or Units Generation — same treatment as the earlier restyle changes.

- `frames.py` — 7 new pure functions added: `object_inventory_frame`, `usage_logs_frame`, `criticality_frame`, `data_volume_frame`, `complexity_frame`, `dependency_nodes_frame`, `dependency_edges_frame`. Each takes only `Landscape` and returns raw records with no derived columns, preserving BR-P12.2 (no Unit 2 component computes scores).
- `views/source_data.py` (new) — dataset selectbox, source (bundled/uploaded) indicator, `st.dataframe` per table, per-table "Download as CSV" button. Dependency Map splits into Nodes/Edges tabs since it has two record collections.
- `main.py` — `VIEW_NAMES` extended with `"Source Data"`; dispatch branch added.
- `requirements.md` — new §2.6.5 FR-11.1 to FR-11.4.
- `frontend-components.md` — component tree, frame table, test-key table, story coverage table all updated.
- `business-rules.md` — new `BR-P13` section (7 rules), story coverage row added for the new capability (labelled S9.1, a post-approval addition outside the original 12-story inventory).
- Tests: 7 new frame tests in `test_frames.py` (row counts: object_inventory 22, usage_logs 22, criticality 12, data_volume 22 storage sum 604, complexity 22, dependency_nodes 16, dependency_edges 21). `test_smoke_views.py` `VIEWS` tuple extended to include `"Source Data"`, reusing the existing per-view smoke-render loop.
- Verified: 82/82 tests pass (75 previous + 7 new).

## Post-Approval Change: Lighter Sidebar + Dark-Mode Toggle Disabled (2026-08-19, third iteration)
User feedback: (1) sidebar still needed to be lighter overall (even the revised dark blue was too heavy against the light/blue theme); (2) Streamlit's Settings-menu dark mode toggle produced a visually broken result.

- New palette role `sidebar_background` (`#eef4ff`, pale blue tint) added. Sidebar fill changed from a dark `header`→`accent` gradient to a light `sidebar_background`→`card` gradient. `header` (`#001d6c`) is now the sidebar **text** colour only, not a fill — 13.66:1 on `#eef4ff`, 15.08:1 on `#ffffff`, both AAA. `header` remains defined for other uses (chart markers) but no longer fills any default UI surface.
- **Root cause of the dark-mode break**: the app renders its entire look via custom CSS injected in `theme.apply()`. Streamlit's native dark theme only recolours built-in widget chrome, not this injected CSS, so the two overlapped incoherently. Fixed by disabling the switcher rather than authoring and maintaining a second, parallel dark CSS theme (out of scope for this demo/PoC) — `.streamlit/config.toml` sets `client.toolbarMode = "minimal"`.
- `business-rules.md` — BR-P1.1a revision note added; new BR-P1.6 documents the theme-switch decision.
- `test_theme_contrast.py` — added `test_header_text_passes_aa_on_sidebar_background`.
- Verified: 75/75 tests pass.

## In Flight: Frontend Design Refresh + Colour Theme (2026-08-19, seventh iteration)
User request: improve the frontend design, and fix menu colours that look wrong against the rest of the application.

**Stage**: 🔵 INCEPTION — Requirements Analysis (Standard depth). Request type Enhancement, scope single unit (`presentation-app` C11-C16), complexity Moderate. Underspecified on visual direction and layout scope, so a clarification round was opened before touching code — same treatment as the Source Data View addition.

**Root cause of the menu colours — verified, not assumed**: `.streamlit/config.toml` has a `[client]` block but **no `[theme]` block**. Confirmed empirically that `theme.primaryColor` is `None` on the installed streamlit 1.61.1, and that `#ff4b4b` (`red70`) ships in Streamlit's bundled front-end palette as the built-in default primary. Every *native* widget accent therefore renders Streamlit red: the selected sidebar nav radio dot, slider handles and filled tracks, checkbox fills, focus rings — against the app's own blue/green CSS (`#0050e6`, `#001d6c`, `#eef4ff`). **This is why iterations 1-3 did not fix it**: all three edited the CSS injected by `theme.apply()`, which cannot reach Streamlit's native widget accents. Only a `[theme]` block in `config.toml` can.

**Secondary observations recorded from code review** (offered as options, none assumed): borderless/unpadded white metric and dataframe cards on a flat `#e8e8e8` background; `warm_neutral` now byte-identical to `app_background`, so guard badges lost their intended warm tint; `PALETTE["header"].permitted_uses` still claims `"fill"` after iteration 3 removed its last fill use; `h1/h2/h3` share `#0050e6` with the interactive accent, so blue means both "heading" and "clickable"; Dashboard is a single five-section scroll with exports at the very bottom; chart titles come from Plotly on some views and `st.subheader` on others.

**Gate**: awaiting answers in `aidlc-docs/inception/requirements/frontend-design-refresh-questions.md` (10 questions). No code modified. Q3 (design scope) and Q10 (AI-DLC treatment) must agree — will be checked for contradiction before proceeding.

### Frontend Design Refresh — COMPLETE (2026-08-19, seventh iteration)
Answers: Q1=A, Q2=A, Q3=B, Q4=A, Q5=A, Q6=A, Q7=A, Q8=A, Q9=A, Q10=A. Checked for contradiction — Q3=B with Q10=A is the consistent pairing (layout refinement stays inside existing component boundaries, so no gate reopened). No clarification round needed.

**1. Native widget accent fixed at source (Q1=A).** `.streamlit/config.toml` gained a `[theme]` and a `[theme.sidebar]` block: `primaryColor` `#0050e6`, `backgroundColor` `#f4f6fa`, `secondaryBackgroundColor` `#ffffff`, `textColor` `#001d6c`, `linkColor`, `borderColor` `#d0d7e6`, `dataframeBorderColor`, `dataframeHeaderBackgroundColor`, `showWidgetBorder`, `showSidebarBorder`, `baseRadius`. **Verified through Streamlit's own delivery path**, not just the file: called `_populate_theme_msg` and inspected the `CustomThemeConfig` protobuf sent to the browser — `primary_color: "#0050e6"` for both namespaces.
- **`theme.font` deliberately left unset** — it accepts only a generic family, a `fontFaces` name, or a `name:url` pair, never a fallback stack. NFR-3.2 requires the full system-font chain for offline use, so typography stays in `theme.py` CSS. Documented deviation from the letter of Q1=A; the requirement outranks the suggestion, same precedent as BR-P1.2's forced hex substitution.
- Discovered along the way: Streamlit 1.61.1's theme config is far richer than assumed (a whole `[theme.sidebar]` namespace, `borderColor`, `showWidgetBorder`, `baseRadius`, `chartCategoricalColors`, `dataframe*`). Recorded in BR-P1.7 as the new division of labour — config owns anything it can express, CSS covers only the rest.

**2. Palette consolidated (Q5=A + Q8=A forced a structural choice).** Q5=A moved headings to navy `#001d6c`, which made `heading` byte-identical to `header` — exactly the duplicate-hex defect Q8=A asked me to fix. Rather than leave two identical roles, `header`/`heading` were **retired and consolidated into `ink`**, and `header_text` renamed `text_on_accent`. New roles: `card_border`, `gridline`, `sidebar_hover`, `ink_muted`. 14 roles total, all contrast-verified. `warm_neutral` restored to a real sand tint `#f9ecd9` (was `#e8e8e8`, identical to the page background, which had silently turned guard badges into grey chrome).
- Two new invariants added as tests (BR-P1.8): no two roles may share a hex **where their permitted uses overlap** (scoped this way because `#ffffff` is legitimately both the `card` fill and `text_on_accent`), and `warm_neutral` must be genuinely warm and distinct from both surfaces. My first attempt at the first invariant was too strict and failed on the legitimate white pair — the test was wrong, not the palette, and was corrected.
- All ratios computed with the checker re-validated against all five WCAG anchors first. Headline figures: ink 13.94/15.08/13.66/12.15:1 on the four light surfaces, accent 5.90/6.38/5.78:1, white-on-accent 6.38:1, decommission-on-sand 5.08:1. `#82ce71` still correctly fails on white and remains prohibited for text.

**3. Layout refinement (Q3=B, Q4=A, Q6=A, Q7=A, Q9=A).** `widgets.page_header` on all six views; `st.divider()` section rhythm; cards for metrics/dataframes/charts; Dashboard exports moved from `main.py` into `dashboard.render` directly under the KPI strip; sidebar split into Navigation / Scoring / Data blocks; nav radio restyled as a menu with hover and a filled selected row; chart interiors, gridlines and axis text on palette roles.
- **All chart Plotly titles removed** (BR-P6.13) — titles are now `st.subheader` in the calling view, so a section title looks the same over a chart, a table or text. This also killed a double title on the dependency heatmap ("Dependency Heatmap" from Streamlit plus "Dependency Matrix" from Plotly).
- No test key added, removed, or renamed, which is why `test_smoke_views.py` needed no changes.

**4. Documentation drift found and corrected.** `requirements.md` NFR-4.1 and §3.4.1 still described the **original green palette** (`#f2f7f1`, `#02462f`, `#0d6a4b`) — the three earlier restyles updated `business-rules.md` only, so the two documents had disagreed for four iterations. NFR-4.1 is now explicitly marked superseded rather than silently rewritten, with the live palette in new NFR-4.1a and its verified table in new §3.4.2; the green table is retained as historical. Also corrected BR-P3.1/BR-P3.2, which still said the navigation had five options after `Source Data` made it six.

**5. Accepted residual, recorded not hidden.** Two hex literals remain in `charts.py` (`#666666` threshold lines, `#9c4f1f` DMK freeze line), which technically breach BR-P1.4a. Q9=B offered to convert them and Q9=A was chosen, scoping chart work to backgrounds/gridlines/axis text. Neither is a contrast risk and `#9c4f1f` equals `category_decommission` numerically. Logged under BR-P1.4 for a later round.

**Not verifiable by the test suite, stated plainly**: the menu row styling and card treatment are CSS against Streamlit's internal `data-testid` DOM. `AppTest` runs the Python render path only — it evaluates no CSS and does not apply the `[theme]` block. Those need a human eye in a browser. The CSS is additive, so a selector broken by a future Streamlit release degrades to default chrome, not a broken layout.

**Artifacts changed**: `.streamlit/config.toml`, `theme.py` (rewritten), `charts.py` (rewritten), `widgets.py`, `main.py`, all 6 view files, `tests/app/test_theme_contrast.py` (rewritten, 8 → 12 tests), `requirements.md` (§2.6.6 FR-12.1–12.8, NFR-4.1a, NFR-4.7, §3.4.1 marked historical, new §3.4.2), `business-rules.md` (BR-P1.7, BR-P1.7a, BR-P1.8, BR-P3.1/3.2 corrected, BR-P3.6–3.8, BR-P6.13–6.16, BR-P14), `frontend-components.md` (component tree, C11/C13/C14 tables, test keys, smoke targets, story coverage).

**Verified**: 89/89 tests pass (was 85; +4 net new theme tests). `get_diagnostics` clean on all 11 touched source and test files. Headless `streamlit run` boots clean, HTTP 200, no config warnings. Throwaway verification script deleted.
