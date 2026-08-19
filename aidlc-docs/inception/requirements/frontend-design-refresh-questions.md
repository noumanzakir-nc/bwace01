# Frontend Design Refresh + Colour Theme — Clarifying Questions

**Stage**: 🔵 INCEPTION — Requirements Analysis (Standard depth)
**Request**: improve the frontend design; fix menu colours that look wrong against the rest of the app
**Target unit**: `presentation-app` (C11-C16). No engine change is contemplated by any option below.

Please answer each question by filling in the letter choice after the `[Answer]:` tag. If none of the options match, choose the last option (Other) and describe your preference.

---

## Diagnosis you should know before answering

I found a concrete cause for the menu colours, verified rather than guessed.

`.streamlit/config.toml` has a `[client]` block but **no `[theme]` block**. I confirmed on your installed Streamlit 1.61.1 that `theme.primaryColor` is unset, and that `#ff4b4b` is Streamlit's built-in default primary. So every **native widget accent** is Streamlit red:

- the selected dot of the sidebar navigation radio
- the Value/Effort slider handles and their filled tracks
- checkbox fills and keyboard focus rings

Meanwhile `theme.py` paints everything *around* those widgets in blue (`#0050e6` accent, `#001d6c` text, `#eef4ff` sidebar). Red-on-pale-blue is the clash you are seeing.

This also explains why the three previous restyle rounds did not fix it: they all edited the CSS that `theme.py` injects, and injected CSS cannot reach Streamlit's native widget accents. Only a `[theme]` block in `config.toml` can.

**Binding constraint on every option below**: NFR-4.2 requires WCAG 2.1 AA (4.5:1 for normal text). Any colour I introduce gets its contrast computed with the validated checker before it ships, never estimated. The three classification colours (Rebuild `#02462f`, Replicate `#82ce71`, Decommission `#9c4f1f`) are semantic business-rule colours under NFR-4.4 and I propose leaving them alone — Q4 lets you say otherwise.

---

## Question 1
How should the native widget accent (the red radio dot, red slider handles, red focus rings) be fixed?

A) Add a `[theme]` block to `.streamlit/config.toml` setting `primaryColor` to the existing accent `#0050e6`, plus matching `backgroundColor`, `secondaryBackgroundColor`, `textColor`, and `font`. Native widgets then inherit the app palette instead of Streamlit's red, and the `theme.py` CSS keeps its current role for everything Streamlit does not expose. *(Recommended — smallest change that actually removes the red, and it fixes sliders and focus rings at the same time, not just the menu.)*

B) Same `[theme]` block, and additionally move as much styling as possible out of the injected CSS into native theme config, shrinking the custom CSS to only what config cannot express.

C) Leave `config.toml` alone and override the red with more targeted CSS selectors against Streamlit's internal `data-testid` attributes.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 2
The sidebar navigation is currently `st.radio` with five... six entries. Even once the red is gone, a radio group reads as a form control rather than a menu — no hover state, no active highlight, no icons. Change it?

A) Keep `st.radio`, but style it as a proper menu: full-width hoverable rows, a filled/left-bordered active row, and the radio circles hidden. Navigation logic and `active_view` session state stay exactly as they are, so nothing downstream changes. *(Recommended — a clear visual menu with no structural risk and no change to the existing tests.)*

B) Replace it with a vertical stack of full-width `st.button` rows, one per view, with the active one visually pinned.

C) Replace it with Streamlit's native multipage navigation (`st.navigation` + `st.Page`). This is the most idiomatic result but restructures `main.py`'s single-entry-point dispatch and the session-state ownership described in `business-logic-model.md #1`.

D) Add icons to each menu entry as well as whichever styling option above you pick.

E) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 3
How far should "improve the design" go? This sets the scope of everything that follows.

A) **Chrome polish only** — colour/accent coherence, card treatment, spacing, typography, menu styling. No view is reorganised, no content moves, no chart changes.

B) **Chrome polish plus layout refinement** — everything in A, plus a consistent page header on each view, chart/table content wrapped in visible card containers, consistent section dividers, and consistent chart titling (today some titles come from Plotly and some from `st.subheader`). Content stays on the same views it is on now. *(Recommended — the visible weaknesses are mostly framing and rhythm rather than information architecture, and this stays comfortably inside the existing component boundaries.)*

C) **Full redesign** — everything in B, plus reorganising which content sits on which view, splitting the long Dashboard scroll into tabs, and reworking the sidebar's division of labour. This is the largest option and I would expect to reopen Unit 2 Functional Design for it.

D) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 4
The app background is a flat mid-grey `#e8e8e8`, inherited from the IBM Cloud reference. White cards sit on it with no border, no radius, and no padding, so they read as bare white rectangles rather than panels.

A) Lighten the background to a very light cool neutral (around `#f4f6fa`) and give cards a 1px subtle border with a small radius and internal padding. Cards then read as deliberate surfaces, and the whole app looks lighter. *(Recommended — the flat grey plus borderless white is the single biggest reason the app looks unfinished; this is also the closest match to the Carbon-style reference you asked for originally.)*

B) Keep `#e8e8e8` and only add the borders, radius, and padding to cards.

C) Lighten the background and use a soft drop shadow on cards instead of borders.

D) Leave background and cards as they are; restrict this change to the menu only.

E) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 5
Right now `h1`, `h2`, and `h3` are all `#0050e6` — the same bright blue as the interactive accent. Blue therefore means both "heading" and "clickable".

A) Move headings to the dark navy `#001d6c` and reserve `#0050e6` exclusively for interactive elements (accents, active menu row, links, buttons, focus). One colour, one meaning. *(Recommended — it also raises heading contrast: navy on a light background measures over 12:1 versus roughly 6:1 for the current blue.)*

B) Keep blue headings, and differentiate interactivity by weight and underline instead of hue.

C) Use navy for `h1`/`h2` but keep `h3` blue as a lighter sub-level.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 6
The Dashboard is one long scroll: KPI strip, donut and top-value bar side by side, full-width quadrant scatter, Decommission Candidates table, dependency heatmap, then two download buttons at the very bottom. In a live demo the download buttons in particular are easy to miss.

A) Keep the single scroll, but add clear section headers and dividers, and move the two export buttons up next to the KPI strip where they are visible without scrolling.

B) Keep the single scroll and section framing, and leave the export buttons where they are.

C) Split the Dashboard into tabs (for example Overview / Decommission Candidates / Dependencies), with exports on the Overview tab.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 7
The sidebar carries the navigation menu, the two scoring threshold sliders, a Guard Rule Parameters expander, a Reset button, and a Data Sources expander containing six file uploaders. It is long, and navigation sits above a lot of controls that only some views use.

A) Keep everything in the sidebar, but separate it into visually distinct blocks with dividers and small section captions, so navigation is clearly not part of the scoring controls. *(Recommended — the thresholds genuinely do affect every view, so they belong somewhere global; the problem is grouping, not placement.)*

B) Keep navigation in the sidebar and move the scoring thresholds into a control bar at the top of the main content area.

C) Keep everything where it is and collapse the scoring controls into an expander that starts closed.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 8
Two palette leftovers from the earlier restyle rounds, both real but both cosmetic:

- `warm_neutral` is now byte-identical to `app_background` (`#e8e8e8`), so the guard-rule badge that BR-P1 designed to sit on a warm tint is actually sitting on plain grey.
- `PALETTE["header"].permitted_uses` still advertises `"fill"`, but the third restyle iteration removed its last fill use; it is text and chart markers only now.

A) Fix both — give `warm_neutral` a genuine soft sand/amber tint so guard badges read as warnings again, and correct `header`'s `permitted_uses` metadata to match reality. Contrast recomputed for the new tint. *(Recommended — small, and it restores an intended signal rather than inventing a new one.)*

B) Fix only the stale `permitted_uses` metadata; leave the badge on grey.

C) Leave both as they are.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 9
Chart interiors are currently pure white with default Plotly gridlines, sitting on the grey page. Should chart styling be brought in line with whatever card treatment you chose in Q4?

A) Yes — align chart paper/plot backgrounds with the card colour, soften gridlines to a light neutral, and apply the palette to axis and annotation text so charts look native to the app rather than dropped in. Data colours (classification and risk) are untouched. *(Recommended.)*

B) Yes, and additionally restyle the threshold marker lines on the quadrant scatter and the DMK freeze line on the Gantt to use palette roles instead of the grey and terracotta literals currently hardcoded there.

C) No — leave charts exactly as they are.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 10
How should this be run through AI-DLC? Your six previous post-approval changes were all implemented directly against the built `presentation-app` unit, with `business-rules.md`, `frontend-components.md`, and `aidlc-state.md` updated afterwards and no gate reopened.

A) Same treatment — implement directly as a post-approval change to `presentation-app`, then update the functional-design documents and state, and rerun the full test suite. *(Recommended if you answered A or B to Q3, since neither changes a component boundary.)*

B) Reopen Unit 2 Functional Design properly: revise `business-rules.md` BR-P1/BR-P2 and `frontend-components.md` first, take an approval gate on the design, and only then generate code. *(Appropriate if you answered C to Q3.)*

C) Fix only the red native widget accent now (Q1) and defer every other design change to a later round.

D) Other (please describe after [Answer]: tag below)

[Answer]: A

---

**When you have filled in all ten answers, tell me you are done.** I will check the set for contradictions — Q3 and Q10 in particular have to agree on scope — raise a short clarification round if I find any, and otherwise write the requirements up and proceed.
