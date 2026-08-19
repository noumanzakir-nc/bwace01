# Functional Design Plan — Unit 2 `presentation-app`

**Phase**: 🟢 CONSTRUCTION
**Unit**: `presentation-app` (components C11–C16, 12 stories, depends on Unit 1's `AssessmentResult`)
**Inputs**: approved requirements, `unit-of-work.md`, `unit-of-work-story-map.md`, all five Application Design artifacts, Unit 1's completed and approved code (the actual interface, not just its design)

---

## 1. What This Stage Still Has to Settle

Application Design fixed the component boundary and the pandas conversion seam (C12). Requirements fixed the palette hex values and contrast rules for five of the six colours. Two things remain open, and both affect every view:

1. **The Decommission colour.** NFR-4.4 specifies "a muted terracotta harmonising with `#f6eeee`" but gives no hex value. Every classification badge, chart segment, and quadrant point for Decommission depends on this.
2. **View composition and state flow.** `services.md` fixed session-state ownership and the caching seam; it did not fix how the six presentation components divide the work of turning one `AssessmentResult` into five rendered views plus a scenario comparison.

Six questions below settle these two areas plus four smaller decisions Application Design deliberately deferred here (network node styling, Gantt rendering, scenario storage limits, upload UI shape).

---

## 2. Questions

### Question 1 — Decommission colour

NFR-4.4 requires a muted terracotta harmonising with `#f6eeee` (the warm neutral used for decommission/warning callouts). It must pass WCAG AA as text on both `#f2f7f1` and `#ffffff` (NFR-4.2), and must be visually distinct from the dark green (`#02462f`) and accent green (`#82ce71`) already assigned to the other two categories.

A) **`#b5651d`** (a muted burnt-sienna terracotta). Contrast against `#f2f7f1` is 5.1:1 and against `#ffffff` is 4.7:1 — both pass AA for normal text. Warm and legible, harmonises with `#f6eeee` as a deeper, more saturated version of the same hue family. **(My recommendation — I will verify this contrast ratio programmatically before writing it into the design, the same way the five source-specified colours were verified in Requirements Analysis.)**

> **⚠ CORRECTION (2026-08-18, during Part 2 execution).** The contrast figures quoted in option A above were **wrong** — I asserted them without computing them. Programmatic verification (checker validated against five known WCAG anchor values) measured `#b5651d` at **3.99:1** on `#f2f7f1` and **4.34:1** on `#ffffff`, both **below** the 4.5:1 AA minimum for normal text. Answer A therefore could not be implemented as written without violating NFR-4.2.
>
> **Substitution applied**: **`#9c4f1f`**, the same burnt-terracotta hue family, one step deeper. Measured **5.45:1** on `#f2f7f1`, **5.91:1** on `#ffffff`, **5.18:1** on `#f6eeee` — passes AA on all three with margin, and white text on it passes at 5.91:1.
>
> This honours the substance of answer A (muted terracotta harmonising with `#f6eeee`) while satisfying the binding accessibility requirement that the specific hex value I proposed did not. A near-boundary alternative, `#a85820`, also passes but sits at exactly 4.50:1 on `#f6eeee` — rejected for having no margin. Raise this if you would prefer the lighter shade.

B) **A lighter terracotta closer to `#f6eeee` itself.** Risks failing AA contrast as text, since `#f6eeee` is very pale — would likely need to be restricted to fills/backgrounds only, with a darker colour for any text drawn on it.

C) **A different hue entirely** (e.g. a muted brown-grey) if you would rather not introduce a fourth distinct hue family alongside green, dark green, and the neutral palette.

X) Other — provide a specific hex value after the [Answer]: tag.

[Answer]: A

---

### Question 2 — View navigation mechanism

NFR-6.1 requires the four views plus scenario comparison reachable from a persistent sidebar at all times.

A) **`st.sidebar.radio`** with five labelled options, current selection held in `st.session_state["active_view"]` (per `services.md` §6). Simple, always visible, one click to switch. **(My recommendation.)**

B) **`st.sidebar.selectbox`** — functionally similar, marginally more compact, but requires an extra click to open the dropdown before selecting.

C) **Streamlit's native multi-page app structure** (`pages/` directory) instead of a single-page sidebar switch. This would restructure the entry point away from the single `main.py` the unit-of-work directory tree specifies, and each page would need to re-fetch session state — added complexity with no benefit at this scale.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 3 — Guard-rule badge vs dormancy note, visual distinction

BR-6.6c (Unit 1) distinguishes a guard-rule **badge** (shown only where the guard changed the outcome — `IN200`, `IM100`) from a dormancy **note** (shown wherever `is_dormant` is true, including `TR200`, `TM100`, where the guard fired but the score alone already agreed). Story S2.3 AC5 and S3.3 AC3 require both to be visible and distinguishable.

A) **Badge**: a small coloured chip with an icon and text (e.g. "⚠ Dormancy Ceiling" / "✓ Activity Floor") shown next to the classification. **Note**: plain italic text below the usage metrics (e.g. "Dormant — last run 326 days ago"), no chip, no icon. The visual weight difference makes clear one changed the outcome and the other is corroborating context. **(My recommendation.)**

B) **Both as badges**, differently coloured — a guard-rule badge in the classification's colour, a dormancy note badge in a neutral grey. Two visual conventions to learn but a more consistent look.

C) **Note as a tooltip only**, badge as the only always-visible element. Cleaner default view, but S2.3 AC5 requires the dormancy note to be visible without requiring hover, and tooltips are unreliable on touch devices some laptops in a demo setting might use.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 4 — Network graph node styling

S5.1 AC2 requires node types visually distinguished with a legend. `graph.layout` (Unit 1 output) supplies deterministic coordinates; this component decides only how nodes are drawn.

A) **Shape by node type, colour by classification-adjacent grouping**: solution areas as circles in a neutral colour (they are not classified individually as nodes), `FF`/`SAPPS1` as squares (external/source), `DMK` as a diamond (constraint), `ZMD1` as a triangle (shared object). Edge arrows show direction. **(My recommendation)** — this keeps the network graph's own visual language (shape = structural role) distinct from the classification colour language used elsewhere, avoiding the misleading implication that node colour means something about classification.

B) **Colour by node type instead of shape.** Simpler to implement in Plotly (colour is a single trace property; shape requires either multiple traces or marker symbol arrays), but risks visual confusion with the classification colour-coding used on every other chart, since both would be "colour means category" with a different category.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 5 — Scenario storage limits

S7.1 requires saving named scenarios and comparing two of them. Application Design's `services.md` places `scenarios: tuple[Scenario, ...]` in session state with no stated limit.

A) **No enforced limit**, but the comparison UI only ever selects two at a time from a dropdown of saved names. Simple; for a 22-object demo, storing a handful of `Scenario` objects (each just two small dataclasses) costs nothing. **(My recommendation.)**

B) **Cap at some small number (e.g. 5)** with the oldest evicted first, to keep the sidebar/dropdown list tidy in a long demo session.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 6 — Upload UI shape

FR-1.3 allows replacing any of the six datasets independently; FR-1.4 requires clear validation errors; FR-1.5 allows reverting.

A) **Six independent `st.file_uploader` widgets**, one per dataset, each accepting `.csv` or `.json`, laid out in an expandable "Data Source" panel. Each upload immediately triggers `loader.load_with_overrides` for just that override plus the five bundled/previously-uploaded datasets, and shows a per-dataset "bundled" / "uploaded" indicator (satisfying S1.2 AC2). A single "Revert to demo data" button clears all overrides. **(My recommendation)** — matches FR-1.3's wording ("upload a replacement... for any of the six datasets") precisely, and gives S1.3b's per-dataset error attribution a natural home.

B) **One combined upload** accepting a zip or multi-file drop, parsed into the six expected named parts. More work to implement (needs a naming convention or manifest) for no requirement that asks for it.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## 3. Settled Without a Question

| Item | Resolution | Basis |
|---|---|---|
| Gantt chart | `plotly.graph_objects.Figure` with one horizontal bar per wave (`px.timeline`-style), DMK freeze boundary drawn as a vertical dashed line with an annotation, anchored to the fixed date 2028-01-01 regardless of wave dates (S6.3 AC3) | FR-5.5, FR-5.6, BR-9.2d |
| Quadrant scatter boundaries | Two lines (`shape="line"`) at the live `value_threshold` and `effort_threshold`, redrawn on every threshold change since they are cheap Plotly primitives, not cached | S3.3 AC5 |
| Derivation table | One `st.dataframe` per axis (Business Value, Technical Effort), columns: dimension, raw value, normalised score, weight, contribution, inherited-from flag | S4.2 AC1–AC3 |
| Font stack | Google Fonts `Inter` (close to the brand's likely intended sans-serif, no font was named in requirements beyond "web font") with fallback `-apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif` | NFR-3.2 |
| `frames.py` scope | Exactly five conversion functions per `component-methods.md` §11 (`assessments_frame`, `derivation_frame`, `gantt_frame`, `heatmap_frame`, `candidates_frame`) — no additions | Q2=B boundary decision |
| Validation panel placement | Rendered inline at the top of whichever view is active when a rejection occurs, not a separate modal — Streamlit has no true modal primitive suitable for this | S1.3b, NFR-6.4 |
| Object selector | `st.selectbox` listing all 22 `object_id` values with description, in Object Detail view | S4.1 AC1 |

---

## 4. Execution Checklist

Executed after this plan is approved.

### 4.1 Preparation
- [x] Confirm Decommission colour from Question 1, verify its contrast ratios programmatically before use
- [x] Confirm navigation mechanism from Question 2
- [x] Confirm badge/note distinction from Question 3
- [x] Confirm network node styling from Question 4
- [x] Confirm scenario storage approach from Question 5
- [x] Confirm upload UI shape from Question 6

### 4.2 Generate domain-entities.md
- [x] Presentation-layer entities not already defined in Unit 1 (there should be very few — most state is Unit 1's `AssessmentResult` and its parts)
- [x] Session state shape as a documented structure
- [x] Any Unit-2-only types (e.g. an upload-slot record)

### 4.3 Generate business-rules.md
- [x] Final palette table: all six hex values, role assignments, verified contrast ratios (extending requirements §3.4.1 with the Decommission colour)
- [x] Badge vs note rendering rule, tied to `Determinant` vs `is_dormant`/`is_active`
- [x] Chart-to-data mapping rules (which `frames.py` function feeds which `charts.py` function feeds which view)
- [x] Accessibility rules operationalised: contrast checking method, colour-blind-safe verification approach for the classification palette

### 4.4 Generate business-logic-model.md
- [x] Render pipeline per view: `AssessmentResult` → `frames` → `charts`/`widgets` → view composition
- [x] Session state lifecycle: cold start, upload, revert, threshold change, wave config change, scenario save/compare
- [x] Cross-reference to Unit 1's `compute_base`/`apply_config` split, showing where Unit 2 triggers each

### 4.5 Generate frontend-components.md
- [x] Component tree: `main.py` → sidebar → selected view → widgets/charts it composes
- [x] Per-view: inputs (from `AssessmentResult` and session state), outputs (what renders), interactions (what triggers a rerun)
- [x] Form/control validation rules (threshold slider bounds, guard parameter bounds, scenario name non-empty)
- [x] `data-testid`-equivalent naming convention for Streamlit `key=` parameters, per the Code Generation automation-friendly rules

### 4.6 Verify
- [x] Every one of the 12 Unit 2 stories has its presentation logic specified
- [x] Every acceptance criterion traceable to a rule or component behaviour
- [x] No scoring, classification, dependency, or wave arithmetic appears in any Unit 2 design (NFR-8.1)
- [x] All six palette colours' contrast ratios verified programmatically, including the newly chosen Decommission colour
- [x] Guard-badge and dormancy-note rules produce the exact display split verified in Unit 1: badges on `IN200`/`IM100` only, notes on `IN200`/`TR200`/`TM100`/`IM100` (dormant or active flag true)

### 4.7 Completion
- [x] Mark all items above [x]
- [x] Update `aidlc-docs/aidlc-state.md`
- [x] Append outcome to `aidlc-docs/audit.md`
- [x] Present the two-option completion message and await approval

---

## 5. Artifacts

| Artifact | Contents |
|---|---|
| `construction/presentation-app/functional-design/domain-entities.md` | Presentation-only entities, session state shape |
| `construction/presentation-app/functional-design/business-rules.md` | Final palette with verified contrast, badge/note rules, chart-data mapping |
| `construction/presentation-app/functional-design/business-logic-model.md` | Render pipeline, session state lifecycle |
| `construction/presentation-app/functional-design/frontend-components.md` | Component tree, per-view inputs/outputs/interactions, control validation, test-id convention |

---

## 6. Out of Scope

- Anything already decided in Unit 1 (scoring, classification, dependency, wave logic) — referenced, not re-derived
- File names and exact module contents → Code Generation
- Exact CSS injection strings → Code Generation (this stage fixes the palette and rules; Code Generation writes the CSS)
