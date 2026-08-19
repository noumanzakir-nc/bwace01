# Business Rules — Unit 2 `presentation-app`

**Phase**: 🟢 CONSTRUCTION — Functional Design
**Decisions applied**: Q1 (Decommission colour, with a forced substitution — see BR-P1.2), Q2=A (sidebar radio), Q3=A (chip badge vs italic note), Q4=A (shape by node type), Q5=A (no scenario cap), Q6=A (six independent uploaders)

Rules are prefixed `BR-P` (presentation) to keep them distinct from Unit 1's `BR-` rules, which remain in force and are referenced rather than restated.

---

## BR-P1 — Palette

### BR-P1.1 Final palette

**Superseded 2026-08-19** — chrome palette (background, card, header, heading, accent, warm_neutral) re-themed on explicit user request to match the IBM Cloud cost estimator's visual style (`#161616`, `#ffffff`, `#e8e8e8`, `#0050e6`). The three `category_*` classification colours are unchanged — they are governed by NFR-4.4 as semantic business-rule colours, independent of the chrome restyle.

| Role | Hex | Permitted uses | Source |
|---|---|---|---|
| `app_background` | `#e8e8e8` | page background | User request 2026-08-19 |
| `card` | `#ffffff` | card and container background | User request 2026-08-19 |
| `header` | `#001d6c` | header bar, sidebar background (gradient start) | User request 2026-08-19, revised 2026-08-19 |
| `header_text` | `#ffffff` | text on `header` | User request 2026-08-19 |
| `heading` | `#0050e6` | headings, emphasis text | User request 2026-08-19 |
| `accent` | `#0050e6` | chart fills, borders, highlight blocks, sidebar gradient end, **text on light backgrounds** | User request 2026-08-19 |
| `warm_neutral` | `#e8e8e8` | decommission and warning callout backgrounds | User request 2026-08-19 |
| `category_rebuild` | `#02462f` | fill, border, text on light | NFR-4.4 (unchanged) |
| `category_replicate` | `#82ce71` | **fill and border only** — never text on light | NFR-4.4, NFR-4.3 (unchanged) |
| `category_decommission` | `#9c4f1f` | fill, border, text on light | NFR-4.4, BR-P1.2 (unchanged) |

### BR-P1.1a Verified contrast ratios — re-themed chrome palette

Computed with the same checker used in BR-P1.3, re-verified for the new roles:

| Foreground | Background | Ratio | AA normal text |
|---|---|---|---|
| `#001d6c` | `#ffffff` | 15.08:1 | Pass (AAA) |
| `#001d6c` | `#e8e8e8` | 12.31:1 | Pass (AAA) |
| `#ffffff` | `#001d6c` | 15.08:1 | Pass (AAA) |
| `#0050e6` | `#ffffff` | 6.38:1 | Pass |
| `#0050e6` | `#e8e8e8` | 5.21:1 | Pass |
| `#0050e6` | `#001d6c` | 2.36:1 | **Fail — not used for text on `header`** |
| `#9c4f1f` | `#e8e8e8` | 4.83:1 | Pass (unchanged rule, new background) |
| `#02462f` | `#e8e8e8` | 8.93:1 | Pass (unchanged rule, new background) |

Sidebar text remains white-on-`header` (unaffected), never blue-on-`header`. The sidebar background is a CSS gradient from `header` (`#001d6c`) to `accent` (`#0050e6`); because the gradient's later stops extend past the visible sidebar edge (`160deg`, stop at 140%), the actually-rendered region stays dark enough that the white `header_text` sidebar text keeps AA/AAA contrast throughout — verified visually, not by a single flat ratio, since gradients do not have one contrast value.

**Revision 2026-08-19 (same day, follow-up feedback)**: the initial `header` value `#161616` (near-black) was replaced with `#001d6c` (a dark blue, IBM Carbon "Blue 80") on user feedback that the near-black sidebar clashed visually with the rest of the blue/light theme. Contrast figures above reflect the revised value; the `#161616` → `#0050e6` gradient direction and mechanism are unchanged, only the dark endpoint moved into the same colour family as the light endpoint.

**Revision 2026-08-19 (second follow-up)**: user reported the sidebar still needed to be *lighter* overall. The sidebar background itself changed from a dark `header`-to-`accent` gradient to a light `sidebar_background` (`#eef4ff`, a pale blue tint) to `card` (`#ffffff`) gradient. `header` (`#001d6c`) is now used only as the sidebar **text** colour, not its fill — giving 13.66:1 contrast against `#eef4ff` and 15.08:1 against `#ffffff`, both AAA. This makes the sidebar visually consistent with the light, blue-accented body rather than standing apart as a dark panel. `header` remains defined (still used for `PALETTE["header"]`-based chart markers in `charts.py` and retained in case a future dark surface is reintroduced) but no longer fills any area of the UI by default.

### BR-P1.6 Theme switching disabled

Streamlit's built-in Settings-menu light/dark theme switcher recolours only native widget chrome; it does not touch the custom CSS this application injects via `theme.apply()` (backgrounds, sidebar gradient, heading colours). Toggling it therefore produced a broken, half-dark/half-light rendering with no coherent theme. `.streamlit/config.toml` sets `client.toolbarMode = "minimal"`, which hides the Settings menu's theme switcher entirely, since the application deliberately renders one single, fixed, WCAG-verified theme rather than supporting parallel light/dark variants.

### BR-P1.7 Native widget accents come from config, not CSS — supersedes BR-P1.1 and BR-P1.1a

**Defect found 2026-08-19** (frontend-design-refresh-questions.md Q1 = A). `.streamlit/config.toml` contained only a `[client]` block. With `theme.primaryColor` unset, Streamlit applies its built-in default primary `#ff4b4b` (`red70` in the bundled front-end palette) to every **native** widget accent: the selected dot of the sidebar navigation radio, slider handles and filled tracks, checkbox fills, and keyboard focus rings.

**Why the three preceding restyle rounds did not fix it**: all three edited the CSS injected by `theme.apply()`. Injected CSS cannot reach Streamlit's native widget accents, which are driven by the front-end theme object. Only a `[theme]` block in `config.toml` can. Each round therefore recoloured everything *around* the widgets and left the red widgets untouched.

**Rule**: any colour that Streamlit exposes as a theme config option is set in `.streamlit/config.toml`. The CSS in `theme.py` covers only what config cannot express (menu row styling, card borders, sidebar caption treatment, typography fallback).

Config now sets, for both the main area and the `[theme.sidebar]` namespace: `primaryColor`, `backgroundColor`, `secondaryBackgroundColor`, `textColor`, `linkColor`, `borderColor`, `dataframeBorderColor`, `dataframeHeaderBackgroundColor`, `showWidgetBorder`, `showSidebarBorder`, `baseRadius`.

**Verified** by calling Streamlit's own `_populate_theme_msg` and inspecting the `CustomThemeConfig` protobuf actually delivered to the browser — it reports `primary_color: "#0050e6"` for both namespaces. This checks the whole delivery path, not merely that the file parses.

**`theme.font` deliberately left unset.** It accepts only a generic family, a `[[theme.fontFaces]]` name, or a `"name:url"` pair — not a fallback stack. NFR-3.2 requires the full system-font chain so that offline use degrades gracefully, so typography remains owned by the CSS `font-family` declaration in `theme.py`. This is a documented deviation from the letter of Q1 = A, which listed `font` among the keys to set; the requirement outranks the suggestion, in the same way BR-P1.2 outranked a proposed hex.

### BR-P1.7a Live palette — supersedes the BR-P1.1 role table

`header`, `header_text`, and `heading` are **retired**. `header` and `heading` had drifted to carry the same navy `#001d6c` once Q5 = A moved headings off the accent blue, which would have re-created the exact duplicate-hex defect BR-P1.8 exists to prevent. They are consolidated into `ink`; `header_text` is renamed `text_on_accent`, which is what it had actually become.

| Role | Hex | Permitted uses | Source |
|---|---|---|---|
| `app_background` | `#f4f6fa` | page background | Q4 = A |
| `card` | `#ffffff` | card and container background | unchanged |
| `card_border` | `#d0d7e6` | card and widget borders | Q4 = A |
| `gridline` | `#e3e8f0` | chart gridlines and zero lines | Q9 = A |
| `sidebar_background` | `#eef4ff` | sidebar fill | unchanged |
| `sidebar_hover` | `#dce7ff` | hovered navigation row fill | Q2 = A |
| `ink` | `#001d6c` | headings, body text, sidebar text, chart node markers | Q5 = A, Q8 = A (replaces `header` + `heading`) |
| `ink_muted` | `#4c5a72` | captions, metric labels, chart axis ticks | Q4 = A, Q9 = A |
| `accent` | `#0050e6` | **interactive only** — selected nav row, links, buttons, focus, heatmap scale | Q5 = A |
| `text_on_accent` | `#ffffff` | text on `accent`, `category_rebuild`, `category_decommission` fills | renamed from `header_text` |
| `warm_neutral` | `#f9ecd9` | guard-rule and warning callout backgrounds | Q8 = A |
| `category_rebuild` | `#02462f` | fill, border, text on light | NFR-4.4 (unchanged) |
| `category_replicate` | `#82ce71` | **fill and border only** — never text on light | NFR-4.4, NFR-4.3 (unchanged) |
| `category_decommission` | `#9c4f1f` | fill, border, text on light | NFR-4.4, BR-P1.2 (unchanged) |

Verified contrast ratios for this palette are in `requirements.md` §3.4.2 and are re-asserted by `tests/app/test_theme_contrast.py`, which recomputes every ratio after re-validating the checker against all five WCAG anchors.

**Colour now means one thing.** `accent` is interactive, `ink` is text, the three `category_*` roles are classification. Before this round, `#0050e6` was simultaneously the heading colour and the interactive colour.

### BR-P1.8 One meaning, one value

| ID | Rule |
|---|---|
| BR-P1.8a | No two palette roles may share a hex value **if their `permitted_uses` overlap**. Roles with disjoint uses may share a value: `#ffffff` is legitimately both the `card` fill and `text_on_accent`. Asserted by test. |
| BR-P1.8b | `warm_neutral` must be a genuinely warm tint (red channel greater than blue) and must differ from both `app_background` and `card`. Asserted by test. |

**Why these exist.** Two silent regressions motivated them, both introduced by earlier restyles and both invisible until this round:

- `warm_neutral` had been set to `#e8e8e8`, byte-identical to `app_background`. Guard-rule badges, which BR-P9 designs to sit on a warm warning tint, were rendering on plain grey chrome. Restored to `#f9ecd9` (`#9c4f1f` text measures 5.08:1 on it).
- `PALETTE["header"].permitted_uses` still advertised `"fill"` after the second revision removed its last fill use, so the metadata that BR-P1.4b enforces was describing a use that no longer existed.

A fill-only-roles test now also asserts that surface roles do not claim text permissions.

### BR-P1.2 Decommission colour — substitution recorded

NFR-4.4 specified "a muted terracotta harmonising with `#f6eeee`" without a hex value. The functional design plan proposed `#b5651d` and answer A approved it.

**`#b5651d` was then measured and fails AA**: 3.99:1 on `#f2f7f1` and 4.34:1 on `#ffffff`, against the 4.5:1 minimum NFR-4.2 requires for normal text. The figures quoted in the plan's option A were asserted, not computed, and were wrong.

**`#9c4f1f` is used instead** — same burnt-terracotta family, one step deeper, passing on all three backgrounds with margin. NFR-4.2 is a binding requirement and takes precedence over a specific hex value that was only ever a suggestion; the substance of answer A (muted terracotta harmonising with the warm neutral) is preserved.

`#a85820` also passes but measures exactly 4.50:1 on `#f6eeee`, leaving no margin against rounding. Rejected for that reason.

### BR-P1.3 Verified contrast ratios

Computed with a checker validated against five known WCAG anchors (black-on-white 21:1, identical 1:1, `#767676`-on-white 4.542:1, `#595959`-on-white 7.005:1, red-on-white 3.998:1 — all matched exactly).

| Foreground | Background | Ratio | AA normal text |
|---|---|---|---|
| `#02462f` | `#f2f7f1` | 10.08:1 | Pass (AAA) |
| `#02462f` | `#ffffff` | 10.94:1 | Pass (AAA) |
| `#ffffff` | `#02462f` | 10.94:1 | Pass (AAA) |
| `#0d6a4b` | `#f2f7f1` | 6.08:1 | Pass |
| `#0d6a4b` | `#ffffff` | 6.60:1 | Pass |
| `#82ce71` | `#02462f` | 5.74:1 | Pass |
| `#82ce71` | `#ffffff` | 1.91:1 | **Fail — prohibited** |
| `#9c4f1f` | `#f2f7f1` | 5.45:1 | Pass |
| `#9c4f1f` | `#ffffff` | 5.91:1 | Pass |
| `#9c4f1f` | `#f6eeee` | 5.18:1 | Pass |
| `#ffffff` | `#9c4f1f` | 5.91:1 | Pass |

Requirements §3.4.1 has been corrected with these computed figures; every verdict there was unchanged, and two combinations proved better than first recorded.

### BR-P1.4 Palette enforcement

| ID | Rule |
|---|---|
| BR-P1.4a | No view, chart, or widget refers to a hex literal. All colour access is by `PaletteRole` name, resolved from C2 `config`'s `PALETTE` (NFR-8.2). |
| BR-P1.4b | A role whose `permitted_uses` excludes `text_on_light` must never be passed to a text-colour parameter. Asserted by test. |
| BR-P1.4c | Every colour pair actually used for text must be present in the BR-P1.3 table with a Pass verdict. A test recomputes the ratios rather than trusting the table. |

**Known outstanding BR-P1.4a exceptions**, recorded rather than silently fixed. Two hex literals remain in `charts.py`: the `#666666` dashed threshold lines on the quadrant scatter, and the `#9c4f1f` dotted DMK freeze line on the Gantt. Q9 = B offered to convert both to palette roles and the user chose Q9 = A, which scoped chart restyling to backgrounds, gridlines, and axis text only. Neither is a contrast risk (`#666666` on `#ffffff` measures 5.74:1) and `#9c4f1f` is numerically identical to `category_decommission`, so the deviation is cosmetic and confined to two annotation lines. Carry into a later round if BR-P1.4a is to hold without exception.

### BR-P1.5 Greyscale separability

Relative luminances of the three category colours: Rebuild `0.0460`, Decommission `0.1541`, Replicate `0.5008`. Pairwise luminance contrast: Rebuild/Replicate 5.74:1, Rebuild/Decommission 2.13:1, Replicate/Decommission 2.70:1.

All three remain distinguishable in greyscale. This is a **secondary** safeguard only — BR-P5 still requires a text label on every category indicator regardless, because NFR-4.5 is not satisfied by luminance separation alone.

---

## BR-P2 — Typography

| ID | Rule |
|---|---|
| BR-P2.1 | Primary font is `Inter`, loaded from a CDN. No font was named in requirements beyond "web font", so a neutral, highly legible sans-serif is chosen. |
| BR-P2.2 | The fallback stack is `-apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`, applied as a CSS `font-family` list so that failure to reach the CDN falls through silently (NFR-3.2). |
| BR-P2.3 | No layout dimension may depend on the web font being present. Metrics-dependent layout (fixed pixel heights sized to text) is prohibited (S8.3b AC2). |
| BR-P2.4 | The font link is never a blocking prerequisite for render. If it fails, the app renders in the fallback with no error and no unstyled element. |

---

## BR-P3 — Navigation and View Selection

| ID | Rule |
|---|---|
| BR-P3.1 | Navigation is a sidebar radio group, always visible (Q2=A, NFR-6.1). **Corrected 2026-08-19**: six options, not five — `Source Data` was added post-approval (BR-P13) and this rule was not updated at the time. |
| BR-P3.2 | The six view names are `Dashboard`, `Object Detail`, `Dependencies`, `Wave Planner`, `Scenario Compare`, `Source Data`. |
| BR-P3.3 | Selection is held in session state key `active_view`; changing it triggers a rerun that renders only the selected view. |
| BR-P3.4 | Sidebar controls that affect all views (scoring thresholds, guard parameters, data source, reset) sit **below** navigation and remain visible in every view, so a threshold can be moved without leaving the current view (S2.4b AC2). |
| BR-P3.5 | Wave configuration controls appear in the Wave Planner view body, not the global sidebar, because they affect only wave outputs. Exception to BR-P3.4, recorded deliberately. |
| BR-P3.6 | The radio group **presents** as a menu (Q2=A, FR-12.2): one full-width row per view, radio circle hidden, hover fill `sidebar_hover`, and the selected row filled `accent` with `text_on_accent` text and a 3px `ink` left border. The control remains `st.radio` and the group label is collapsed. |
| BR-P3.7 | BR-P3.6 is presentation only. The widget, its key `sidebar-view-nav`, the `active_view` session key, and the rerun behaviour in BR-P3.3 are unchanged, so no test or downstream consumer is affected. |
| BR-P3.8 | The sidebar is divided into three labelled blocks separated by rules — `Navigation`, `Scoring`, `Data` (Q7=A, FR-12.3). This preserves BR-P3.4's global placement of the scoring controls while making clear they are not part of the menu. |

---

## BR-P4 — Guard Badge and Dormancy Note

Implements Q3=A over Unit 1's BR-6.6c. This is the rule set that makes the Unit 1 determinant/predicate distinction visible.

### BR-P4.1 Display matrix

| ID | Condition | Rendered |
|---|---|---|
| BR-P4.1a | `determinant` is `DORMANCY_CEILING` | Chip badge: icon + "Dormancy Ceiling" |
| BR-P4.1b | `determinant` is `ACTIVITY_FLOOR` | Chip badge: icon + "Activity Floor" |
| BR-P4.1c | `determinant` is `SCORE` | No chip badge |
| BR-P4.1d | `is_dormant` is true | Italic note: "Dormant — last run {n} days ago, {m} executions/month" |
| BR-P4.1e | `is_active` is true | Italic note: "In active use — {m} executions/month across {u} users" |

Conditions are independent, not exclusive. An object may show a badge and a note together.

### BR-P4.2 Expected display on the bundled dataset

Derived from Unit 1's verified output, not from inspection:

| Object | Chip badge | Italic note |
|---|---|---|
| `IN200` | Dormancy Ceiling | Dormant |
| `IM100` | Activity Floor | In active use |
| `TR200` | *none* | Dormant |
| `TM100` | *none* | Dormant |
| all other 18 | *none* | *none* |

| ID | Rule |
|---|---|
| BR-P4.3 | Chip badges appear on exactly two objects at default configuration. A test asserts this against the rendered set, catching any drift from BR-6.6a. |
| BR-P4.4 | The badge names the rule; it never merely says "guard rule applied" (S2.3 AC5). |
| BR-P4.5 | Visual weight must differ: chip badges carry background fill, border, and icon; notes carry none of these. This is what communicates "this changed the outcome" versus "this is corroborating evidence" without requiring text to explain the difference. |
| BR-P4.6 | In the quadrant scatter, an object with a chip-badge determinant is drawn with a distinct marker outline so it does not appear to contradict the boundary lines (S3.3 AC3). `IN200` sits right of the Value boundary yet is Decommission; the outline is what makes that legible rather than looking like a defect. |

---

## BR-P5 — Never Colour Alone

| ID | Rule |
|---|---|
| BR-P5.1 | Every element conveying classification carries a text label. No exceptions (NFR-4.5). |
| BR-P5.2 | The donut chart labels each segment with its category name and count, not only a legend swatch (S3.2 AC1). |
| BR-P5.3 | The quadrant scatter uses a text legend naming all three categories. |
| BR-P5.4 | Risk bands render as a text label (`Low` / `Medium` / `High`) alongside any colour treatment. |
| BR-P5.5 | Category indicators additionally carry an icon (BR-P1 `CategoryStyle.icon`), giving a third channel beyond colour and text. |
| BR-P5.6 | Meaning must survive greyscale rendering. Verified by inspection during Code Generation and supported by BR-P1.5. |

---

## BR-P6 — Chart Rules

| ID | Rule |
|---|---|
| BR-P6.1 | Every chart has labelled axes where axes exist, a legend where more than one category appears, and hover text identifying the data point (NFR-4.6, S8.2 AC6). |
| BR-P6.2 | Quadrant scatter draws the **live** `value_threshold` and `effort_threshold` as boundary lines, redrawn on every threshold change (S3.3 AC5). Lines are cheap Plotly shapes and are never cached. |
| BR-P6.3 | Top-objects bar chart shows the top 10 by Business Value, descending. `SC100` is first on the bundled dataset (S3.2 AC2). |
| BR-P6.12 | Classification donut labels render inside the slices (`textposition="inside"`), with wider top/bottom figure margins, so labels never overflow the chart's card boundary. Added 2026-08-19 on user feedback that labels were clipped. |
| BR-P6.4 | Dependency heatmap is a 12×12 area grid using `graph.area_order` for both axes, labelled with area names (S5.1 AC1). |
| BR-P6.5 | Dependency network distinguishes node types by **marker shape** (Q4=A): solution areas circles, external and source squares, constraint diamond, shared object triangle. A legend names each shape's meaning (S5.1 AC2). |
| BR-P6.6 | Network node colour is **not** used to encode node type, deliberately, so that colour continues to mean classification everywhere in the application and never means two different things. |
| BR-P6.7 | Network edges show direction with arrow markers (S5.1 AC2). |
| BR-P6.8 | Network layout uses `graph.layout` coordinates from Unit 1 verbatim. Unit 2 computes no layout, guaranteeing the view does not shift between reruns (BR-7.7). |
| BR-P6.9 | Wave Gantt draws one horizontal bar per wave over its date range, in wave order, with readable date labels (S6.3 AC1). |
| BR-P6.10 | The DMK freeze marker is a vertical line anchored to the fixed date 2028-01-01 with a text annotation. It never moves when wave dates change (S6.3 AC3). |
| BR-P6.11 | An empty wave still renders its bar with a zero-count label, so `wave_count` > 5 does not produce a silently missing row. |
| BR-P6.13 | No chart carries an internal Plotly `title` (Q3=B, FR-12.6). Every chart is titled by its calling view with `st.subheader`, so a section title looks identical whether it heads a chart, a table, or text. This also removed a double title on the dependency heatmap, which previously showed "Dependency Heatmap" from `st.subheader` **and** "Dependency Matrix" from Plotly. The single title is now "Dependency Matrix" in both places it appears. |
| BR-P6.14 | Chart interiors use `card` for both plot and paper background, `gridline` for gridlines and zero lines, `card_border` for axis lines and network edges, `ink_muted` for tick labels, and `ink` for axis titles and legend text (Q9=A, FR-12.8). Applied centrally by `_style_axes`. Data colours are untouched and remain governed by NFR-4.4. |
| BR-P6.15 | The dependency heatmap colour scale runs `card` → `accent`. It previously ran white → `heading`; since `heading` was the same `#0050e6` now held by `accent`, the rendered scale is unchanged, but the role reference is now semantically correct — a data scale, not a heading. |
| BR-P6.16 | The DMK freeze annotation text is interpolated from the `freeze_until` argument rather than hardcoding "2028-01-01" in the label. Renders identically, since `DMK_FREEZE_UNTIL = date(2028, 1, 1)`, but the date can no longer drift out of step with the constant. Refines BR-P6.10. |

---

## BR-P7 — Scenario Handling

| ID | Rule |
|---|---|
| BR-P7.1 | A scenario is saved from the *current* `scoring_config` and `wave_config` under a user-supplied name (S7.1 AC1). |
| BR-P7.2 | No cap on saved scenario count (Q5=A). |
| BR-P7.3 | Scenario name must be non-empty. An empty name is rejected with an inline message; the save does not occur. |
| BR-P7.4 | Saving under an existing name replaces that scenario, since `Scenario` identity is `name`. The UI states that a replacement occurred. |
| BR-P7.5 | Comparison selects exactly two scenarios by name from a dropdown. Fewer than two saved scenarios disables the comparison control with an explanatory message rather than erroring. |
| BR-P7.6 | Comparison output is Unit 1's `ScenarioDiff`, rendered as: a configuration comparison table, a distribution comparison table, then the changed-object list with each object's category under each scenario (S7.1 AC2). |
| BR-P7.7 | An empty `changed` sequence renders an explicit "no classifications differ between these scenarios" statement, never a blank area (S7.1 AC4). |
| BR-P7.8 | The changed count is stated numerically (S7.1 AC3). |
| BR-P7.9 | The distribution comparison is rendered as a table (`st.dataframe`), one row per category present in either scenario, one column per scenario — never as a raw dict/JSON dump (post-approval addition, 2026-08-19). |
| BR-P7.10 | The configuration comparison table shows all nine adjustable parameters (six `ScoringConfig` fields, three `WaveConfig` fields) for both scenarios side by side, so a viewer can see *what changed* between scenarios, not only *what it did* (post-approval addition, 2026-08-19). |

---

## BR-P8 — Data Source and Upload

| ID | Rule |
|---|---|
| BR-P8.1 | Six independent upload controls, one per dataset, each accepting `.csv` or `.json` (Q6=A, FR-1.3). |
| BR-P8.2 | An upload writes its bytes into session state `uploads` under the dataset name, then triggers `loader.load_with_overrides(uploads)` — so uploading a second dataset does not discard the first. |
| BR-P8.3 | Each dataset displays a `bundled` or `uploaded` indicator, read from `landscape.sources` (S1.2 AC2). |
| BR-P8.4 | A single revert control clears `uploads` entirely and reloads bundled data, restoring the reference distribution (S1.2 AC3, FR-1.5). |
| BR-P8.5 | On a fatal `ValidationReport`, `landscape` in session state is **not** replaced. The previous dataset stays active and every view stays usable (S1.3b, BR-11.13). |
| BR-P8.6 | The offending upload is also removed from `uploads`, so a rerun does not retry a payload already known to be fatal and produce a repeating error. |
| BR-P8.7 | On a non-fatal report containing warnings, the upload **is** applied and warnings are displayed alongside the updated views. |

---

## BR-P9 — Validation Display

| ID | Rule |
|---|---|
| BR-P9.1 | Every issue in a `ValidationReport` is displayed naming its dataset, field, and record where present (S1.3b). |
| BR-P9.2 | `ERROR` issues render as error styling; `WARNING` issues as warning styling on `warm_neutral`. Severity is always named in text, not conveyed by colour alone. |
| BR-P9.3 | No Python traceback or raw exception text ever reaches the user (S1.3b, NFR-6.4). |
| BR-P9.4 | Warnings state how the affected object is treated in scoring — e.g. that a missing volume record scores that dimension 0 (S1.3b, BR-11.8). |
| BR-P9.5 | The panel renders inline at the top of the active view, not in a modal. Streamlit has no modal primitive appropriate for content of variable length. |
| BR-P9.6 | An unexpected internal exception anywhere in a view is caught at the C16 boundary and rendered as a readable message (NFR-6.4). Programming errors in engine constants are exempt — those are defects and should surface loudly in development. |

---

## BR-P10 — Control Rules

| ID | Rule | Bounds |
|---|---|---|
| BR-P10.1 | Value threshold slider | 0–100, default 33, step 1 |
| BR-P10.2 | Effort threshold slider | 0–100, default 67, step 1 |
| BR-P10.3 | Dormancy days | 1–730, default 180 |
| BR-P10.4 | Dormancy executions | 0–100, default 5 |
| BR-P10.5 | Activity days | 1–365, default 90, **and constrained below dormancy days** |
| BR-P10.6 | Activity executions | 0–500, default 25 |
| BR-P10.7 | Wave count | 1–10, default 5 |
| BR-P10.8 | Wave months | 1–12, default 3 |
| BR-P10.9 | Start date | any date, default 2027-01-01 |

| ID | Rule |
|---|---|
| BR-P10.10 | Every control displays its current value and its default (NFR-6.2, S2.4b AC1). |
| BR-P10.11 | The activity-days control's maximum is dynamically clamped to `dormancy_days - 1`, making `ScoringConfig`'s invariant unreachable through the UI rather than merely validated after the fact (SS-3). |
| BR-P10.12 | A single reset control restores every scoring and guard parameter to its documented default, restoring the reference distribution (S2.4b AC5, FR-3.4). |
| BR-P10.13 | Any control change triggers a rerun, which recomputes `apply_config` and re-renders. `compute_base` is not re-executed because the fingerprint has not changed (S8.3a, NFR-5.1). |

---

## BR-P11 — Object Detail Rules

| ID | Rule |
|---|---|
| BR-P11.1 | All 22 objects are selectable from a dropdown showing ID and description (S4.1 AC1). |
| BR-P11.2 | Metadata, classification with both axis scores, usage metrics, and dependencies in both directions all render for the selected object (S4.1 AC2–AC5). |
| BR-P11.3 | The derivation table shows all seven dimensions with raw value, normalised score, weight, and contribution, grouped under their axis totals (S4.2 AC1–AC2). |
| BR-P11.4 | A dimension with `inherited_from` set is marked as inherited and names the source area (S4.2 AC3). |
| BR-P11.5 | For `ZMD1`, the view states that its criticality of 82.5 is the average of Production (85) and Inventory Management (80) (S4.1 AC6). This is read from `inherited_from` naming both areas, not hardcoded. |
| BR-P11.6 | The rationale is rendered verbatim from `classification.rationale`. Unit 2 composes no rationale text — that is FR-3.5, owned by Unit 1 (BR-12). |
| BR-P11.7 | Contributions displayed must visibly sum to the axis total shown (S4.2 AC1). Rounding is applied at display only; the underlying sum is Unit 1's and is already asserted there. |

---

## BR-P12 — Determinism and Statelessness of Rendering

| ID | Rule |
|---|---|
| BR-P12.1 | No component other than C16 reads or writes session state. C12–C14 are pure functions of their arguments; C15 views receive `AssessmentResult` and render. |
| BR-P12.2 | No Unit 2 component computes a score, applies a threshold, classifies, walks the dependency graph for degree, or assigns a wave. All such values are read from `AssessmentResult` (NFR-8.1). |
| BR-P12.3 | Rendering the same `AssessmentResult` twice produces identical output. No randomness, no wall-clock reads, no layout computation. |
| BR-P12.4 | Figures and frames are never cached, so a configuration change cannot leave stale visuals on screen (`services.md` §5). |

---

## BR-P13 — Source Data View Rules (post-approval addition, 2026-08-19)

| ID | Rule |
|---|---|
| BR-P13.1 | The view exposes all six raw datasets (Object Inventory, Usage Logs, Criticality Matrix, Dependency Map, Data Volume, Complexity Scores) via a single dataset selector, regardless of whether each is bundled or uploaded. |
| BR-P13.2 | Each dataset renders as a plain, read-only table with every column and row exactly as loaded (post-validation, pre-scoring) — no derived or computed columns. |
| BR-P13.3 | The Dependency Map, being two record collections rather than one, splits into two tabs (Nodes, Edges) rather than one table. |
| BR-P13.4 | The current source (`bundled` or `uploaded`) is shown next to the dataset selector, consistent with the indicator already used in the sidebar Data Sources expander (`main.py` `DATASET_LABELS`). |
| BR-P13.5 | Each visible table has its own "Download as CSV" button, serialising exactly the displayed frame (BR-P12.3 — deterministic, no hidden state). |
| BR-P13.6 | This view reads only `Landscape`, never `AssessmentResult` — it cannot be affected by scoring thresholds, guard parameters, or wave configuration, and changing any of those does not trigger a rerender of this view's data (only `main.py`'s dispatch does, which is a no-op recompute here). |
| BR-P13.7 | No component other than C16 (`main.py`) reads or writes session state (BR-P12.1) — `source_data.render` takes `landscape` as its only argument and holds no state itself. |

---

## BR-P14 — Page Structure and Card Surfaces (post-approval refresh, 2026-08-19)

Implements Q3=B (chrome polish plus layout refinement), Q4=A (bordered cards on a lighter background), Q6=A (single scroll, exports raised).

| ID | Rule |
|---|---|
| BR-P14.1 | Every view opens with `widgets.page_header(title, subtitle)`, which renders `st.header(title)`, a one-line `st.caption` describing the view's purpose, and a rule (FR-12.4). |
| BR-P14.2 | `page_header` must emit `st.header` **first**, and `title` must equal the navigation entry name exactly. `test_smoke_views` asserts `at.get("header")[0].value == view` for all six views, so this is a hard constraint, not a convention. |
| BR-P14.3 | Major sections within a view are separated by `st.divider()` and titled with `st.subheader`. Sub-blocks inside a column keep bold markdown, because a subheader in a half-width column is visually too heavy. |
| BR-P14.4 | Metrics, dataframes, and Plotly charts render on `card` fill with a 1px `card_border` and an 8px radius, so they read as deliberate surfaces against the `app_background` page (FR-12.5). Applied by CSS selector, not per call site. |
| BR-P14.5 | Dashboard export buttons sit directly beneath the KPI strip, above all analytical content (Q6=A, FR-12.7). They previously rendered after the full five-section scroll, where they were easy to miss in a live demo. |
| BR-P14.6 | The export buttons moved from `main.py` into `dashboard.render`, since they are Dashboard content. Their keys `export-classification-csv` and `export-wave-json` are unchanged. `main.py` no longer imports `classification_csv` or `wave_recommendation_json`. |
| BR-P14.7 | Object Detail's section framing is consistent with the other views: `Usage Metrics`, `Dependencies`, `Score Derivation`, and `Rationale` are `st.subheader` sections with rules between them. The paired incoming/outgoing dependency columns are relabelled `Incoming` / `Outgoing` under a single `Dependencies` subheader, rather than repeating the word in both column titles. |

**Not verifiable by the test suite.** BR-P3.6 and BR-P14.4 are delivered by CSS selectors targeting Streamlit's internal DOM (`div[data-testid="stRadio"] label`, `div[data-testid="stMetric"]`, `div[data-testid^="stDataFrame"]`, `div[data-testid="stPlotlyChart"]`). `AppTest` exercises the Python render path only; it does not evaluate CSS or assert on rendered HTML. These selectors therefore need a human eye in a browser, and may need revision if a future Streamlit release renames a `data-testid`. The CSS is written to be additive, so a selector that stops matching degrades to unstyled default chrome rather than a broken layout.

---

## 13. Story Coverage

| Story | Rules |
|---|---|
| S1.3b | BR-P9.1–BR-P9.6, BR-P8.5, BR-P8.6 |
| S2.4b | BR-P10.1, BR-P10.2, BR-P10.10, BR-P10.12, BR-P10.13, BR-P3.4 |
| S3.1 | BR-P5.4, and `LandscapeKpis` rendering per `frontend-components.md` §3.1 |
| S3.2 | BR-P6.1, BR-P6.3, BR-P5.2 |
| S3.3 | BR-P6.2, BR-P4.6, BR-P5.3 |
| S3.4 | BR-P11.6, BR-P4.1, and the candidates frame |
| S4.1 | BR-P11.1, BR-P11.2, BR-P11.5 |
| S4.2 | BR-P11.3, BR-P11.4, BR-P11.6, BR-P11.7 |
| S6.3 | BR-P6.9, BR-P6.10, BR-P6.11 |
| S8.1 | Deferred to Code Generation (launch scripts) |
| S8.2 | BR-P1.x, BR-P5.x, BR-P6.1 |
| S8.3b | BR-P2.2, BR-P2.3, BR-P2.4 |
| S9.1 (post-approval addition) | BR-P13.1–BR-P13.7 |
| S7.1 (revised, post-approval, 2026-08-19) | BR-P7.9, BR-P7.10 added |
| S8.2 (revised, post-approval, 2026-08-19) | BR-P1.7, BR-P1.7a, BR-P1.8, BR-P3.6–BR-P3.8, BR-P6.13–BR-P6.16, BR-P14.1–BR-P14.7 |

All 12 Unit 2 stories have their presentation rules specified. S8.1 is the one story whose substance is launch scripting rather than rendering; its rules belong to Code Generation and are listed in `frontend-components.md` §8 for traceability. S9.1 is a post-approval enhancement, added outside the original 12-story inventory (see `aidlc-state.md` Post-Approval Change log).
