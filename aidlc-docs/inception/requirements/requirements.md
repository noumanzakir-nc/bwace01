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
| **Primary success criterion** | The tool must be credible and legible in front of an Arla audience: every classification must be explainable, and the visuals must be on-brand and readable. |

### 1.1 Why this is a PoC and what that implies

The application will be run locally on a presenter's laptop for a customer demo. It has no multi-user access, no persistence beyond files, no authentication, and no network exposure beyond localhost. Security and resiliency extensions were explicitly opted out (see §7). This shapes the non-functional requirements substantially: startup simplicity, offline robustness, and visual polish matter far more than scalability or fault tolerance.

---

## 2. Functional Requirements

### 2.1 Data Ingestion

| ID | Requirement | Priority |
|---|---|---|
| FR-1.1 | The system shall load six datasets from JSON files: BW object inventory, usage logs, business criticality matrix, dependency map, data volume metrics, and complexity scores. | Must |
| FR-1.2 | The system shall ship with the simulated Arla dataset pre-loaded: 22 objects across 12 solution areas (plus one multi-area custom table), exactly as specified in sections 3.1–3.6 of the source requirement document. | Must |
| FR-1.3 | The system shall allow a user to upload a replacement CSV or JSON file for any of the six datasets at runtime through the UI, and recompute all classifications against the uploaded data. | Must |
| FR-1.4 | The system shall validate uploaded data against the expected schema and report clear, human-readable errors without crashing when validation fails. | Must |
| FR-1.5 | The system shall allow a user to revert to the bundled Arla demo dataset at any time. | Should |

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
| NFR-7.2 | Tests shall assert the documented reference classification for the bundled Arla dataset, so that regressions in the analytical model are caught. |
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
- Encryption at rest or in transit
- Audit logging, monitoring, alerting, or observability tooling
- High availability, failover, backup, or disaster recovery
- Live connection to a real SAP BW system — all data is file-based and simulated
- Write-back of any kind to SAP systems
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

The approved model was implemented as a throwaway script and executed against the full 22-object Arla dataset before writing this document. The model behaves well overall, but validation surfaced two defects that require a decision.

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

No action is proposed. With the Effort threshold exposed as a slider (FR-3.3) this is an asset rather than a defect: nudging one control visibly moves Arla's flagship P&L query between treatments, which makes the sensitivity of the model tangible to an audience. It is recorded here so the behaviour is understood in advance rather than discovered live.

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
