# Requirements — BW Object Assessment & Classification Engine (BW-ACE)

**Project**: BW-ACE
**Version**: 1.0
**Date**: 2026-08-18
**Status**: Awaiting approval

---

## 1. Intent Analysis

| Aspect | Assessment |
|---|---|
| **User request** | Build a tool that analyses SAP BW metadata, usage logs, and dependencies to classify BW objects as Decommission, Replicate As-Is, or Rebuild as Data Product, with a dashboard, object detail view, and wave planner. Source: `requirements/requirement-document.txt`. |
| **Request type** | New Project (greenfield) |
| **Scope** | System-wide — a new standalone application |
| **Complexity** | Moderate. The data model is small and fully specified; the analytical model and three-view UI carry the complexity. |
| **Project nature** | Demo / Proof of Concept for a customer presentation. Not a production workload. |
| **Primary success criterion** | The tool must be credible and legible in front of an Acme audience: every classification must be explainable, and the visuals must be on-brand and readable. |

### 1.1 Why this is a PoC and what that implies

The application will be run locally on a presenter's laptop for a customer demo. It has no multi-user access, no persistence beyond files, no authentication, and no network exposure beyond localhost. Security and resiliency extensions were explicitly opted out (see §7). This shapes the non-functional requirements substantially: startup simplicity, offline robustness, and visual polish matter far more than scalability or fault tolerance.

---

## 2. Functional Requirements

### 2.1 Data Ingestion

| ID | Requirement | Priority |
|---|---|---|
| FR-1.1 | The system shall load six datasets from JSON files: BW object inventory, usage logs, business criticality matrix, dependency map, data volume metrics, and complexity scores. | Must |
| FR-1.2 | The system shall ship with the simulated Acme dataset pre-loaded: 22 objects across 12 solution areas (plus one multi-area custom table), exactly as specified in sections 3.1–3.6 of the source requirement document. | Must |
| FR-1.3 | The system shall allow a user to upload a replacement CSV or JSON file for any of the six datasets at runtime through the UI, and recompute all classifications against the uploaded data. | Must |
| FR-1.4 | The system shall validate uploaded data against the expected schema and report clear, human-readable errors without crashing when validation fails. | Must |
| FR-1.5 | The system shall allow a user to revert to the bundled Acme demo dataset at any time. | Should |

**Decision reference**: Q11 = B (bundled JSON plus live upload).

**Note on FR-1.2**: The source document states "22 objects across 13 solution areas". The data itself contains 22 objects, 12 entries in the criticality matrix, and 12 solution-area nodes in the dependency graph. The 13th area arises from `ZMD1`, whose solution area is recorded as `"Production/Inventory"` — a composite of two existing areas rather than a distinct thirteenth area. The system will treat this as 12 solution areas plus one cross-area object.

### 2.2 Scoring Engine — Two-Axis Model

The classification model computes two independent scores per object rather than a single composite score.

| ID | Requirement | Priority |
|---|---|---|
| FR-2.1 | The system shall compute a **Business Value** score (0–100) per object from usage frequency, distinct users, business criticality, outgoing dependencies, and incoming dependencies. | Must |
| FR-2.2 | The system shall compute a **Technical Effort** score (0–100) per object from technical complexity and data volume. | Must |
| FR-2.3 | The system shall normalise every input dimension to 0–100 using **fixed absolute bands** with documented business thresholds, not dataset-relative scaling, so that scores are stable and independently explainable. | Must |
| FR-2.4 | The system shall preserve the weight ratios of the source document when renormalising each axis (see §2.2.1). | Must |
| FR-2.5 | The system shall expose the derivation of every score in the UI, so any classification can be traced to its inputs. | Must |

**Decision reference**: Q1 = D (two-axis model), Q3 = B (fixed absolute bands), CQ3 = A (faithful renormalisation).

#### 2.2.1 Axis weights

The source document's seven weights sum to 100% across a single score. Splitting them across two axes requires renormalising within each axis, preserving the original ratios.

**Business Value axis** (source weights totalling 85%):

| Dimension | Source weight | Renormalised | Data source |
|---|---|---|---|
| Usage Frequency | 25% | 29.41% | Usage Logs (§3.2) |
| Distinct Users | 15% | 17.65% | Usage Logs (§3.2) |
| Business Criticality | 20% | 23.53% | Criticality Matrix (§3.3) |
| Outgoing Dependencies | 15% | 17.65% | Dependency Map (§3.4) |
| Incoming Dependencies | 10% | 11.76% | Dependency Map (§3.4) |

**Technical Effort axis** (source weights totalling 15%):

| Dimension | Source weight | Renormalised | Data source |
|---|---|---|---|
| Technical Complexity | 10% | 66.67% | Complexity Scores (§3.6) |
| Data Volume | 5% | 33.33% | Data Volume Metrics (§3.5) |

Each of these two dimensions is itself a composite. Technical Complexity draws on `hana_cv_count`, `transformation_count`, `custom_logic_present`, and `interface_count`. Data Volume draws on `record_count`, `storage_gb`, and `load_frequency`. The Effort axis therefore rests on seven underlying attributes despite having only two top-level weights.

#### 2.2.2 Deviation from the source document, and why

The source document specifies a single weighted score with all seven dimensions summed, banded 0–33 / 34–67 / 68–100. That formula has a directional defect: Technical Complexity and Data Volume contribute *positively*, so an object that is large and complex but unused is pushed *towards* "Rebuild as Data Product" and *away* from "Decommission" — contradicting the document's own definition of Decommission as "zero or near-zero usage; no active business owner; no strategic value".

The two-axis model resolves this by separating *worth keeping* from *cost to move*. Complexity and volume no longer inflate business value; they determine treatment only once an object has already proven its value.

### 2.3 Classification

| ID | Requirement | Priority |
|---|---|---|
| FR-3.1 | The system shall classify each object into one of three categories — **Decommission**, **Replicate As-Is**, or **Rebuild as Data Product** — by position on the Value/Effort matrix. | Must |
| FR-3.2 | The system shall apply the value-first quadrant mapping defined in §2.3.1. | Must |
| FR-3.3 | The system shall expose the **Value threshold** (default 33) and the **Effort threshold** (default 67) as adjustable controls in the UI, recomputing all classifications live. | Must |
| FR-3.4 | The system shall provide a reset-to-defaults control for all adjustable thresholds. | Should |
| FR-3.5 | The system shall generate a human-readable rationale for each classification, naming the dominant contributing factors. | Must |

**Decision reference**: CQ1 = A (value-first mapping), CQ2 = A (Value threshold 33, Effort threshold 67, both adjustable), Q2 = B (configurable with documented defaults).

#### 2.3.1 Quadrant mapping

| | Effort < 67 | Effort ≥ 67 |
|---|---|---|
| **Value ≥ 33** | Replicate As-Is | Rebuild as Data Product |
| **Value < 33** | Decommission | Decommission |

Low business value means decommission regardless of technical effort. Among objects worth keeping, effort decides whether to lift as-is or rebuild as a data product.

### 2.4 Dependency Analysis

| ID | Requirement | Priority |
|---|---|---|
| FR-4.1 | The system shall build a directed graph from the dependency map, including solution areas, external systems, source systems, shared objects, and constraint nodes. | Must |
| FR-4.2 | The system shall count all dependency edges equally, regardless of edge type (`logical`, `operational`, `constraint`). | Must |
| FR-4.3 | The system shall expand the wildcard edge `ALL → DMK` into an explicit outgoing edge for every solution area. | Must |
| FR-4.4 | The system shall derive each object's dependency counts from its solution area, since the dependency map is defined at area level. | Must |
| FR-4.5 | For objects spanning multiple solution areas, the system shall use the **average** of the constituent areas' criticality and dependency counts. | Must |
| FR-4.6 | The system shall render dependencies both as a solution-area × solution-area **matrix heatmap** and as an interactive **node-link network graph**. | Must |

**Decision reference**: Q5 = A (all edges equal, `ALL` expanded), Q4 = B (inherit with averaging).

**Consequence of FR-4.3 (documented for transparency)**: Because the `ALL → DMK` edge applies uniformly to all 12 solution areas, it shifts every object's outgoing dependency count by exactly one. It therefore adds no discriminating signal between objects — it is a constant offset. This was an explicit choice (Q5 = A) and is implemented as specified; it is recorded here so the effect is not mistaken for a defect.

**Consequence of FR-4.5**: `ZMD1` is the only such object. Its criticality becomes the average of Production (85) and Inventory Management (80) = **82.5**, and its dependency counts likewise average the two areas. Note that `ZMD1` *also* appears as a node in its own right in the dependency graph with two incoming edges (from `PR` and `IN`). Those edges are shown in the dependency visualisations, but per Q4 = B its *scoring* uses the inherited area averages rather than its own node degree.

### 2.5 Wave Planner

| ID | Requirement | Priority |
|---|---|---|
| FR-5.1 | The system shall assign objects to migration waves led by the `migration_priority` field (1–5) from the criticality matrix. | Must |
| FR-5.2 | The system shall validate wave assignments against the dependency graph and flag any dependency violation — where an object is scheduled in an earlier wave than something it depends on — as an explicit risk. | Must |
| FR-5.3 | The system shall allow the number of waves and the duration of each wave to be configured, defaulting to **5 waves of 3 months**. | Must |
| FR-5.4 | The system shall allow the project start date to be configured. | Must |
| FR-5.5 | The system shall render waves as a Gantt-style timeline. | Must |
| FR-5.6 | The system shall display the DMK constraint ("limited changes before 2028") as a visual marker on the timeline. | Must |
| FR-5.7 | The system shall add a DMK risk contribution to the risk score of any wave scheduled to complete before 2028. | Must |
| FR-5.8 | The system shall compute a per-wave risk score from average technical complexity, count of cross-wave dependencies, and downtime tolerance (lower `downtime_tolerance_hours` increasing risk). | Must |
| FR-5.9 | The system shall band wave risk scores into Low / Medium / High for at-a-glance reading. | Should |

**Decision reference**: Q6 = B (priority-led with dependency validation), Q7 = C (configurable, 5 × 3 months default), Q8 = B (marker plus risk flag), Q9 = B (complexity + dependencies + downtime tolerance).

### 2.6 User Interface

#### 2.6.1 Dashboard view

| ID | Requirement | Priority |
|---|---|---|
| FR-6.1 | An executive KPI strip shall display headline landscape figures: total objects, total storage, percentage recommended for decommission, and estimated storage reclaimed. | Must |
| FR-6.2 | A donut chart shall show object counts by classification. | Must |
| FR-6.3 | A bar chart shall show the top 10 objects by Business Value score. | Must |
| FR-6.4 | A Value/Effort scatter plot shall position all objects on the two axes with quadrant boundaries drawn, coloured by classification. | Must |
| FR-6.5 | A table shall list decommission candidates with their rationale. | Must |
| FR-6.6 | A dependency heatmap shall show inter-area dependencies. | Must |

**Decision reference**: Q22 = D (executive KPI strip included), Q16 = B (matrix plus network graph).

**Note on FR-6.3**: The source document specifies "top 10 objects by raw score". Since the two-axis model has no single raw score, this is interpreted as top 10 by Business Value, which is the score that determines whether an object is retained.

**Note on FR-6.4**: This chart is not in the source document. It is added because the two-axis model makes the quadrant view the most direct visual expression of the classification logic, and it is the clearest way to justify decisions to an audience.

#### 2.6.2 Object detail view

| ID | Requirement | Priority |
|---|---|---|
| FR-7.1 | The view shall display object metadata: ID, type, solution area, and description. | Must |
| FR-7.2 | The view shall display the assigned classification with both axis scores. | Must |
| FR-7.3 | The view shall display usage metrics: last run date, monthly executions, distinct users, and business owner. | Must |
| FR-7.4 | The view shall display incoming and outgoing dependencies. | Must |
| FR-7.5 | The view shall display a full score breakdown showing each dimension's raw value, normalised score, weight, and weighted contribution. | Must |
| FR-7.6 | The view shall display a narrative rationale for the classification decision. | Must |

#### 2.6.3 Wave planner view

| ID | Requirement | Priority |
|---|---|---|
| FR-8.1 | The view shall display recommended wave assignments. | Must |
| FR-8.2 | The view shall display a Gantt timeline with the DMK constraint marked. | Must |
| FR-8.3 | The view shall display per-wave risk assessment with contributing factors. | Must |
| FR-8.4 | The view shall list any dependency violations detected in the current wave plan. | Must |

#### 2.6.4 What-if comparison

| ID | Requirement | Priority |
|---|---|---|
| FR-9.1 | The system shall allow the current scoring configuration (thresholds and any adjustable weights) to be saved as a named scenario. | Must |
| FR-9.2 | The system shall allow two saved scenarios to be compared side by side, showing which objects change classification between them. | Must |

**Decision reference**: Q22 = D (what-if comparison included).

### 2.6.5 Source Data view (post-approval addition, 2026-08-19)

| ID | Requirement | Priority |
|---|---|---|
| FR-11.1 | The system shall provide a view that displays all six raw source datasets exactly as loaded (bundled or uploaded), independent of scoring configuration. | Must |
| FR-11.2 | The view shall let the user select which dataset to display; the Dependency Map dataset shall present its nodes and edges as separate tables. | Must |
| FR-11.3 | The view shall indicate whether the displayed dataset is the bundled demo data or a user-uploaded replacement. | Should |
| FR-11.4 | The view shall provide a per-table "Download as CSV" button for the currently displayed table. | Should |

**Decision reference**: source-data-view-questions.md — Q1=A (all six datasets), Q2=A (new sidebar nav entry), Q3=A (plain read-only table per dataset), Q4=A (no search/filter), Q5=B (per-dataset CSV download).

**Rationale**: requested directly by the user as a follow-up enhancement after Build and Test. Treated as a small, well-scoped addition to the already-approved `presentation-app` unit — no new component boundary, no scoring logic, no change to `AssessmentResult`. Read-only and stateless, so it carries no risk to the existing NFR-8.1 engine/presentation separation.

### 2.6.6 Interface presentation and navigation (post-approval refresh, 2026-08-19)

| ID | Requirement | Priority |
|---|---|---|
| FR-12.1 | Native Streamlit widget accents (selection indicators, slider handles and tracks, focus rings) shall use the application accent colour, not the framework default. | Must |
| FR-12.2 | The sidebar navigation shall present as a menu: one full-width row per view, with a hover state and a visually distinct selected row. | Must |
| FR-12.3 | The sidebar shall separate navigation, global scoring controls, and data sources into visually distinct labelled blocks. | Should |
| FR-12.4 | Every view shall open with a consistent page header comprising the view name and a one-line description of the view's purpose. | Should |
| FR-12.5 | Metrics, tables, and charts shall render as bordered card surfaces distinguishable from the page background. | Should |
| FR-12.6 | Section titles shall be rendered by the application uniformly, whether the section contains a chart, a table, or text. No chart shall carry its own internal title. | Should |
| FR-12.7 | The Dashboard export controls shall be reachable without scrolling past the analytical content. | Should |
| FR-12.8 | Chart interiors, gridlines, and axis text shall use the application palette so charts read as part of the app. Data colours remain governed by NFR-4.4. | Should |

**Decision reference**: frontend-design-refresh-questions.md — Q1 = A (native `[theme]` block), Q2 = A (styled radio menu), Q3 = B (chrome polish plus layout refinement), Q4 = A (lighter background, bordered cards), Q5 = A (navy headings, accent reserved for interaction), Q6 = A (single scroll, exports moved up), Q7 = A (sidebar blocks), Q8 = A (palette hygiene), Q9 = A (chart styling aligned), Q10 = A (post-approval implementation).

**Rationale**: requested directly by the user after Build and Test. FR-12.1 addresses a defect rather than a preference — with no `[theme]` block in `.streamlit/config.toml`, Streamlit applied its built-in `#ff4b4b` primary to every native widget accent, which is what made the navigation look wrong against the blue palette. Three earlier restyle rounds failed to fix it because they only changed the CSS injected by `theme.py`, which cannot reach native widget accents. No component boundary, no scoring logic, and no change to `AssessmentResult` is involved.

### 2.7 Outputs

| ID | Requirement | Priority |
|---|---|---|
| FR-10.1 | The system shall provide an on-demand download of a classification report as CSV, reflecting the currently active configuration. | Must |
| FR-10.2 | The system shall provide an on-demand download of the wave recommendation as JSON, reflecting the currently active configuration. | Must |
| FR-10.3 | Exported files shall include the configuration values used to produce them, so any export is reproducible. | Should |

**Decision reference**: Q12 = B (export on demand).

---

## 3. Non-Functional Requirements

### 3.1 Technology stack

| ID | Requirement |
|---|---|
| NFR-1.1 | The application shall be implemented in Python using Streamlit for the UI, Pandas for data manipulation, NetworkX for dependency graph analysis, and Plotly for visualisation. |
| NFR-1.2 | Dependency versions shall be pinned explicitly to guarantee reproducible installs. |
| NFR-1.3 | The application shall run on the Python version available on the presenter's machine without requiring an additional Python installation (see §5.1). |

**Decision reference**: Q10 = A.

### 3.2 Portability and execution

| ID | Requirement |
|---|---|
| NFR-2.1 | The application shall run on both Windows and Linux. |
| NFR-2.2 | A single script (`run.bat` on Windows, `run.sh` on Linux/macOS) shall create a virtual environment, install pinned dependencies, and launch the application. |
| NFR-2.3 | Python shall be the only prerequisite. No Node.js, Docker, or database installation shall be required. |
| NFR-2.4 | The README shall document setup and execution for both platforms, including a troubleshooting section. |
| NFR-2.5 | Re-running the launch script on an already-provisioned environment shall skip reinstallation and start immediately. |

**Decision reference**: Q21 = A.

### 3.3 Offline capability

| ID | Requirement |
|---|---|
| NFR-3.1 | Once dependencies are installed, the application shall be fully functional without internet access. |
| NFR-3.2 | The web font shall be loaded with a complete system-font fallback stack, so that loss of network access degrades typography gracefully without breaking layout or breaking brand colours. |

**Rationale for NFR-3.2**: Q15 = B selected a CDN-hosted web font. Because the application is intended for a customer demo where venue connectivity cannot be assumed, the font is specified with a fallback chain (Segoe UI on Windows, system sans-serif on Linux) rather than as a hard dependency. This preserves the chosen typography when online and guarantees a correct render when offline.

### 3.4 Visual design and accessibility

| ID | Requirement |
|---|---|
| NFR-4.1 | **Superseded — see NFR-4.1a.** Original: the application shall use a light theme: `#f2f7f1` application background, `#ffffff` cards, `#02462f` dark-green header and sidebar with white text, `#0d6a4b` for headings and emphasis, `#82ce71` restricted to chart accents and highlights, `#f6eeee` as a warm neutral for decommission and warning callouts. |
| NFR-4.1a | The application shall use a light theme built on the chrome palette recorded in §3.4.2: `#f4f6fa` application background, `#ffffff` cards with a `#d0d7e6` border, `#eef4ff` sidebar, `#001d6c` for headings and body text, `#0050e6` reserved exclusively for interactive elements, `#f9ecd9` as a warm neutral for guard-rule and warning callouts. |
| NFR-4.2 | All text and background colour combinations shall meet WCAG 2.1 AA contrast (4.5:1 for normal text, 3:1 for large text). |
| NFR-4.3 | `#82ce71` shall never be used for text on white or light backgrounds. |
| NFR-4.4 | Classification categories shall be colour-coded as: Rebuild as Data Product `#02462f`, Replicate As-Is `#82ce71`, Decommission a muted terracotta (`#9c4f1f`, fixed in Unit 2 Functional Design). |
| NFR-4.5 | Classification shall never be conveyed by colour alone; every colour-coded element shall carry a text label or icon. |
| NFR-4.6 | Charts shall have accessible labels, legends, and hover text. |
| NFR-4.7 | A single colour shall carry a single meaning. No hex value shall be used for two roles whose permitted uses overlap, and the interactive accent shall not double as a heading or body-text colour. |

**Decision reference**: Q13 = A (light theme), Q14 = A (palette-derived classification colours), Q15 = B (web font with fallback per NFR-3.2). NFR-4.1a and NFR-4.7 from frontend-design-refresh-questions.md Q4 = A, Q5 = A, Q8 = A.

**Documentation-drift correction, 2026-08-19**: NFR-4.1 and the original §3.4.1 table below still described the **first** green palette (`#f2f7f1`, `#02462f`, `#0d6a4b`) long after three restyle rounds had replaced it. Those rounds updated `business-rules.md` BR-P1 but never this document, so the two disagreed for four iterations. NFR-4.1 is now explicitly marked superseded rather than silently edited, and the live palette is stated in NFR-4.1a with its own verified table in §3.4.2. NFR-4.2 to NFR-4.6 were always palette-independent and are unchanged.

#### 3.4.1 Verified contrast ratios — original green palette (historical)

Retained for traceability. **These colours are no longer in the application.** Measured against WCAG 2.1 AA.

**Figures corrected 2026-08-18** during Unit 2 Functional Design, when the ratios were computed programmatically for the first time (checker validated against five known WCAG anchor values: black-on-white 21:1, identical-colour 1:1, `#767676`-on-white 4.54:1, `#595959`-on-white 7.00:1, red-on-white 3.998:1 — all matched exactly). The original figures in this table were hand-estimated and were off by up to 0.5. **Every verdict was unchanged**; two combinations proved better than first recorded.

| Foreground | Background | Ratio | Verdict |
|---|---|---|---|
| `#02462f` | `#f2f7f1` | 10.08:1 | Pass (AAA) |
| `#02462f` | `#ffffff` | 10.94:1 | Pass (AAA) |
| `#ffffff` | `#02462f` | 10.94:1 | Pass (AAA) |
| `#0d6a4b` | `#f2f7f1` | 6.08:1 | Pass (AA) — better than the 5.8 first recorded |
| `#0d6a4b` | `#ffffff` | 6.60:1 | Pass (AA) — better than the 6.2 first recorded |
| `#82ce71` | `#02462f` | 5.74:1 | Pass (AA) — accent on dark green |
| `#82ce71` | `#ffffff` | 1.91:1 | **Fail** — prohibited for text (NFR-4.3) |
| `#ffffff` | `#82ce71` | 1.91:1 | **Fail** — prohibited for text (NFR-4.3) |
| `#9c4f1f` | `#f2f7f1` | 5.45:1 | Pass (AA) — Decommission colour, chosen in Unit 2 Functional Design |
| `#9c4f1f` | `#ffffff` | 5.91:1 | Pass (AA) |
| `#9c4f1f` | `#f6eeee` | 5.18:1 | Pass (AA) — on the warm neutral callout background |
| `#ffffff` | `#9c4f1f` | 5.91:1 | Pass (AA) — white text on the Decommission colour |

#### 3.4.2 Verified contrast ratios — live palette

Computed 2026-08-19 with the same checker, re-validated against all five WCAG anchors before use. The full role table lives in `business-rules.md` BR-P1.7a; this records the AA verdicts that NFR-4.2 depends on.

| Foreground | Background | Ratio | Verdict |
|---|---|---|---|
| `#001d6c` ink | `#f4f6fa` app background | 13.94:1 | Pass (AAA) |
| `#001d6c` ink | `#ffffff` card | 15.08:1 | Pass (AAA) |
| `#001d6c` ink | `#eef4ff` sidebar | 13.66:1 | Pass (AAA) |
| `#001d6c` ink | `#dce7ff` sidebar hover | 12.15:1 | Pass (AAA) |
| `#4c5a72` ink muted | `#ffffff` card | 6.97:1 | Pass (AA) |
| `#4c5a72` ink muted | `#f4f6fa` app background | 6.44:1 | Pass (AA) |
| `#0050e6` accent | `#ffffff` card | 6.38:1 | Pass (AA) |
| `#0050e6` accent | `#f4f6fa` app background | 5.90:1 | Pass (AA) |
| `#0050e6` accent | `#eef4ff` sidebar | 5.78:1 | Pass (AA) |
| `#ffffff` | `#0050e6` accent fill (selected menu row) | 6.38:1 | Pass (AA) |
| `#02462f` Rebuild | `#f4f6fa` app background | 10.11:1 | Pass (AAA) |
| `#02462f` Rebuild | `#82ce71` Replicate fill | 5.74:1 | Pass (AA) |
| `#9c4f1f` Decommission | `#f4f6fa` app background | 5.46:1 | Pass (AA) |
| `#9c4f1f` Decommission | `#f9ecd9` warm neutral | 5.08:1 | Pass (AA) — guard badge |
| `#ffffff` | `#9c4f1f` Decommission fill | 5.91:1 | Pass (AA) |
| `#82ce71` Replicate | `#ffffff` card | 1.91:1 | **Fail** — prohibited for text (NFR-4.3) |

`#82ce71` remains valid as a chart fill, a border, or a highlight block, and as text only on the dark green `#02462f`.

### 3.5 Performance

| ID | Requirement |
|---|---|
| NFR-5.1 | Full recomputation of all scores and classifications for the 22-object dataset shall complete fast enough to feel instantaneous when a threshold slider is moved (target under 500 ms). |
| NFR-5.2 | Application startup to first rendered view shall complete within 10 seconds on a typical laptop. |
| NFR-5.3 | The scoring engine shall remain responsive for datasets up to approximately 1,000 objects, to allow a customer's real extract to be loaded during a demo. |

### 3.6 Usability

| ID | Requirement |
|---|---|
| NFR-6.1 | Navigation between the dashboard, object detail, dependency, and wave planner views shall be available at all times from a persistent sidebar. |
| NFR-6.2 | All adjustable parameters shall display their current value and their default. |
| NFR-6.3 | Every classification shall be explainable from the UI without reference to source code or documentation. |
| NFR-6.4 | The application shall degrade gracefully on malformed input, showing a clear message rather than a stack trace. |

### 3.7 Quality and testing

| ID | Requirement |
|---|---|
| NFR-7.1 | The scoring engine, classification logic, normalisation bands, dependency analysis, and wave planner shall have unit test coverage. |
| NFR-7.2 | Tests shall assert the documented reference classification for the bundled Acme dataset, so that regressions in the analytical model are caught. |
| NFR-7.3 | Each UI view shall have a smoke test verifying it renders without error. |
| NFR-7.4 | Tests shall be runnable with a single command on both Windows and Linux. |

**Decision reference**: Q17 = C (engine unit tests plus UI smoke tests).

### 3.8 Maintainability

| ID | Requirement |
|---|---|
| NFR-8.1 | Scoring logic shall be separated from presentation logic, with no scoring calculations embedded in UI modules. |
| NFR-8.2 | All weights, thresholds, normalisation bands, and colour values shall be defined in a single configuration location, not scattered as literals. |
| NFR-8.3 | Public functions shall carry type hints. |
| NFR-8.4 | Code shall be self-explanatory rather than commented. Comments shall be written only where genuinely critical (a non-obvious constraint or a deliberate deviation) and kept to a single brief line. Design rationale belongs in `aidlc-docs/`, not in source files. |

### 3.9 Explicitly out of scope

Derived from the PoC nature of the project and the extension opt-outs in §7:

- Authentication, authorisation, and user management
- Network exposure beyond localhost; no public deployment
- Encryption at rest or in transit — ~~as originally written~~ **partially superseded 2026-08-19 (§10)**: outbound OData calls are TLS-verified and verification cannot be disabled (NFR-9.4). Encryption at rest remains out of scope; no credentials are written to disk (NFR-9.1).
- Audit logging, monitoring, alerting, or observability tooling
- High availability, failover, backup, or disaster recovery
- ~~Live connection to a real SAP BW system — all data is file-based and simulated~~ — **superseded 2026-08-19 by §10**. Live SAP OData connectivity is now in scope, read-only, with demo mode retained as the default.
- Write-back of any kind to SAP systems — **still out of scope and now explicit**: NFR-9.6 permits HTTP GET only.
- Property-based testing

---

## 3.10 Resolved Open Decisions

Both decisions flagged at the approval gate were resolved by user approval on 2026-08-18, adopting the recommendations as written.

| Decision | Resolution |
|---|---|
| Guard rules (§4.4) | **Adopted.** Dormancy ceiling and activity floor both implemented — see FR-3.6 and FR-3.7. Supersedes clarification answer CQ4 = A, which predated the numerical evidence. |
| Python version (§5.1) | **Adopted.** Target Python 3.11 or newer; run on the installed 3.14.0. No additional Python installation required. Supersedes the "Python 3.12" element of Q10 = A. |

### 3.10.1 Guard rule requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-3.6 | The system shall classify an object as **Decommission** regardless of its computed scores when it has not run for more than 180 days *and* records fewer than 5 monthly executions (**dormancy ceiling**). | Must |
| FR-3.7 | The system shall never classify an object as **Decommission** when it has run within the last 90 days *and* records at least 25 monthly executions (**activity floor**); such an object falls to Replicate As-Is or Rebuild according to its Effort score. | Must |
| FR-3.8 | The system shall badge any object whose classification was set by a guard rule, naming the rule that fired, and shall state this in the object's rationale. | Must |
| FR-3.9 | Guard rule thresholds shall be configurable alongside the other scoring parameters. | Should |

Expected effect on the bundled dataset: `IN200` moves to Decommission via the dormancy ceiling, `IM100` moves to Replicate As-Is via the activity floor, no other object is affected, and the distribution remains 5 Rebuild / 13 Replicate / 4 Decommission.

---

## 4. Validation Findings

The approved model was implemented as a throwaway script and executed against the full 22-object Acme dataset before writing this document. The model behaves well overall, but validation surfaced two defects that require a decision.

### 4.1 Overall result — healthy

| Classification | Count |
|---|---|
| Rebuild as Data Product | 5 |
| Replicate As-Is | 13 |
| Decommission | 4 |

Business Value spans 18.8 to 86.5; Technical Effort spans 16.3 to 92.0. Both axes use their range well, and the three categories are all meaningfully populated — the model will not produce a flat-looking demo.

The high-value/high-effort objects are `SC100` (S&OP Planning), `SC200` (Demand Planning), `SA100` (Sales Model v2.0), `PR100` (Production Variance), and `PR200` (Price/Volume/Use Variance) — an intuitively correct set of rebuild candidates.

### 4.2 Finding 1 — A dormant object is not classified for decommission

`IN200` (Catch Weight Reporting) scores **Value 35.9**, placing it just above the Value threshold of 33, so it classifies as **Replicate As-Is**.

This is wrong on the evidence. `IN200` last ran on 2025-08-04 — a full year before the dataset's reference date — with 2 monthly executions and 1 distinct user. It is the clearest decommission candidate in the landscape and the source document's own definition of Decommission describes it precisely.

**Cause**: area-level inheritance (FR-4.4, FR-4.5, from Q4 = B). Business Criticality (23.53%), outgoing dependencies (17.65%), and incoming dependencies (11.76%) together make up **52.94%** of the Business Value axis, and all three are inherited from the solution area. `IN200` and the heavily-used `IN100` receive identical values for all three. Inventory Management's criticality of 80 therefore establishes a floor of roughly 36 for any object in that area, no matter how dead it is.

### 4.3 Finding 2 — An actively used object is classified for decommission

`IM100` (CAPEX Tracking) scores **Value 31.8**, just below the threshold, so it classifies as **Decommission**.

This is also wrong, and more damaging than Finding 1. `IM100` ran on 2026-08-07, a week before the reference date, with 40 monthly executions and 10 distinct users. Recommending that a customer switch off a report that ten people use every month would undermine the tool's credibility in the room.

**Cause**: the same area-level dominance, acting in the opposite direction. Investment Management has a low criticality (55), no incoming dependencies, and only the uniform DMK outgoing edge. The area's low profile drags down an object that is demonstrably in active use.

### 4.4 Recommended mitigation

Add two symmetric guard rules that act on **object-level usage evidence**, which is the signal area inheritance dilutes:

- **Dormancy ceiling** — an object not run in over 180 days *and* with fewer than 5 monthly executions is classified **Decommission** regardless of its computed scores.
- **Activity floor** — an object run within the last 90 days *and* with at least 25 monthly executions is never classified **Decommission**; it falls to Replicate As-Is or Rebuild according to its Effort score.

This was tested against the dataset. It reclassifies exactly the two problem objects — `IN200` to Decommission, `IM100` to Replicate As-Is — touches nothing else, and leaves the overall distribution unchanged at 5 / 13 / 4. Both rules are simple to state and defensible to a customer, and each triggering object would be badged in the UI with the rule that fired.

This relates to clarification question CQ4, where the answer was **A (no override)**. That answer was given before the numerical evidence existed. Two rules are now proposed rather than one, and they are narrower and symmetric. **This requires your decision** — see the approval options below.

### 4.5 Finding 3 — One object sits on a knife edge

`FI100GC` (Main P&L Query) scores **Effort 66.3** against an Effort threshold of 67, so it classifies as **Replicate As-Is** by a margin of 0.7 points. Any small change to the effort bands flips it to Rebuild.

No action is proposed. With the Effort threshold exposed as a slider (FR-3.3) this is an asset rather than a defect: nudging one control visibly moves Acme's flagship P&L query between treatments, which makes the sensitivity of the model tangible to an audience. It is recorded here so the behaviour is understood in advance rather than discovered live.

### 4.6 Proposed addition — usage recency

The source document assigns Usage Frequency a single data source, "Usage Logs", which contains both `monthly_executions` and `last_run_date`. The validated model uses execution counts banded absolutely, multiplied by a recency factor derived from `last_run_date`: 1.0 within 90 days, 0.75 within 180, 0.5 within 365, and 0.25 beyond, measured against the latest run date in the dataset for determinism.

Recency is not explicitly called for in the source document, but for a decommissioning assessment an object with a high historical execution count that has not run for a year is materially different from one running daily. Without recency, that distinction is invisible. This is flagged as an addition rather than assumed, and can be removed on request.

---

## 5. Technology Decisions Requiring Confirmation

### 5.1 Python version

Q10 = A specified Python 3.12. The target machine has **only Python 3.14.0** installed, with no 3.12 present.

The full stack was installed and imported successfully on Python 3.14.0 during requirements validation:

| Package | Version resolved |
|---|---|
| streamlit | 1.61.1 |
| pandas | 3.0.5 |
| networkx | 3.6.1 |
| plotly | 6.9.0 |

Streamlit's documentation confirms support for Python 3.10 through 3.14 ([Streamlit sanity checks](https://docs.streamlit.io/knowledge-base/using-streamlit/sanity-checks)). *Content was rephrased for compliance with licensing restrictions.*

**Recommendation**: target **Python 3.11 or newer** and run on the installed 3.14, rather than requiring a 3.12 installation. The launch scripts will detect the available interpreter and verify it meets the minimum. This honours the "simple way to run" requirement — no additional Python install needed on either platform.

One caveat worth recording: `pandas` resolved to **3.x**, a major version with behavioural changes from the 2.x series that most existing examples assume (copy-on-write semantics and string dtype handling in particular). Pinning the resolved versions explicitly (NFR-1.2) contains this risk.

---

## 6. Traceability

Every requirement traces to either the source requirement document or a recorded decision.

| Source | Covered by |
|---|---|
| §2.1 Data Sources | FR-1.1, FR-1.2 |
| §2.2 Classification Rules Engine | FR-2.1 – FR-2.5, FR-3.1 – FR-3.5 |
| §2.2 Scoring Weights | §2.2.1 (renormalised across two axes) |
| §2.3.1 Dashboard View | FR-6.1 – FR-6.6 |
| §2.3.2 Object Detail View | FR-7.1 – FR-7.6 |
| §2.3.3 Wave Planner View | FR-8.1 – FR-8.4 |
| §3.1 – §3.6 Simulated Data | FR-1.2 |
| §4.1 Stack | NFR-1.1 – NFR-1.3 |
| §4.2 Folder Structure | Reference only; final structure set during Code Generation |
| User instruction: run on Windows and Linux, document in README | NFR-2.1 – NFR-2.5 |
| User instruction: stable/LTS technology | NFR-1.2, §5.1 |
| User instruction: brand colours with contrast checked | NFR-4.1 – NFR-4.6, §3.4.1 |
| User instruction: demo/PoC for customer | §1.1, §3.9 |

---

## 7. Extension Configuration

| Extension | Enabled | Basis |
|---|---|---|
| Security Baseline | No | Q18 = B — PoC, local-only, no sensitive data |
| Resiliency Baseline | No | Q19 = B — PoC, rapid iteration prioritised |
| Property-Based Testing | No | Q20 = C — conventional unit tests selected instead (Q17 = C) |

Per deferred rule loading, none of the three full extension rule files were loaded. The corresponding concerns are recorded as out of scope in §3.9.

---

## 8. Assumptions

| ID | Assumption |
|---|---|
| A-1 | All data is simulated. No connection to a real SAP BW system is required or attempted. |
| A-2 | The application is presented by a single operator on one machine. Concurrent multi-user use is not required. |
| A-3 | Dataset scale remains modest (tens to low hundreds of objects). |
| A-4 | The reference date for recency calculations is the latest `last_run_date` in the dataset (2026-08-14), making results deterministic and reproducible regardless of when the demo is run. |
| A-5 | `business_owner` from the usage logs is displayed as metadata but does not contribute to any score. The source document mentions "no active business owner" in the Decommission definition, but provides an owner for every object, so it carries no discriminating signal in this dataset. |
| A-6 | The `object_type` field is displayed but does not affect scoring. All 22 objects are Queries except `ZMD1` (Custom Table). |
| A-7 | `migration_priority` and `downtime_tolerance_hours` are used by the wave planner only, not by the classification model. |

---

## 9. Summary of Key Requirements

- A two-axis analytical model separates **Business Value** from **Technical Effort**, correcting a directional defect in the source document's single-score formula.
- Classification is value-first: low value means decommission; among valuable objects, effort decides replicate versus rebuild.
- All seven source dimensions are retained with their weight ratios preserved, normalised by fixed absolute bands so that every score is independently explainable.
- Thresholds are adjustable live, defaulting to the documented 33 and 67, enabling sensitivity demonstration during a customer presentation.
- Four views: dashboard with executive KPI strip, object detail with full score derivation, dependency matrix plus network graph, and a configurable wave planner with risk scoring and DMK constraint marking.
- What-if scenario comparison and on-demand CSV/JSON export.
- Streamlit, Pandas, NetworkX, and Plotly on Python 3.11+, launched by a single script on Windows or Linux with Python as the only prerequisite.
- Brand palette applied with all text combinations verified against WCAG 2.1 AA; `#82ce71` restricted to non-text use on light backgrounds.
- Two guard rules on object-level usage evidence — a dormancy ceiling and an activity floor — correcting the two misclassifications found during validation.
- Unit tests on the analytical engine, smoke tests on the UI. Minimal code comments; rationale kept in `aidlc-docs/`.

**Status**: Approved 2026-08-18. Both open decisions resolved in favour of the stated recommendations (§3.10).

---

## 10. Live SAP OData Connectivity (new feature, eighth iteration, 2026-08-19)

This section extends the approved requirements rather than replacing any part of them. Nothing in §1-§9 changes except §7 (extension configuration, restated in §10.11) and the out-of-scope list in §3.9, from which "no SAP integration" is now removed.

### 10.1 Intent analysis

| Aspect | Assessment |
|---|---|
| **User request** | Add OData connectivity so BW-ACE can run against a live SAP BW system, switchable with demo mode, with a Connection Settings page, Basic (or OAuth) authentication, and credentials supplied through environment variables. |
| **Request type** | New Feature — the first external integration in the product; every prior iteration was internal. |
| **Scope** | Multiple Components, both units. `assessment-engine` gains a connector layer and a second data ingress alongside `loader.py`; `presentation-app` gains a Connection Settings view, a mode switch, and provenance indication. |
| **Complexity** | Complex. First network I/O, first secret handling, first new runtime dependency since inception, and the first code path that cannot be exercised against a real system from this environment. |
| **Requirements depth** | Comprehensive. |
| **Primary success criterion** | In the room, it must always be unambiguous which data is on screen, and a live connection failure must never silently degrade into demo data presented as if it were the customer's own. |

### 10.2 Finding: the named services are not SAP-delivered

The source requirement names three services as though SAP ships them: `/RSOD_ADSO_SRV`, `/RSPC_API_SRV`, `/RSOD_CATALOG_SRV`. SAP's documentation and community sources were searched before this section was written and **no SAP-delivered OData service by any of those names could be found**.

What SAP does deliver is the framework, and on that point the business analyst is correct: SAP Gateway publishes OData services under `/sap/opu/odata/sap/<SERVICE_NAME>`, each exposing `$metadata` and entity-set collections, and this is a legitimate, modern, read-friendly route into BW. The documented BW pattern, however, is that such a service is **created and activated** over BW metadata or a BW query in the customer's own system — see the community-documented procedure for creating an OData service for a BW query, which ends with the new service appearing in the Gateway service catalogue.

The three names are therefore treated as **illustrative placeholder defaults**, not as endpoints that will exist in an Acme system. Hardcoding them would produce a tool that demonstrates perfectly and fails on first contact with the real landscape. FR-13.3 makes every service path configurable with those names as the shipped defaults, so the demo still shows exactly the endpoint list that was promised while remaining pointable at whatever the customer has actually activated.

**Presentation obligation (FR-15.6)**: the Connection Settings page states that the default paths are placeholders. The tool must not assert to a customer that SAP delivers services it does not deliver.

### 10.3 FR-13 — Connection and configuration

| ID | Requirement | Priority |
|---|---|---|
| FR-13.1 | The application shall support two data source modes: **Demo Data** (bundled or uploaded files, the existing behaviour) and **Live OData**. Demo Data shall be the default on every startup. | Must |
| FR-13.2 | Live OData mode shall be enterable only after a successful connection test in the current session. | Must |
| FR-13.3 | The base URL, the service root path (default `/sap/opu/odata/sap`), and the service/entity-set path for each live dataset shall be configurable through environment variables, with the defaults in §10.4. | Must |
| FR-13.4 | The Connection Settings page shall display the effective resolved URL for each configured endpoint, so a misconfiguration is visible before a fetch is attempted. | Must |
| FR-13.5 | A "Test Connection" action shall issue a `$metadata` request per configured service and report a per-endpoint outcome: reachable / authenticated / not found (404) / unauthorised (401 or 403) / TLS failure / timeout. | Must |
| FR-13.6 | Connection configuration shall be read once at process start and re-read on an explicit user action, never cached across a process restart. | Should |
| FR-13.7 | Authentication shall support HTTP Basic over TLS. The connector shall be structured so that an OAuth 2.0 client-credentials strategy can be added without reshaping the fetch or mapping layers. | Must |
| FR-13.8 | OAuth 2.0 and X.509 client-certificate authentication are **out of scope for this iteration** and shall be stated as such on the Connection Settings page rather than shown as non-functioning controls. | Must |

**Decision reference**: Q1 = A, Q2 = A, Q4 = A.

### 10.4 FR-14 — Fetch, mapping, failure and refresh

#### 10.4.1 Dataset to endpoint mapping

The five endpoints named in the request do not map one-to-one onto BW-ACE's six datasets. `criticality` is the clearest case: business criticality, migration priority, and downtime tolerance per solution area are **business judgements**, not BW metadata, and no BW service can supply them.

| BW-ACE dataset | Live source | Default path (placeholder) | Environment variable |
|---|---|---|---|
| `object_inventory` | Object catalogue | `RSOD_CATALOG_SRV/ObjectCatalog` | `BWACE_ODATA_SERVICE_INVENTORY` |
| `complexity` | ADSO metadata | `RSOD_ADSO_SRV/AdsoMetadata` | `BWACE_ODATA_SERVICE_COMPLEXITY` |
| `data_volume` | ADSO volume metrics | `RSOD_ADSO_SRV/AdsoVolume` | `BWACE_ODATA_SERVICE_VOLUME` |
| `dependencies` | Process chains | `RSPC_API_SRV/ProcessChains` | `BWACE_ODATA_SERVICE_DEPENDENCIES` |
| `usage_logs` | Query results | `RSOD_USAGE_SRV/Results` | `BWACE_ODATA_SERVICE_USAGE` |
| `criticality` | **No live source.** Always bundled or uploaded. | n/a | n/a |

| ID | Requirement | Priority |
|---|---|---|
| FR-14.1 | Live mode shall fetch the five datasets above and shall continue to use the bundled or uploaded `criticality` matrix. | Must |
| FR-14.2 | Each dataset's provenance shall be recorded and displayed as `live`, `uploaded`, or `bundled`. No dataset shall ever be presented without its provenance being discoverable. | Must |
| FR-14.3 | Live records shall be mapped onto the existing dataset schemas by an explicit, field-by-field, per-dataset mapping, and shall then pass through the **existing** validation and referential-integrity checks unchanged, surfacing in the existing validation panel. | Must |
| FR-14.4 | Collection retrieval shall honour OData V2 server-side paging (`__next`, with `$skip`/`$top` where required) and continue until the collection is exhausted. | Must |
| FR-14.5 | A configurable maximum record count per dataset (`BWACE_ODATA_MAX_RECORDS`, default 5,000) shall bound retrieval. Reaching the cap shall raise a clearly worded warning, never a silent truncation. | Must |
| FR-14.6 | A live refresh shall replace the working landscape **only** when all five live datasets have been retrieved and assembled into a valid landscape. On any failure the previously displayed landscape shall be retained unchanged and the failure reported per endpoint. | Must |
| FR-14.7 | Live data shall be fetched on entering live mode and on an explicit "Refresh from SAP" action only. It shall never be re-fetched as a side effect of a threshold change, a navigation change, or any other Streamlit rerun. | Must |
| FR-14.8 | The last successful fetch timestamp shall be recorded and displayed. | Must |
| FR-14.9 | `$metadata` shall be used for connection testing (FR-13.5) and shall not be parsed to infer field mappings. | Must |
| FR-14.10 | Every request shall carry an explicit connect and read timeout (`BWACE_ODATA_TIMEOUT_SECONDS`, default 30). A transient failure (timeout, connection reset, HTTP 5xx) shall be retried a bounded number of times with backoff; an authentication or not-found failure shall not be retried. | Must |

**Decision reference**: Q7 = A, Q8 = A, Q9 = A, Q10 = A, Q11 = A, Q12 = A.

**Note on FR-14.4/FR-14.5**: unpaged retrieval is the most dangerous failure mode available to this feature. A service returning its default page size would silently truncate the landscape, and BW-ACE would then compute a complete-looking assessment over partial data — individually plausible classifications that are collectively wrong, with nothing on screen to reveal it. Paging is a correctness requirement here, not a performance one.

**Note on FR-14.1 read together with FR-14.6**: these are not in conflict. `criticality` is excluded from the live fetch set by design, so the all-or-nothing rule in FR-14.6 applies to the five datasets live mode is expected to supply. A hybrid landscape is the intended, labelled steady state; a hybrid landscape that arose from a *failed* fetch is what FR-14.6 forbids.

**Note on FR-14.3**: reusing `loader.py`'s validators is what makes live data trustworthy on arrival — a live record missing a required field, or referencing a solution area absent from the criticality matrix, produces exactly the same error as a bad upload, in the same panel. It also preserves the existing content-fingerprint cache key, so the two-phase `compute_base` / `apply_config` caching from the approved Application Design continues to work untouched.

### 10.5 NFR-9 — Credential and transport security

| ID | Requirement |
|---|---|
| NFR-9.1 | Credentials shall be supplied only through environment variables (`BWACE_ODATA_USER`, `BWACE_ODATA_PASSWORD`), optionally loaded from a git-ignored `.env` file at startup. The application shall never write credentials to disk. |
| NFR-9.2 | Credentials shall not be stored in Streamlit session state, and shall not be rendered to the screen in any form. The Connection Settings page shall report only whether each variable is **set**, never its value. |
| NFR-9.3 | Credentials, `Authorization` headers, and cookies shall be masked in every error message, exception path, and log line. No response body or request header shall be echoed raw into the UI. |
| NFR-9.4 | TLS certificate verification shall always be enabled. A custom CA bundle may be supplied via `BWACE_ODATA_CA_BUNDLE` for private or self-signed certificate authorities. **There shall be no option to disable verification.** |
| NFR-9.5 | A TLS verification failure shall produce an error that names the cause and points explicitly at `BWACE_ODATA_CA_BUNDLE` as the remedy. |
| NFR-9.6 | Only read operations (HTTP GET) shall be issued against the customer's system. The connector shall contain no code path that writes, and no CSRF-token handling is therefore required. |
| NFR-9.7 | The `.env` file pattern shall be present in `.gitignore` before any connector code is written. |

**Decision reference**: Q5 = A, Q6 = A.

**Accepted consequence of NFR-9.4, recorded rather than buried**: SAP on-premise Gateway hosts commonly present self-signed or private-CA certificates. With no opt-out, a demo against such a sandbox is **blocked** until someone supplies the CA file. This is the direct cost of choosing Q6 = A over Q6 = B, and it is accepted deliberately: an opt-out is the kind of switch that gets set once for a sandbox and never unset. NFR-9.5 exists to make the remedy obvious in the moment rather than a debugging exercise in front of a customer.

### 10.6 NFR-10 — Reliability and behaviour under failure

| ID | Requirement |
|---|---|
| NFR-10.1 | A slow or unresponsive SAP host shall not hang the application. Every request is bounded by FR-14.10's timeout, and the UI shall show progress during a fetch. |
| NFR-10.2 | Demo mode shall remain fully functional with no network access, no environment variables set, and no HTTP client reachable. Offline behaviour (NFR-3.1, NFR-3.2) is unchanged by this feature. |
| NFR-10.3 | Every failure shall be attributable to a specific endpoint and a specific cause. A single "connection failed" message for five endpoints is not acceptable. |
| NFR-10.4 | Mode and provenance shall never be ambiguous on screen. The current mode indicator shall be visible on every view. |

### 10.7 NFR-11 — Testability and maintainability

| ID | Requirement |
|---|---|
| NFR-11.1 | The HTTP transport shall be injectable so that every connector and mapper branch is testable without a network. |
| NFR-11.2 | Recorded-fixture tests shall cover, at minimum: a normal single-page response, a `__next` paged response spanning at least two pages, the record cap being hit, HTTP 401, HTTP 404, HTTP 500 followed by a successful retry, a timeout, a malformed JSON body, and a payload missing a required field. |
| NFR-11.3 | The existing test suite shall remain entirely offline and shall not slow measurably. No test shall attempt a real network connection. |
| NFR-11.4 | Documentation shall state plainly that connector logic is verified by fixtures and that end-to-end live connectivity is unverified until run against a customer system. Fixture coverage shall not be described as live-verified. |
| NFR-11.5 | The new HTTP client dependency shall be pinned to an exact version, consistent with the existing four pinned dependencies. |

**Decision reference**: Q3 = A (`httpx`, pinned, synchronous client — per-operation timeouts and explicit TLS context control, both of which FR-14.10 and NFR-9.4 depend on), Q14 = A.

### 10.8 FR-15 — Frontend presentation

| ID | Requirement | Priority |
|---|---|---|
| FR-15.1 | A seventh navigation entry, **Connection Settings**, shall be added to the sidebar. | Must |
| FR-15.2 | The Connection Settings page shall contain: the mode selector, environment variable presence indicators, resolved endpoint URLs, the Test Connection action with per-endpoint results, the Refresh from SAP action, the last successful fetch timestamp, and the per-dataset provenance table. | Must |
| FR-15.3 | A persistent mode indicator shall appear in the page header of every view, reading `Demo Data` or `Live: <host>` with the last fetch time. | Must |
| FR-15.4 | The mode indicator shall use the existing palette roles and shall satisfy NFR-4.2 contrast. No new hex literal shall be introduced. | Must |
| FR-15.5 | Live mode with a stale or failed last fetch shall be visually distinct from live mode with fresh data. | Must |
| FR-15.6 | The page shall state that the default service paths are placeholders to be pointed at the customer's activated services, and shall state that OAuth and client certificates are not implemented in this iteration. | Must |
| FR-15.7 | The existing per-dataset upload controls and "Revert to Demo Data" behaviour shall continue to work unchanged in demo mode. | Must |

**Decision reference**: Q13 = A.

### 10.9 Contradiction and consistency analysis

Performed on the answer set before this section was written, per the mandatory analysis step. All fifteen substantive answers are A. Three pairings were checked specifically because an inconsistent combination is easy to select by accident:

| Pairing | Risk | Verdict |
|---|---|---|
| Q1 (explicit mode, no silent fallback) vs Q11 (all-or-nothing, retain previous data) | Could have required both "never swap data silently" and "substitute bundled data on failure" | **Consistent.** Both point the same way: on failure the app stays in live mode, keeps what it had, and reports the error. Neither substitutes data silently. |
| Q7 (hybrid provenance — `criticality` stays bundled) vs Q11 (all-or-nothing replacement) | Reads as a direct contradiction: a permanent hybrid landscape versus a refusal to accept partial data | **Consistent once scoped.** Q7 fixes *which* datasets live mode fetches at all (five of six, by design). Q11 governs what happens when a dataset that *should* have arrived did not. Written explicitly into the FR-14.1 / FR-14.6 note so the distinction survives into design. |
| Q4 (Basic auth only) vs Q16 (security extension off) | Could have combined a reduced auth scope with reduced security enforcement | **Consistent, and mitigated.** NFR-9.x makes the security behaviours binding requirements independent of extension status; see §10.11. |

No clarification round was raised. One genuine ambiguity in the *instruction* rather than the answers is recorded in §10.11.

### 10.10 Out of scope for this iteration

Removed from §3.9: "no SAP integration". Everything below remains out of scope and is stated here so the boundary is explicit:

- OAuth 2.0 and X.509 client-certificate authentication (FR-13.8)
- Gateway service-catalogue discovery (Q2 option C)
- `$metadata` / EDMX parsing for schema inference or a schema-diff report (Q9 option B)
- A user-editable mapping file (Q8 option B)
- Writing anything back to SAP — read-only by NFR-9.6
- Automatic or background refresh, and any refresh TTL (Q12 options B and C)
- A live source for `criticality`
- Credential entry through the UI (Q5 option B) and `secrets.toml` support (Q5 option C)
- Proxy configuration, SAP Cloud Connector, and SNC
- End-to-end verification against a real SAP system — impossible from this environment (NFR-11.4)

### 10.11 Extension configuration — unchanged, with the reasoning stated

The three extension opt-ins were deliberately re-asked this round, because the reasoning behind the inception "No" answers (a demo/PoC with no network exposure) does not survive the arrival of credential handling and authenticated outbound calls.

The instruction was to use the recommended answers. **Q16-Q18 carried no unambiguous recommendation** — their option text recommends A for production-grade applications and B for PoCs, and BW-ACE is a PoC that has just grown a credentialed integration. Rather than record a guess as a user decision, the inception answers were **carried forward unchanged** and flagged:

| Extension | Enabled | Basis |
|---|---|---|
| Security Baseline | No | Carried forward from inception. Not re-decided. |
| Resiliency Baseline | No | Carried forward from inception. Not re-decided. |
| Property-Based Testing | No | Carried forward from inception. Not re-decided. |

No extension rule files were loaded. The practical exposure is limited, deliberately:

- The security behaviours are binding as **NFR-9.1 to NFR-9.7**, not as extension rules. Extension status affects whether there is a formal per-stage compliance audit; it does not license storing credentials in session state, disabling TLS verification, or leaking secrets into error text.
- The resiliency behaviours that matter here — timeouts, bounded retries, explicit failure states, no partial replacement — are functional requirements FR-14.6, FR-14.7 and FR-14.10 plus NFR-10.x.

**Open for the user**: enabling the Security Baseline (Q16 = A) is cheap now and expensive after Code Generation. Property-Based Testing at "Partial" (Q18 = B) would apply naturally to the OData response mapper, which is a pure parse-and-transform function and close to an ideal PBT target.

### 10.12 Assumptions

| ID | Assumption |
|---|---|
| A-8 | The customer's BW system exposes, or will expose, activated SAP Gateway OData services carrying the metadata BW-ACE needs. The named default paths are placeholders (§10.2). |
| A-9 | Those services return OData V2 JSON (`$format=json` or an `Accept: application/json` header honoured). OData V4 payload shapes are not handled in this iteration. |
| A-10 | The usage service can supply per-object aggregates equivalent to `last_run_date`, `monthly_executions`, `distinct_users`, and `business_owner`, or a shape that reduces to them. `business_owner` in particular may have no BW source and may need to arrive with the criticality matrix. |
| A-11 | A live landscape stays within the ~1,000-object envelope of NFR-5.3. The FR-14.5 cap of 5,000 records per dataset sits above that with headroom. |
| A-12 | Basic authentication over TLS is acceptable to the customer for a read-only PoC connection. |

### 10.13 Traceability

| Requirement | Source |
|---|---|
| FR-13.1, FR-13.2 | User request ("switch between live OData mode and demo mode"), Q1 = A |
| FR-13.3, FR-13.4, FR-15.6 | §10.2 finding, Q2 = A |
| FR-13.5, FR-14.9 | User request (`$metadata`), Q9 = A |
| FR-13.7, FR-13.8 | User request ("Basic Authentication (or OAuth...)"), Q4 = A |
| FR-14.1, FR-14.2 | Six-dataset / five-endpoint gap analysis, Q7 = A |
| FR-14.3 | Existing `loader.py` validators, Q8 = A |
| FR-14.4, FR-14.5 | OData V2 paging semantics, Q10 = A |
| FR-14.6 | Q11 = A |
| FR-14.7, FR-14.8 | Q12 = A, existing rerun/caching behaviour |
| FR-14.10, NFR-10.1 | Q3 = A, Q10 = A |
| FR-15.1 to FR-15.5, FR-15.7 | User request ("reflected on frontend application", "connection settings page"), Q13 = A |
| NFR-9.1 to NFR-9.7 | User request ("secure credential storage via environment variables"), Q5 = A, Q6 = A |
| NFR-11.1 to NFR-11.5 | Q14 = A, Q3 = A, existing NFR-7.x testing requirements |

### 10.14 Summary

- Two explicit modes, **Demo Data by default**, live mode gated behind a successful connection test. No silent substitution in either direction.
- The three service names in the source requirement are **not SAP-delivered**; they ship as configurable placeholder defaults and the UI says so.
- **Five of six datasets** come from live OData. `criticality` has no BW source and stays bundled or uploaded, labelled.
- Live records are mapped field-by-field and then pushed through the **existing** validators, so live data faces the same checks as an upload and the existing fingerprint cache keeps working.
- **Paging is a correctness requirement.** An unpaged GET would silently truncate and yield a confidently wrong assessment.
- All-or-nothing replacement: a failed fetch never leaves a half-live landscape on screen.
- Credentials live in environment variables only, never in session state, never rendered, always masked. **TLS verification cannot be disabled** — with the accepted cost that a self-signed sandbox needs a CA bundle before it will connect.
- `httpx`, pinned, injectable transport. Connector logic verified by recorded fixtures; live connectivity is explicitly unverified until run against a real system.
