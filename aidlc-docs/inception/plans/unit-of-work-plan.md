# Unit of Work Plan — BW-ACE

**Stage**: INCEPTION — Units Generation (Part 1: Planning)
**Inputs**: approved requirements, 22 stories, 3 personas, execution plan, and the five Application Design artifacts
**Purpose**: Decide how the system is decomposed into units of work for development, and how code is organised on disk.

---

## 1. Context

A unit of work is a logical grouping of stories for development. Each unit runs its own Construction loop — Functional Design, then Code Generation — before the next begins.

Two things are already settled and are **not** reopened here:

- The **execution plan** (approved) recommended two units, `assessment-engine` and `presentation-app`, and set the build order.
- **Application Design** (approved) established 16 components in six layers, with the unit boundary between Layer 1 and Layer 2, crossed outward by exactly one type: `AssessmentResult`.

What remains is to confirm the decomposition, resolve where a few boundary-straddling stories belong, and decide the on-disk structure. BW-ACE is a **monolith** — one Streamlit process — so units are logical modules within one deployable application, not independently deployable services.

---

## 2. Questions

Seven questions. Recommendations given with reasoning.

---

### Question 1 — Unit decomposition

Application Design assigned every component to one of two units. Confirm or change that.

A) **Two units** — `assessment-engine` (C1–C10) and `presentation-app` (C11–C16). Matches the approved execution plan and the component layering. The engine is built and verified against the reference distribution before any view exists, which is what mitigates the top risk in the plan: a scoring defect reaching a customer demo. **(My recommendation.)**

B) **One unit** — build everything in a single Construction loop. Fewest gates and fastest to a running app. Cost: the engine and the UI are designed and generated together, so there is no checkpoint at which scoring correctness has been established independently. A scoring bug then surfaces during UI work, where it is harder to isolate.

C) **Three units** — `assessment-engine` (C1–C7, C9, C10), `wave-planning` (C8), `presentation-app` (C11–C16). Arguable on domain grounds: wave planning serves a different persona (Programme Manager) and consumes different fields (`migration_priority`, `downtime_tolerance_hours`) that the classification model never touches. Cost: `C8 waves` depends on classifications, so this adds a dependency rather than removing one, plus two extra approval gates.

D) **Two units split differently** — `data-and-scoring` (C1–C6) and `analysis-and-presentation` (C7–C16). Puts dependency and wave analysis with the UI. I would not recommend it: it places pure computation in the presentation unit, weakening the NFR-8.1 boundary that Application Design established structurally.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 2 — Boundary-straddling stories

Three of the 22 stories touch both units. How should they be assigned?

- **S1.3 Understand why my data was rejected** — validation logic is C3 (engine); error presentation is C14/C16 (app)
- **S2.4 Test how sensitive my recommendation is** — classification is C6 (engine); the controls are C14/C16 (app)
- **S8.3 Work offline and respond instantly** — caching is C10 (engine); font fallback is C11 (app)

A) **Assign to the unit owning the primary behaviour, note the secondary.** S1.3 and S2.4 to the engine (the logic is the substance; presentation is a thin wiring), S8.3 to the presentation app (the user-visible concern is typography and responsiveness). Each story is listed once as owner with a cross-reference. **(My recommendation.)**

B) **Split each into two sub-stories**, one per unit, so no story spans a boundary. Cleaner traceability per unit; inflates the story count to 25 and fragments acceptance criteria that read naturally together.

C) **Assign all three to the presentation app**, on the basis that the user-observable outcome is what the story describes. Simple rule, but it would place the engine's own validation and caching acceptance criteria outside the unit that implements them.

X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

### Question 3 — Inter-unit dependency and integration

Application Design settled *what* crosses the boundary (`AssessmentResult` outward; `Landscape` and two config objects inward). This question is about *how* the units relate as code.

A) **One Python project, two packages.** A single `pyproject.toml`, with the engine and app as sibling packages in one importable tree. The app imports the engine directly. Simplest to build and run; the boundary is enforced by import discipline and verified by the dependency checks already in Application Design. **(My recommendation.)**

B) **Two installable packages** with separate dependency manifests, the app declaring the engine as a dependency. Makes the boundary structurally unbreakable and would let the engine be reused elsewhere. Costs a build and local-install step, which works against NFR-2.3's "Python is the only prerequisite" and NFR-2.5's fast second run.

C) **One package, module-level separation only.** Everything in one package with subdirectories. Least ceremony; weakest boundary signal.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 4 — Team alignment and ownership

Unit decomposition is often driven by enabling parallel work across people.

A) **Single developer, sequential.** Units exist to sequence the work and create verification checkpoints, not to parallelise it. Build order is strictly engine then app. **(My recommendation, and my assumption unless told otherwise — this is a PoC being assembled for a demo.)**

B) **Multiple developers, parallel.** Units are ownership boundaries and both could progress simultaneously against an agreed interface. This would change my advice on Question 3 toward option B, since a hard contract matters more when two people work either side of it.

C) **Single developer, but structure for possible handover.** Sequential build, but documentation and boundaries treated as if another person will take over.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 5 — Technical considerations: does the engine need a second consumer?

The engine is pure Python with no UI dependency. That makes a non-UI entry point cheap to add.

A) **No — Streamlit is the only consumer.** Build exactly what the stories require. **(My recommendation.)**

B) **Add a small CLI** that runs the assessment and writes the classification CSV and wave JSON without launching the UI. Useful for regenerating outputs in a batch, and it independently proves the engine has no UI coupling. Modest effort, but no approved story asks for it, so it is scope beyond the requirements.

C) **Expose the engine as an importable library with a documented public API**, on the assumption it may be embedded elsewhere later. More documentation effort for speculative benefit.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 6 — Business domain boundaries

Requirements assumption A-7 recorded that `migration_priority` and `downtime_tolerance_hours` feed the wave planner only and never the classification model. That is a genuine seam between two bounded contexts: *assessment* (what should happen to each object) and *planning* (in what order and at what risk).

Should that seam shape the units?

A) **No — keep planning inside the engine unit.** The seam is real but thin, and wave planning depends on classification output, so separating them creates a dependency chain without reducing coupling. Reflect the seam in module structure (`waves` as its own module, which Application Design already does) rather than in unit structure. **(My recommendation.)**

B) **Yes — planning becomes its own unit.** This is Question 1 option C. Honours the domain boundary and the persona split at the cost of two extra gates.

C) **Yes, but as a sub-package rather than a unit** — group `waves` under a `planning` sub-package inside the engine to make the seam visible in the directory tree without adding a Construction loop.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 7 — Code organisation on disk

The AI-DLC rules give three greenfield patterns. For a monolith with multiple units the pattern is `src/{unit-name}/` and `tests/{unit-name}/`.

Your source requirement document (§4.2) suggested a different, flatter layout: `app.py` at the root with `engine/`, `ui/`, `data/`, `demo/`, `outputs/`. You noted the structure was a reference and could change for technical reasons.

A) **AI-DLC monolith pattern, unit-named.**
```
src/bwace/engine/        Unit 1 — models, config, loader, normalisation,
                         scoring, classification, dependencies, waves,
                         export, service
src/bwace/app/           Unit 2 — theme, frames, charts, widgets, views
src/bwace/app/main.py    Streamlit entry point
tests/engine/            Unit 1 tests
tests/app/               Unit 2 smoke tests
data/                    the six bundled JSON datasets
run.bat  run.sh  pyproject.toml  README.md
```
Follows the prescribed pattern, keeps the unit boundary visible in the tree, and a single top-level package avoids import ambiguity. **(My recommendation.)**

B) **Close to the source document's layout.**
```
app.py                   Streamlit entry point at root
engine/                  Unit 1
ui/                      Unit 2
data/                    bundled datasets
tests/
```
Familiar to anyone reading the original requirement document, and shallower. Deviates from the AI-DLC pattern, and top-level packages named `engine` and `ui` are generic enough to risk import collisions.

C) **Hybrid** — `src/` layout as in A, but with directories named `engine/` and `ui/` to echo the source document's vocabulary rather than `engine/` and `app/`.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## 3. Execution Checklist

Executed in Part 2 after this plan is approved.

### 3.1 Preparation
- [x] Confirm decomposition from Question 1
- [x] Confirm boundary-straddling story assignment from Question 2
- [x] Confirm integration approach from Question 3
- [x] Confirm ownership model from Question 4
- [x] Confirm engine consumers from Question 5
- [x] Confirm domain boundary treatment from Question 6
- [x] Confirm directory structure from Question 7
- [x] Re-read Application Design component-to-unit assignments

### 3.2 Generate unit-of-work.md
- [x] Define each unit: name, purpose, scope, responsibilities
- [x] List the components each unit contains
- [x] State each unit's external interface
- [x] Record build order with reasoning
- [x] **Greenfield**: document the code organisation strategy and full directory tree
- [x] State the verification criteria that must hold before a unit is considered done

### 3.3 Generate unit-of-work-dependency.md
- [x] Unit dependency matrix
- [x] Direction and nature of every inter-unit dependency
- [x] The exact types crossing each boundary
- [x] Confirm no circular dependencies between units
- [x] Confirm Unit 1 is buildable and testable with Unit 2 absent
- [x] Record the integration and verification checkpoint between units

### 3.4 Generate unit-of-work-story-map.md
- [x] Map all 22 stories to units
- [x] Mark owner unit and any contributing unit for boundary-straddling stories
- [x] Confirm every story is assigned
- [x] Confirm every acceptance criterion has an implementing unit
- [x] Summarise story counts and epic coverage per unit

### 3.5 Validate
- [x] Every story assigned to exactly one owning unit
- [x] Every component assigned to exactly one unit
- [x] No unit depends on a later unit in the build order
- [x] Unit 1 verification is possible without Unit 2
- [x] Directory structure covers every component
- [x] Diagrams validated per `common/content-validation.md`, with text alternatives

### 3.6 Completion
- [x] Mark all items above [x]
- [x] Update `aidlc-docs/aidlc-state.md`
- [x] Append outcome to `aidlc-docs/audit.md`
- [x] Present completion message and await approval

---

## 4. Mandatory Artifacts

| Artifact | Contents |
|---|---|
| `application-design/unit-of-work.md` | Unit definitions, responsibilities, build order, and the greenfield code organisation strategy |
| `application-design/unit-of-work-dependency.md` | Unit dependency matrix and boundary contracts |
| `application-design/unit-of-work-story-map.md` | All 22 stories mapped to units |

---

## 5. Reference — AI-DLC Greenfield Structure Patterns

From `construction/code-generation.md`, for context on Question 7:

| Project shape | Pattern |
|---|---|
| Greenfield, single unit | `src/`, `tests/`, `config/` at workspace root |
| Greenfield, multi-unit microservices | `{unit-name}/src/`, `{unit-name}/tests/` |
| Greenfield, multi-unit monolith | `src/{unit-name}/`, `tests/{unit-name}/` |

BW-ACE is a multi-unit monolith: one process, one deployable, logical modules within it.

**Fixed rules regardless of the answer to Question 7**: application code lives at the workspace root, never inside `aidlc-docs/`; `aidlc-docs/` holds documentation only.

---

## 6. Out of Scope for This Stage

- Normalisation bands, sub-weights, guard rule ordering, wave algorithm → Unit 1 Functional Design
- Colour system, view layout, chart specifications → Unit 2 Functional Design
- Individual file names within each package, dependency version pins → Code Generation
- Test framework selection → Code Generation
