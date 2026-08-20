# Units of Work — BW-ACE

**Stage**: INCEPTION — Units Generation
**Project shape**: Greenfield, multi-unit **monolith** — one Streamlit process, one deployable, logical modules within it
**Decisions applied**: Q1=A (two units), Q2=B (split boundary-straddling stories), Q3=A (one project, two packages), Q4=A (single developer, sequential), Q5=A (Streamlit the only consumer), Q6=A (planning stays inside the engine unit), Q7=A (AI-DLC monolith structure pattern)

---

## 1. Decomposition Summary

| Unit | Name | Components | Stories | Depends on |
|---|---|---|---|---|
| 1 | `assessment-engine` | C1–C10 | 14 | nothing |
| 2 | `presentation-app` | C11–C16 | 12 | Unit 1 |

**Build order**: Unit 1, then Unit 2. Strictly sequential — Q4=A confirmed a single developer, so units exist to create verification checkpoints rather than to parallelise work.

Units are **logical modules**, not independently deployable services. There is one process and one deployable artifact.

---

## 2. Unit 1 — `assessment-engine`

### Purpose

Turn six datasets into a complete, explained assessment: every object scored on two axes, classified, with dependencies resolved and a migration wave plan produced. Pure computation with no user interface.

### Scope

| Component | Responsibility |
|---|---|
| C1 `models` | Typed frozen domain objects; the shared vocabulary |
| C2 `config` | Every static default — weights, bands, thresholds, palette values, guard parameters |
| C3 `loader` | Read bundled files and uploads, validate, fingerprint |
| C4 `normalisation` | Raw values to 0–100 via fixed absolute bands; area inheritance |
| C5 `scoring` | Weight and sum both axes, preserving per-dimension contributions |
| C6 `classification` | Quadrant mapping, guard rules, rationale generation |
| C7 `dependencies` | Graph construction, wildcard expansion, degrees, matrix, layout |
| C8 `waves` | Wave assignment, violation detection, risk scoring |
| C9 `export` | CSV and JSON serialisation with configuration embedded |
| C10 `service` | Orchestration; the sole outward interface |

### External interface

Outward: `AssessmentResult`.
Inward: `Landscape`, `ScoringConfig`, `WaveConfig`.

Nothing else crosses the boundary. No component in this unit imports Streamlit, Plotly, or pandas.

### Dependencies

None on other units. Only `networkx` from outside the standard library, and only in C7.

### Definition of done

Unit 1 is complete when all of the following hold, verifiable without Unit 2 existing:

| # | Criterion |
|---|---|
| 1 | Bundled dataset loads and validates, producing 22 objects across 12 solution areas, one of which (`ZMD1`) is cross-area |
| 2 | Every object carries both axis scores and a classification; none null |
| 3 | Reference distribution is exactly 5 Rebuild, 13 Replicate As-Is, 4 Decommission |
| 4 | Rebuild set is exactly `SC100`, `SC200`, `SA100`, `PR100`, `PR200` |
| 5 | Decommission set is exactly `IN200`, `TR100`, `TR200`, `TM100` |
| 6 | `IN200` is Decommission by dormancy ceiling; `IM100` is Replicate As-Is by activity floor; comparing `classify` against `classify_by_score` shows exactly those two differences |
| 7 | Lowering the Effort threshold to 66 moves `FI100GC` to Rebuild |
| 8 | `ALL → DMK` expands to 12 outgoing edges, one per solution area |
| 9 | Wave plan assigns every object exactly once; violations are detected; risk decomposes into named contributions |
| 10 | Malformed input returns a `ValidationReport` naming dataset, field, and record — never raises |
| 11 | Exports contain 22 data rows and embed the configuration that produced them |
| 12 | All Unit 1 unit tests pass |

Criterion 6 is the one that matters most: it is the check that would have caught the `IM100` misclassification found during Requirements Analysis.

**Correction (2026-08-18)**: criteria 1, 11 and Unit 2 criterion 3 originally stated 23 objects. The dataset contains **22** objects; the 23 figure was the story count, mistakenly carried across. Verified by counting source §3.1 (22 records) and corroborated by the reference distribution, since 5 + 13 + 4 = 22. `ZMD1` is one of the 22, not an additional object.

---

## 3. Unit 2 — `presentation-app`

### Purpose

Present the assessment through four views serving three personas, on-brand and accessible, with live configuration controls, scenario comparison, and export.

### Scope

| Component | Responsibility |
|---|---|
| C11 `theme` | Palette application, CSS, web font with system fallback |
| C12 `frames` | The only pandas-touching module; domain objects to DataFrames |
| C13 `charts` | Donut, top-value bar, quadrant scatter, heatmap, network graph, Gantt |
| C14 `widgets` | KPI strip, classification and guard badges, derivation table, controls, validation panel |
| C15 `views` | Dashboard, object detail, dependency view, wave planner, scenario compare |
| C16 `main` | Entry point, sidebar navigation, session state, upload and revert |

### External interface

Consumes `AssessmentResult` from Unit 1. Passes `Landscape`, `ScoringConfig`, and `WaveConfig` inward. Performs no scoring, classification, dependency, or wave arithmetic.

### Dependencies

Unit 1, plus `streamlit`, `plotly`, and `pandas`.

### Definition of done

| # | Criterion |
|---|---|
| 1 | All four views plus scenario comparison render without error |
| 2 | Sidebar navigation reaches every view at all times |
| 3 | KPI strip shows 22 objects, total storage, decommission percentage, reclaimable storage |
| 4 | Threshold controls display current value and default; changes propagate live to every view |
| 5 | Reset restores defaults and the reference distribution |
| 6 | Guard-rule badges appear on `IN200` (dormancy ceiling) and `IM100` (activity floor) naming the rule that determined the outcome; a separate dormancy note appears on `TR200` and `TM100`, where the predicate fires but does not change the classification |
| 7 | Every text and background combination meets WCAG 2.1 AA; `#82ce71` never used as text on a light background |
| 8 | No element conveys classification by colour alone |
| 9 | All views render with the network disconnected; typography falls back without breaking layout |
| 10 | Threshold change recomputes and re-renders in under 500 ms |
| 11 | Upload rejection shows a readable message; no traceback reaches the user |
| 12 | Download controls produce the CSV and JSON from Unit 1 |
| 13 | `run.bat` and `run.sh` both start the application from a clean checkout |
| 14 | All Unit 2 smoke tests pass |

---

## 4. Code Organisation Strategy

Q7=A selected the AI-DLC greenfield multi-unit monolith pattern: `src/{unit}/` and `tests/{unit}/`. Q3=A selected one project with two packages under a single `pyproject.toml`.

### 4.1 Directory tree

```
c:\git\rfp\acme-sap\
├── pyproject.toml                       single project definition, pinned deps
├── README.md                            setup and run for Windows and Linux
├── run.bat                              Windows launcher
├── run.sh                               Linux and macOS launcher
├── .gitignore
│
├── data/                                bundled Acme datasets (source sections 3.1-3.6)
│   ├── object_inventory.json
│   ├── usage_logs.json
│   ├── criticality.json
│   ├── dependencies.json
│   ├── data_volume.json
│   └── complexity.json
│
├── src/
│   └── bwace/
│       ├── __init__.py
│       │
│       ├── engine/                      UNIT 1 - assessment-engine
│       │   ├── __init__.py
│       │   ├── models.py                C1
│       │   ├── config.py                C2
│       │   ├── loader.py                C3
│       │   ├── normalisation.py         C4
│       │   ├── scoring.py               C5
│       │   ├── classification.py        C6
│       │   ├── dependencies.py          C7
│       │   ├── waves.py                 C8
│       │   ├── export.py                C9
│       │   └── service.py               C10
│       │
│       └── app/                         UNIT 2 - presentation-app
│           ├── __init__.py
│           ├── main.py                  C16  Streamlit entry point
│           ├── theme.py                 C11
│           ├── frames.py                C12
│           ├── charts.py                C13
│           ├── widgets.py               C14
│           └── views/
│               ├── __init__.py
│               ├── dashboard.py         C15
│               ├── object_detail.py     C15
│               ├── dependency_view.py   C15
│               ├── wave_planner.py      C15
│               └── scenario_compare.py  C15
│
├── tests/
│   ├── engine/                          UNIT 1 tests
│   │   ├── test_loader.py
│   │   ├── test_normalisation.py
│   │   ├── test_scoring.py
│   │   ├── test_classification.py
│   │   ├── test_dependencies.py
│   │   ├── test_waves.py
│   │   ├── test_export.py
│   │   ├── test_service.py
│   │   └── test_reference_dataset.py    the 5/13/4 and edge-case assertions
│   └── app/                             UNIT 2 tests
│       ├── test_frames.py
│       ├── test_theme_contrast.py       computes contrast ratios programmatically
│       └── test_smoke_views.py
│
└── aidlc-docs/                          DOCUMENTATION ONLY - never application code
```

### 4.2 Structure rationale

**Why `src/bwace/` rather than top-level `engine/` and `ui/`** (as the source document §4.2 suggested): a single top-level package removes any chance of the generic names `engine`, `ui`, or `app` colliding with an installed distribution. It also makes the import path state which project a module belongs to, which matters once tests, launcher scripts, and Streamlit all import the same tree.

**Why a `src/` layout**: the package cannot be imported accidentally from the working directory, so tests exercise the installed package rather than a shadow copy. This is what makes "the tests passed" mean the same thing as "the app will work".

**Why one `pyproject.toml`** (Q3=A): the launcher does one editable install and both packages are importable. Two manifests would need a build and local-install step per unit, working against NFR-2.3's "Python is the only prerequisite" and NFR-2.5's fast second run.

**Why `tests/engine/` and `tests/app/`**: mirrors the unit split, so Unit 1 tests can be run alone during Unit 1 Construction, before any Unit 2 file exists.

**Why `data/` at root rather than inside the package**: the six datasets are user-facing content that a presenter may want to inspect or replace, not library resources.

### 4.3 Deviation from the source document, recorded

Source §4.2 proposed `app.py` at root with `engine/`, `ui/`, `data/`, `demo/`, `outputs/`. This plan differs in three ways:

| Source | Here | Why |
|---|---|---|
| `app.py` at root | `src/bwace/app/main.py` | AI-DLC monolith pattern; avoids import shadowing |
| `ui/` | `src/bwace/app/` | Aligns the directory name with the unit name `presentation-app` |
| `demo/` with a data generator | omitted | The datasets are fixed and specified in full in source §3.1–3.6. Generating them adds a component with no story behind it. |
| `outputs/` with pre-written files | omitted | Q12=B chose on-demand export, so files are produced by download rather than written to disk |

You noted the structure was a reference that could change for technical reasons. These are those reasons, recorded so the deviation is visible rather than silent.

### 4.4 Fixed rules

- Application code lives at the workspace root tree, **never** inside `aidlc-docs/`
- `aidlc-docs/` holds markdown documentation only
- Unit 1 files never import from `src/bwace/app/`

---

## 5. Domain Boundary Treatment

Q6=A kept wave planning inside Unit 1.

The seam is real: requirements assumption A-7 established that `migration_priority` and `downtime_tolerance_hours` feed the wave planner alone and are never used by the classification model. That is a genuine division between two bounded contexts — *assessment* (what should happen to each object) and *planning* (in what order, at what risk) — and it lines up with the persona split, since the Programme Manager is the wave planner's primary user.

It is not made a unit boundary because `C8 waves` consumes classification output. Separating them would introduce a dependency chain rather than remove coupling, and would add two approval gates for no verification benefit. The seam is instead expressed as a module boundary: `waves.py` is its own module with its own tests, importing from `models` and `config` but not from `classification`.

---

## 6. Verification Checkpoint Between Units

Unit 1 must satisfy all twelve of its completion criteria before Unit 2 Construction begins. This is the checkpoint that the two-unit split exists to create.

The rationale, from execution plan §1.4: the highest-consequence risk on this project is a visibly wrong recommendation reaching a customer demo. Requirements Analysis already demonstrated the failure mode — reasoning about the model on paper produced one that classified a dormant object as worth keeping and an actively used object as safe to switch off. Both were caught only by running it against real data.

Establishing the reference distribution before any view exists means a later disagreement between screen and expectation is a presentation defect, not a scoring one. That halves the search space for every bug found during Unit 2.
