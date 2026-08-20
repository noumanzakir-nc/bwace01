# User Stories Assessment — BW-ACE

## Request Analysis

- **Original Request**: Build BW-ACE, a tool that analyses SAP BW metadata, usage logs, and dependencies to classify BW objects as Decommission, Replicate As-Is, or Rebuild as Data Product, presented through a dashboard, object detail view, dependency visualisation, and wave planner. Demo/PoC for an Acme customer presentation.
- **User Impact**: **Direct.** The entire deliverable is a user interface. Every requirement in §2.6 of the requirements document describes something a person looks at and interacts with.
- **Complexity Level**: **Medium-to-complex.** The data model is small, but the analytical model has non-obvious behaviour (two axes, guard rules, adjustable thresholds) and four distinct views serving different jobs.
- **Stakeholders**: The presenter running the demo, and the Acme audience being presented to. Within that audience, the requirements imply several distinct interests — technical migration decisions, business ownership of individual reports, and programme-level sequencing.

## Assessment Criteria Met

### High Priority
- [x] **New User Features** — the whole application is new user-facing functionality
- [x] **Multi-Persona Systems** — the three views map to three different jobs: technical assessment (dashboard, object detail), business validation (object detail, rationale), programme sequencing (wave planner). The data reinforces this: `business_owner` names a different role per solution area, and `migration_priority` / `downtime_tolerance_hours` are programme-level concerns rather than object-level ones.
- [x] **Complex Business Logic** — the classification model has multiple interacting scenarios: two axes, four quadrants collapsed to three categories, two guard rules that override computed scores, and live-adjustable thresholds that change outcomes

### Medium Priority
- [x] **Scope** — four views plus an export path plus a scenario comparison; work spans multiple user touchpoints
- [x] **Ambiguity** — validation already proved that plausible-sounding requirements can produce wrong outcomes (`IN200` and `IM100` in §4.2–4.3). Stories with explicit acceptance criteria give those cases a testable home.
- [x] **Risk** — this is shown to a customer. A visibly wrong recommendation damages credibility. High business impact for a small codebase.
- [x] **Testing** — NFR-7.2 requires tests asserting the reference classification for the bundled dataset. Acceptance criteria are the natural source for those assertions.

### Not a skip case
This is not refactoring, not a bug fix, not infrastructure, not tooling, and not documentation. None of the skip conditions apply.

## Decision

**Execute User Stories**: **Yes**

**Reasoning**: Three independent factors make this worthwhile despite the project being a PoC.

First, the personas are real and distinguishable, not invented. The requirements already separate technical assessment from business validation from programme sequencing, and the source dataset carries fields that only make sense for one audience or another. Naming those personas will sharpen which view answers which question, and reduce the risk of building four views that all serve the same imaginary user.

Second, acceptance criteria feed directly into a requirement that already exists. NFR-7.2 mandates tests that pin the reference classification for the bundled dataset. Writing stories with concrete criteria produces exactly the assertions those tests need, so the effort is not additive — it is work that would otherwise be done less rigorously during Code Generation.

Third, validation has already demonstrated that this domain punishes assumptions. Reasoning about the scoring model on paper produced a model that misclassified a dormant object as worth keeping and an actively used object as safe to switch off. Both were caught only by executing it against real data. Stories with explicit expected outcomes per object make that class of defect visible at design time rather than at demo time.

The cost is modest. The scope is well bounded and the requirements are already detailed, so stories will be quick to write and will mostly formalise decisions already made rather than reopening them.

## Expected Outcomes

- Clear separation of which view serves which persona, preventing redundant or unfocused views
- Testable acceptance criteria that become the unit and smoke test specifications required by NFR-7.1 to NFR-7.4
- Explicit expected classifications for the edge-case objects (`IN200`, `IM100`, `FI100GC`), so guard rules and threshold sensitivity are verified rather than assumed
- A demo narrative that follows a persona's journey, which is more persuasive to a customer audience than a feature tour
- Shared vocabulary between the requirements document and the eventual code structure
