# Unit of Work Story Map — BW-ACE

**Stage**: INCEPTION — Units Generation
**Decision applied**: Q2 = B — boundary-straddling stories are split into per-unit sub-stories so that no story spans a unit boundary

---

## 1. Story Count Reconciliation

| | Count |
|---|---|
| Stories in approved `stories.md` | 23 |
| Split into per-unit sub-stories (Q2=B) | 3 → 6 |
| **Total after split** | **26** |

**Note on the approved document**: `stories.md` originally stated 22 stories in three places. The actual inventory is 23 — the per-epic counts (3, 4, 4, 2, 1, 4, 2, 3) were correct and sum to 23. The document has been corrected and the correction recorded in it. No story content changed.

---

## 2. The Q2=B Split

Three stories had acceptance criteria that could not be satisfied within one unit. Each becomes two sub-stories, with the parent's acceptance criteria allocated between them rather than duplicated.

### S1.3 → S1.3a + S1.3b

**Parent**: Understand why my data was rejected (FR-1.4, NFR-6.4)

| Sub-story | Unit | Scope | Parent ACs |
|---|---|---|---|
| **S1.3a** — Detect and report invalid data | 1 | Validation produces a report identifying dataset, field, and offending record; returns rather than raises; flags unreferenced objects as warnings | AC1 detection, AC2 detection, AC3 return-not-raise, AC4 detection |
| **S1.3b** — See why my upload was rejected | 2 | The report is rendered readably, the previous dataset stays active, the app stays usable, no traceback is shown | AC1 display, AC2 display, AC3 no-traceback-rendered, AC4 display and treatment statement |

**S1.3a acceptance criteria**

- **Given** a usage log missing `monthly_executions`, **When** validation runs, **Then** a `ValidationReport` is returned with `is_fatal` true and an issue naming the dataset and the missing field
- **Given** a `distinct_users` value that is not numeric, **When** validation runs, **Then** an issue names the field and identifies the record
- **Given** a payload that is neither valid CSV nor valid JSON, **When** parsing runs, **Then** a `ValidationReport` is returned and no exception propagates
- **Given** an inventory containing an object with no usage log entry, **When** referential integrity runs, **Then** an issue with severity `WARNING` names the affected object

**S1.3b acceptance criteria**

- **Given** a fatal `ValidationReport`, **When** the app renders, **Then** each issue is displayed naming dataset, field, and record
- **Given** a rejected upload, **When** the app renders, **Then** the previously loaded dataset remains active and every view stays usable
- **Given** any `ValidationReport`, **When** it is displayed, **Then** no Python traceback or raw exception text appears
- **Given** a warning-severity issue, **When** displayed, **Then** the app states how the affected object is treated in scoring

---

### S2.4 → S2.4a + S2.4b

**Parent**: Test how sensitive my recommendation is (FR-3.3, FR-3.4, FR-3.5)

| Sub-story | Unit | Scope | Parent ACs |
|---|---|---|---|
| **S2.4a** — Classification responds correctly to configuration | 1 | Reclassification is a pure function of `ScoringConfig`; specific threshold changes produce specific reclassifications | AC3, AC4 |
| **S2.4b** — Adjust thresholds and see the effect immediately | 2 | Controls exist showing current and default; changes propagate live everywhere; reset works | AC1, AC2, AC5 |

**S2.4a acceptance criteria**

- **Given** default thresholds, **When** `FI100GC` is classified, **Then** it is Replicate As-Is; **and Given** the Effort threshold is 66, **Then** it is Rebuild as Data Product
- **Given** the Value threshold is raised to 40, **When** classification recomputes, **Then** the Decommission count increases **and** `IM100` remains Replicate As-Is because the activity floor still protects it
- **Given** any two identical `ScoringConfig` values, **When** classification runs twice, **Then** results are identical — classification is pure

**S2.4b acceptance criteria**

- **Given** the app is running, **When** I look for scoring controls, **Then** both thresholds are adjustable and each displays its current value and its default of 33 and 67
- **Given** I change either threshold, **When** the change applies, **Then** every classification, chart, count, and table across all views reflects it with no manual refresh
- **Given** I have changed thresholds, **When** I reset, **Then** defaults are restored and the reference distribution of 5 / 13 / 4 returns

---

### S8.3 → S8.3a + S8.3b

**Parent**: Work reliably without network, and respond instantly (NFR-3.1, NFR-3.2, NFR-5.1, NFR-5.2, NFR-5.3)

| Sub-story | Unit | Scope | Parent ACs |
|---|---|---|---|
| **S8.3a** — Recompute fast enough to explore freely | 1 | Two-phase caching; recomputation cost; scale headroom; no network dependency in the engine | AC3, AC5 |
| **S8.3b** — Work without venue network access | 2 | Views render offline; typography falls back; startup time | AC1, AC2, AC4 |

**S8.3a acceptance criteria**

- **Given** the bundled dataset and a warm base, **When** only a threshold changes, **Then** reclassification and aggregation complete in under 500 ms
- **Given** a dataset of approximately 1,000 objects, **When** the full pipeline runs, **Then** it completes without the recomputation path degrading disproportionately
- **Given** `compute_base` has been computed for a fingerprint, **When** a threshold changes, **Then** `compute_base` is not re-executed
- **Given** any engine operation, **When** it runs, **Then** it makes no network request

**S8.3b acceptance criteria**

- **Given** dependencies are installed, **When** the network is disconnected and the app starts, **Then** every view renders and every function works
- **Given** no network access, **When** any view renders, **Then** text uses a system fallback font, layout is intact, and no element is unstyled
- **Given** a provisioned environment, **When** the app starts, **Then** the first view renders within 10 seconds

---

## 3. Unit 1 — `assessment-engine` (14 stories)

| Story | Title | Epic | Requirements |
|---|---|---|---|
| S1.1 | Load the bundled Acme landscape | Data Foundation | FR-1.1, FR-1.2 |
| S1.2 | Assess my own landscape extract | Data Foundation | FR-1.3, FR-1.5 |
| **S1.3a** | Detect and report invalid data | Data Foundation | FR-1.4 |
| S2.1 | See each object scored on business value and technical effort | Scoring | FR-2.1 – FR-2.4 |
| S2.2 | Get a three-way classification I can act on | Scoring | FR-3.1, FR-3.2 |
| S2.3 | Trust that usage evidence overrides the score | Scoring | FR-3.6 – FR-3.9 |
| **S2.4a** | Classification responds correctly to configuration | Scoring | FR-3.3, FR-3.5 |
| S5.1 | Understand what depends on what | Dependency Analysis | FR-4.1 – FR-4.4, FR-4.6 |
| S6.1 | Get a recommended migration sequence | Wave Planning | FR-5.1, FR-5.2, FR-8.1, FR-8.4 |
| S6.2 | Shape the wave structure to my programme | Wave Planning | FR-5.3, FR-5.4 |
| S6.4 | Understand the risk in each wave | Wave Planning | FR-5.7 – FR-5.9, FR-8.3 |
| S7.1 | Compare two assessment stances | Scenario & Export | FR-9.1, FR-9.2 |
| S7.2 | Take the assessment away with me | Scenario & Export | FR-10.1 – FR-10.3 |
| **S8.3a** | Recompute fast enough to explore freely | Platform | NFR-5.1, NFR-5.3 |

### Cross-unit acceptance criteria in Unit 1 stories

Five Unit 1 stories carry a small number of criteria that require a rendered UI. Rather than split these stories — the parent behaviour is unambiguously engine work — the specific criteria are recorded here as **deferred to Unit 2 integration verification**, so nothing is silently dropped.

| Story | Criterion deferred to Unit 2 | Reason |
|---|---|---|
| S1.2 | AC1 "every view reflects the recomputed result" | Requires views to exist |
| S2.3 | AC5 badge naming the rule that fired | Rendering concern; the `Determinant` value it displays is engine output and is tested in Unit 1 |
| S5.1 | AC1 matrix rendered, AC2 network rendered, AC6 note displayed | Rendering; the underlying graph facts are tested in Unit 1 |
| S6.1 | AC4 violations listed together, count visible without scrolling | Layout concern; violation detection is tested in Unit 1 |
| S6.2 | AC1 defaults displayed in controls | Controls belong to Unit 2; redistribution logic is tested in Unit 1 |

**Interpretation note**: Q2=B was answered against the three stories named in the question. It was applied to exactly those three. The five stories above have a minor presentation criterion attached to substantial engine behaviour, so splitting them would have produced sub-stories with a single trivial criterion each and fragmented the parent's narrative. If you would prefer these split as well, say so and I will restructure — it is a judgement call, not a settled fact.

---

## 4. Unit 2 — `presentation-app` (12 stories)

| Story | Title | Epic | Requirements |
|---|---|---|---|
| **S1.3b** | See why my upload was rejected | Data Foundation | FR-1.4, NFR-6.4 |
| **S2.4b** | Adjust thresholds and see the effect immediately | Scoring | FR-3.3, FR-3.4 |
| S3.1 | See headline landscape figures at a glance | Landscape Overview | FR-6.1 |
| S3.2 | See the shape of the landscape | Landscape Overview | FR-6.2, FR-6.3 |
| S3.3 | See where objects sit on value against effort | Landscape Overview | FR-6.4 |
| S3.4 | See which objects I can switch off | Landscape Overview | FR-6.5 |
| S4.1 | Inspect a single object in full | Object Interrogation | FR-7.1 – FR-7.4, FR-4.5 |
| S4.2 | See exactly how a classification was reached | Object Interrogation | FR-7.5, FR-7.6, FR-2.5, NFR-6.3 |
| S6.3 | See the plan on a timeline with constraints marked | Wave Planning | FR-5.5, FR-5.6, FR-8.2 |
| S8.1 | Run the tool anywhere with one command | Platform | NFR-1.2, NFR-1.3, NFR-2.1 – NFR-2.5 |
| S8.2 | Read every screen comfortably | Platform | NFR-4.1 – NFR-4.6 |
| **S8.3b** | Work without venue network access | Platform | NFR-3.1, NFR-3.2, NFR-5.2 |

### Engine-supplied data behind Unit 2 stories

These stories render values computed in Unit 1. The computation is already tested there; Unit 2 verifies presentation.

| Story | Engine-supplied input |
|---|---|
| S3.1 | `LandscapeKpis` — object count, storage, decommission percentage, reclaimable storage |
| S3.2 | `distribution` and Business Value ordering |
| S3.3 | Both axis scores, active thresholds, `Determinant` for override marking |
| S3.4 | Decommission set with rationale and determinant |
| S4.1 | `ObjectAssessment` with resolved dependencies and averaged `ZMD1` criticality |
| S4.2 | `DimensionScore` derivation with weights, contributions, and inheritance flags |
| S6.3 | `WavePlan` dates and the DMK freeze boundary |

---

## 5. Epic Coverage per Unit

| Epic | Unit 1 | Unit 2 | Total |
|---|---|---|---|
| 1 Data Foundation | 3 | 1 | 4 |
| 2 Scoring and Classification | 4 | 1 | 5 |
| 3 Landscape Overview | 0 | 4 | 4 |
| 4 Object Interrogation | 0 | 2 | 2 |
| 5 Dependency Analysis | 1 | 0 | 1 |
| 6 Wave Planning | 3 | 1 | 4 |
| 7 Scenario and Export | 2 | 0 | 2 |
| 8 Platform, Presentation, Performance | 1 | 3 | 4 |
| **Total** | **14** | **12** | **26** |

The pattern is what the decomposition intended: Unit 1 owns Epics 1, 2, 5, 6 and 7 — the analytical substance. Unit 2 owns Epics 3, 4 and 8 — everything a person looks at.

---

## 6. Persona Coverage per Unit

| Persona | Unit 1 stories | Unit 2 stories |
|---|---|---|
| P1 Migration Architect | S1.1, S1.2, S1.3a, S2.1, S2.2, S2.4a, S5.1, S7.1 | S1.3b, S2.4b, S3.2, S3.3, S8.1 |
| P2 Solution / Business Owner | S2.3 | S3.4, S4.1, S4.2, S8.2 |
| P3 Programme Manager | S6.1, S6.2, S6.4, S7.2, S8.3a | S3.1, S6.3, S8.3b |

Every persona is served by both units, as expected — Unit 1 produces what they need to know, Unit 2 shows it to them.

---

## 7. Validation

| Check | Result |
|---|---|
| Every story assigned to exactly one unit | Yes — 14 + 12 = 26, no duplicates |
| Every component assigned to exactly one unit | Yes — C1–C10 Unit 1, C11–C16 Unit 2 |
| Every acceptance criterion has an implementing unit | Yes — the three split stories allocate parent criteria explicitly; the five cross-unit criteria in §3 are named and assigned |
| No unit depends on a later unit in the build order | Yes — Unit 2 depends on Unit 1 only |
| Unit 1 verifiable without Unit 2 | Yes — all 14 Unit 1 stories testable by unit tests |
| Every functional requirement covered | Yes — FR-1 to FR-10 all mapped |
| Every non-functional requirement covered or explained | Yes — NFR-1.1 and NFR-6.1/6.2 remain verified by inspection and smoke tests, as recorded in `stories.md` |
| Directory structure covers every component | Yes — see `unit-of-work.md` §4.1 |
