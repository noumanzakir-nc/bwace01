# Story Generation Plan — BW-ACE

**Stage**: INCEPTION — User Stories (Part 1: Planning)
**Assessment**: See `user-stories-assessment.md` — User Stories confirmed as valuable
**Input**: `aidlc-docs/inception/requirements/requirements.md` (approved 2026-08-18)

---

## 1. Purpose of this Plan

This plan sets out **how** stories will be written, not what they say. It records the methodology, the breakdown approach, the format, and the persona set, so that story generation is mechanical rather than improvised.

Because the requirements document is already detailed and approved, most story content is constrained. The decisions below concern structure and emphasis.

---

## 2. Questions

Please fill in each `[Answer]:` tag. Where I have a recommendation it is marked, and the reasoning is given so you can disagree with it on substance.

Six questions.

---

### Question 1 — Persona set

The requirements imply several distinct audiences. My reading of the data and the three views suggests these four:

- **Migration Architect** — owns the technical decision. Wants to know which objects are complex, what depends on what, and where the effort sits. Primary user of the dashboard and object detail.
- **Solution / Business Owner** — owns a specific reporting area. The `business_owner` field names one per object (Finance Controller, Sales Director, S&OP Lead, Treasurer, and so on). Wants to challenge a recommendation about *their* report and see the evidence behind it.
- **Programme Manager** — owns sequencing and risk. Wants waves, timeline, DMK constraint, and per-wave risk. Primary user of the wave planner.
- **Demo Presenter** — the consultant operating the tool in the room. Has needs the others don't: load data, adjust thresholds live, compare scenarios, export a takeaway. Several requirements (FR-1.3, FR-3.3, FR-9.1, FR-10.1) exist almost solely for this person.

Which persona set should the stories use?

A) **All four as listed** — including the Demo Presenter as a first-class persona. Reflects that this is a demo tool and that a material share of the requirements serve the operator rather than the analytical audience. **(My recommendation.)**

B) **The three analytical personas only** — Migration Architect, Solution Owner, Programme Manager. Treat presenter-facing capability as non-functional tooling rather than persona-driven stories. Cleaner if you want the stories to read as a product spec rather than a demo script.

C) **Two personas** — collapse Migration Architect and Programme Manager into a single "Migration Lead", keeping Solution Owner and Demo Presenter. Simpler, but loses the distinction between object-level technical judgement and programme-level sequencing, which is exactly the split between the dashboard and the wave planner.

D) **Five or more** — as A, plus split the Solution Owner into distinct finance / supply chain / production variants to reflect the different criticality profiles in the data.

X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

### Question 2 — Story breakdown approach

How should stories be organised?

A) **Persona-based** — group stories under each persona. Makes the "who benefits" question immediate and reads well alongside a demo narrative, but scatters related technical work across groups.

B) **Feature-based** — group by capability: data ingestion, scoring engine, classification, dependency analysis, wave planning, export. Maps cleanly onto the eventual code structure and onto the units of work, but obscures user value.

C) **User journey-based** — follow the path an assessment actually takes: load the landscape → see the overall picture → interrogate a specific object → understand dependencies → plan the waves → export the recommendation. Strong for a demo, because the story order *is* the demo order.

D) **Hybrid: epics by capability, stories written from a persona's perspective** — six or seven capability epics, each containing stories phrased as "As a [persona], I want…". Gives the traceability to requirements and units of work that B provides, while keeping user value explicit as in A. **(My recommendation.)**

X) Other (please describe after [Answer]: tag below)

[Answer]: D

---

### Question 3 — Story granularity

How finely should stories be split?

A) **Coarse — roughly 8 to 12 stories.** One per major capability. Fast to read, but individual stories become large and harder to test as single units.

B) **Moderate — roughly 15 to 22 stories.** Each story is one coherent piece of user-visible value, small enough to implement and verify independently. Fits the INVEST criteria comfortably at this project size. **(My recommendation.)**

C) **Fine — 30 or more stories.** One per individual UI component and engine rule. Thorough, but at this scale the overhead outweighs the benefit and the story list becomes a restatement of the requirements list.

X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

### Question 4 — Acceptance criteria format

Every story will carry acceptance criteria. What form should they take?

A) **Given/When/Then (Gherkin-style)** — explicit and directly translatable into test cases. More verbose, but the structure forces the precondition to be stated, which matters for the threshold-dependent behaviour in this tool. **(My recommendation.)**

B) **Checklist of verifiable statements** — concise bullet list of conditions that must hold. Faster to read and write; slightly weaker at capturing state-dependent behaviour.

C) **Mixed** — Given/When/Then for engine and classification stories where preconditions matter, checklists for straightforward UI presence stories.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 5 — Concrete data expectations in acceptance criteria

NFR-7.2 requires tests asserting the reference classification for the bundled Arla dataset. Validation established specific expected outcomes, including three edge cases: `IN200` must be Decommission via the dormancy ceiling, `IM100` must be Replicate As-Is via the activity floor, and `FI100GC` sits 0.7 points below the Effort threshold.

Should acceptance criteria name specific objects and expected results?

A) **Yes, including the full reference distribution** — criteria cite the expected 5 Rebuild / 13 Replicate / 4 Decommission split and name each edge-case object with its expected classification and the rule responsible. Stories become the executable specification for the tests. Ties stories to the bundled dataset, which is acceptable because that dataset is a fixed requirement (FR-1.2). **(My recommendation.)**

B) **Edge cases only** — name `IN200`, `IM100`, and `FI100GC` explicitly, but leave the overall distribution to the tests rather than the stories. Keeps stories more implementation-neutral.

C) **No specific data** — criteria stay behavioural ("a dormant object is classified Decommission") with no object names. Most portable if the dataset ever changes, but loses the direct link to the tests NFR-7.2 requires.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 6 — Non-functional coverage in stories

The requirements include substantial non-functional content: WCAG AA contrast, offline font fallback, cross-platform launch scripts, minimal code comments, performance targets.

How should this appear in the stories?

A) **Dedicated non-functional stories** — a small set of stories covering accessibility, cross-platform launch, and offline robustness, written from the affected persona's perspective (for example, the Demo Presenter needing the app to work without venue wifi). Makes these testable and visible rather than buried in a requirements table. **(My recommendation.)**

B) **As acceptance criteria on functional stories** — fold contrast, readability, and performance expectations into the criteria of the relevant UI stories. No separate stories. Avoids the awkwardness of a "story" that no user requested, but risks these being deprioritised.

C) **Excluded from stories** — leave all non-functional requirements in the requirements document only, and let stories cover functional behaviour exclusively.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## 3. Execution Checklist

To be executed in Part 2 after this plan is approved. Steps are marked `[x]` as completed.

### 3.1 Preparation
- [x] Re-read approved requirements, including §3.10 guard rules and §4 validation findings
- [x] Confirm persona set from Question 1
- [x] Confirm breakdown approach from Question 2
- [x] Confirm granularity target from Question 3
- [x] Confirm acceptance criteria format from Questions 4 and 5
- [x] Confirm non-functional treatment from Question 6

### 3.2 Generate personas
- [x] Create `aidlc-docs/inception/user-stories/personas.md`
- [x] For each persona: name, role, context, goals, frustrations, what success looks like
- [x] Ground each persona in evidence from the requirements or source dataset, not invention
- [x] Identify which of the four views is each persona's primary entry point

### 3.3 Generate stories
- [x] Create `aidlc-docs/inception/user-stories/stories.md`
- [x] Organise per the approved breakdown approach
- [x] Write each story in the approved format with a stated persona
- [x] Attach acceptance criteria to every story in the approved format
- [x] Include the concrete data expectations agreed in Question 5
- [x] Include non-functional coverage per Question 6

### 3.4 Verify story quality
- [x] Check every story against INVEST: Independent, Negotiable, Valuable, Estimable, Small, Testable
- [x] Confirm each story delivers value to a named persona
- [x] Confirm no story depends on another to be understood
- [x] Confirm every story is verifiable from its criteria alone

### 3.5 Traceability
- [x] Map every story to the requirement IDs it satisfies
- [x] Map every persona to its relevant stories
- [x] Confirm no approved requirement is left uncovered by any story
- [x] Record any deliberate gaps with rationale

### 3.6 Completion
- [x] Mark all checklist items above `[x]`
- [x] Update `aidlc-docs/aidlc-state.md`
- [x] Append outcome to `aidlc-docs/audit.md`
- [x] Present completion message and await approval

---

## 4. Story Breakdown Options — Trade-offs

Recorded for the decision in Question 2.

| Approach | Strength | Weakness | Fit here |
|---|---|---|---|
| User journey-based | Story order mirrors the demo order; naturally persuasive | Cross-cutting engine work is hard to place in a journey | Good for the demo, awkward for the scoring engine |
| Feature-based | Maps cleanly to code structure and units of work | User value becomes implicit; reads like a task list | Good for construction, weak for stakeholder communication |
| Persona-based | Makes "who benefits" immediate | Related technical work scatters across personas; duplication likely | Good for framing, weak for traceability |
| Domain-based | Aligns to business domains | This tool has one domain (BW landscape assessment); little to divide | Poor fit |
| Epic-based hybrid | Capability epics with persona-phrased stories | Slightly more structure to maintain | Strong fit — keeps traceability and user value together |

---

## 5. Mandatory Artifacts

Both will be produced regardless of the answers above:

- `aidlc-docs/inception/user-stories/personas.md` — user archetypes with characteristics
- `aidlc-docs/inception/user-stories/stories.md` — stories satisfying INVEST, each with acceptance criteria, each mapped to a persona and to requirement IDs

---

## 6. Out of Scope for this Stage

Deliberately excluded, per the stage rules:

- Prioritisation, estimation, or sprint planning
- Technical design or implementation detail
- Development timelines
- Decomposition into units of work (that is the Units Generation stage)
