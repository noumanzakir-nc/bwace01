# Components — BW-ACE

**Stage**: INCEPTION — Application Design
**Design decisions applied**: Q1=B (7 engine modules), Q2=B (typed domain objects internally, DataFrames at the presentation boundary), Q3=A (single Python config module), Q4=B (cache dataset-dependent stages), Q5=A (single orchestration service), Q6=A (hand-rolled validation)

Business rules and numeric values are deliberately absent from this document. They are defined in Unit 1 Functional Design.

---

## 1. Component Inventory

| # | Component | Unit | Depends on UI libraries | Pure |
|---|---|---|---|---|
| C1 | `models` | 1 — engine | No | n/a (types only) |
| C2 | `config` | 1 — engine | No | n/a (constants only) |
| C3 | `loader` | 1 — engine | No | No (file I/O) |
| C4 | `normalisation` | 1 — engine | No | Yes |
| C5 | `scoring` | 1 — engine | No | Yes |
| C6 | `classification` | 1 — engine | No | Yes |
| C7 | `dependencies` | 1 — engine | No | Yes |
| C8 | `waves` | 1 — engine | No | Yes |
| C9 | `export` | 1 — engine | No | Yes |
| C10 | `assessment_service` | 1 — engine | No | Yes (given a loaded landscape) |
| C11 | `theme` | 2 — presentation | Yes | n/a |
| C12 | `frames` | 2 — presentation | pandas only | Yes |
| C13 | `charts` | 2 — presentation | Yes | Yes |
| C14 | `widgets` | 2 — presentation | Yes | No (renders) |
| C15 | `views` | 2 — presentation | Yes | No (renders) |
| C16 | `app` | 2 — presentation | Yes | No (entry point) |

**NFR-8.1 compliance**: components C1–C10 have no import of Streamlit, Plotly, or any presentation library. Components C11–C16 contain no scoring, classification, dependency, or wave arithmetic — they read values from the result object produced by C10.

---

## 2. Unit 1 — Assessment Engine

### C1 — `models`

**Purpose**: Define every typed domain object that flows through the engine.

**Responsibilities**
- Declare frozen dataclasses for input records, dimension and axis scores, classifications, dependency structures, wave structures, and the consolidated result
- Provide the single vocabulary shared by all other engine components
- Contain no logic beyond trivial derived properties

**Interface**: type declarations only. No functions.

**Design note**: collection fields use `tuple` rather than `list` so that instances are immutable and safely shareable across Streamlit reruns. Immutability is what makes the result object safe to cache and to hold in session state.

---

### C2 — `config`

**Purpose**: Hold every static default in one place, satisfying NFR-8.2.

**Responsibilities**
- Axis weights for both Business Value and Technical Effort
- Normalisation band definitions per dimension
- Complexity and volume sub-weights
- Default threshold values and guard rule parameters
- Recency factor tiers
- Wave planning defaults
- Colour palette and classification colour roles
- Risk banding boundaries

**Interface**: module-level frozen dataclass instances and constants.

**Design note**: this component holds *defaults*. Runtime-adjusted values (FR-3.3, FR-3.9, FR-5.3, FR-5.4) travel as configuration objects passed into the service, never by mutating this module.

---

### C3 — `loader`

**Purpose**: Turn files on disk or uploaded bytes into a validated `Landscape`, or into a precise list of errors.

**Responsibilities**
- Read the six bundled JSON datasets
- Accept uploaded CSV or JSON replacements for any individual dataset
- Validate structure, required fields, and types
- Validate cross-dataset referential integrity, including objects with no usage record
- Produce human-readable errors naming the dataset, field, and offending record
- Compute a content fingerprint of the loaded dataset for use as a cache key
- Track which datasets are bundled and which are uploaded

**Interface**: functions returning either a validated `Landscape` or a `ValidationReport`. Never raises for user-supplied data problems.

**Satisfies**: FR-1.1, FR-1.2, FR-1.3, FR-1.4, FR-1.5, NFR-6.4

---

### C4 — `normalisation`

**Purpose**: Convert raw input values to 0–100 scores using fixed absolute bands.

**Responsibilities**
- Apply banded normalisation to each scoring dimension
- Apply the recency factor to usage frequency
- Compose the multi-attribute complexity and volume sub-scores
- Resolve solution-area inheritance, including averaging for cross-area objects
- Report, for each dimension, both the raw input and the normalised result so that derivation is displayable

**Interface**: pure functions from raw values to `DimensionScore`.

**Satisfies**: FR-2.3, FR-4.4, FR-4.5

**Design note**: normalisation depends only on the dataset, never on thresholds. This is the property that makes the Q4=B caching strategy correct.

---

### C5 — `scoring`

**Purpose**: Compute the two axis scores from normalised dimensions.

**Responsibilities**
- Weight and sum the five Business Value dimensions
- Weight and sum the two Technical Effort dimensions
- Preserve per-dimension weight and contribution for display
- Guarantee both axis totals fall within 0–100

**Interface**: pure functions from a `Landscape` and an object to a pair of `AxisScore`.

**Satisfies**: FR-2.1, FR-2.2, FR-2.4, FR-2.5

---

### C6 — `classification`

**Purpose**: Assign a category and explain why.

**Responsibilities**
- Apply the value-first quadrant mapping against the active thresholds
- Apply the dormancy ceiling and the activity floor
- Record which mechanism determined the outcome — score, dormancy ceiling, or activity floor
- Generate the plain-language rationale naming the dominant factors

**Interface**: pure functions from axis scores plus usage plus configuration to a `Classification`.

**Satisfies**: FR-3.1, FR-3.2, FR-3.5, FR-3.6, FR-3.7, FR-3.8

**Design note**: guard rules are evaluated here rather than in `scoring`, keeping scores untouched by overrides. A guard rule changes the *category*, never the numbers, which is what allows the UI to show an object sitting on the "wrong" side of a boundary and explain it (story S3.3 AC3).

---

### C7 — `dependencies`

**Purpose**: Build and interrogate the dependency graph.

**Responsibilities**
- Construct a directed graph from nodes and edges using NetworkX
- Expand the `ALL` wildcard edge across every solution area
- Compute per-area incoming and outgoing degree
- Produce the area-by-area adjacency matrix for the heatmap
- Resolve an object's incoming and outgoing edges via its solution area
- Expose graph layout positions for the network visualisation

**Interface**: pure functions producing a `DependencyGraph`.

**Satisfies**: FR-4.1, FR-4.2, FR-4.3, FR-4.6, FR-6.6, FR-7.4

**Design note**: this component returns layout coordinates but draws nothing. Rendering belongs to C13.

---

### C8 — `waves`

**Purpose**: Produce a migration wave plan with risk and violations.

**Responsibilities**
- Assign objects to waves led by migration priority
- Compute wave date ranges from start date, wave count, and duration
- Detect dependency violations against the graph
- Compute per-wave risk from complexity, cross-wave dependencies, and downtime tolerance
- Add the DMK constraint contribution for waves completing before 2028
- Band risk scores

**Interface**: pure functions from assessments plus graph plus wave configuration to a `WavePlan`.

**Satisfies**: FR-5.1 to FR-5.9, FR-8.1, FR-8.3, FR-8.4

---

### C9 — `export`

**Purpose**: Serialise results for download.

**Responsibilities**
- Produce the classification report as CSV text
- Produce the wave recommendation as a JSON-serialisable structure
- Embed the active configuration into both, so exports are self-describing

**Interface**: pure functions from an `AssessmentResult` to `str` and to `dict`.

**Satisfies**: FR-10.1, FR-10.2, FR-10.3

**Design note**: placed in Unit 1 despite being an output concern, because serialisation is pure and story S7.2 carries five acceptance criteria worth unit-testing. C15 only wires the download control.

---

### C10 — `assessment_service`

**Purpose**: The single orchestrator. Turns a landscape plus a configuration into one immutable result.

**Responsibilities**
- Sequence loading, normalisation, scoring, classification, dependency analysis, and wave planning
- Assemble the `AssessmentResult`
- Compute landscape KPIs
- Compute the classification distribution
- Support scenario comparison by producing two results and diffing them
- Expose the caching seam described in `services.md`

**Interface**: see `services.md`.

**Satisfies**: FR-6.1, FR-9.1, FR-9.2, and the orchestration implied by every view story

---

## 3. Unit 2 — Presentation App

### C11 — `theme`

**Purpose**: Apply the brand palette and typography.

**Responsibilities**
- Streamlit theme configuration
- CSS injection for elements the theme cannot reach
- Web font link with a full system fallback stack
- Expose classification colour roles for chart and badge use

**Satisfies**: NFR-3.2, NFR-4.1, NFR-4.3, NFR-4.4

**Design note**: exact hex values and role mapping are decided in Unit 2 Functional Design, not here.

---

### C12 — `frames`

**Purpose**: The single conversion boundary from typed domain objects to pandas DataFrames.

**Responsibilities**
- Convert assessments to display frames for tables and charts
- Convert score breakdowns to a derivation frame
- Convert the wave plan to a Gantt-shaped frame
- Convert the adjacency matrix to a heatmap frame

**Satisfies**: the Q2=B boundary decision

**Design note**: this is the only component in the system that touches pandas. Confining it here is what reduces the pandas 3.x risk from project-wide to local, as argued in the execution plan §1.4.

---

### C13 — `charts`

**Purpose**: Build Plotly figures.

**Responsibilities**
- Classification donut, top-objects bar, Value/Effort quadrant scatter
- Dependency matrix heatmap and network node-link graph
- Wave Gantt timeline with the DMK marker
- Apply theme colours and ensure labels, legends, and hover text are present

**Satisfies**: FR-6.2, FR-6.3, FR-6.4, FR-6.6, FR-8.2, NFR-4.6

---

### C14 — `widgets`

**Purpose**: Reusable UI fragments.

**Responsibilities**
- Executive KPI strip
- Classification badge carrying colour plus text label
- Guard-rule badge naming the rule that fired
- Score derivation table
- Threshold and guard parameter controls with current value and default shown
- Validation error and warning presentation

**Satisfies**: FR-6.1, FR-3.3, FR-3.4, FR-3.8, FR-7.5, NFR-4.5, NFR-6.2

---

### C15 — `views`

**Purpose**: The four views plus scenario comparison.

**Responsibilities**
- `dashboard` — KPI strip, classification charts, quadrant scatter, decommission candidates
- `object_detail` — metadata, classification, usage, dependencies, derivation, rationale
- `dependency_view` — matrix heatmap and network graph
- `wave_planner` — assignments, timeline, risk, violations
- `scenario_compare` — save, select, and diff two configurations
- Wire export download controls

**Satisfies**: FR-6.x, FR-7.x, FR-8.x, FR-9.x, FR-10.x presentation aspects

---

### C16 — `app`

**Purpose**: Streamlit entry point.

**Responsibilities**
- Page configuration and theme application
- Persistent sidebar navigation across all views
- Session state ownership: active configuration, loaded landscape, saved scenarios
- Data upload and revert controls
- Invoke the service and pass the result to the selected view

**Satisfies**: NFR-6.1, FR-1.3, FR-1.5

---

## 4. Story Coverage

| Story | Components |
|---|---|
| S1.1 | C3, C10, C16 |
| S1.2 | C3, C10, C16 |
| S1.3 | C3, C14, C16 |
| S2.1 | C4, C5 |
| S2.2 | C6 |
| S2.3 | C6, C14 |
| S2.4 | C6, C10, C14, C16 |
| S3.1 | C10, C14, C15 |
| S3.2 | C12, C13, C15 |
| S3.3 | C12, C13, C15 |
| S3.4 | C6, C12, C15 |
| S4.1 | C7, C12, C15 |
| S4.2 | C4, C5, C6, C14, C15 |
| S5.1 | C7, C12, C13, C15 |
| S6.1 | C8, C15 |
| S6.2 | C8, C14, C16 |
| S6.3 | C8, C13, C15 |
| S6.4 | C8, C15 |
| S7.1 | C10, C15 |
| S7.2 | C9, C15 |
| S8.1 | C16 plus launch scripts (Code Generation) |
| S8.2 | C11, C13, C14 |
| S8.3 | C10, C11 |

Every story has at least one owning component. Every component serves at least one story.
