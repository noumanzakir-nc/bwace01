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
