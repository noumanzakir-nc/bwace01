# Business Logic Model — Unit 1 `assessment-engine`

**Phase**: 🟢 CONSTRUCTION — Functional Design
**Companion documents**: `domain-entities.md`, `business-rules.md`

---

## 1. Pipeline

```
INPUT: six datasets (bundled files or uploaded bytes)
                    │
    ┌───────────────┴────────────────────────────────────────┐
    │  STAGE 1  PARSE AND VALIDATE                    BR-11  │
    │  Detect format, parse, validate structure, types,      │
    │  and cross-dataset referential integrity.              │
    │  Compute content fingerprint.                          │
    │  OUT: LoadOutcome — Landscape, or fatal report         │
    └───────────────┬────────────────────────────────────────┘
                    │  Landscape
    ╔═══════════════╧════════════════════════════════════════╗
    ║  PHASE A — DATASET-DEPENDENT              CACHED       ║
    ║  Takes no ScoringConfig. See BR-10.                    ║
    ╟────────────────────────────────────────────────────────╢
    ║  STAGE 2  BUILD DEPENDENCY GRAPH               BR-7    ║
    ║  Expand ALL wildcard, compute degrees,                 ║
    ║  build area matrix, compute deterministic layout       ║
    ║  OUT: DependencyGraph                                  ║
    ║                    │                                   ║
    ║  STAGE 3  NORMALISE DIMENSIONS         BR-1 to BR-5    ║
    ║  Per object, seven DimensionScores.                     ║
    ║  Resolve area inheritance, apply recency.              ║
    ║  OUT: DimensionScore collections                       ║
    ║                    │                                   ║
    ║  STAGE 4  COMPUTE AXIS SCORES            BR-6.1        ║
    ║  Weight and sum both axes.                             ║
    ║  OUT: BaseScores — graph, axis scores, reference date   ║
    ╚═══════════════╤════════════════════════════════════════╝
                    │  BaseScores
    ┌───────────────┴────────────────────────────────────────┐
    │  PHASE B — CONFIGURATION-DEPENDENT      RECOMPUTED     │
    ├────────────────────────────────────────────────────────┤
    │  STAGE 5  CLASSIFY                        BR-6         │
    │  Quadrant mapping, guard predicates,                   │
    │  determinant resolution, rationale                     │
    │                    │                                   │
    │  STAGE 6  AGGREGATE                                    │
    │  Distribution counts and landscape KPIs                │
    │                    │                                   │
    │  STAGE 7  PLAN WAVES                  BR-8, BR-9       │
    │  Assign, date, detect violations, score risk           │
    │                    │                                   │
    │  STAGE 8  ASSEMBLE                                     │
    │  OUT: AssessmentResult                                 │
    └───────────────┬────────────────────────────────────────┘
                    │
OUTPUT: AssessmentResult  ──>  Unit 2, and export
```

### Why the phase split is exact

No operation in Phase A accepts a `ScoringConfig`. Dimension scores are a function of the dataset alone. A threshold change cannot alter any score — it can only alter which side of a boundary a score falls on. Caching Phase A on the dataset fingerprint is therefore exact rather than an approximation, which is what allows the sub-500 ms target to hold by design (BR-10.3).

---

## 2. Stage Detail

### Stage 1 — Parse and validate

1. For each of the six datasets, take bundled file bytes unless an upload overrides it
2. Detect JSON or CSV by content
3. Parse to raw records; a parse failure yields an `ERROR` (BR-11.4)
4. Validate each dataset: required fields, types, ranges (BR-11.2, BR-11.3, BR-11.5, BR-11.6)
5. Validate referential integrity across datasets (BR-11.7 to BR-11.11)
6. Compute the fingerprint over the source bytes
7. If any `ERROR` exists, return the report with no landscape (BR-11.12). Otherwise construct the `Landscape`.

### Stage 2 — Build dependency graph

1. Register all 16 nodes
2. Expand any `ALL` source into one edge per solution area (BR-7.2) — 21 declared edges become 32
3. Count outgoing and incoming degree per node, all edge types equal (BR-7.3, BR-7.4)
4. Build the 12×12 area matrix in fixed order (BR-7.5)
5. Compute deterministic layout coordinates (BR-7.7)

### Stage 3 — Normalise dimensions

Determine the reference date as the latest `last_run_date` (BR-3.2). Then per object:

| Dimension | Steps |
|---|---|
| Usage frequency | Band executions (BR-2.1); compute elapsed days; apply recency factor (BR-3); record both in `raw_display` |
| Distinct users | Band (BR-2.2) |
| Business criticality | Resolve area, averaging for composite (BR-4.3); use directly (BR-2.3); set `inherited_from` |
| Outgoing dependencies | Resolve area degree, averaging for composite; band (BR-2.4); set `inherited_from` |
| Incoming dependencies | As above with incoming degree (BR-2.5) |
| Technical complexity | Band each of four attributes; combine at 40/30/20/10 (BR-5.1) |
| Data volume | Band each of three attributes; combine at 40/40/20 (BR-5.2) |

### Stage 4 — Compute axis scores

Multiply each dimension's normalised score by its axis weight; sum. Both axes land in 0–100 because every dimension is 0–100 and weights sum to 1 (BR-6.1).

### Stage 5 — Classify

1. Compute the pure-score category by quadrant mapping (BR-6.2)
2. Evaluate both guard predicates (BR-6.3)
3. Apply guard effects (BR-6.5)
4. Set `determinant` to a guard value **only if** the category differs from the pure-score result (BR-6.6a)
5. Record `is_dormant` and `is_active` regardless (BR-6.6b)
6. Generate rationale from the matching template (BR-12)

### Stage 6 — Aggregate

Count categories; compute the four KPIs from assessments and volume metrics.

### Stage 7 — Plan waves

1. Map each area's priority to a wave (BR-8.2)
2. Assign objects, composite areas taking the latest constituent wave (BR-8.3)
3. Compute wave date ranges (BR-8.5)
4. Detect violations over area-to-area edges only (BR-9.1)
5. Per wave, compute the four risk contributions and band the total (BR-9.2, BR-9.3)

### Stage 8 — Assemble

Construct the `AssessmentResult`, embedding both configurations so it is self-describing.

---

## 3. Worked Example — `SC100`, a Rebuild candidate

Inputs: Supply Chain, 320 executions, 100 users, last run 2026-08-14, `hana_cv_count` 20, `transformation_count` 15, custom logic true, `interface_count` 8, 18,000,000 records, 95 GB, Hourly.

**Business Value**

| Dimension | Raw | Normalised | Weight | Contribution |
|---|---|---|---|---|
| Usage frequency | 320 exec, 0 days elapsed | 100 × 1.00 = 100 | 29.41% | 29.41 |
| Distinct users | 100 | 100 | 17.65% | 17.65 |
| Business criticality | 95 (inherited) | 95 | 23.53% | 22.35 |
| Outgoing dependencies | 4 (inherited) | 80 | 17.65% | 14.12 |
| Incoming dependencies | 1 (inherited) | 25 | 11.76% | 2.94 |
| | | | | **86.5** |

**Technical Effort**

Complexity: cv 20 → 80 (×0.40 = 32.0); transformations 15 → 100 (×0.30 = 30.0); interfaces 8 → 80 (×0.20 = 16.0); custom logic true → 100 (×0.10 = 10.0). Total **88.0**.

Volume: records 18M → 100 (×0.40 = 40.0); storage 95 GB → 100 (×0.40 = 40.0); Hourly → 100 (×0.20 = 20.0). Total **100.0**.

Effort = 88.0 × 0.6667 + 100.0 × 0.3333 = **92.0**

**Classification**: Value 86.5 ≥ 33 and Effort 92.0 ≥ 67 → `REBUILD_AS_DATA_PRODUCT`. Neither guard predicate holds. Determinant `SCORE`.

---

## 4. Worked Example — `IN200`, dormancy ceiling overriding the score

Inputs: Inventory Management, 2 executions, 1 user, last run 2025-08-04 (375 days before reference).

**Business Value**

| Dimension | Raw | Normalised | Weight | Contribution |
|---|---|---|---|---|
| Usage frequency | 2 exec, 375 days | 0 × 0.25 = 0 | 29.41% | 0.00 |
| Distinct users | 1 | 0 | 17.65% | 0.00 |
| Business criticality | 80 (inherited) | 80 | 23.53% | 18.82 |
| Outgoing dependencies | 4 (inherited) | 80 | 17.65% | 14.12 |
| Incoming dependencies | 1 (inherited) | 25 | 11.76% | 2.94 |
| | | | | **35.9** |

Effort = **25.7**

**Pure-score result**: Value 35.9 ≥ 33 → `REPLICATE_AS_IS`. **Wrong on the evidence.** The object has not run in over a year and has a single user. Its score is held up entirely by inherited area attributes, which contribute 35.9 of its 35.9 — the two object-specific dimensions contribute nothing.

**Guard evaluation**: dormant, since 375 > 180 and 2 < 5. Active is false.

**Final**: `DECOMMISSION`, determinant `DORMANCY_CEILING`, `is_dormant` true.

This is the case that motivated the guard rules, found by executing the model during Requirements Analysis rather than by inspection.

---

## 5. Worked Example — `IM100`, activity floor protecting an object in use

Inputs: Investment Management, 40 executions, 10 users, last run 2026-08-07 (7 days before reference).

**Business Value**

| Dimension | Raw | Normalised | Weight | Contribution |
|---|---|---|---|---|
| Usage frequency | 40 exec, 7 days | 40 × 1.00 = 40 | 29.41% | 11.76 |
| Distinct users | 10 | 20 | 17.65% | 3.53 |
| Business criticality | 55 (inherited) | 55 | 23.53% | 12.94 |
| Outgoing dependencies | 1 (inherited) | 20 | 17.65% | 3.53 |
| Incoming dependencies | 0 (inherited) | 0 | 11.76% | 0.00 |
| | | | | **31.8** |

Effort = **31.0**

**Pure-score result**: Value 31.8 < 33 → `DECOMMISSION`. **Also wrong**, and more damaging than the `IN200` case. Recommending that a customer switch off a report used by ten people every month would undermine the tool in the room. The cause is the same inheritance effect acting inversely: Investment Management has low criticality, no incoming dependencies, and only the uniform DMK outgoing edge.

**Guard evaluation**: active, since 7 ≤ 90 and 40 ≥ 25. Dormant is false.

**Final**: Effort 31.0 < 67 → `REPLICATE_AS_IS`, determinant `ACTIVITY_FLOOR`, `is_active` true.

---

## 6. Worked Example — `TR200`, dormant but not overridden

Inputs: Treasury Management, 3 executions, 2 users, last run 2025-09-22 (326 days elapsed). Value **18.8**, Effort **16.3**.

**Pure-score result**: 18.8 < 33 → `DECOMMISSION`.

**Guard evaluation**: dormant, since 326 > 180 and 3 < 5.

**Final**: `DECOMMISSION`. But the category is unchanged from the pure-score result, so per BR-6.6a the determinant remains **`SCORE`**, not `DORMANCY_CEILING`. `is_dormant` is recorded true.

This is why the determinant and predicate flags are separate fields. `TR200` and `TM100` both behave this way. Recording a guard determinant here would imply an override that never happened and would make the guard badge meaningless — it would appear on four objects when only two were actually overridden.

---

## 7. Worked Example — Wave plan at defaults

Configuration: 5 waves, 3 months each, starting 2027-01-01.

| Wave | Dates | Areas | Objects |
|---|---|---|---|
| 1 | 2027-01-01 → 2027-03-31 | FI | 5 |
| 2 | 2027-04-01 → 2027-06-30 | SA, SC | 4 |
| 3 | 2027-07-01 → 2027-09-30 | IN, PR | 5 |
| 4 | 2027-10-01 → 2027-12-31 | LC, PC, PO | 3 |
| 5 | 2028-01-01 → 2028-03-31 | IM, QM, TM, TR | 5 |

**Violation detection**: nine area-to-area edges evaluated. Eight are satisfied. One fails — `LC` (wave 4) depends on `TM` (wave 5), so Logistics Costing is scheduled before the Transport Management data it needs for shipment costing.

**Risk**

| Wave | Cplx | XDep | Down | DMK | Score | Band |
|---|---|---|---|---|---|---|
| 1 | 36.4 | 0 | 100 | 100 | 49.6 | Medium |
| 2 | 76.0 | 50 | 100 | 100 | 77.9 | High |
| 3 | 54.0 | 25 | 60 | 100 | 52.9 | Medium |
| 4 | 45.3 | 100 | 40 | 100 | 63.1 | Medium |
| 5 | 23.6 | 25 | 40 | 0 | 25.7 | Low |

Wave 2 is High for defensible reasons: it holds the Sales and Supply Chain objects, the most complex in the landscape, against Supply Chain's four-hour downtime tolerance, and it completes before the DMK freeze lifts. Wave 4's cross-wave contribution reaches 100 because the violation is double-weighted. Wave 5 is the only wave finishing after 2028, so it alone escapes the DMK contribution.

---

## 8. Edge Cases

| Case | Handling | Rule |
|---|---|---|
| Composite solution area | Criticality and dependency counts averaged; wave takes the latest constituent | BR-4.3, BR-8.3 |
| Object also present as a graph node | Node degree displayed, not scored | BR-4.6 |
| Both guard predicates would fire | Impossible — `activity_days` < `dormancy_days` is invariant. Asserted by test. | BR-6.4 |
| Neither guard fires | Pure score classification. Includes long-idle-but-heavy and recent-but-light. | BR-6.5c |
| Guard fires without changing the outcome | Determinant stays `SCORE`; predicate flag records it | BR-6.6a |
| Value exactly on a threshold | `≥` retains, so Value exactly 33 is not Decommission | BR-6.2 |
| Value exactly on a band boundary | Takes the band whose upper limit it is | BR-1.3 |
| `wave_count` > 5 | Waves 6 upward are empty, risk 0, band Low | BR-8.2, BR-9.2e |
| `wave_count` < 5 | Priorities compressed by the floor formula | BR-8.2 |
| Edge to a non-area node | Excluded from violation detection | BR-9.1b |
| Same-wave dependency | Not a violation | BR-9.1c |
| Missing usage record | `WARNING`; missing dimensions score 0 | BR-11.7 |
| Missing criticality for a referenced area | `ERROR` — 23.53% of the axis cannot be defaulted | BR-11.9 |
| Edge referencing an unknown node | `WARNING`; edge dropped | BR-11.10 |
| Conflicting `hana_cv_count` between datasets | Complexity dataset wins; `WARNING` names both | BR-5.3 |
| Unparseable upload | `ERROR`; previous landscape retained | BR-11.4, BR-11.13 |
| Empty dataset | `ERROR`; no landscape constructed | BR-11.12 |

---

## 9. Determinism Guarantees

| Guarantee | Mechanism |
|---|---|
| Reference date is stable | Derived from the data, never from the system clock (BR-3.2) |
| Repeat runs are identical | No randomness anywhere (BR-10.4) |
| Graph layout is stable | Deterministic coordinates (BR-7.7) |
| Scores are dataset-relative-free | Fixed absolute bands (BR-1.1, BR-1.2) |
| Iteration order is stable | Ordered sequences throughout, never unordered sets in output |
| Caching cannot change results | Phase A takes no configuration (BR-10.3) |

---

## 10. Story Logic Coverage

| Story | Logic |
|---|---|
| S1.1 | Stage 1 with bundled inputs |
| S1.2 | Stage 1 with overrides; fingerprint change forces Phase A recomputation |
| S1.3a | Stage 1 validation, BR-11 |
| S2.1 | Stages 3 and 4, BR-1 to BR-5 |
| S2.2 | Stage 5, BR-6.2 |
| S2.3 | Stage 5, BR-6.3 to BR-6.6 |
| S2.4a | Stage 5 as a pure function of `ScoringConfig` |
| S5.1 | Stage 2, BR-7 |
| S6.1 | Stage 7, BR-8.1 to BR-8.6, BR-9.1 |
| S6.2 | Stage 7 with varied `WaveConfig`, BR-8.2 |
| S6.4 | Stage 7, BR-9.2, BR-9.3 |
| S7.1 | Two Phase B passes over one cached Phase A |
| S7.2 | Serialisation from `AssessmentResult` with embedded configuration |
| S8.3a | The BR-10 phase split |

All 14 Unit 1 stories have their logic specified.

---

## 11. Verification

The complete rule set was executed against the bundled dataset before this document was finalised. Results are tabulated in `business-rules.md` §13. Every figure quoted in the worked examples above comes from that run, not from hand calculation.
