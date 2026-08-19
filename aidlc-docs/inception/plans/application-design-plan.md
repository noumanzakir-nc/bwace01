# Application Design Plan — BW-ACE

**Stage**: INCEPTION — Application Design (Part 1: Planning)
**Inputs**: `requirements/requirements.md`, `user-stories/stories.md`, `user-stories/personas.md`, `plans/execution-plan.md` (all approved)
**Scope**: High-level component identification, interfaces, and service orchestration. Detailed business rules and numeric values are deliberately **out of scope** here — they belong to Unit 1 Functional Design.

---

## 1. What This Stage Decides

The execution plan justified this stage on one point above all: NFR-8.1 requires that scoring logic contain no presentation code and presentation modules contain no scoring calculations. That boundary has to be drawn before code exists, because it is also the boundary that makes the engine independently unit-testable (NFR-7.1) and the boundary along which the two units split.

Four views, two export paths, and a scenario comparison all consume the same computed result. What that result looks like, and who is allowed to compute it, is the central decision here.

---

## 2. Questions

Six questions. Each has a recommendation with reasoning, so you can disagree on substance rather than guess.

---

### Question 1 — Engine component granularity

The source document's reference structure suggested `scoring.py`, `classification.py`, `dependency_analyzer.py`, `wave_planner.py`. The approved requirements added normalisation bands, guard rules, and data validation as distinct concerns.

How finely should the engine be divided?

A) **Coarse — 4 modules.** `scoring`, `classification`, `dependencies`, `waves`. Matches the source document's suggestion exactly. Fewest files, but normalisation, guard rules, and validation get folded into larger modules where they are harder to test in isolation.

B) **Moderate — 7 modules.** `loader` (read and validate), `normalisation` (the fixed absolute bands), `scoring` (two-axis computation), `classification` (quadrant mapping and guard rules), `dependencies` (graph build and analysis), `waves` (assignment, validation, risk), `models` (shared types). Each module has one reason to change, and the four most test-critical concerns — normalisation, scoring, classification, guard rules — are separately addressable. **(My recommendation.)**

C) **Fine — 10 or more modules.** As B, but split classification from guard rules, wave assignment from wave risk, and graph construction from graph analysis. Maximum isolation, but at this project size the indirection costs more than it returns.

X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

### Question 2 — How data moves through the engine

This is the most consequential decision in this stage, and it interacts with a known risk: the stack resolved to **pandas 3.x**, whose copy-on-write semantics and string dtype handling differ from the 2.x series most examples assume.

A) **Pandas DataFrames throughout.** One wide DataFrame carries objects, inputs, scores, and classifications. Idiomatic for Streamlit and Plotly, minimal conversion code, vectorised and fast. Weakness: column names become an untyped implicit contract, type hints add little value, and pandas 3.x behavioural changes touch every part of the engine.

B) **Typed domain objects internally, DataFrames only at the presentation boundary.** Frozen dataclasses for each object, its dimension scores, and its classification result. The engine is pure Python and fully type-hinted, so it is trivially unit-testable and pandas 3.x behaviour is confined to a thin conversion layer feeding charts and tables. Weakness: an explicit conversion step, and slightly more code. **(My recommendation.)**

C) **Hybrid — DataFrames for bulk input loading, typed objects for computed results.** Load and validate with pandas, convert to dataclasses for scoring, expose both. Pragmatic, but two representations of the same data coexist, which invites drift.

**Why I recommend B**: three approved requirements point the same way. NFR-8.3 wants type hints, which are close to meaningless over DataFrame column access. NFR-7.1 wants the engine unit-testable, which is far easier when a function takes a typed object and returns a typed result. And the pandas 3.x risk flagged in the execution plan shrinks from a project-wide concern to a boundary concern. At 22 objects there is no performance argument for vectorisation.

[Answer]: B

---

### Question 3 — Where configuration lives

NFR-8.2 requires all weights, thresholds, normalisation bands, and colour values in a single location rather than scattered as literals.

A) **A single Python module of typed constants.** One `config.py` holding frozen dataclasses for weights, thresholds, bands, guard rule parameters, and the colour palette. Type-checked, importable, no parsing, no file to keep in sync. Not editable without touching code. **(My recommendation.)**

B) **An external YAML or JSON file loaded at startup.** Lets you or a customer retune the model without editing Python. Costs a parsing and validation layer, and creates a second source of truth that can drift from the defaults the tests assert.

C) **Python defaults with optional external override.** Ship A, and load an optional external file if present to override. Most flexible, most machinery.

**Note**: this concerns *static defaults*. The live-adjustable thresholds (FR-3.3) and guard parameters (FR-3.9) are runtime UI state regardless of which option you choose, and are not affected by this answer.

[Answer]: A

---

### Question 4 — Recomputation strategy under Streamlit

Streamlit re-executes the script top to bottom on every interaction. NFR-5.1 requires recomputation under 500 ms when a threshold moves, and NFR-5.3 asks for headroom to roughly 1,000 objects.

A) **Recompute everything on every interaction, no caching.** Simplest possible model, no cache invalidation bugs, and at 22 objects certainly fast enough. Risk: the 1,000-object headroom requirement is met by hope rather than design.

B) **Cache the expensive, deterministic stages; recompute the cheap ones.** Data loading, normalisation, and per-dimension scoring depend only on the dataset, so they are computed once and cached. Threshold changes then only re-run classification and aggregation, which is trivially cheap. Directly satisfies both NFR-5.1 and NFR-5.3, and reflects a real property of the model: moving a threshold cannot change any dimension score. **(My recommendation.)**

C) **Cache everything keyed on the full configuration.** Cache the entire result keyed by dataset plus every threshold. Fast on repeated settings, but a cold cache still pays full cost and memory grows with each combination explored.

[Answer]: B

---

### Question 5 — Orchestration between engine and views

Four views, two exports, and the scenario comparison all need the same computed result.

A) **A single orchestration service.** One `AssessmentService` that takes a dataset and a configuration and returns one immutable result object containing every object's scores, classification, rationale, the dependency graph, and the wave plan. Views read from it and never compute. This is the mechanism that actually enforces NFR-8.1 rather than merely hoping for it, and it makes the scenario comparison (S7.1) natural — two configurations produce two result objects to diff. **(My recommendation.)**

B) **Views call engine modules directly.** Each view imports what it needs. Less indirection, but nothing prevents a view from doing its own arithmetic, which is precisely the NFR-8.1 violation the execution plan flagged. Also means the scenario comparison has to re-orchestrate the pipeline itself.

C) **Two services — assessment and planning.** Split scoring/classification from wave planning, since the wave planner serves a different persona and consumes different fields. Defensible, but the wave planner needs classifications as input, so the split creates a dependency between services rather than removing one.

[Answer]: A

---

### Question 6 — Schema validation for uploaded data

FR-1.4 requires uploads to be validated with clear, human-readable errors naming the offending field and record, and NFR-6.4 forbids stack traces reaching the user. Story S1.3 has four acceptance criteria on this.

A) **Hand-rolled validation.** Explicit checks per dataset: required fields, types, referential integrity between datasets. No new dependency, complete control over message wording, and the messages are the deliverable here. More code to write. **(My recommendation, narrowly.)**

B) **Pydantic.** Mature, declarative, excellent error detail. Adds a dependency, and its default messages need translating into the field-and-record phrasing S1.3 asks for.

C) **Pandera.** Purpose-built for validating tabular data, expressive about column constraints. Adds a dependency, and it is DataFrame-oriented, which sits awkwardly with a typed-domain-object engine if you chose Q2 = B.

**Why I lean A**: the requirement is not really "validate a schema" but "produce a specific quality of error message", including cross-dataset referential checks (S1.3 AC4, an object with no usage log entry) that none of these libraries handle natively. A validation library would do the easy half and leave the half that matters.

[Answer]: A

---

## 3. Execution Checklist

Executed in Part 2 after this plan is approved.

### 3.1 Preparation
- [x] Confirm component granularity from Question 1
- [x] Confirm data representation from Question 2
- [x] Confirm configuration approach from Question 3
- [x] Confirm recomputation strategy from Question 4
- [x] Confirm orchestration shape from Question 5
- [x] Confirm validation approach from Question 6
- [x] Re-read requirements §2 and §3 for interface obligations
- [x] Re-read the 22 stories to confirm every capability has a component home

### 3.2 Generate components.md
- [x] Define each component: name, purpose, responsibilities
- [x] State each component's interface at a high level
- [x] Assign each component to Unit 1 (engine) or Unit 2 (presentation)
- [x] Confirm no presentation component holds scoring logic (NFR-8.1)

### 3.3 Generate component-methods.md
- [x] Method signatures with input and output types for every component
- [x] One-line purpose per method
- [x] Explicitly defer business rules and numeric values to Functional Design
- [x] Note which methods are pure and therefore directly unit-testable

### 3.4 Generate services.md
- [x] Define the orchestration service and its responsibilities
- [x] Define the result object shape that views and exports consume
- [x] Describe orchestration sequence from raw files to rendered result
- [x] Describe how a configuration change propagates

### 3.5 Generate component-dependency.md
- [x] Dependency matrix across all components
- [x] Communication patterns
- [x] Data flow diagram, validated per `common/content-validation.md` with a text alternative
- [x] Confirm no circular dependencies
- [x] Confirm the engine has no dependency on Streamlit, Plotly, or any UI library

### 3.6 Generate application-design.md
- [x] Consolidate the four documents above into one
- [x] Include the design decisions from Questions 1 to 6 with rationale
- [x] Map every one of the 22 stories to the components that satisfy it
- [x] Map components to the two units, confirming the split is clean

### 3.7 Validate
- [x] Every functional requirement has an owning component
- [x] Every story maps to at least one component
- [x] No component has an undefined dependency
- [x] Unit 1 is independently testable without Unit 2 present
- [x] Diagrams validated before writing

### 3.8 Completion
- [x] Mark all items above [x]
- [x] Update `aidlc-docs/aidlc-state.md`
- [x] Append outcome to `aidlc-docs/audit.md`
- [x] Present completion message and await approval

---

## 4. Mandatory Artifacts

Produced regardless of the answers above:

| Artifact | Contents |
|---|---|
| `application-design/components.md` | Component definitions, purposes, responsibilities, interfaces |
| `application-design/component-methods.md` | Method signatures with input/output types |
| `application-design/services.md` | Service definitions and orchestration patterns |
| `application-design/component-dependency.md` | Dependency matrix, communication patterns, data flow |
| `application-design/application-design.md` | Consolidation of the above |

---

## 5. Out of Scope for This Stage

Deferred deliberately, to avoid pre-empting later stages:

- Exact normalisation band boundaries and complexity sub-weights → Unit 1 Functional Design
- Guard rule evaluation order and the recency multiplier → Unit 1 Functional Design
- Wave assignment algorithm detail and risk score formula → Unit 1 Functional Design
- Terracotta hex selection, palette role mapping, chart specifications → Unit 2 Functional Design
- View layout and navigation structure → Unit 2 Functional Design
- File and directory layout → Code Generation
- Dependency version pinning → Code Generation
