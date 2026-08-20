# Business Rules — Unit 1 `assessment-engine`

**Phase**: 🟢 CONSTRUCTION — Functional Design
**Decisions applied**: Q1=A through Q8=A — all validated values retained

Every rule carries an identifier for test traceability. Rules were executed against the bundled dataset before this document was written; §12 records the verification.

---

## BR-1 — Normalisation Principles

| ID | Rule |
|---|---|
| BR-1.1 | Every dimension normalises to 0–100 using **fixed absolute bands** with documented boundaries. Bands never depend on the composition of the dataset. |
| BR-1.2 | Adding or removing unrelated objects must not change any remaining object's score. |
| BR-1.3 | A value falling exactly on a band boundary takes the band in which the boundary is the upper limit. Bands below are inclusive of their upper bound. |
| BR-1.4 | A value above the highest band scores 100. A value below the lowest scores 0. |
| BR-1.5 | Every normalisation records the raw input alongside the normalised result, so derivation is displayable without recomputation. |

---

## BR-2 — Business Value Dimensions

Axis weights, from approved requirements §2.2.1. Sum to 100%.

| ID | Dimension | Weight |
|---|---|---|
| BR-2.1 | Usage frequency | 29.41% |
| BR-2.2 | Distinct users | 17.65% |
| BR-2.3 | Business criticality | 23.53% |
| BR-2.4 | Outgoing dependencies | 17.65% |
| BR-2.5 | Incoming dependencies | 11.76% |

### BR-2.1 Usage frequency

Banded `monthly_executions`, multiplied by the recency factor of BR-3.

| Executions | Score |
|---|---|
| 0–5 | 0 |
| 6–25 | 20 |
| 26–75 | 40 |
| 76–150 | 60 |
| 151–300 | 80 |
| 301+ | 100 |

### BR-2.2 Distinct users

| Users | Score |
|---|---|
| 0–2 | 0 |
| 3–10 | 20 |
| 11–20 | 40 |
| 21–40 | 60 |
| 41–70 | 80 |
| 71+ | 100 |

### BR-2.3 Business criticality

Used **directly**, with no banding — the source value is already 0–100. Inherited from the solution area per BR-4.

### BR-2.4 Outgoing dependencies

Banded outgoing degree of the object's solution area, after `ALL` expansion (BR-7.2).

| Count | Score |
|---|---|
| 0 | 0 |
| 1 | 20 |
| 2 | 40 |
| 3 | 60 |
| 4 | 80 |
| 5+ | 100 |

### BR-2.5 Incoming dependencies

| Count | Score |
|---|---|
| 0 | 0 |
| 1 | 25 |
| 2 | 50 |
| 3–4 | 75 |
| 5+ | 100 |

---

## BR-3 — Recency Factor

| ID | Rule |
|---|---|
| BR-3.1 | The usage frequency score is multiplied by a recency factor derived from `last_run_date`. |
| BR-3.2 | The reference date is the **latest** `last_run_date` in the dataset, making results reproducible whenever the demo runs. For the bundled data this is 2026-08-14. |
| BR-3.3 | Elapsed days are counted as whole days from `last_run_date` to the reference date. |

| Days elapsed | Factor |
|---|---|
| 0–90 | 1.00 |
| 91–180 | 0.75 |
| 181–365 | 0.50 |
| 366+ | 0.25 |

| ID | Rule |
|---|---|
| BR-3.4 | Recency applies **only** to usage frequency. No other dimension is affected. |
| BR-3.5 | Recency is recorded in `raw_display` so the derivation table shows both the execution count and the elapsed days. |

---

## BR-4 — Solution Area Inheritance

| ID | Rule |
|---|---|
| BR-4.1 | Business criticality, outgoing dependencies, and incoming dependencies are properties of a **solution area**, not an object. Every object inherits its area's values. |
| BR-4.2 | A solution area label containing `/` denotes a composite of two areas. |
| BR-4.3 | For a composite area, criticality and both dependency counts are the **arithmetic mean** of the constituent areas' values. |
| BR-4.4 | Inherited dimensions record the source area in `inherited_from`, so the UI can mark them as inherited rather than object-specific. |
| BR-4.5 | For a composite area, `inherited_from` names both constituents. |
| BR-4.6 | An object that also exists as a graph node has its node degree displayed but **not** scored. Scoring uses inherited area values only. |

**Applies to**: `ZMD1` alone. Criticality = mean(Production 85, Inventory Management 80) = **82.5**. Its own node has two incoming edges, from `PR` and `IN`; these are shown but not scored (BR-4.6).

**Known consequence, documented not defective**: criticality plus both dependency dimensions total 52.94% of the Business Value axis and are identical for every object in an area. An unused object in a critical area therefore cannot score below roughly 36. This is precisely why the guard rules of BR-6 exist.

---

## BR-5 — Technical Effort Dimensions

| ID | Dimension | Weight |
|---|---|---|
| BR-5.1 | Technical complexity | 66.67% |
| BR-5.2 | Data volume | 33.33% |

### BR-5.1 Technical complexity

A weighted composite of four attributes.

| Attribute | Sub-weight |
|---|---|
| `hana_cv_count` | 40% |
| `transformation_count` | 30% |
| `interface_count` | 20% |
| `custom_logic_present` | 10% |

| `hana_cv_count` | Score | | `transformation_count` | Score | | `interface_count` | Score |
|---|---|---|---|---|---|---|---|
| 0 | 0 | | 0 | 0 | | 0 | 0 |
| 1–5 | 20 | | 1–3 | 20 | | 1–2 | 20 |
| 6–10 | 40 | | 4–6 | 40 | | 3–4 | 40 |
| 11–15 | 60 | | 7–9 | 60 | | 5–6 | 60 |
| 16–20 | 80 | | 10–12 | 80 | | 7–8 | 80 |
| 21+ | 100 | | 13+ | 100 | | 9+ | 100 |

`custom_logic_present`: false → 0, true → 100.

### BR-5.2 Data volume

| Attribute | Sub-weight |
|---|---|
| `record_count` | 40% |
| `storage_gb` | 40% |
| `load_frequency` | 20% |

| `record_count` | Score | | `storage_gb` | Score | | `load_frequency` | Score |
|---|---|---|---|---|---|---|---|
| < 500,000 | 0 | | 0–4 | 0 | | Monthly | 0 |
| 500,000–1,000,000 | 20 | | 5–10 | 20 | | Weekly | 25 |
| 1,000,001–3,000,000 | 40 | | 11–25 | 40 | | Daily | 75 |
| 3,000,001–8,000,000 | 60 | | 26–50 | 60 | | Hourly | 100 |
| 8,000,001–15,000,000 | 80 | | 51–80 | 80 | | | |
| 15,000,001+ | 100 | | 81+ | 100 | | | |

| ID | Rule |
|---|---|
| BR-5.3 | Where `hana_cv_count` differs between the inventory and the complexity dataset, the **complexity** value is used and a warning is raised naming both. |
| BR-5.4 | `adso_count` and `custom_table_count` are displayed but not scored. |
| BR-5.5 | `data_volume_label` is displayed but not scored; the Volume dimension uses measured metrics. |

---

## BR-6 — Classification

### BR-6.1 Axis totals

Each axis total is the sum of its dimensions' weighted contributions, guaranteed within 0–100 because every dimension is 0–100 and weights sum to 1.

### BR-6.2 Quadrant mapping (value-first)

| | Effort < `effort_threshold` | Effort ≥ `effort_threshold` |
|---|---|---|
| Value ≥ `value_threshold` | Replicate As-Is | Rebuild as Data Product |
| Value < `value_threshold` | Decommission | Decommission |

Defaults: Value 33, Effort 67. Both adjustable.

### BR-6.3 Guard predicates

| ID | Predicate | Condition |
|---|---|---|
| BR-6.3a | **Dormant** | elapsed days > `dormancy_days` **and** `monthly_executions` < `dormancy_executions` |
| BR-6.3b | **Active** | elapsed days ≤ `activity_days` **and** `monthly_executions` ≥ `activity_executions` |

Defaults: 180 days / 5 executions; 90 days / 25 executions.

### BR-6.4 Mutual exclusivity

| ID | Rule |
|---|---|
| BR-6.4 | The two predicates cannot both hold, because `activity_days` < `dormancy_days` is an invariant of `ScoringConfig`. Dormant requires elapsed > 180; Active requires elapsed ≤ 90. **Evaluation order is therefore irrelevant** and must not be relied upon. A test asserts no object satisfies both. |

### BR-6.5 Guard rule effects

| ID | Rule |
|---|---|
| BR-6.5a | **Dormancy ceiling** — a dormant object is classified `DECOMMISSION` regardless of its scores. |
| BR-6.5b | **Activity floor** — an active object is never `DECOMMISSION`. It takes `REBUILD_AS_DATA_PRODUCT` if Effort ≥ `effort_threshold`, otherwise `REPLICATE_AS_IS`. |
| BR-6.5c | An object satisfying neither predicate is classified by BR-6.2 alone. This includes long-idle but historically heavy objects (elapsed > 180, executions ≥ 5) and recent but lightly used objects (elapsed ≤ 90, executions < 25). Guard rules are exceptions, not a complete partition. |

### BR-6.6 Determinant semantics

| ID | Rule |
|---|---|
| BR-6.6a | `determinant` records the **effective cause**. It is set to a guard value only where that guard **changed** the category relative to BR-6.2 alone. Otherwise it is `SCORE`. |
| BR-6.6b | `is_dormant` and `is_active` record the raw predicate results independently, regardless of whether they changed anything. |
| BR-6.6c | A guard-rule badge is shown where `determinant` is a guard value. A dormancy note may be shown wherever `is_dormant` is true. |

**Why this distinction exists.** Executing the rules against the bundled dataset showed the dormancy predicate true for three objects — `IN200`, `TR200`, `TM100` — but changing the outcome for only `IN200`. `TR200` (Value 18.8) and `TM100` (Value 20.6) are already below the Value threshold, so the ceiling agrees with the score rather than overriding it. Recording a guard determinant for those two would imply an override that did not occur, and would make a badge meaningless. The predicate flags preserve the dormancy information without that distortion.

### BR-6.7 Category completeness

Every object receives exactly one of the three categories. There is no fourth value and no unclassified state.

---

## BR-7 — Dependency Graph

| ID | Rule |
|---|---|
| BR-7.1 | The graph is directed. An edge from A to B means A depends on B. |
| BR-7.2 | An edge whose source is the literal `ALL` expands to one edge per **solution area**. Non-area nodes are not included in the expansion. |
| BR-7.3 | All edge types — logical, operational, constraint — count **equally** in degree computation. |
| BR-7.4 | Outgoing degree is the count of edges leaving a node; incoming degree the count arriving. |
| BR-7.5 | The area matrix is a square grid over the 12 solution areas in a fixed order. Cell (i, j) is 1 where an edge runs from area i to area j, else 0. Non-area nodes are excluded from the matrix. |
| BR-7.6 | An object's incoming and outgoing edges are those of its solution area. For a composite area, the **union** of its constituents' edges, de-duplicated. |
| BR-7.7 | Node layout coordinates must be deterministic for a given graph so the network view does not shift between reruns. |

**Verified on bundled data**: 21 declared edges expand to 32; `ALL → DMK` becomes 12 edges, giving `DMK` an incoming degree of 12. Outgoing degrees range 1–6. Nine edges have both endpoints as solution areas.

**Documented consequence**: because `ALL → DMK` applies to all 12 areas uniformly, it shifts every object's outgoing dependency score by the same amount and adds no discriminating power. Retained deliberately per approved Q5=A.

---

## BR-8 — Wave Assignment

| ID | Rule |
|---|---|
| BR-8.1 | Assignment is led by the solution area's `migration_priority` (1–5). Lower priority number means earlier wave. |
| BR-8.2 | Mapping priority to wave, where W is `wave_count`: **if W ≥ 5**, wave = priority, leaving waves 6 to W empty. **If W < 5**, wave = ⌊(priority − 1) × W ÷ 5⌋ + 1, clamped to 1…W. |
| BR-8.3 | An object in a composite solution area takes the **latest** wave of its constituent areas, so nothing is scheduled before an area it spans. |
| BR-8.4 | Only `SOLUTION_AREA` nodes receive waves. `FF`, `SAPPS1`, `DMK` and `ZMD1` are not schedulable. |
| BR-8.5 | Wave n runs from `start_date` plus (n − 1) × `wave_months` months, to the day before wave n + 1 begins. |
| BR-8.6 | Every object is assigned to exactly one wave. |

**Verified compression behaviour**

| W | Wave membership |
|---|---|
| 5 | w1 FI · w2 SA SC · w3 IN PR · w4 LC PC PO · w5 IM QM TM TR |
| 3 | w1 FI SA SC · w2 IN LC PC PO PR · w3 IM QM TM TR |
| 7 | as W=5, with waves 6 and 7 empty |

Object counts per wave at defaults: 5, 4, 5, 3, 5 — totalling 22.

---

## BR-9 — Violations and Risk

### BR-9.1 Violation detection

| ID | Rule |
|---|---|
| BR-9.1a | A violation exists where a dependent area's wave is **earlier** than the wave of an area it depends on. |
| BR-9.1b | Both endpoints must be `SOLUTION_AREA` nodes with an assigned wave. Edges to `FF`, `SAPPS1`, `DMK` or `ZMD1` are excluded — they are outside programme scope and cannot be sequenced. The DMK constraint is handled instead as a risk contribution (BR-9.2d). |
| BR-9.1c | Same-wave dependencies are **not** violations. Concurrent migration is acceptable. |
| BR-9.1d | Each violation records both areas and both wave numbers. |

**Verified on bundled data at defaults**: exactly **one** violation — Logistics Costing (priority 4, wave 4) depends on Transport Management (priority 5, wave 5) for shipment costs. Nine area-to-area edges were evaluated.

### BR-9.2 Risk contributions

Each contribution is computed 0–100, then weighted.

| ID | Contribution | Weight | Derivation |
|---|---|---|---|
| BR-9.2a | Average technical complexity | 40% | Mean of the wave's objects' complexity composite scores |
| BR-9.2b | Cross-wave dependencies | 25% | Count of edges from the wave's areas to areas in other waves, with violations counted **twice**, then banded |
| BR-9.2c | Downtime tolerance | 25% | Banded from the **minimum** `downtime_tolerance_hours` among the wave's areas — the tightest window governs |
| BR-9.2d | DMK constraint | 10% | 100 if the wave's end date falls before 2028-01-01, else 0 |

Cross-wave dependency bands: 0 → 0, 1 → 25, 2 → 50, 3–4 → 75, 5+ → 100.

Downtime bands: ≤ 4h → 100, 5–8h → 80, 9–12h → 60, 13–24h → 40, 25–48h → 20, > 48h → 0.

| ID | Rule |
|---|---|
| BR-9.2e | An empty wave has risk 0 and band `LOW`. |
| BR-9.2f | Contributions are stored **unweighted** so the UI can display both the raw factor and its weighted effect. |

### BR-9.3 Risk banding

| Score | Band |
|---|---|
| 0–39 | Low |
| 40–69 | Medium |
| 70–100 | High |

**Verified on bundled data at defaults**

| Wave | Dates | Cplx | XDep | Down | DMK | Risk | Band |
|---|---|---|---|---|---|---|---|
| 1 | 2027-01-01 → 2027-03-31 | 36.4 | 0 | 100 | 100 | 49.6 | Medium |
| 2 | 2027-04-01 → 2027-06-30 | 76.0 | 50 | 100 | 100 | 77.9 | High |
| 3 | 2027-07-01 → 2027-09-30 | 54.0 | 25 | 60 | 100 | 52.9 | Medium |
| 4 | 2027-10-01 → 2027-12-31 | 45.3 | 100 | 40 | 100 | 63.1 | Medium |
| 5 | 2028-01-01 → 2028-03-31 | 23.6 | 25 | 40 | 0 | 25.7 | Low |

Wave 2 is High on genuine grounds: it carries the Sales and Supply Chain objects, the most complex in the landscape, against Supply Chain's 4-hour downtime tolerance. Wave 4 carries the dependency violation, which is why its cross-wave contribution reaches 100. Wave 5 is the only wave ending after the DMK freeze, so it alone escapes that contribution.

---

## BR-10 — Computation Phasing

| ID | Rule |
|---|---|
| BR-10.1 | Loading, graph construction, normalisation and axis scoring depend on the **dataset alone**. None takes a `ScoringConfig`. |
| BR-10.2 | Classification, distribution, KPIs and wave planning depend on configuration and are recomputed on every change. |
| BR-10.3 | Because of BR-10.1, caching the first phase on the dataset fingerprint is **exact**, not approximate. A threshold cannot change any dimension score, only which side of a boundary it falls on. |
| BR-10.4 | Given identical inputs, every computation must produce identical output. No wall-clock reads, no randomness, no iteration-order dependence. |

---

## BR-11 — Validation

| ID | Rule |
|---|---|
| BR-11.1 | No validation failure on user-supplied data raises. Every failure returns a `ValidationReport`. |
| BR-11.2 | A missing required field produces an `ERROR` naming the dataset and field. |
| BR-11.3 | A value of the wrong type produces an `ERROR` naming the dataset, field, and record identifier or row number. |
| BR-11.4 | A payload that is neither valid JSON nor valid CSV produces an `ERROR` naming the dataset. |
| BR-11.5 | A date that does not parse as ISO-8601 produces an `ERROR` naming the record. |
| BR-11.6 | A negative value where non-negative is required produces an `ERROR`. |
| BR-11.7 | An object present in the inventory with no usage record produces a `WARNING` naming the object, and the report states how it is treated. |
| BR-11.8 | An object with no volume or complexity record produces a `WARNING`; missing dimensions score 0. |
| BR-11.9 | A solution area referenced by an object but absent from the criticality matrix produces an `ERROR` — criticality is 23.53% of the value axis and cannot be defaulted. |
| BR-11.10 | An edge referencing an unknown node produces a `WARNING`; the edge is dropped from the graph. |
| BR-11.11 | `load_frequency` outside the known set produces a `WARNING` and scores 0. |
| BR-11.12 | A `Landscape` cannot be constructed while any `ERROR` exists. |
| BR-11.13 | On fatal failure the previously loaded landscape remains active. |

---

## BR-12 — Rationale Generation

| ID | Rule |
|---|---|
| BR-12.1 | Rationale is **template-driven** with evidence inserted, so output is deterministic and assertable. |
| BR-12.2 | A distinct template exists per category and per guard determinant. |
| BR-12.3 | A score-driven rationale names the **two highest-contributing** Business Value dimensions and, for Rebuild, the dominant Effort factor. |
| BR-12.4 | A guard-driven rationale states that the computed score would have placed the object elsewhere, names the guard, and cites the evidence — elapsed days and execution count. |
| BR-12.5 | Rationale is plain language and requires no interpretation of raw scores. |
| BR-12.6 | Where `is_dormant` is true but the determinant is `SCORE`, the rationale notes dormancy as **corroborating** rather than deciding. |

### Template shapes

| Case | Shape |
|---|---|
| Rebuild, score | "High business value ({value}) driven by {factor1} and {factor2}, combined with high technical effort ({effort}) from {effort_factor}. Modernising as a data product is warranted." |
| Replicate, score | "Business value of {value} justifies retention, driven by {factor1} and {factor2}. Technical effort of {effort} is below the rebuild threshold, so a pragmatic lift is appropriate." |
| Decommission, score | "Business value of {value} falls below the retention threshold of {threshold}. {factor1} and {factor2} are the weakest contributors." |
| Decommission, score, dormant | As above, plus: "Last run {days} days ago with {executions} executions per month, which corroborates the assessment." |
| Decommission, dormancy ceiling | "Last run {days} days ago with only {executions} executions per month. The dormancy ceiling classifies this for decommission regardless of its computed value of {value}, which is inflated by inherited solution-area attributes." |
| Replicate or Rebuild, activity floor | "Computed value of {value} falls below the retention threshold, but {executions} executions per month across {users} users within the last {days} days means this is in active use. The activity floor prevents decommission." |

---

## 13. Verification Record

Every rule above was executed against the bundled dataset before this document was finalised.

| Check | Result |
|---|---|
| Distribution | 5 Rebuild, 13 Replicate As-Is, 4 Decommission |
| Rebuild set | `SC100`, `SC200`, `SA100`, `PR100`, `PR200` |
| Decommission set | `IN200`, `TR100`, `TR200`, `TM100` |
| Object count | 22 (5 + 13 + 4) |
| Guard predicates fire | 4 objects — `IN200`, `TR200`, `TM100` dormant; `IM100` active |
| Guard changes outcome | 2 objects — `IN200`, `IM100` |
| `FI100GC` at Effort 67 | Replicate As-Is (Effort 66.3) |
| `FI100GC` at Effort 66 | Rebuild as Data Product |
| `ALL` expansion | 12 edges; `DMK` incoming degree 12 |
| Wave assignment W=5 | 5, 4, 5, 3, 5 objects; 22 total |
| Wave compression W=3 | 3, 5, 4 areas |
| Wave count W=7 | Waves 6 and 7 empty |
| Violations | Exactly 1 — `LC` → `TM`, waves 4 and 5 |
| Risk bands | 1 Low, 3 Medium, 1 High |

Two prior errors were corrected as a result of this run: story S6.1 AC5 had named a Purchasing-to-Supply-Chain conflict that is not a violation, and `unit-of-work.md` Unit 2 criterion 6 had implied only two objects carry any dormancy indication.

---

## BR-13 — Live SAP OData Ingress (added 2026-08-19, requirements §10)

Implemented in `engine/odata.py` (C17). Verified by `tests/engine/test_odata.py` (37 tests, no network).

| ID | Rule |
|---|---|
| BR-13.1 | Exactly five datasets have a live source: `object_inventory`, `complexity`, `data_volume`, `dependencies`, `usage_logs`. `criticality` has none and always comes from the bundled or uploaded file. Business criticality, migration priority, and downtime tolerance are business judgements, not BW metadata. |
| BR-13.2 | Connection configuration resolves from environment variables with the §10.4.1 defaults. Service paths are placeholders and must remain overridable. |
| BR-13.3 | `OdataSettings` holds no credential. Credentials are read only when a transport is constructed, live only for that transport's lifetime, and never enter a settings object, session state, or a rendered value. |
| BR-13.4 | `BasicAuth.__repr__` masks both user and password, so no traceback or log line can leak them. |
| BR-13.5 | Every user-reachable message passes through `scrub()`, which removes URL userinfo and any known secret value. |
| BR-13.6 | TLS verification is `True` or a CA bundle path. `False` is unreachable by construction — there is no code path and no environment variable that produces it. |
| BR-13.7 | A TLS failure's detail names `BWACE_ODATA_CA_BUNDLE` as the remedy. |
| BR-13.8 | Retries apply only to `TIMEOUT`, `SERVER_ERROR`, and `TRANSPORT_ERROR`. `UNAUTHORISED` (401/403) and `NOT_FOUND` (404) are terminal on the first attempt. |
| BR-13.9 | Collection retrieval follows `d.__next` (V2) or `@odata.nextLink` (V4) until exhausted. Reaching the record cap sets `truncated` and produces a warning naming `BWACE_ODATA_MAX_RECORDS`; it never returns quietly. |
| BR-13.10 | Mapping accepts either the SAP property name or the BW-ACE field name for each field. `/Date(ms)/` and ISO-8601-with-time both normalise to an ISO date. A non-numeric value in a numeric field raises `MappingError`, which is reported as `MALFORMED` against that endpoint. |
| BR-13.11 | Mapped records are serialised to JSON bytes and passed to `loader._load_all` through `load_with_live`, so live data receives identical structural, type, and referential-integrity validation to an uploaded file, and the content fingerprint is computed the same way. Provenance precedence is live over uploaded over bundled. |
| BR-13.12 | `fetch_landscape` populates `load` only when every live endpoint succeeded **and** the assembled landscape validated. Any endpoint failure returns `load=None`, leaving the caller's existing landscape untouched. |
| BR-13.13 | Only HTTP GET is issued. There is no write path, so no CSRF token handling exists. |
| BR-13.14 | `httpx` is imported inside `HttpxTransport.get`, so the engine imports, and demo mode runs, with the package absent. A missing package surfaces as a `TRANSPORT_ERROR` with a plain message. |

**Verification record**: paging across two pages, the record cap, 401, 404, 500-then-success, timeout exhausting three attempts, a non-JSON body, a payload with no collection, a live payload missing a required field, and a five-endpoint fetch assembling the full 22-object landscape were each executed as tests before this section was written. `criticality` provenance asserted as `bundled` in the same run.
