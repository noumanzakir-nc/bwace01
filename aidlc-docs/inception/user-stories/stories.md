# User Stories — BW-ACE

**Structure**: Capability epics containing persona-phrased stories (Q2 = D)
**Granularity**: 23 stories (Q3 = B, target roughly 15–22; one over, retained rather than forcing a merge)
**Acceptance criteria format**: Given / When / Then (Q4 = A)
**Data expectations**: Concrete, including the full reference distribution (Q5 = A)
**Non-functional coverage**: Dedicated stories (Q6 = A) — Epic 8
**Personas**: See `personas.md` — P1 Migration Architect, P2 Solution/Business Owner, P3 Programme Manager

---

## Reference Dataset Expectations

Established by executing the approved model against the bundled Arla dataset during Requirements Analysis. Cited by acceptance criteria throughout.

**Expected distribution after guard rules: 5 Rebuild / 13 Replicate As-Is / 4 Decommission**

| Classification | Objects |
|---|---|
| Rebuild as Data Product | `SC100`, `SC200`, `SA100`, `PR100`, `PR200` |
| Replicate As-Is | `FI100GC`, `FI120`, `FI108GC`, `FI200`, `FI901GC`, `SA200`, `IN100`, `ZMD1`, `PC100`, `LC100`, `PO100`, `QM100`, `IM100` |
| Decommission | `IN200`, `TR100`, `TR200`, `TM100` |

**Named edge cases**

| Object | Expected | Why it matters |
|---|---|---|
| `IN200` | Decommission | Set by the **dormancy ceiling**, not by score. Its computed Value (~36) sits above the threshold because area-level inheritance floors it. |
| `IM100` | Replicate As-Is | Protected by the **activity floor**. Its computed Value (~32) sits below the threshold, but 40 monthly executions across 10 users within the last 90 days forbids Decommission. |
| `FI100GC` | Replicate As-Is | Effort ≈ 66.3 against a threshold of 67 — classified by a margin under one point. Must flip to Rebuild on a small downward threshold adjustment. |

**Note on precision**: classifications and the distribution above are binding. Individual axis scores are *indicative*, because the exact normalisation band boundaries and complexity sub-weights are finalised in Functional Design (requirements §4.6). Acceptance criteria therefore assert classifications and orderings, not exact score values, except where a margin is the point of the test.

---

# Epic 1 — Data Foundation

*Requirements: FR-1.1 to FR-1.5*

## S1.1 — Load the bundled Arla landscape

**As a** Migration Architect
**I want** the tool to open with the full simulated Arla landscape already loaded
**So that** I can begin assessing immediately without preparing data

**Requirements**: FR-1.1, FR-1.2

### Acceptance Criteria

**AC1 — All six datasets load**
- **Given** a clean installation of the application
- **When** I start it
- **Then** all six datasets are loaded: object inventory, usage logs, criticality matrix, dependency map, data volume metrics, and complexity scores
- **And** no manual data preparation step is required

**AC2 — Complete object coverage**
- **Given** the application has started
- **When** I view the landscape
- **Then** 22 objects are present
- **And** 12 solution areas are represented
- **And** `ZMD1` is present as a cross-area object with solution area `Production/Inventory`

**AC3 — Every object is scored**
- **Given** the bundled dataset is loaded
- **When** scoring completes
- **Then** all 22 objects carry a Business Value score, a Technical Effort score, and a classification
- **And** no object is left unclassified or shows a null score

---

## S1.2 — Assess my own landscape extract

**As a** Migration Architect
**I want** to upload my own object, usage, criticality, dependency, volume, or complexity data
**So that** I can run the assessment against a real landscape rather than the sample

**Requirements**: FR-1.3, FR-1.5

### Acceptance Criteria

**AC1 — Upload replaces a dataset**
- **Given** the bundled dataset is loaded
- **When** I upload a valid replacement file for any one of the six datasets, in CSV or JSON
- **Then** that dataset is replaced
- **And** all scores and classifications recompute against the new data
- **And** every view reflects the recomputed result

**AC2 — Partial replacement is supported**
- **Given** I have uploaded a replacement usage log only
- **When** scoring recomputes
- **Then** the remaining five bundled datasets are still in use
- **And** the application indicates which datasets are bundled and which are uploaded

**AC3 — Revert to the demo dataset**
- **Given** I have uploaded one or more replacement datasets
- **When** I choose to revert to the bundled demo data
- **Then** all six datasets return to their bundled state
- **And** the reference distribution of 5 Rebuild / 13 Replicate / 4 Decommission is restored

---

## S1.3 — Understand why my data was rejected

**As a** Migration Architect
**I want** a clear explanation when an upload cannot be used
**So that** I can correct my extract rather than guess at the problem

**Requirements**: FR-1.4, NFR-6.4

### Acceptance Criteria

**AC1 — Missing required field**
- **Given** I upload a usage log missing the `monthly_executions` field
- **When** validation runs
- **Then** the upload is rejected
- **And** a message names the missing field and the dataset it belongs to
- **And** the previously loaded data remains active and the application stays usable

**AC2 — Wrong data type**
- **Given** I upload a file where `distinct_users` contains a non-numeric value
- **When** validation runs
- **Then** the upload is rejected
- **And** the message identifies the offending field and the row or record where it occurred

**AC3 — No stack traces**
- **Given** any malformed input, including a file that is not valid CSV or JSON at all
- **When** validation runs
- **Then** the user sees a readable message
- **And** no Python traceback or raw exception text is displayed

**AC4 — Unreferenced object**
- **Given** I upload an object inventory containing an object with no corresponding usage log entry
- **When** validation runs
- **Then** the condition is reported as a warning naming the affected object
- **And** the application makes clear how that object is treated in scoring

---

# Epic 2 — Scoring and Classification Engine

*Requirements: FR-2.1 to FR-2.5, FR-3.1 to FR-3.9*

## S2.1 — See each object scored on business value and technical effort

**As a** Migration Architect
**I want** every object scored independently on business value and on technical effort
**So that** how much an object is worth is never confused with how hard it is to move

**Requirements**: FR-2.1, FR-2.2, FR-2.3, FR-2.4

### Acceptance Criteria

**AC1 — Two independent scores**
- **Given** the bundled dataset
- **When** scoring runs
- **Then** each object carries a Business Value score in the range 0–100 and a Technical Effort score in the range 0–100
- **And** neither score is derived from the other

**AC2 — Business Value composition**
- **Given** an object's Business Value score
- **When** I inspect its composition
- **Then** it is composed of usage frequency (29.41%), distinct users (17.65%), business criticality (23.53%), outgoing dependencies (17.65%), and incoming dependencies (11.76%)
- **And** those weights sum to 100%

**AC3 — Technical Effort composition**
- **Given** an object's Technical Effort score
- **When** I inspect its composition
- **Then** it is composed of technical complexity (66.67%) and data volume (33.33%)
- **And** complexity draws on `hana_cv_count`, `transformation_count`, `custom_logic_present`, and `interface_count`
- **And** volume draws on `record_count`, `storage_gb`, and `load_frequency`

**AC4 — Absolute normalisation, not relative**
- **Given** an object with a known set of input values
- **When** I remove unrelated objects from the dataset and rescore
- **Then** that object's scores are unchanged
- **And** scores therefore do not depend on the composition of the rest of the dataset

**AC5 — Highest and lowest are correct**
- **Given** the bundled dataset
- **When** objects are ranked by Business Value
- **Then** `SC100` ranks highest
- **And** `TR200` ranks lowest
- **When** ranked by Technical Effort
- **Then** `SC100` ranks highest
- **And** `TR200` ranks lowest

---

## S2.2 — Get a three-way classification I can act on

**As a** Migration Architect
**I want** each object placed into Decommission, Replicate As-Is, or Rebuild as Data Product
**So that** I have an actionable recommendation rather than a pair of numbers

**Requirements**: FR-3.1, FR-3.2

### Acceptance Criteria

**AC1 — Value-first mapping**
- **Given** default thresholds of Value 33 and Effort 67
- **When** an object's Value is below 33
- **Then** it is classified Decommission irrespective of its Effort score
- **When** Value is at or above 33 and Effort is below 67
- **Then** it is classified Replicate As-Is
- **When** Value is at or above 33 and Effort is at or above 67
- **Then** it is classified Rebuild as Data Product

**AC2 — Reference distribution**
- **Given** the bundled dataset and default thresholds
- **When** classification completes
- **Then** exactly 5 objects are Rebuild as Data Product, 13 are Replicate As-Is, and 4 are Decommission

**AC3 — Rebuild set is exact**
- **Given** the bundled dataset and default thresholds
- **When** classification completes
- **Then** the Rebuild set is exactly `SC100`, `SC200`, `SA100`, `PR100`, `PR200`

**AC4 — Decommission set is exact**
- **Given** the bundled dataset and default thresholds
- **When** classification completes
- **Then** the Decommission set is exactly `IN200`, `TR100`, `TR200`, `TM100`

**AC5 — No fourth category**
- **Given** any object in any dataset
- **When** it is classified
- **Then** its classification is one of exactly three values
- **And** no object is reported as unclassified

---

## S2.3 — Trust that usage evidence overrides the score

**As a** Solution / Business Owner
**I want** demonstrable usage to override the computed score in both directions
**So that** a dormant report is not kept and an actively used report is not switched off

**Requirements**: FR-3.6, FR-3.7, FR-3.8, FR-3.9

### Acceptance Criteria

**AC1 — Dormancy ceiling forces Decommission**
- **Given** an object that last ran more than 180 days ago and records fewer than 5 monthly executions
- **When** it is classified
- **Then** it is Decommission regardless of its computed Value and Effort scores

**AC2 — `IN200` is caught by the dormancy ceiling**
- **Given** the bundled dataset
- **When** `IN200` is classified
- **Then** its classification is Decommission
- **And** its computed Business Value is above the Value threshold, so the classification is attributable to the dormancy ceiling rather than to its score

**AC3 — Activity floor forbids Decommission**
- **Given** an object that last ran within the past 90 days and records at least 25 monthly executions
- **When** it is classified
- **Then** it is not Decommission
- **And** it is Replicate As-Is or Rebuild as Data Product according to its Effort score

**AC4 — `IM100` is protected by the activity floor**
- **Given** the bundled dataset
- **When** `IM100` is classified
- **Then** its classification is Replicate As-Is
- **And** its computed Business Value is below the Value threshold, so the classification is attributable to the activity floor

**AC5 — Guard rules are visible, not silent**
- **Given** an object whose classification was set by either guard rule
- **When** I view that object
- **Then** it carries a badge naming the rule that fired
- **And** its rationale states that a guard rule determined the outcome and why

**AC6 — Guard rules affect only the intended objects**
- **Given** the bundled dataset
- **When** guard rules are applied
- **Then** exactly two objects change classification relative to pure score-based classification: `IN200` and `IM100`
- **And** the overall distribution remains 5 / 13 / 4

**AC7 — Guard thresholds are configurable**
- **Given** the guard rule parameters
- **When** I view the configuration
- **Then** the dormancy day count, dormancy execution count, activity day count, and activity execution count are all adjustable
- **And** their defaults are 180 days, 5 executions, 90 days, and 25 executions

---

## S2.4 — Test how sensitive my recommendation is

**As a** Migration Architect
**I want** to move the Value and Effort thresholds and see classifications update immediately
**So that** I know which recommendations are robust and which are borderline

**Requirements**: FR-3.3, FR-3.4, FR-3.5

### Acceptance Criteria

**AC1 — Both thresholds adjustable**
- **Given** the application is running
- **When** I look for scoring controls
- **Then** the Value threshold and the Effort threshold are both adjustable
- **And** each displays its current value and its default (33 and 67 respectively)

**AC2 — Live recomputation**
- **Given** I change either threshold
- **When** the change is applied
- **Then** every classification, chart, count, and table across all views reflects the new threshold
- **And** no manual refresh is required

**AC3 — `FI100GC` demonstrates the margin**
- **Given** default thresholds
- **When** `FI100GC` is classified
- **Then** it is Replicate As-Is
- **Given** the Effort threshold is lowered to 66
- **When** classification recomputes
- **Then** `FI100GC` becomes Rebuild as Data Product

**AC4 — Raising the Value threshold expands Decommission**
- **Given** default thresholds produce 4 Decommission objects
- **When** I raise the Value threshold to 40
- **Then** the Decommission count increases
- **And** `IM100` still does not become Decommission, because the activity floor continues to protect it

**AC5 — Reset restores defaults**
- **Given** I have changed one or more thresholds
- **When** I reset
- **Then** all thresholds return to their documented defaults
- **And** the reference distribution of 5 / 13 / 4 is restored

---

# Epic 3 — Landscape Overview

*Requirements: FR-6.1 to FR-6.6*

## S3.1 — See headline landscape figures at a glance

**As a** Programme Manager
**I want** the key landscape numbers presented prominently
**So that** I can report the scale and the opportunity without deriving figures myself

**Requirements**: FR-6.1

### Acceptance Criteria

**AC1 — KPI strip present**
- **Given** I open the dashboard
- **When** the page renders
- **Then** a prominent strip displays total object count, total storage, percentage of objects recommended for decommission, and estimated storage reclaimed

**AC2 — Figures are correct for the bundled dataset**
- **Given** the bundled dataset and default thresholds
- **When** the KPI strip renders
- **Then** total objects reads 22
- **And** total storage reads 596 GB
- **And** the decommission percentage reads approximately 18% (4 of 22)
- **And** estimated storage reclaimed reads 21 GB, being the combined storage of `IN200`, `TR100`, `TR200`, and `TM100`

**AC3 — Figures track configuration changes**
- **Given** I change a threshold such that the Decommission set changes
- **When** the KPI strip re-renders
- **Then** the decommission percentage and reclaimed storage update to match

---

## S3.2 — See the shape of the landscape

**As a** Migration Architect
**I want** the classification split and the highest-value objects shown graphically
**So that** I can grasp the overall picture before examining individual objects

**Requirements**: FR-6.2, FR-6.3

### Acceptance Criteria

**AC1 — Classification donut**
- **Given** I open the dashboard
- **When** it renders
- **Then** a donut chart shows object counts by classification
- **And** for the bundled dataset the segments read 5 Rebuild, 13 Replicate As-Is, and 4 Decommission
- **And** each segment carries a text label, not colour alone

**AC2 — Top objects ranked**
- **Given** I open the dashboard
- **When** it renders
- **Then** a bar chart shows the top 10 objects by Business Value in descending order
- **And** `SC100` appears first

**AC3 — Charts respond to configuration**
- **Given** I change a threshold
- **When** the dashboard re-renders
- **Then** both the donut and the bar chart reflect the new classification outcome

---

## S3.3 — See where objects sit on value against effort

**As a** Migration Architect
**I want** all objects plotted on the two axes with the quadrant boundaries drawn
**So that** I can see the classification logic rather than just its output

**Requirements**: FR-6.4

### Acceptance Criteria

**AC1 — Scatter plot with boundaries**
- **Given** I open the dashboard
- **When** it renders
- **Then** a scatter plot positions every object with Business Value on one axis and Technical Effort on the other
- **And** the active Value and Effort thresholds are drawn as boundary lines
- **And** points are coloured by classification with a text legend

**AC2 — Quadrant occupancy matches classification**
- **Given** the bundled dataset and default thresholds
- **When** I read the plot
- **Then** the high-value, high-effort region contains `SC100`, `SC200`, `SA100`, `PR100`, and `PR200`
- **And** every point left of the Value boundary is classified Decommission, except where a guard rule has overridden it

**AC3 — Guard rule overrides are distinguishable**
- **Given** `IN200` sits right of the Value boundary yet is classified Decommission
- **When** I view the plot
- **Then** `IN200` is visually distinguishable as a guard-rule override rather than appearing to contradict the boundaries

**AC4 — Object identification**
- **Given** the plot is rendered
- **When** I hover over or select a point
- **Then** the object ID, description, both scores, and the classification are shown

**AC5 — Boundaries move with thresholds**
- **Given** I change either threshold
- **When** the plot re-renders
- **Then** the boundary lines move to the new values and point colours update

---

## S3.4 — See which objects I can switch off

**As a** Solution / Business Owner
**I want** decommission candidates listed with the reason for each
**So that** I can review the claim about my area and contest it if the evidence is weak

**Requirements**: FR-6.5

### Acceptance Criteria

**AC1 — Candidate table**
- **Given** I open the dashboard
- **When** it renders
- **Then** a table lists every object classified Decommission
- **And** each row shows the object ID, description, solution area, business owner, last run date, monthly executions, distinct users, and a rationale

**AC2 — Correct candidates for the bundled dataset**
- **Given** the bundled dataset and default thresholds
- **When** the table renders
- **Then** it contains exactly 4 rows: `IN200`, `TR100`, `TR200`, `TM100`

**AC3 — Rationale distinguishes cause**
- **Given** the candidate table
- **When** I read the rationale for `IN200`
- **Then** it attributes the classification to the dormancy ceiling and cites the last run date and execution count
- **When** I read the rationale for `TR200`
- **Then** it attributes the classification to a low Business Value score and names the dominant contributing factors

**AC4 — Reclaimable storage shown**
- **Given** the candidate table
- **When** it renders
- **Then** the storage attributable to each candidate is shown
- **And** a total is presented

---

# Epic 4 — Object Interrogation

*Requirements: FR-7.1 to FR-7.6, FR-3.5*

## S4.1 — Inspect a single object in full

**As a** Solution / Business Owner
**I want** one place showing everything known about an object
**So that** I can evaluate a recommendation about a report I own without assembling the picture myself

**Requirements**: FR-7.1, FR-7.2, FR-7.3, FR-7.4

### Acceptance Criteria

**AC1 — Object selection**
- **Given** I am in the object detail view
- **When** I select an object
- **Then** its detail is displayed
- **And** all 22 bundled objects are selectable

**AC2 — Metadata**
- **Given** an object is selected
- **When** its detail renders
- **Then** object ID, object type, solution area, and description are shown

**AC3 — Classification and scores**
- **Given** an object is selected
- **When** its detail renders
- **Then** the classification is shown alongside both the Business Value and Technical Effort scores

**AC4 — Usage metrics**
- **Given** `FI100GC` is selected
- **When** its detail renders
- **Then** last run date reads 2026-08-13, monthly executions reads 280, distinct users reads 45, and business owner reads Finance Controller

**AC5 — Dependencies both directions**
- **Given** an object is selected
- **When** its detail renders
- **Then** incoming and outgoing dependencies are listed separately
- **And** each dependency shows its target and its type

**AC6 — Cross-area object is handled**
- **Given** `ZMD1` is selected
- **When** its detail renders
- **Then** its solution area shows as `Production/Inventory`
- **And** the view states that its criticality of 82.5 is the average of Production (85) and Inventory Management (80)

---

## S4.2 — See exactly how a classification was reached

**As a** Solution / Business Owner
**I want** the full derivation of an object's scores together with a plain-language explanation
**So that** I can either accept the recommendation or make a specific case against it

**Requirements**: FR-7.5, FR-7.6, FR-3.5, NFR-6.3

### Acceptance Criteria

**AC1 — Dimension-by-dimension breakdown**
- **Given** an object is selected
- **When** I view its score breakdown
- **Then** each of the seven dimensions shows its raw input value, its normalised 0–100 score, its weight, and its weighted contribution
- **And** the contributions sum to the axis score shown

**AC2 — Both axes broken down**
- **Given** the breakdown is displayed
- **When** I read it
- **Then** the five Business Value dimensions and the two Technical Effort dimensions are presented separately under their respective axis totals

**AC3 — Inherited values are labelled as inherited**
- **Given** an object whose criticality and dependency counts come from its solution area
- **When** I view the breakdown
- **Then** those dimensions are marked as inherited from the solution area
- **And** the source area is named

**AC4 — Narrative rationale**
- **Given** any object
- **When** I read its rationale
- **Then** it is expressed in plain language
- **And** it names the factors that most influenced the classification
- **And** it does not require the reader to interpret raw scores

**AC5 — Rationale for a rebuild candidate**
- **Given** `SC100` is selected
- **When** I read its rationale
- **Then** it identifies high business value and high technical effort as the basis for Rebuild as Data Product
- **And** it cites specific evidence such as its 100 distinct users and its complexity profile

**AC6 — Rationale where a guard rule fired**
- **Given** `IM100` is selected
- **When** I read its rationale
- **Then** it states that the computed score would have placed it in Decommission
- **And** it explains that the activity floor prevented this, citing 40 monthly executions across 10 users

---

# Epic 5 — Dependency Analysis

*Requirements: FR-4.1 to FR-4.6, FR-6.6*

## S5.1 — Understand what depends on what

**As a** Migration Architect
**I want** dependencies presented both as a precise matrix and as a visual network
**So that** I can look up a specific relationship and also grasp the overall coupling

**Requirements**: FR-4.1, FR-4.2, FR-4.3, FR-4.6, FR-6.6

### Acceptance Criteria

**AC1 — Matrix heatmap**
- **Given** I open the dependency view
- **When** it renders
- **Then** a solution-area by solution-area matrix is shown
- **And** cells are shaded to indicate dependency presence or strength
- **And** both axes are labelled with area names

**AC2 — Network graph**
- **Given** I open the dependency view
- **When** it renders
- **Then** a node-link graph is shown containing solution areas, external systems, source systems, shared objects, and constraint nodes
- **And** edge direction is visible
- **And** node types are visually distinguished with a legend

**AC3 — Known relationships are present**
- **Given** the bundled dependency map
- **When** the graph renders
- **Then** `PR` has an outgoing edge to `ZMD1` of type operational
- **And** `SC`, `PR`, `IN`, and `FI` each have an outgoing edge to `SAPPS1`
- **And** `FI` receives incoming edges from `SA`, `PR`, `PC`, `SC`, and `TR`

**AC4 — Wildcard constraint expanded**
- **Given** the dependency map contains the edge `ALL → DMK`
- **When** the graph is built
- **Then** each of the 12 solution areas has an outgoing edge to `DMK`
- **And** `DMK` has 12 incoming edges

**AC5 — Edge types counted equally**
- **Given** an area with both logical and operational outgoing edges
- **When** its outgoing dependency count is computed
- **Then** both edge types contribute equally to the count

**AC6 — Shared object visible in its own right**
- **Given** `ZMD1` exists both as an object and as a graph node
- **When** the graph renders
- **Then** the `ZMD1` node shows its two incoming edges from `PR` and `IN`
- **And** the view notes that `ZMD1` scoring uses inherited area averages rather than this node degree

---

# Epic 6 — Wave Planning

*Requirements: FR-5.1 to FR-5.9, FR-8.1 to FR-8.4*

## S6.1 — Get a recommended migration sequence

**As a** Programme Manager
**I want** objects assigned to waves led by business priority and checked against dependencies
**So that** I start from a defensible sequence rather than a blank plan

**Requirements**: FR-5.1, FR-5.2, FR-8.1, FR-8.4

### Acceptance Criteria

**AC1 — Priority-led assignment**
- **Given** the bundled dataset
- **When** the wave plan is generated
- **Then** every object is assigned to exactly one wave
- **And** assignment is led by the `migration_priority` value of the object's solution area

**AC2 — Priority mapping is correct**
- **Given** default settings of 5 waves
- **When** the plan is generated
- **Then** Financial Performance objects, having priority 1, appear in the earliest wave
- **And** Transport Management, Treasury Management, Quality Management, and Investment Management objects, having priority 5, appear in the latest wave

**AC3 — Dependency violations are detected**
- **Given** a generated wave plan
- **When** validation runs against the dependency graph
- **Then** any case where an area is scheduled earlier than an area it depends on is reported as a violation
- **And** each violation names the dependent area, the depended-upon area, and the two wave numbers

**AC4 — Violations are listed, not hidden**
- **Given** violations exist in the current plan
- **When** I view the wave planner
- **Then** all violations are listed together in one place
- **And** the count is visible without scrolling through the plan

**AC5 — Known violation is surfaced**
- **Given** the bundled dataset with default settings of 5 waves
- **When** validation runs
- **Then** exactly one dependency violation is reported: Logistics Costing (priority 4, wave 4) depends on Transport Management (priority 5, wave 5) for shipment costs, so it is scheduled before what it depends on
- **And** the violation names both areas and both wave numbers

**Correction (2026-08-18)**: this criterion originally cited Purchasing depending on Supply Chain as the example. That is not a violation — Purchasing is priority 4 (wave 4) and Supply Chain is priority 2 (wave 2), so the dependency is already satisfied. The actual and only violation in the bundled data is Logistics Costing to Transport Management, confirmed by executing the specified rules against the dataset during Unit 1 Functional Design.

---

## S6.2 — Shape the wave structure to my programme

**As a** Programme Manager
**I want** to set the number of waves, their duration, and the project start date
**So that** the plan reflects my actual programme shape rather than a fixed assumption

**Requirements**: FR-5.3, FR-5.4

### Acceptance Criteria

**AC1 — Defaults**
- **Given** I open the wave planner
- **When** it renders
- **Then** the wave count defaults to 5, wave duration defaults to 3 months, and a project start date is set and editable

**AC2 — Changing wave count**
- **Given** the default 5 waves
- **When** I change the count to 3
- **Then** all objects are redistributed across 3 waves
- **And** every object remains assigned to exactly one wave
- **And** dependency validation re-runs against the new structure

**AC3 — Changing duration and start date**
- **Given** a generated plan
- **When** I change wave duration or project start date
- **Then** the timeline shifts accordingly
- **And** wave membership is unaffected by a pure date or duration change

**AC4 — Risk recomputes**
- **Given** I change the wave structure
- **When** the plan regenerates
- **Then** per-wave risk scores recompute for the new grouping

---

## S6.3 — See the plan on a timeline with constraints marked

**As a** Programme Manager
**I want** the waves drawn on a timeline with the DMK freeze visible
**So that** I can present a plan that visibly respects the constraints we are bound by

**Requirements**: FR-5.5, FR-5.6, FR-8.2

### Acceptance Criteria

**AC1 — Gantt timeline**
- **Given** a generated wave plan
- **When** I view the timeline
- **Then** each wave is drawn as a bar spanning its date range
- **And** waves appear in sequence with readable date labels

**AC2 — DMK constraint marked**
- **Given** the timeline is rendered
- **When** I look for the DMK constraint
- **Then a** visual marker or band indicates the "limited changes before 2028" period
- **And** it is labelled so its meaning is clear without external explanation

**AC3 — Marker responds to date changes**
- **Given** I change the project start date so waves move relative to 2028
- **When** the timeline re-renders
- **Then** the DMK marker remains anchored to 2028 rather than moving with the waves

---

## S6.4 — Understand the risk in each wave

**As a** Programme Manager
**I want** a risk score per wave that I can decompose
**So that** I can direct attention to the right wave and defend the assessment when challenged

**Requirements**: FR-5.7, FR-5.8, FR-5.9, FR-8.3

### Acceptance Criteria

**AC1 — Risk score per wave**
- **Given** a generated wave plan
- **When** I view risk assessment
- **Then** every wave carries a risk score
- **And** the score is banded Low, Medium, or High with a text label

**AC2 — Composition is visible**
- **Given** a wave's risk score
- **When** I inspect it
- **Then** the contribution of average technical complexity, cross-wave dependency count, and downtime tolerance is each shown separately

**AC3 — Tight downtime tolerance raises risk**
- **Given** two waves alike in complexity and dependencies
- **When** one contains areas with lower `downtime_tolerance_hours`
- **Then** that wave carries the higher risk score

**AC4 — DMK adds risk before 2028**
- **Given** a wave scheduled to complete before 2028
- **When** its risk is computed
- **Then** a DMK constraint contribution is included
- **And** that contribution is identified by name in the breakdown

**AC5 — DMK adds no risk after 2028**
- **Given** a wave scheduled entirely after 2028
- **When** its risk is computed
- **Then** no DMK contribution is included

**AC6 — Complexity drives risk as expected**
- **Given** the bundled dataset with default settings
- **When** risk is computed across waves
- **Then** the wave containing `SC100`, `PR100`, and `PR200` carries a higher complexity contribution than the wave containing `TR100`, `TR200`, and `TM100`

---

# Epic 7 — Scenario Comparison and Export

*Requirements: FR-9.1, FR-9.2, FR-10.1 to FR-10.3*

## S7.1 — Compare two assessment stances

**As a** Migration Architect
**I want** to save a configuration and compare it against another
**So that** I can show what changes under a different assumption instead of arguing it abstractly

**Requirements**: FR-9.1, FR-9.2

### Acceptance Criteria

**AC1 — Save a scenario**
- **Given** a configuration of thresholds and any adjustable weights
- **When** I save it under a name
- **Then** it is retained and selectable for comparison

**AC2 — Compare two scenarios**
- **Given** two saved scenarios
- **When** I compare them
- **Then** the classification counts for each are shown side by side
- **And** every object whose classification differs between them is listed with its classification under each

**AC3 — Unchanged objects are excluded from the difference list**
- **Given** a comparison of two scenarios
- **When** I view the differences
- **Then** only objects whose classification changed are listed
- **And** the count of changed objects is stated

**AC4 — Identical scenarios yield no differences**
- **Given** two scenarios with identical settings
- **When** compared
- **Then** the difference list is empty and this is stated clearly rather than shown as a blank area

**AC5 — A concrete comparison works end to end**
- **Given** a scenario saved at default thresholds and a second with the Effort threshold at 66
- **When** compared
- **Then** `FI100GC` is listed as changing from Replicate As-Is to Rebuild as Data Product

---

## S7.2 — Take the assessment away with me

**As a** Programme Manager
**I want** to download the classification report and the wave recommendation
**So that** I can circulate the outcome and reference it outside the tool

**Requirements**: FR-10.1, FR-10.2, FR-10.3

### Acceptance Criteria

**AC1 — Classification report as CSV**
- **Given** any active configuration
- **When** I download the classification report
- **Then** a CSV is produced containing one row per object
- **And** each row includes object ID, type, solution area, description, both axis scores, classification, and rationale

**AC2 — Wave recommendation as JSON**
- **Given** a generated wave plan
- **When** I download the wave recommendation
- **Then** a JSON file is produced containing wave assignments, wave date ranges, per-wave risk scores, and any dependency violations

**AC3 — Exports reflect current configuration, not defaults**
- **Given** I have changed a threshold from its default
- **When** I export
- **Then** the exported classifications match what is displayed on screen

**AC4 — Configuration is embedded**
- **Given** any export
- **When** I inspect the file
- **Then** the threshold values, guard rule parameters, and wave settings used to produce it are included
- **And** the export is therefore reproducible from its own contents

**AC5 — Bundled dataset export is complete**
- **Given** the bundled dataset at default settings
- **When** I export the classification report
- **Then** it contains 22 data rows
- **And** the classification column totals 5 Rebuild, 13 Replicate As-Is, and 4 Decommission

---

# Epic 8 — Platform, Presentation and Performance

*Non-functional stories per Q6 = A. Requirements: NFR-2.x, NFR-3.x, NFR-4.x, NFR-5.x*

## S8.1 — Run the tool anywhere with one command

**As a** Migration Architect
**I want** to start the application with a single command on Windows or Linux
**So that** getting it running is never the obstacle

**Requirements**: NFR-2.1 to NFR-2.5, NFR-1.2, NFR-1.3

### Acceptance Criteria

**AC1 — Windows launch**
- **Given** a machine with a supported Python and a clean checkout
- **When** I run `run.bat`
- **Then** a virtual environment is created, pinned dependencies are installed, and the application starts
- **And** no step other than running that one script is required

**AC2 — Linux launch**
- **Given** a Linux machine with a supported Python and a clean checkout
- **When** I run `run.sh`
- **Then** the same outcome is achieved

**AC3 — Python is the only prerequisite**
- **Given** a machine without Node.js, Docker, or any database
- **When** I run the launch script
- **Then** the application starts successfully

**AC4 — Second run is fast**
- **Given** the environment has already been provisioned
- **When** I run the launch script again
- **Then** dependency installation is skipped and the application starts directly

**AC5 — Unsupported Python is reported clearly**
- **Given** a machine whose Python is older than the supported minimum
- **When** I run the launch script
- **Then** it stops with a message naming the version found and the version required
- **And** it does not fail with an obscure dependency resolution error

**AC6 — Versions are pinned**
- **Given** the dependency specification
- **When** I inspect it
- **Then** every dependency carries an explicit pinned version

**AC7 — README covers both platforms**
- **Given** the README
- **When** I follow it on either platform
- **Then** prerequisites, launch steps, and a troubleshooting section are present and sufficient

---

## S8.2 — Read every screen comfortably

**As a** Solution / Business Owner
**I want** the interface to be legible and to convey meaning without relying on colour
**So that** I can follow a discussion about my reports in an unfamiliar meeting room

**Requirements**: NFR-4.1 to NFR-4.6

### Acceptance Criteria

**AC1 — Brand palette applied**
- **Given** any view
- **When** it renders
- **Then** the application background is `#f2f7f1`, cards are `#ffffff`, and the header and sidebar are `#02462f` with white text

**AC2 — Contrast meets AA**
- **Given** any text in the application
- **When** its contrast against its background is measured
- **Then** it meets at least 4.5:1 for normal text and 3:1 for large text

**AC3 — Prohibited combination absent**
- **Given** the rendered application
- **When** all text colours are inspected
- **Then** `#82ce71` is never used for text on a white or light background

**AC4 — Classification colours as specified**
- **Given** any classification indicator
- **When** it renders
- **Then** Rebuild as Data Product uses `#02462f`, Replicate As-Is uses `#82ce71`, and Decommission uses the specified muted terracotta

**AC5 — Never colour alone**
- **Given** any element conveying classification
- **When** it renders
- **Then** a text label or icon accompanies the colour
- **And** the meaning survives being viewed in greyscale

**AC6 — Charts are labelled**
- **Given** any chart
- **When** it renders
- **Then** axes are labelled, a legend is present where more than one series or category appears, and hover text identifies data points

---

## S8.3 — Work reliably without network, and respond instantly

**As a** Programme Manager
**I want** the tool to work without internet access and to react immediately to changes
**So that** neither venue connectivity nor sluggishness disrupts a discussion

**Requirements**: NFR-3.1, NFR-3.2, NFR-5.1, NFR-5.2, NFR-5.3

### Acceptance Criteria

**AC1 — Fully functional offline**
- **Given** dependencies are already installed
- **When** I disconnect from the network and start the application
- **Then** every view renders and every function works

**AC2 — Typography degrades gracefully**
- **Given** the application is running without network access
- **When** any view renders
- **Then** text renders in a system fallback font
- **And** layout is not broken and no element is left unstyled or misaligned

**AC3 — Recomputation feels instant**
- **Given** the bundled 22-object dataset
- **When** I move a threshold control
- **Then** all scores and classifications recompute in under 500 ms

**AC4 — Startup is prompt**
- **Given** a provisioned environment
- **When** I start the application
- **Then** the first view is rendered within 10 seconds

**AC5 — Headroom for a real extract**
- **Given** a dataset of approximately 1,000 objects
- **When** scoring and classification run
- **Then** the application remains responsive and usable

---

## Traceability — Story to Requirement

| Story | Requirements covered |
|---|---|
| S1.1 | FR-1.1, FR-1.2 |
| S1.2 | FR-1.3, FR-1.5 |
| S1.3 | FR-1.4, NFR-6.4 |
| S2.1 | FR-2.1, FR-2.2, FR-2.3, FR-2.4 |
| S2.2 | FR-3.1, FR-3.2 |
| S2.3 | FR-3.6, FR-3.7, FR-3.8, FR-3.9 |
| S2.4 | FR-3.3, FR-3.4, FR-3.5 |
| S3.1 | FR-6.1 |
| S3.2 | FR-6.2, FR-6.3 |
| S3.3 | FR-6.4 |
| S3.4 | FR-6.5 |
| S4.1 | FR-7.1, FR-7.2, FR-7.3, FR-7.4, FR-4.5 |
| S4.2 | FR-7.5, FR-7.6, FR-3.5, FR-2.5, NFR-6.3 |
| S5.1 | FR-4.1, FR-4.2, FR-4.3, FR-4.4, FR-4.6, FR-6.6 |
| S6.1 | FR-5.1, FR-5.2, FR-8.1, FR-8.4 |
| S6.2 | FR-5.3, FR-5.4 |
| S6.3 | FR-5.5, FR-5.6, FR-8.2 |
| S6.4 | FR-5.7, FR-5.8, FR-5.9, FR-8.3 |
| S7.1 | FR-9.1, FR-9.2 |
| S7.2 | FR-10.1, FR-10.2, FR-10.3 |
| S8.1 | NFR-1.2, NFR-1.3, NFR-2.1 – NFR-2.5 |
| S8.2 | NFR-4.1 – NFR-4.6 |
| S8.3 | NFR-3.1, NFR-3.2, NFR-5.1 – NFR-5.3 |

### Requirements not covered by any story — with rationale

| Requirement | Why not storied |
|---|---|
| NFR-1.1 (stack choice) | An implementation decision, not user-observable behaviour. Verified by inspection. |
| NFR-6.1, NFR-6.2 (navigation, control defaults) | Structural UI behaviour, verified by the smoke tests in NFR-7.3 and implicitly exercised by every story above. |
| NFR-7.1 – NFR-7.4 (testing) | Requirements *about* verification rather than about product behaviour. Satisfied by the acceptance criteria in this document becoming test cases. |
| NFR-8.1 – NFR-8.4 (maintainability, comments) | Code quality constraints with no user-visible manifestation. Enforced at Code Generation. |
| §3.9 (out of scope items) | Explicitly excluded from the product. |

---

## Persona to Story Map

| Persona | Stories |
|---|---|
| **P1 Migration Architect** | S1.1, S1.2, S1.3, S2.1, S2.2, S2.4, S3.2, S3.3, S5.1, S7.1, S8.1 |
| **P2 Solution / Business Owner** | S2.3, S3.4, S4.1, S4.2, S8.2 |
| **P3 Programme Manager** | S3.1, S6.1, S6.2, S6.3, S6.4, S7.2, S8.3 |

Counts: P1 = 11, P2 = 5, P3 = 7, totalling 23 — one persona per story across all 23 stories, no story attributed twice.

**Correction (2026-08-18)**: this document originally stated 22 stories in three places. The actual count is 23; the per-epic counts (3, 4, 4, 2, 1, 4, 2, 3) were correct throughout and sum to 23. Corrected during Units Generation, before the story-to-unit map was built.

---

## INVEST Verification

| Criterion | How the story set satisfies it |
|---|---|
| **Independent** | Each story is understandable and testable alone. Epic 2 stories share the engine but each asserts a distinct behaviour: composition (S2.1), mapping (S2.2), overrides (S2.3), sensitivity (S2.4). Epic 3 and 4 stories each target one view component. |
| **Negotiable** | Stories state the outcome sought, not the implementation. No story prescribes a library, layout, or code structure. |
| **Valuable** | Every story names a persona and the benefit to them. Epic 8 stories are framed by the persona affected rather than as technical chores. |
| **Estimable** | Scope is bounded by concrete acceptance criteria with named objects and expected values, leaving little unknown. |
| **Small** | 23 stories across 8 epics for a PoC of this size. The largest, S5.1, covers two visualisations of one dataset; the smallest cover a single chart. |
| **Testable** | Every criterion is expressed as Given/When/Then with an observable outcome. Criteria citing specific objects and the 5/13/4 distribution translate directly into the assertions NFR-7.2 requires. |
