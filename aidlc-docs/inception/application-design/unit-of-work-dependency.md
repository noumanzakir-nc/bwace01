# Unit of Work Dependencies — BW-ACE

**Stage**: INCEPTION — Units Generation

---

## 1. Unit Dependency Matrix

Rows depend on columns.

| depends on → | Unit 1 `assessment-engine` | Unit 2 `presentation-app` |
|---|---|---|
| **Unit 1 `assessment-engine`** | — | **No** |
| **Unit 2 `presentation-app`** | **Yes** | — |

Single dependency, one direction. No cycles.

---

## 2. Boundary Contract

Exactly four types cross the boundary.

### Outward — Unit 1 to Unit 2

| Type | Purpose |
|---|---|
| `AssessmentResult` | The complete computed assessment: per-object scores with derivation, classifications with determinant and rationale, dependency graph, wave plan, KPIs, and the configuration that produced it |

### Inward — Unit 2 to Unit 1

| Type | Purpose |
|---|---|
| `Landscape` | The validated dataset, obtained by Unit 2 calling `loader` and passed to `service` |
| `ScoringConfig` | Live thresholds and guard rule parameters from the UI controls |
| `WaveConfig` | Live wave count, duration, and start date from the UI controls |

Two further types cross for error handling:

| Type | Direction | Purpose |
|---|---|---|
| `ValidationReport` | outward | Upload validation outcome, rendered by C14 |
| `Scenario` | inward | A named configuration pair for comparison |

### Called interface

Unit 2 calls only `C10 service` and `C3 loader`. It does not call C4–C9 directly. `C9 export` is invoked through the download controls but takes an `AssessmentResult`, so it needs no other engine knowledge.

---

## 3. Dependency Nature

| Property | Value |
|---|---|
| Coupling mechanism | Direct Python import within one project (Q3=A) |
| Coupling strength | Loose — one aggregate type outward, three configuration types inward |
| Communication | Synchronous function calls, immutable arguments |
| Shared mutable state | None |
| Network or IPC | None |
| Serialisation across the boundary | None — same process, same objects |
| Versioning | Not applicable — single project, single version |

Because both units live in one process and one repository, there is no contract versioning problem. The boundary is a code discipline, verified by the checks in §5.

---

## 4. Build and Integration Sequence

```
STEP 1  Unit 1 — assessment-engine
        Functional Design  ->  Code Generation  ->  Unit 1 tests pass
        │
        │  GATE: all 12 Unit 1 completion criteria met
        │  (reference distribution 5/13/4, guard rules affect exactly
        │   IN200 and IM100, FI100GC flips at Effort 66, ALL->DMK
        │   expands to 12 edges, validation never raises)
        v
STEP 2  Unit 2 — presentation-app
        Functional Design  ->  Code Generation  ->  Unit 2 smoke tests pass
        │
        v
STEP 3  Build and Test
        Full suite, launch scripts verified from clean state,
        reference distribution confirmed end to end
```

Unit 1 is fully verifiable at the gate with no Unit 2 file present. This is the whole point of the split.

---

## 5. Unit Independence Verification

| Check | Result | How it is enforced |
|---|---|---|
| Does Unit 1 import anything from Unit 2? | No | No `from bwace.app` import may appear in `src/bwace/engine/` |
| Does Unit 1 import Streamlit? | No | Absent from engine imports |
| Does Unit 1 import Plotly? | No | Absent from engine imports |
| Does Unit 1 import pandas? | No | pandas confined to C12 in Unit 2 |
| Can Unit 1 be tested with Unit 2 absent? | Yes | `tests/engine/` imports only `bwace.engine` |
| Can Unit 1 be tested without a display or browser? | Yes | Pure functions and file I/O only |
| Does Unit 2 perform any scoring arithmetic? | No | It holds outputs, never the inputs required to score |
| Is the boundary enforced structurally or by convention? | Structurally | Unit 2 receives a computed `AssessmentResult`; the data needed to score is not in scope |

### External library reach

| Library | Reaches | Unit |
|---|---|---|
| stdlib only | C1, C2, C3, C4, C5, C6, C8, C9, C10 | 1 |
| `networkx` | C7 only | 1 |
| `pandas` | C12 only | 2 |
| `plotly` | C13 only | 2 |
| `streamlit` | C11, C14, C15, C16 | 2 |

Nine of Unit 1's ten components need nothing beyond the Python standard library. That is why Unit 1 tests require no fixtures beyond data, satisfying NFR-7.1.

---

## 6. Data Flow Across the Boundary

```
                        UNIT 2  presentation-app
                        ┌──────────────────────────────────────┐
                        │  C16 main                            │
   user interaction ───>│    reads controls, owns session state│
                        └───────────────┬──────────────────────┘
                                        │
             Landscape, ScoringConfig, WaveConfig  (inward)
                                        │
                                        v
                        UNIT 1  assessment-engine
                        ┌──────────────────────────────────────┐
                        │  C3 loader   -> Landscape            │
                        │  C10 service -> compute_base CACHED  │
                        │              -> apply_config         │
                        │     delegating to C4 C5 C6 C7 C8     │
                        └───────────────┬──────────────────────┘
                                        │
                          AssessmentResult  (outward)
                                        │
                                        v
                        UNIT 2  presentation-app
                        ┌──────────────────────────────────────┐
                        │  C12 frames  -> DataFrames           │
                        │  C13 charts  -> Plotly figures       │
                        │  C14 widgets -> KPI strip, badges    │
                        │  C15 views   -> rendered screens     │
                        │  C9 export   -> CSV and JSON download│
                        └──────────────────────────────────────┘
```

The inward direction carries only configuration and data. The outward direction carries only computed results. Nothing loops back.

---

## 7. Risks in the Unit Structure

| Risk | Level | Assessment | Mitigation |
|---|---|---|---|
| Boundary erosion during Unit 2 work | Low | The tempting shortcut is a small calculation inside a view, for instance recomputing a percentage. | `AssessmentResult` already carries KPIs and distribution, so the shortcut has no motive. Import discipline checked at Build and Test. |
| `AssessmentResult` becoming a god object | Moderate | A single aggregate accumulates fields as views ask for more. | Grouped sub-objects (`kpis`, `wave_plan`, `graph`) rather than a flat structure |
| Unit 1 gate slipping | Low | Temptation to start Unit 2 before all twelve criteria pass. | The reference-distribution test is binary and cheap to run |
| Sequential build has no parallel slack | Accepted | Q4=A confirmed a single developer, so there is nothing to parallelise. | None needed |
| One `pyproject.toml` weakens the boundary versus two packages | Low | Q3=A accepted this deliberately for launch simplicity. | Boundary verified by the import checks in §5 rather than by packaging |
