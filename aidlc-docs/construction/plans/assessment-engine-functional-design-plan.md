# Functional Design Plan — Unit 1 `assessment-engine`

**Phase**: 🟢 CONSTRUCTION
**Unit**: `assessment-engine` (components C1–C10, 14 stories)
**Inputs**: approved requirements, `unit-of-work.md`, `unit-of-work-story-map.md`, all five Application Design artifacts

---

## 1. Why This Stage Carries More Weight Than Usual

Requirements §4.6 and the execution plan both deferred a specific set of numbers to this stage: the normalisation band boundaries, the complexity and volume sub-weights, and the recency multiplier. Those values determine **every classification the tool produces**.

There is a hard constraint on them. Unit 1's definition of done fixes the reference distribution at **5 Rebuild / 13 Replicate As-Is / 4 Decommission**, names the exact membership of the Rebuild and Decommission sets, and requires `FI100GC` to flip to Rebuild when the Effort threshold drops to 66. Those are now binding acceptance criteria with tests behind them.

**Consequence**: the bands and sub-weights are not free parameters. They were derived during Requirements Analysis by executing the model against the real dataset, and that run is what produced the 5/13/4 figures in the first place. If you change any of them here, the reference distribution may move, and the definition of done plus its tests would have to be updated to match.

Each question below therefore states whether an alternative would break the reference distribution.

---

## 2. Questions

Eight questions. Where a validated value exists, it is shown in full so you are choosing against evidence rather than description.

---

### Question 1 — Normalisation bands

These bands were used in the Requirements Analysis validation run that produced 5/13/4.

**Usage frequency** (`monthly_executions`, observed range 2–450)

| Executions | Score |
|---|---|
| 0–5 | 0 |
| 6–25 | 20 |
| 26–75 | 40 |
| 76–150 | 60 |
| 151–300 | 80 |
| 301+ | 100 |

**Distinct users** (observed range 1–100)

| Users | Score |
|---|---|
| 0–2 | 0 |
| 3–10 | 20 |
| 11–20 | 40 |
| 21–40 | 60 |
| 41–70 | 80 |
| 71+ | 100 |

**Business criticality** — used directly, already 0–100 in the source (observed 45–95)

**Outgoing dependencies** (observed 1–6 after `ALL → DMK` expansion)

| Count | Score |
|---|---|
| 0 | 0 |
| 1 | 20 |
| 2 | 40 |
| 3 | 60 |
| 4 | 80 |
| 5+ | 100 |

**Incoming dependencies** (observed 0–5 for solution areas)

| Count | Score |
|---|---|
| 0 | 0 |
| 1 | 25 |
| 2 | 50 |
| 3–4 | 75 |
| 5+ | 100 |

**Complexity sub-attributes**

| `hana_cv_count` | Score | | `transformation_count` | Score | | `interface_count` | Score |
|---|---|---|---|---|---|---|---|
| 0 | 0 | | 0 | 0 | | 0 | 0 |
| 1–5 | 20 | | 1–3 | 20 | | 1–2 | 20 |
| 6–10 | 40 | | 4–6 | 40 | | 3–4 | 40 |
| 11–15 | 60 | | 7–9 | 60 | | 5–6 | 60 |
| 16–20 | 80 | | 10–12 | 80 | | 7–8 | 80 |
| 21+ | 100 | | 13+ | 100 | | 9+ | 100 |

`custom_logic_present`: false → 0, true → 100

**Volume sub-attributes**

| `record_count` | Score | | `storage_gb` | Score | | `load_frequency` | Score |
|---|---|---|---|---|---|---|---|
| < 500k | 0 | | < 5 | 0 | | Monthly | 0 |
| 500k–1M | 20 | | 5–10 | 20 | | Weekly | 25 |
| 1M–3M | 40 | | 11–25 | 40 | | Daily | 75 |
| 3M–8M | 60 | | 26–50 | 60 | | Hourly | 100 |
| 8M–15M | 80 | | 51–80 | 80 | | | |
| 15M+ | 100 | | 81+ | 100 | | | |

A) **Adopt these bands as validated.** They produce the reference distribution the definition of done requires. **(My recommendation.)**

B) **Adopt with adjustments I will specify** after the `[Answer]:` tag. Note that this will likely change the reference distribution, and I will re-run the model and report the new figures before writing the design.

C) **Re-derive the bands from scratch** using a different method (percentile, logarithmic). This contradicts Q3=B from Requirements Analysis, which chose fixed absolute bands, and will change the reference distribution.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 2 — Complexity sub-weights

Technical complexity is 66.67% of the Effort axis and is composed of four attributes. The validated run used:

| Attribute | Sub-weight |
|---|---|
| `hana_cv_count` | 40% |
| `transformation_count` | 30% |
| `interface_count` | 20% |
| `custom_logic_present` | 10% |

Reasoning: HANA calculation views are the dominant migration artefact and the most numerous, transformations are the next largest body of work, interfaces represent integration effort, and the custom-logic flag is binary so a large weight would make it a step change rather than a contributor.

A) **Adopt 40 / 30 / 20 / 10 as validated.** **(My recommendation.)**

B) **Equal weights, 25% each.** Simpler to explain, but treats a binary flag as equal in weight to a count ranging 0–25, which overstates it.

C) **Different weights I will specify.** I will re-run and report the effect on the reference distribution.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 3 — Volume sub-weights

Data volume is 33.33% of the Effort axis. The validated run used:

| Attribute | Sub-weight |
|---|---|
| `record_count` | 40% |
| `storage_gb` | 40% |
| `load_frequency` | 20% |

A) **Adopt 40 / 40 / 20 as validated.** Record count and storage are two views of the same underlying size and are weighted equally; load frequency is a genuine but secondary effort driver. **(My recommendation.)**

B) **Drop `load_frequency`, split 50 / 50.** Records and storage correlate strongly in this dataset, so load frequency is arguably the only independent signal — removing it would be the wrong simplification.

C) **Raise `load_frequency` to 40%**, splitting 30 / 30 / 40, on the basis that an hourly load is a materially harder cutover than a weekly one.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 4 — Recency multiplier

Requirements §4.6 flagged this as an addition rather than something the source document asked for. It multiplies the banded usage-frequency score. The validated run used, measured against the latest `last_run_date` in the dataset (2026-08-14, per assumption A-4):

| Days since last run | Multiplier |
|---|---|
| ≤ 90 | 1.00 |
| 91–180 | 0.75 |
| 181–365 | 0.50 |
| 366+ | 0.25 |

A) **Adopt as validated.** **(My recommendation.)** It is what distinguishes an object running daily from one with the same historical execution count that has not run in a year — the distinction a decommissioning assessment exists to make.

B) **Remove recency entirely**, using banded executions alone. Closer to a literal reading of the source document. Effect: `TR100` rises from 25.3 to about 28, `IN200` from 35.9 to about 36 — neither changes classification, because the dormancy ceiling now catches `IN200` regardless. So this is **safe for the reference distribution**, and is a legitimate choice if you want to defend a simpler model.

C) **Steeper decay** — 1.00 / 0.5 / 0.25 / 0.0. Sharpens the dormancy signal; risks zeroing a dimension entirely, which makes the derivation table read oddly.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 5 — Wave assignment when wave count is not 5

Wave assignment is priority-led (Q6=B from Requirements Analysis) and `migration_priority` takes values 1–5. Wave count is user-configurable, defaulting to 5 (Q7=C).

With 5 waves the mapping is one-to-one. With a different wave count it is undefined, and this needs a rule.

A) **Proportional compression.** Map the priority range onto the wave range proportionally, so with 3 waves priorities 1–2 land in wave 1, 3 in wave 2, and 4–5 in wave 3. With more than 5 waves, later waves are left empty rather than splitting a priority. Predictable and preserves relative ordering. **(My recommendation.)**

B) **Balanced object count.** Distribute so each wave holds a similar number of objects, respecting priority order. Produces even waves, but two areas of equal priority can land in different waves, which is hard to justify to a business owner.

C) **Clamp.** Priorities above the wave count all collapse into the final wave, so with 3 waves priorities 3, 4 and 5 all land in wave 3. Simplest rule; produces very lopsided waves.

D) **Restrict wave count to 5.** Remove the configurability and keep the one-to-one mapping. Contradicts Q7=C, which explicitly asked for configurable waves.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 6 — Dependency violation semantics

Violations are detected between solution areas. But the dependency graph also contains non-area nodes that have no wave: `FF` (Financial Forecasting, external), `SAPPS1` (source system), `DMK` (constraint), and `ZMD1` (shared object).

How should edges to non-area nodes be treated when detecting violations?

A) **Ignore edges to non-area nodes.** A violation requires both endpoints to be solution areas with an assigned wave. `FF`, `SAPPS1` and `DMK` are outside programme scope and cannot be sequenced; the DMK constraint is handled separately as a risk contribution (FR-5.7). **(My recommendation.)**

B) **Treat `ZMD1` as schedulable, ignore the rest.** `ZMD1` is an object in the inventory and does receive a wave, so `PR → ZMD1` and `IN → ZMD1` could be genuine ordering constraints — the shared control table arguably needs migrating before or with its consumers.

C) **Treat all non-area nodes as wave 0** (must exist before everything), so any edge to them is satisfied by definition. Equivalent to A in outcome, more machinery.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 7 — Wave risk formula

Requirements Q9=B fixed the inputs: average technical complexity, cross-wave dependency count, and downtime tolerance, plus a DMK contribution before 2028 (FR-5.7). The combination is undefined.

A) **Weighted sum of four normalised contributions**, each 0–100, then banded:

| Contribution | Weight | Derivation |
|---|---|---|
| Average technical complexity | 40% | Mean Effort-axis complexity score of the wave's objects |
| Cross-wave dependencies | 25% | Count of the wave's dependency violations plus edges crossing wave boundaries, banded |
| Downtime tolerance | 25% | Inverted — lower `downtime_tolerance_hours` yields a higher contribution |
| DMK constraint | 10% | 100 if the wave ends before 2028, else 0 |

Bands: 0–39 Low, 40–69 Medium, 70–100 High. Each contribution is stored separately so the breakdown required by S6.4 AC2 is available. **(My recommendation.)**

B) **Equal weights, 25% each.** Simpler, but gives the binary DMK flag the same influence as complexity, which would push nearly every early wave to High and flatten the signal.

C) **Multiplicative** — a base risk from complexity, scaled by dependency and downtime factors. More sensitive, harder to decompose into the named contributions S6.4 AC2 requires.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 8 — Rationale wording

FR-3.5 and S4.2 AC4–AC6 require a plain-language rationale naming the dominant factors. Story S3.4 AC3 additionally requires that a score-driven rationale reads differently from a guard-rule one.

A) **Template-driven with slotted evidence.** A small set of templates — one per classification, one per guard rule — with the top contributing dimensions and their values inserted. Deterministic, so testable by assertion, and consistent in tone across all 22 objects. **(My recommendation.)**

B) **Rule-composed sentences.** Build the sentence from a series of conditional clauses, producing more varied phrasing. More natural to read, harder to test and to keep consistent.

C) **Structured fields rather than prose** — return the top factors as data and let the UI compose the wording. Cleanest separation, but moves an FR-3.5 responsibility into Unit 2, weakening the boundary.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## 3. Settled Without a Question

Recorded so you can see what I decided rather than asked, and object if you disagree.

| Item | Resolution | Basis |
|---|---|---|
| **Guard rule evaluation order** | Order is irrelevant — the two rules are mutually exclusive. Dormancy requires more than 180 days idle; the activity floor requires 90 days or fewer. No object can satisfy both. The design will assert this with a test rather than rely on ordering. | Arithmetic |
| **Objects satisfying neither guard rule** | Fall through to pure score-based classification. Includes the two interesting middle cases: long-idle but historically heavy (days > 180, executions ≥ 5), and recent but barely used (days ≤ 90, executions < 25). | Guard rules are exceptions, not a complete partition |
| **Reference date for recency** | Latest `last_run_date` in the dataset, so results are reproducible whenever the demo is run. | Requirements assumption A-4 |
| **`ZMD1` scoring** | Criticality and dependency counts are the average of Production and Inventory Management. Its own graph node degree is displayed but not scored. | Requirements Q4=B, FR-4.5 |
| **`ALL → DMK` expansion** | Expands to 12 edges, one per solution area, and counts equally with other edge types. Adds a uniform offset with no discriminating power — documented, not treated as a defect. | Requirements Q5=A, FR-4.3 |
| **Axis weights** | Business Value 29.41 / 17.65 / 23.53 / 17.65 / 11.76; Technical Effort 66.67 / 33.33. | Requirements §2.2.1, already approved |
| **Thresholds** | Value 33, Effort 67, both adjustable. Guard parameters 180 days / 5 executions / 90 days / 25 executions, adjustable. | Requirements CQ2=A, FR-3.9 |
| **Object count** | 22 objects across 12 solution areas. `ZMD1` is one of the 22. | Counted from source §3.1; corroborated by 5 + 13 + 4 = 22 |

---

## 4. Execution Checklist

Executed after this plan is approved.

### 4.1 Preparation
- [x] Confirm normalisation bands from Question 1
- [x] Confirm complexity sub-weights from Question 2
- [x] Confirm volume sub-weights from Question 3
- [x] Confirm recency treatment from Question 4
- [x] Confirm wave compression rule from Question 5
- [x] Confirm violation semantics from Question 6
- [x] Confirm risk formula from Question 7
- [x] Confirm rationale approach from Question 8
- [x] **If any answer departs from the validated values, re-run the model against the dataset and report the resulting distribution before writing the design**

### 4.2 Generate domain-entities.md
- [x] Every entity with fields, types, and constraints
- [x] Entity relationships and cardinality
- [x] Identity and equality rules
- [x] Immutability rules and the reason for them
- [x] Enumerations with their complete value sets
- [x] Derived and computed fields distinguished from stored ones

### 4.3 Generate business-rules.md
- [x] Normalisation band tables for all dimensions, as confirmed
- [x] Sub-weight tables, as confirmed
- [x] Recency rule, as confirmed
- [x] Axis weighting and the guarantee that each axis lands in 0–100
- [x] Area inheritance rules, including cross-area averaging
- [x] Quadrant mapping rule
- [x] Both guard rules with their mutual exclusivity asserted
- [x] Wave assignment rule including the compression case
- [x] Violation detection rule including non-area node handling
- [x] Risk formula with contributions and band boundaries
- [x] Validation rules per dataset, with error message shapes
- [x] Referential integrity rules across datasets
- [x] Every rule given an identifier for test traceability

### 4.4 Generate business-logic-model.md
- [x] The full pipeline as an ordered sequence of transformations
- [x] Inputs and outputs of each stage
- [x] The `compute_base` / `apply_config` split and why it is exact
- [x] Worked example: one object traced end to end with real numbers
- [x] Worked example: `IN200`, showing the dormancy ceiling overriding its score
- [x] Worked example: `IM100`, showing the activity floor protecting it
- [x] Edge cases and how each is handled
- [x] Determinism guarantees

### 4.5 Verify
- [x] Every one of the 14 Unit 1 stories has its logic specified
- [x] Every acceptance criterion traceable to a numbered rule
- [x] Reference distribution reproduced by the specified rules
- [x] No rule contradicts an approved requirement
- [x] No presentation concern has leaked into the design
- [x] Re-run the model against the final rule set and confirm 5 / 13 / 4 plus the three named edge cases

### 4.6 Completion
- [x] Mark all items above [x]
- [x] Update `aidlc-docs/aidlc-state.md`
- [x] Append outcome to `aidlc-docs/audit.md`
- [x] Present the two-option completion message and await approval

---

## 5. Artifacts

| Artifact | Contents |
|---|---|
| `construction/assessment-engine/functional-design/domain-entities.md` | Entities, fields, relationships, constraints, enumerations |
| `construction/assessment-engine/functional-design/business-rules.md` | Every numbered rule: bands, weights, guards, waves, risk, validation |
| `construction/assessment-engine/functional-design/business-logic-model.md` | Pipeline, algorithms, worked examples, edge cases |

`frontend-components.md` is not produced — Unit 1 has no UI. It belongs to Unit 2 Functional Design.

---

## 6. Out of Scope

- Colour system, view layout, chart specifications → Unit 2 Functional Design
- File names, dependency pins, test framework choice → Code Generation
- Any Streamlit, Plotly, or pandas concern → Unit 2
