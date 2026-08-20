# Requirements Verification Questions — BW-ACE

Your requirement document is detailed and clear on data and scoring. These questions resolve the remaining ambiguities before I write the requirements document.

**How to answer**: Fill in the letter choice after each `[Answer]:` tag. If none of the options fit, pick the **Other** option and describe what you want after the tag. Tell me when you're done.

---

## Section A — Scoring & Classification Logic

### Question 1 — The scoring formula has a directional conflict
The scoring formula sums all seven dimensions, and a **high** total score means "Rebuild as Data Product" while a **low** total means "Decommission".

But **Technical Complexity** (10%) and **Data Volume** (5%) push in a conflicting direction: an object can be highly complex and huge while barely being used (a classic decommission or replicate candidate), yet complexity/volume would inflate its score toward "Rebuild".

There is a second, related conflict: high technical complexity is normally an argument *against* rebuilding cheaply and *for* replicating as-is or decommissioning — but the document lists complexity as a positive contributor.

How should complexity and volume behave in the score?

A) **Keep as documented** — complexity and volume add positively to the score (higher complexity/volume = more likely Rebuild, on the logic that complex+large objects gain the most from modernisation). Simple, matches the document exactly.

B) **Usage gate + positive complexity** — keep the formula as documented, but add an override rule: if usage is effectively dead (e.g. no runs in the last 6 months AND under ~5 monthly executions), force classification to **Decommission** regardless of the computed score. This preserves the documented formula but prevents unused-but-complex objects being mislabelled.

C) **Invert complexity** — treat complexity as a negative/inverted contributor (high complexity reduces the score, favouring Replicate As-Is over Rebuild), keeping volume positive.

D) **Two-axis model** — compute a *Business Value* score (usage, users, criticality, dependencies) and a separate *Technical Effort* score (complexity, volume), then classify on the value/effort matrix. Most analytically defensible, and gives a strong 2x2 quadrant visual for the demo, but deviates most from the documented formula.

X) Other (please describe after [Answer]: tag below)

[Answer]: D

---

### Question 2 — Score band boundaries
The document defines bands 0-33 (Decommission), 34-67 (Replicate As-Is), 68-100 (Rebuild). With the documented weights and this dataset, most objects will likely land in the middle band, which may make for a flat-looking demo.

How should the thresholds be handled?

A) **Fixed as documented** — hardcode 33 / 67 boundaries exactly as specified.

B) **Configurable with documented defaults** — default to 33 / 67, but expose the two thresholds as sliders in the UI so you can demonstrate sensitivity live in front of the customer. (Recommended — strong demo moment, no loss of fidelity.)

C) **Fully configurable** — expose both thresholds *and* the seven dimension weights as adjustable controls, with a reset-to-default button.

X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

### Question 3 — Normalising each dimension to 0-100
Each dimension must be normalised to 0-100 before weighting, but the document doesn't specify how. This choice materially changes results (e.g. `monthly_executions` ranges from 2 to 450 in your data).

Which normalisation approach do you want?

A) **Min-max relative to the dataset** — the lowest-value object scores 0, the highest scores 100, everything scales linearly between. Simple, always uses the full 0-100 range, but scores shift whenever the dataset changes.

B) **Fixed absolute bands** — define explicit business thresholds per dimension (e.g. executions: 0-5 → 0, 6-25 → 25, 26-100 → 50, 101-250 → 75, 250+ → 100). Scores are stable and explainable to the business, and defensible in a customer conversation. (Recommended for a customer demo — every score can be justified.)

C) **Logarithmic min-max** — log-scale before min-max, to stop very large values (e.g. SC100's 18M records) dominating.

D) **Percentile rank** — each object scored by its percentile position within the dataset.

X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

### Question 4 — Object-level vs solution-area-level data
Business criticality (3.3) and the dependency map (3.4) are defined at **solution area** level, while everything else is at **object** level. Also, object `ZMD1` has solution area `"Production/Inventory"`, which does not match any single entry in the criticality matrix or dependency map.

How should this be resolved?

A) **Inherit from solution area** — every object inherits its solution area's criticality and that area's incoming/outgoing dependency counts. For `ZMD1`, take the **maximum** criticality of Production and Inventory Management (85) and the **union** of both areas' dependencies.

B) **Inherit, with averaging for multi-area objects** — same as A, but `ZMD1` gets the **average** criticality of its two areas (82.5).

C) **Treat ZMD1 as a special shared object** — it appears as a node in the dependency graph in its own right, so give it its own criticality derived from how many areas depend on it, rather than inheriting.

X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

### Question 5 — Counting dependencies
The dependency map mixes several edge kinds: `logical`, `operational`, `constraint`, and node types `solution_area`, `external`, `constraint`, `shared_object`, `source`. There's also a wildcard edge `{"source": "ALL", "target": "DMK"}`.

How should dependency counts feed the score?

A) **All edges count equally** — count every outgoing/incoming edge, expand `ALL` to every solution area, treat all edge types the same.

B) **Exclude the constraint edge, count the rest equally** — the `ALL → DMK` constraint edge applies to everything and so adds no discriminating signal; exclude it from scoring but keep it visible as a global constraint in the wave planner. Count logical and operational edges equally. (Recommended.)

C) **Weighted by edge type** — operational dependencies (hard runtime coupling) weigh more than logical ones; constraint edges excluded from scoring.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Section B — Wave Planner (least-specified area)

### Question 6 — What drives wave assignment?
Section 2.3.3 asks for wave optimisation, a Gantt timeline with "DMK constraints", and per-wave risk scores — but the algorithm isn't defined.

How should objects/areas be grouped into waves?

A) **Dependency-topological** — order waves so that anything an area depends on migrates in an earlier or the same wave; use `migration_priority` from 3.3 to break ties.

B) **Priority-led with dependency validation** — group primarily by the `migration_priority` field (1-5) already in your criticality matrix, then flag any dependency violations as risks. Simplest to explain and directly uses your data. (Recommended.)

C) **Balanced-load optimisation** — topological ordering plus balancing of effort/complexity across waves so no wave is overloaded.

D) **Classification-first** — Wave 0 = decommission everything unused (quick win), then dependency-topological ordering for the rest.

X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

### Question 7 — Wave count and timeline
For the Gantt chart I need a concrete timeline basis.

A) **Derive from priority** — 5 waves matching `migration_priority` values 1-5, each wave a fixed duration (e.g. 3 months), starting from a configurable project start date.

B) **Fixed 4 waves** over a configurable horizon, with objects distributed by the chosen algorithm.

C) **User-configurable** — number of waves and wave duration adjustable in the UI, with sensible defaults (5 waves x 3 months). (Recommended for demo flexibility.)

X) Other (please describe after [Answer]: tag below)

[Answer]: C

---

### Question 8 — The DMK constraint
The dependency map states DMK has "Limited changes before 2028". How should this show up?

A) **Visual marker only** — draw a "DMK freeze until 2028" band/annotation on the Gantt chart, no effect on wave logic.

B) **Visual marker plus risk flag** — as A, plus any wave scheduled to complete before 2028 gets a flagged DMK-constraint risk contribution in its risk score. (Recommended.)

C) **Hard scheduling constraint** — waves are actively pushed out so that DMK-touching work cannot be scheduled before 2028.

X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

### Question 9 — Per-wave risk score
What should the wave risk score be composed of?

A) **Complexity + dependency count** — average technical complexity of the wave's objects plus a penalty for cross-wave dependencies.

B) **Complexity + dependencies + downtime tolerance** — as A, plus a penalty where `downtime_tolerance_hours` is low (tight cutover windows are riskier). (Recommended — uses more of your dataset.)

C) **Composite index** — complexity, dependencies, downtime tolerance, data volume, and business criticality combined into a 0-100 risk index with a Low/Medium/High banding.

X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Section C — Technology Stack

### Question 10 — Frontend / stack choice
You invited alternatives. My assessment of the recommended stack for a customer-facing PoC:

- **Streamlit** — fastest path to a polished multi-view analytical UI in Python, and it handles Plotly, tables, and sidebar filters natively. Its main weakness is fine-grained visual control, but your brand palette is achievable via theme config plus a small CSS injection.
- **Pandas / NetworkX / Plotly** — well suited to this problem; NetworkX gives dependency traversal and topological ordering essentially for free, and Plotly covers donut, bar, heatmap, and Gantt.
- **Python version** — I'd target **Python 3.12** (the current widely-supported stable line with the best library compatibility) rather than the newest release, to minimise install friction on a demo machine.

Which do you prefer?

A) **Keep the recommended stack** — Streamlit + Pandas + NetworkX + Plotly on Python 3.12. Fastest to build, single language, single command to run, works identically on Windows and Linux. (My recommendation for a PoC.)

B) **Streamlit stack, but swap Plotly for Altair/Vega-Lite** — cleaner default aesthetics, but weaker Gantt and network-graph support (I'd have to hand-roll those).

C) **FastAPI backend + React frontend** — much greater visual polish and control, genuinely production-shaped, but several times the build effort and needs Node.js plus a build step on the demo machine.

D) **Dash (Plotly Dash) instead of Streamlit** — more layout control and callback precision than Streamlit, still pure Python, but more boilerplate.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 11 — Data storage
The document specifies JSON/CSV files. Section 2.1 also mentions CSV as an accepted input format.

A) **JSON files only** — six JSON files under `data/`, exactly matching sections 3.1-3.6. Simplest, zero setup.

B) **JSON files, plus the ability to upload a replacement CSV/JSON in the UI** — ships with the Acme demo data but lets you load a customer's own extract live. Good demo differentiator, modest extra effort. (Recommended.)

C) **SQLite database** — seeded from the JSON on first run; enables richer querying but adds a layer with little benefit at this data size.

X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

### Question 12 — Output artefacts
Section 4.2 lists `outputs/classification_report.csv` and `outputs/wave_recommendation.json`.

A) **Generated on app startup** — written to `outputs/` automatically every time the app runs.

B) **Export on demand** — download buttons in the UI for classification CSV and wave recommendation JSON, reflecting the current threshold/weight settings. (Recommended — the export then matches whatever the audience just watched you configure.)

C) **Both** — baseline files written at startup, plus on-demand export buttons.

X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Section D — UI & Branding

### Question 13 — Colour palette application and contrast
You gave backgrounds `#02462f`, `#f2f7f1`, `#f6eeee`, `#ffffff` and text/accent colours `#0d6a4b`, `#82ce71`, `#ffffff`.

I checked the contrast ratios, and two of the combinations you might expect to use are not readable:

- `#0d6a4b` on `#f2f7f1` → **5.8:1** ✅ passes AA for normal text
- `#02462f` on `#f2f7f1` → **10.5:1** ✅ excellent
- `#ffffff` on `#02462f` → **11.4:1** ✅ excellent
- `#82ce71` on `#ffffff` → **1.9:1** ❌ fails badly — unusable for text
- `#82ce71` on `#02462f` → **6.0:1** ✅ passes — good for accents on the dark green
- `#ffffff` on `#82ce71` → **1.9:1** ❌ fails

So `#82ce71` works as a chart colour, a highlight, or as text on the dark green, but must not be used as text on white or light backgrounds.

How would you like me to apply this?

A) **Light theme** — `#f2f7f1` app background, white cards, `#02462f` dark-green header/sidebar with white text, `#0d6a4b` for headings and body emphasis, `#82ce71` reserved for chart accents and highlights only, `#f6eeee` as a warm neutral for warning/decommission callouts. All text combinations meet WCAG AA. (Recommended.)

B) **Dark theme** — `#02462f` as the dominant background with white and `#82ce71` text, light tones used sparingly for cards. Striking, but heavier for dense tables and reduces chart legibility.

C) **Light theme with a dark hero section** — mostly as A, but the dashboard opens with a full-width dark green banner containing headline KPI figures.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 14 — Classification colour coding
The three classification categories need distinct, intuitive colours that still sit within your palette.

A) **Palette-derived** — Rebuild = `#02462f` (dark green), Replicate = `#82ce71` (light green), Decommission = a muted terracotta/red derived to harmonise with `#f6eeee`. Stays on-brand while keeping the "decommission" signal clearly distinct. (Recommended.)

B) **Strictly palette-only** — three tints of green only. Fully on-brand but the categories read as a sequence rather than as distinct decisions, and decommission loses its warning signal.

C) **Conventional traffic-light** — green / amber / red, ignoring the brand palette for these three chips.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 15 — Fonts
No typeface was specified, only colours.

A) **System font stack** — Segoe UI on Windows, system sans on Linux. Zero dependencies, no network calls, guaranteed to render. (Recommended for a demo that may run offline.)

B) **A bundled Google font** (e.g. Inter or Source Sans 3) loaded via CDN — more consistent cross-platform look, but needs internet access at demo time.

C) **A bundled font shipped with the app** — consistent and offline-safe, but adds font files to the repo.

X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

### Question 16 — Dependency heatmap form
Section 2.3.1 asks for a "Dependency Heatmap" showing dependencies between solution areas; 2.3.3 and 2.3.2 also imply a dependency view.

A) **Matrix heatmap only** — solution-area x solution-area grid, cells shaded by dependency presence/strength. Literal reading of the requirement.

B) **Matrix heatmap plus a network graph** — the matrix for precision, and a NetworkX/Plotly node-link diagram for the intuitive visual. The network view is usually the one that lands in a customer demo. (Recommended.)

C) **Network graph only** — replace the matrix with the node-link view.

X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Section E — Scope, Quality & Extensions

### Question 17 — Testing scope
This is a demo/PoC, but the scoring engine is the analytical core and the part a customer is most likely to challenge.

A) **Unit tests for the engine only** — scoring, normalisation, classification, dependency analysis, wave planning. UI verified manually. (Recommended — protects the credibility-critical logic without slowing the build.)

B) **No automated tests** — fastest, but a scoring bug discovered live would be costly.

C) **Engine unit tests plus UI smoke tests** — as A, plus automated checks that each view renders without error.

X) Other (please describe after [Answer]: tag below)

[Answer]: C

---

### Question 18 — Security Extensions
Should security extension rules be enforced for this project?

A) Yes — enforce all SECURITY rules as blocking constraints (recommended for production-grade applications)

B) No — skip all SECURITY rules (suitable for PoCs, prototypes, and experimental projects)

X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

### Question 19 — Resiliency Extensions
Should the resiliency baseline be applied to this project?

**What this extension is.** Enabling it applies a set of **directional, design-time best practices** for building resilient systems, derived from the **AWS Well-Architected Framework (Reliability Pillar)** and resilience-review guidance. It steers requirements, design, and code toward fault tolerance, high availability, observability, and recoverability — covering 15 practice areas across business goals, change management, observability, high availability, disaster recovery, and continuous improvement.

**What this extension is NOT.** Enabling it does **not** make your workload production-ready, nor does it certify or guarantee any availability, RTO, or RPO target. It is a **starting point** that scaffolds good resiliency decisions early — it is not a substitute for a formal **AWS Well-Architected Review** of the built system.

Treat the output as a well-grounded **first draft of your resiliency posture** to build on and validate — not a finished, production-certified result.

A) Yes — apply the resiliency baseline as directional best practices and design-time guidance (recommended for business-critical workloads, as an informed starting point that you can validate and harden before go-live)

B) No — skip the resiliency baseline (suitable for PoCs, prototypes, and experimental projects where rapid iteration matters more than reliability)

X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

### Question 20 — Property-Based Testing Extension
Should property-based testing (PBT) rules be enforced for this project?

A) Yes — enforce all PBT rules as blocking constraints (recommended for projects with business logic, data transformations, serialization, or stateful components)

B) Partial — enforce PBT rules only for pure functions and serialization round-trips (suitable for projects with limited algorithmic complexity)

C) No — skip all PBT rules (suitable for simple CRUD applications, UI-only projects, or thin integration layers with no significant business logic)

X) Other (please describe after [Answer]: tag below)

[Answer]: C

---

### Question 21 — Deployment / run method
You asked for a simple way to run on Windows and Linux, documented in the README.

A) **Scripted local run** — `run.bat` (Windows) and `run.sh` (Linux/macOS) that create a virtual environment, install pinned dependencies, and launch the app. Only prerequisite is Python. (Recommended.)

B) **Docker** — a single `docker compose up`. Fully reproducible and isolated, but requires Docker on the demo machine.

C) **Both** — scripts as the primary path, with a Dockerfile as an alternative for locked-down environments.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 22 — Anything the document doesn't cover that you want in the demo?
Optional. Examples: a cost/effort savings estimate, a "what-if" scenario comparison, an executive summary export (PDF/PowerPoint), or a landscape-level KPI header.

A) **No — build exactly what's in the requirement document.**

B) **Yes — add an executive KPI summary strip** at the top of the dashboard (total objects, total storage, % decommissionable, estimated storage reclaimed).

C) **Yes — add a "what-if" comparison** letting you save and compare two weight/threshold configurations side by side.

D) **Yes — both B and C.**

X) Other (please describe after [Answer]: tag below)

[Answer]: D

---

## Summary of my recommendations

If you'd prefer to move quickly, answering **"use your recommendations"** applies these:

| Q | Topic | Recommended |
|---|---|---|
| 1 | Scoring direction | B — documented formula + dead-usage override |
| 2 | Thresholds | B — configurable, documented defaults |
| 3 | Normalisation | B — fixed absolute bands |
| 4 | Area-level data | A — inherit, max for ZMD1 |
| 5 | Dependency counting | B — exclude constraint edge |
| 6 | Wave algorithm | B — priority-led + dependency validation |
| 7 | Wave count | C — configurable, 5 x 3 months default |
| 8 | DMK constraint | B — marker + risk flag |
| 9 | Wave risk | B — complexity + deps + downtime tolerance |
| 10 | Stack | A — Streamlit/Pandas/NetworkX/Plotly, Python 3.12 |
| 11 | Storage | B — JSON + optional upload |
| 12 | Outputs | B — export on demand |
| 13 | Theme | A — light theme, AA-compliant |
| 14 | Classification colours | A — palette-derived |
| 15 | Fonts | A — system stack |
| 16 | Dependency view | B — matrix + network graph |
| 17 | Testing | A — engine unit tests |
| 18 | Security extension | B — skip (PoC) |
| 19 | Resiliency extension | B — skip (PoC) |
| 20 | PBT extension | C — skip (PoC) |
| 21 | Run method | A — run scripts |
| 22 | Extras | B — executive KPI strip |
