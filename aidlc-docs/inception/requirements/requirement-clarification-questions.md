# Requirements Clarification Questions — BW-ACE

Thanks — all 22 answered. Twenty of them are internally consistent and I can proceed on those directly.

Two answers conflict, and resolving them opens two follow-on decisions. Four questions below.

---

## Contradiction: Q1 (two-axis model) vs Q2 (33/67 score bands)

You chose **Q1 = D**, the two-axis model: a *Business Value* score and a separate *Technical Effort* score, with classification read off the value/effort matrix.

You also chose **Q2 = B**, keeping the documented **33 / 67** band boundaries as configurable defaults.

These can't both apply as written. The 33/67 bands assume a **single composite 0-100 score** cut into three slices. The two-axis model has **no single score** — it has two independent 0-100 axes and classifies by position in a grid. There is nothing for a 33/67 cut to operate on.

There's a second consequence: a 2x2 grid produces **four** quadrants, but the document defines only **three** categories. One quadrant pair has to collapse.

The questions below resolve both points.

---

### Clarification Question 1 — How should the four quadrants map to three categories?

With Business Value on one axis and Technical Effort on the other:

**A) Value-first mapping** — low business value means decommission regardless of effort; among valuable objects, effort decides the treatment.

| | Low Effort | High Effort |
|---|---|---|
| **High Value** | Replicate As-Is | Rebuild as Data Product |
| **Low Value** | Decommission | Decommission |

*Rationale*: matches the document's category definitions closely. Decommission is defined by "zero or near-zero usage", and Rebuild by "high business criticality; high dependency count; modernize for strategic benefit" — i.e. valuable *and* substantial. Complex-but-unused objects correctly fall to Decommission, which was the original problem with the documented formula. **(My recommendation.)**

**B) Pragmatic-effort mapping** — the inverse treatment of effort for valuable objects.

| | Low Effort | High Effort |
|---|---|---|
| **High Value** | Rebuild as Data Product | Replicate As-Is |
| **Low Value** | Decommission | Decommission |

*Rationale*: the argument I raised in the original Q1 — high complexity argues *against* an expensive rebuild and *for* lifting it as-is to limit programme risk. Rebuild the valuable things that are cheap to rebuild. Defensible, but it inverts the document's stated logic for the Rebuild category.

**C) Four quadrants, four labels** — add a fourth category beyond the document's three, e.g. *Retire (high-cost drag)* for Low Value / High Effort, separated from *Decommission* for Low Value / Low Effort. Analytically the cleanest and makes the "expensive things nobody uses" story very vivid in a demo, but adds a category the requirement document doesn't define.

**D) Effort as a tie-breaker only** — classify primarily on Business Value in three bands (low → Decommission, mid → Replicate, high → Rebuild), and use Technical Effort only to move borderline cases up or down one category. Keeps three clean bands and preserves a role for the 33/67 numbers, but the 2x2 becomes presentational rather than decisional.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Clarification Question 2 — What happens to the 33 / 67 thresholds?

You asked to keep 33/67 as configurable defaults. Under a two-axis model they need reinterpreting.

**A) Two independent thresholds, documented defaults reused** — a *Value* threshold defaulting to **33** (below it, an object is low-value → Decommission) and an *Effort* threshold defaulting to **67** (above it, an object is high-effort). Both exposed as sliders. This reuses your documented numbers literally and keeps the demo's sensitivity story intact. **(My recommendation.)**

**B) Two independent thresholds, midpoint defaults** — Value threshold at 33, Effort threshold at **50**. A true grid midpoint on the effort axis, rather than reusing 67 which was designed as an upper band boundary.

**C) Thresholds plus a composite score retained** — classify from the matrix (per CQ1), but *also* compute and display the documented single composite score with its 33/67 bands as a secondary "documented method" figure on the object detail view. Lets you show the customer both the requirement-document method and the improved method side by side. More build effort, but a strong credibility move if the customer wrote that formula.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Clarification Question 3 — What composes the Technical Effort axis?

The documented weights give Technical Complexity 10% and Data Volume 5%. Splitting them onto their own axis means renormalising: **complexity 66.7% / volume 33.3%**. Two inputs is thin for an axis that now drives a third of your classification decision.

Note that each input is already multi-attribute in your data. Section 3.6 gives `hana_cv_count`, `transformation_count`, `custom_logic_present`, `interface_count`. Section 3.5 gives `record_count`, `storage_gb`, `load_frequency`.

**A) Faithful renormalisation** — Effort = Complexity (66.7%) + Volume (33.3%), where Complexity is itself a composite of all four attributes in section 3.6 and Volume a composite of the three in section 3.5. Preserves your documented weight ratio exactly while still drawing on seven underlying attributes. **(My recommendation.)**

**B) Enriched complexity** — as A, but also fold `adso_count` and `custom_table_count` from section 3.1 into the complexity composite. More inputs, slightly further from the documented weights.

**C) Equal split** — Effort = Complexity (50%) + Volume (50%). Simpler to explain, but discards the 2:1 ratio implied by the document's 10%/5%.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Clarification Question 4 — Dead-usage override

The dead-usage override (force Decommission when an object hasn't run in ~6 months and has under ~5 monthly executions) was bundled inside Q1 option B, which you didn't select. So it currently isn't in scope.

Under the two-axis model it's largely redundant — dead objects score low on value and land in the Decommission quadrant anyway. But it does act as a guarantee, and four objects in your data would trigger it: `IN200` (last run Aug 2025, 2 executions), `TR100` (Oct 2025, 6), `TR200` (Sep 2025, 3), `TM100` (Nov 2025, 4).

**A) No override** — trust the two-axis model. Cleaner to explain, one mechanism rather than two. **(My recommendation, given Q1 = D.)**

**B) Add the override as a hard rule** — guarantees dead objects are never classified as anything but Decommission, and gives an unambiguous "these four are safe to switch off today" slide.

**C) Add it as a flag, not an override** — don't change the classification, but tag such objects with a visible "Dormant" badge in the UI and list them separately. Keeps one classification mechanism while still surfacing the quick wins.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Answers I'm treating as settled

No action needed on these — listed so you can see what I've locked in.

| Q | Topic | Your answer |
|---|---|---|
| 3 | Normalisation | B — fixed absolute bands per dimension |
| 4 | Area-level data | B — inherit from solution area; ZMD1 averages Production & Inventory (82.5) |
| 5 | Dependency counting | A — all edges equal, `ALL`→DMK expanded to every area |
| 6 | Wave algorithm | B — priority-led, dependency violations flagged as risks |
| 7 | Wave count | C — configurable, default 5 waves x 3 months |
| 8 | DMK constraint | B — Gantt marker plus risk flag |
| 9 | Wave risk | B — complexity + cross-wave dependencies + downtime tolerance |
| 10 | Stack | A — Streamlit, Pandas, NetworkX, Plotly on Python 3.12 |
| 11 | Storage | B — bundled JSON, plus live CSV/JSON upload |
| 12 | Outputs | B — on-demand export reflecting current settings |
| 13 | Theme | A — light theme, dark green header, WCAG AA throughout |
| 14 | Classification colours | A — palette-derived, muted terracotta for Decommission |
| 15 | Fonts | B — Google font via CDN |
| 16 | Dependency view | B — matrix heatmap plus network graph |
| 17 | Testing | C — engine unit tests plus UI smoke tests |
| 18 | Security extension | B — skipped (PoC) |
| 19 | Resiliency extension | B — skipped (PoC) |
| 20 | PBT extension | C — skipped (PoC) |
| 21 | Run method | A — `run.bat` / `run.sh` |
| 22 | Extras | D — executive KPI strip *and* what-if configuration comparison |

### Two notes on the above

**Q5 (all edges equal).** The `ALL → DMK` edge expands to an outgoing dependency for all 12 solution areas. Because it applies uniformly it adds no discriminating signal between objects — it shifts every object's dependency score by the same amount. That's harmless, just not informative. I'll implement it as you chose and note the effect in the requirements.

**Q15 (CDN font).** A CDN font needs internet access at render time. Since this is going into a customer demo where connectivity isn't guaranteed, I'll implement the web font with a full system-font fallback stack, so the app still renders correctly and on-brand if the venue's network is unavailable. No action needed unless you'd rather I bundle the font file locally instead.

---

**When you've answered the four questions above, let me know and I'll write the requirements document.**
