# Personas — BW-ACE

**Decision reference**: Q1 = B — three analytical personas. The Demo Presenter is not modelled as a persona; capability that exists for whoever operates the tool is attributed to the analytical persona who benefits from it (see §5).

Each persona below is grounded in evidence from the approved requirements or the source dataset, not invented. The evidence is cited so the persona can be challenged on fact rather than taste.

---

## P1 — Migration Architect

**Name**: Katrine Dahl
**Role**: Lead architect for the BW decommissioning and data platform migration
**Primary entry point**: Dashboard → Object Detail → Dependency view

### Context

Katrine owns the technical recommendation for what happens to each of the objects in the BW landscape. She is accountable for the decision being defensible six months later, when someone asks why a particular query was rebuilt rather than lifted. She works across all solution areas rather than owning any one of them.

### Goals

- Reach a per-object decision she can justify with evidence rather than instinct
- Understand where technical effort concentrates, so the programme can be resourced honestly
- Find the objects nobody uses, because those are free capacity
- Know what depends on what before committing to any sequence
- Test how robust her recommendation is — if a small change in assumptions flips a decision, she needs to know that before presenting it

### Frustrations

- Usage data has historically been unavailable or untrusted, so decommissioning arguments collapse into opinion
- Dependency knowledge lives in the heads of long-serving colleagues rather than in any document
- Pressure to lift-and-shift everything, which carries the existing complexity into the new platform unchanged
- Being unable to show *why* a recommendation was reached, which makes it easy for stakeholders to reject

### What success looks like

Every one of the objects has a classification, a score on both axes, and a rationale she can read aloud. She can point at the five rebuild candidates and explain what distinguishes them from the thirteen that should simply be replicated.

### Evidence base

- Complexity scores (source §3.6): `hana_cv_count`, `transformation_count`, `custom_logic_present`, `interface_count` — a technical audience is the only consumer of these
- Object inventory (source §3.1): `adso_count`, `custom_table_count`, object types
- Dependency map (source §3.4), including `operational` edges and source-system load dependencies
- Requirements FR-2.x (scoring), FR-3.3 (threshold sensitivity), FR-4.x (dependency analysis)

---

## P2 — Solution / Business Owner

**Name**: Morten Bech
**Role**: Finance Controller — accountable for the Financial Performance reporting area
**Primary entry point**: Object Detail

### Context

Morten owns a specific set of reports rather than the landscape. Financial Performance carries the highest business criticality in the matrix (95) and the tightest downtime tolerance (4 hours), so he has the least room to absorb disruption. He is the person who will contest a recommendation, and he represents a role that recurs across every solution area.

### Goals

- Confirm that the reports his function depends on survive the migration
- Challenge any recommendation about his objects, and see the evidence behind it
- Understand what changes for his users, and when
- Be confident that "nobody uses this" is a claim backed by data rather than an assumption

### Frustrations

- Being told a report is unused when it is used heavily but only at period-end, which a naive monthly average can hide
- Decisions taken about his area without consulting him
- Recommendations presented as conclusions with no visible derivation, leaving him no way to engage except to object
- Colour-coded dashboards he cannot read comfortably in a meeting room

### What success looks like

He can open any object he owns, see its usage history, see precisely which factors drove its classification and by how much, and either accept the recommendation or make a specific, evidence-based case against it.

### Evidence base

- `business_owner` in the usage logs (source §3.2) names a distinct owning role for every object — Finance Controller, Sales Director, S&OP Lead, Production Lead, Inventory Manager, Product Costing Lead, Quality Manager, Treasurer, Logistics Manager, Procurement Manager, Transport Manager, Investment Manager, Inventory Analyst, Solution Owner
- Business criticality matrix (source §3.3) is defined per solution area, implying area-level ownership
- Requirements FR-7.5 (score breakdown), FR-7.6 (rationale), FR-3.5 (classification rationale), NFR-6.3 (explainability)
- Validation finding §4.3: `IM100` was initially misclassified as Decommission despite ten monthly users — precisely the failure mode this persona exists to catch

---

## P3 — Programme Manager

**Name**: Sofia Lindqvist
**Role**: Migration programme manager — owns sequencing, timeline, and delivery risk
**Primary entry point**: Wave Planner

### Context

Sofia does not make per-object technical decisions. She turns the assessment into a sequenced plan that can actually be delivered, respecting the DMK integration freeze and the downtime windows each business area can tolerate. Her concerns are cross-object and cross-area.

### Goals

- A wave sequence that respects both business priority and technical dependency
- Early warning when a proposed sequence would migrate something before what it depends on
- A timeline she can put in front of a steering committee, with constraints visible
- A quantified risk position per wave, so attention goes where it is warranted
- Headline landscape figures for reporting upward

### Frustrations

- Dependency surprises discovered mid-wave, when the cost of resequencing is highest
- Timelines built without reference to the freeze periods the programme is bound by
- Risk described qualitatively as "high" with nothing underneath it
- Cutover windows agreed without regard to what each area can tolerate

### What success looks like

She has a wave plan with no unflagged dependency violations, a timeline showing the DMK constraint, and a risk score per wave she can decompose into its contributing factors when challenged.

### Evidence base

- `migration_priority` (1–5) and `downtime_tolerance_hours` in the criticality matrix (source §3.3) — neither is used by the classification model; both exist solely for sequencing and cutover planning
- The DMK constraint edge in the dependency map (source §3.4): "Limited changes before 2028"
- Requirements FR-5.x (wave planning), FR-8.x (wave planner view), FR-6.1 (executive KPI strip)

---

## 4. Persona to View Mapping

| View | Primary persona | Secondary |
|---|---|---|
| Dashboard — KPI strip | Programme Manager | Migration Architect |
| Dashboard — classification charts, quadrant scatter | Migration Architect | Programme Manager |
| Dashboard — decommission candidates | Solution / Business Owner | Migration Architect |
| Object Detail | Solution / Business Owner | Migration Architect |
| Dependency view | Migration Architect | Programme Manager |
| Wave Planner | Programme Manager | Migration Architect |
| Scenario comparison | Migration Architect | — |
| Export | Programme Manager | Migration Architect |

---

## 5. Treatment of Operator-Facing Capability

Q1 = B directed that presenter-facing capability be treated as tooling rather than as a persona. Several approved **functional** requirements are nonetheless operator-oriented. Each is attributed to the analytical persona with a genuine interest in it, rather than left without an owner:

| Requirement | Attributed to | Why that persona genuinely wants it |
|---|---|---|
| FR-1.3 – FR-1.5 — runtime data upload, validation, revert | Migration Architect | Assessing a landscape extract is her core task; the bundled dataset is a starting point, not the only input |
| FR-3.3, FR-3.4, FR-3.9 — adjustable thresholds and reset | Migration Architect | Establishing whether a recommendation is robust or borderline is part of making it defensible |
| FR-9.1, FR-9.2 — scenario save and comparison | Migration Architect | Comparing two assessment stances is how she tests a contested assumption |
| FR-10.1, FR-10.3 — classification report export | Migration Architect | The report is the artefact she circulates for review |
| FR-10.2 — wave recommendation export | Programme Manager | The plan is the artefact she takes to a steering committee |
| NFR-2.x — cross-platform one-command launch | Migration Architect | A technical user who installs and runs the tool herself |
| NFR-3.x — offline operation | Programme Manager | Presents in meeting rooms where venue network access cannot be assumed |
| NFR-4.x — readability and contrast | Solution / Business Owner | The persona most likely to be reading a dense screen in an unfamiliar room |
| NFR-5.x — responsiveness | Migration Architect | Exploration is iterative; slow recomputation discourages testing assumptions |
