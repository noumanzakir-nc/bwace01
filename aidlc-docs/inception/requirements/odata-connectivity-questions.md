# OData Connectivity — Requirements Clarification Questions

**Stage**: INCEPTION - Requirements Analysis (Comprehensive depth)
**Feature**: Live SAP OData mode alongside the existing demo mode, plus a Connection Settings page
**Created**: 2026-08-19

Answer each question by putting a letter after the `[Answer]:` tag. If none of the options fit, choose the last option and describe what you want.

Every question carries my recommendation and the reason for it. Where I disagree with the source requirement I say so plainly rather than quietly implementing the option that sounds best.

---

## Read this before answering Q2

The requirement names three services as if SAP delivered them: `/RSOD_ADSO_SRV`, `/RSPC_API_SRV`, `/RSOD_CATALOG_SRV`.

I searched SAP's documentation and community sources and **could not find any SAP-delivered OData service with those names**. What SAP genuinely delivers is the *framework*: SAP Gateway publishes services under `/sap/opu/odata/sap/<SERVICE_NAME>`, each exposing `$metadata` and entity-set collections — and the documented BW pattern is that you **create** a service over BW metadata or a BW query, then activate it in the Gateway service catalogue.

So the analyst's framing is right in substance — OData over SAP Gateway is the modern, SAP-standard, read-only-friendly way in, and it is the same framework SAP Analytics Cloud consumes — but those three specific paths are almost certainly illustrative names rather than endpoints that will exist in Acme's system. If we hardcode them, the tool works in the slide deck and fails on first contact with the real landscape.

This is a requirements decision, not a technical detail, which is why it is Q2 rather than something I decided for you.

---

## Section 1 — Connection & Configuration

## Question 1
How should the demo/live mode switch behave?

A) **Explicit mode selector, demo is the default.** A "Data Source Mode" control with two states (Demo Data / Live OData). Live requires a successful connection test first; if the connection later fails, the app stays in live mode and shows the error rather than silently swapping data underneath the presenter. *(Recommended — a demo tool must never leave the audience unsure which data they are looking at, and a silent fallback mid-presentation is exactly the failure that erodes trust.)*

B) **Automatic**: attempt live on startup if credentials are present in the environment, fall back to demo silently if anything fails.

C) **Live mode is per-dataset**: each of the six datasets is independently switchable between bundled, uploaded, and live.

D) Other (please describe after the `[Answer]:` tag below)

[Answer]: A

## Question 2
How should the OData service paths be handled, given the finding above?

A) **Configurable, defaulting to the names as given.** Base URL plus six service/entity-set paths, each with a default matching the requirement (`RSOD_ADSO_SRV`, `RSPC_API_SRV`, `RSOD_CATALOG_SRV`, and so on), all overridable via environment variables and visible/editable on the Connection Settings page. The documentation states plainly that these are placeholder defaults to be pointed at the customer's actual activated services. *(Recommended — the demo still shows exactly the endpoint list the analyst promised, and the tool survives contact with a real system.)*

B) **Hardcode the paths exactly as specified** and treat any mismatch as a customer configuration problem.

C) **Discover services dynamically** from the Gateway service catalogue (`/sap/opu/odata/iwfnd/catalogservice;v=2/ServiceCollection`) and let the user pick which service feeds which dataset. Most faithful to a real deployment, materially more work.

D) Other (please describe after the `[Answer]:` tag below)

[Answer]: A

## Question 3
Which HTTP client should the engine use? This is the first new runtime dependency since inception.

A) **`httpx`** — pinned version, sync client, first-class timeout and TLS-context control, actively maintained. *(Recommended — timeouts are per-operation and explicit, which matters because a hung SAP Gateway would otherwise freeze the Streamlit rerun loop with no way out.)*

B) **`requests`** — the most familiar option, universally understood, still perfectly capable here.

C) **Standard library `urllib.request`** — adds no dependency at all, but leaves us hand-rolling Basic auth headers, OAuth token exchange, retries and TLS contexts.

D) Other (please describe after the `[Answer]:` tag below)

[Answer]: A

---

## Section 2 — Authentication & Secrets

## Question 4
Which authentication methods must be supported in this iteration?

A) **Basic authentication only**, with the code structured so OAuth can be added later without reshaping the connector. *(Recommended for a demo/PoC — Basic over HTTPS is what a customer sandbox will hand you on day one, and an OAuth flow we cannot test against a real identity provider is speculative code.)*

B) **Basic plus OAuth 2.0 client credentials** (client id/secret, token endpoint, token caching and refresh).

C) **Basic, OAuth 2.0 client credentials, and X.509 client certificates.**

D) Other (please describe after the `[Answer]:` tag below)

[Answer]: A

## Question 5
How are credentials supplied and stored?

A) **Environment variables only** (`BWACE_ODATA_BASE_URL`, `BWACE_ODATA_USER`, `BWACE_ODATA_PASSWORD`), optionally loaded from a git-ignored `.env` file at startup. Never written to disk by the app, never rendered back to the screen, masked in every error message and log line. The Connection Settings page shows *whether* each variable is set, never its value. *(Recommended — matches the requirement's "secure credential storage via environment variables" literally, and keeps secrets out of Streamlit session state, which is the thing most likely to end up in a screenshot.)*

B) **Environment variables plus in-app entry**: a password field on the Connection Settings page for a session-only override, held in session state, never persisted.

C) **Environment variables plus Streamlit's `secrets.toml`** as an alternative source.

D) Other (please describe after the `[Answer]:` tag below)

[Answer]: A

## Question 6
How should TLS certificate verification behave? SAP on-premise Gateway hosts often present self-signed or private-CA certificates.

A) **Verification on by default; a custom CA bundle path can be supplied** via environment variable. No way to disable verification. *(Recommended — but be aware this can block a demo against a sandbox with a self-signed certificate until someone produces the CA file.)*

B) **Verification on by default, with an explicit opt-out** (`BWACE_ODATA_VERIFY_TLS=false`) that surfaces a visible, permanent warning banner in the UI whenever it is active, plus support for a custom CA bundle. Pragmatic for sandbox demos, and the warning keeps the risk honest rather than hidden.

C) **Verification off by default** for demo convenience.

D) Other (please describe after the `[Answer]:` tag below)

[Answer]: A

---

## Section 3 — Data Mapping & Semantics

## Question 7
The five named endpoints do not map one-to-one onto BW-ACE's six datasets. In particular `criticality` (business criticality, migration priority, downtime tolerance per solution area) is a **business judgement matrix** with no plausible BW source, and `usage_logs` requires per-object aggregates (`last_run_date`, `monthly_executions`, `distinct_users`, `business_owner`) that a raw `Results` collection would have to be reduced into. How should the gap be handled?

A) **Hybrid by design.** Live mode fetches what BW can actually provide (object inventory/catalogue, complexity, data volume, dependencies, usage) and continues to use the bundled or uploaded `criticality` matrix, with per-dataset provenance shown in the UI as `live` / `bundled` / `uploaded`. Anything the live source cannot supply is labelled, never silently invented. *(Recommended — it is the only option that is both honest and demonstrable, and `Landscape.sources` already exists to carry exactly this labelling.)*

B) **All six datasets must come from live OData**; a missing `criticality` service is a connection failure.

C) **Live mode covers object metadata only** (inventory, complexity, volume, dependencies); usage and criticality always stay demo data.

D) Other (please describe after the `[Answer]:` tag below)

[Answer]: A

## Question 8
How should OData response fields be mapped onto BW-ACE's record schemas?

A) **A dedicated mapping module** with one documented, typed mapping per dataset — declared field-by-field in one place, unit-tested against recorded sample payloads, and reusing the existing validator functions in `loader.py` so live data is held to exactly the same standard as uploaded files. *(Recommended — reuse of the existing validation is the whole point: live data gets the same referential integrity checks and the same error panel, at no extra cost.)*

B) **A user-editable mapping file** (JSON/YAML) so field names can be re-pointed at a customer site without a code change. More flexible, and one more thing that can be misconfigured live.

C) **Parse `$metadata` (EDMX) and infer the mapping** from entity-set property names.

D) Other (please describe after the `[Answer]:` tag below)

[Answer]: A

## Question 9
What should `$metadata` be used for?

A) **Connection validation only** — the Connection Settings "Test Connection" button fetches `$metadata` per service and reports reachable / authenticated / not found / unauthorised per endpoint. Cheap, read-only, and exactly what the endpoint is good for. *(Recommended.)*

B) **Validation plus a schema report**: parse the EDMX and show which expected properties are present or missing on the customer's services, so a mapping mismatch is diagnosed before it becomes a runtime error.

C) **Not used at all** — test the connection by fetching one page of real data instead.

D) Other (please describe after the `[Answer]:` tag below)

[Answer]: A

## Question 10
How should collection retrieval handle size and OData paging?

A) **Follow paging to completion with a hard safety cap.** Honour OData V2 `__next` links (and `$skip`/`$top` where needed), keep fetching until exhausted, stop at a configurable maximum record count per dataset and warn clearly if the cap is hit. *(Recommended — a single unpaged GET silently truncates at the service's default page size, which would produce a quietly wrong assessment: the worst possible failure mode for this tool.)*

B) **Single request per collection** with a `$top` high enough for a demo; no paging.

C) **Paging plus server-side filtering** (`$select`/`$filter`) to fetch only the properties and rows BW-ACE actually needs.

D) Other (please describe after the `[Answer]:` tag below)

[Answer]: A

---

## Section 4 — Failure & Refresh Behaviour

## Question 11
What should happen when a live fetch fails partway through — say four of six datasets returned and the fifth times out?

A) **All-or-nothing, previous data retained.** The assessment is only replaced when a complete, valid landscape is assembled; on failure the app keeps showing what it had, with a clear per-endpoint error report on the Connection Settings page and a visible banner. *(Recommended — a half-live, half-stale landscape produces classifications that are individually plausible and collectively wrong, and nobody in the room would be able to tell.)*

B) **Best-effort**: use whatever arrived, fall back to bundled data for the rest, and label each dataset's provenance.

C) **Fail hard**: drop to an error state and show no assessment until the connection works.

D) Other (please describe after the `[Answer]:` tag below)

[Answer]: A

## Question 12
How should live data be refreshed?

A) **Manual only.** Fetch on entering live mode and on an explicit "Refresh from SAP" button; cache in session with a visible "last fetched" timestamp. *(Recommended — threshold sliders trigger a Streamlit rerun on every drag, and re-fetching from SAP on each one would be both slow and rude to the customer's Gateway. The existing fingerprint-keyed compute cache already makes this cheap.)*

B) **Manual plus a time-to-live** (configurable, default 15 minutes) after which the next interaction re-fetches.

C) **Automatic on a fixed interval** with a background refresh.

D) Other (please describe after the `[Answer]:` tag below)

[Answer]: A

---

## Section 5 — Frontend Presentation

## Question 13
Where does the Connection Settings page live, and how visible is the current mode?

A) **A seventh sidebar navigation entry ("Connection Settings")**, plus a persistent mode indicator visible on every view — a compact chip in the page header showing `Demo Data` or `Live: <host>` with the last-fetched time. *(Recommended, and consistent with how Source Data was added in the fourth iteration; the persistent chip matters because "which data am I looking at?" must never require navigating away to answer.)*

B) **Sidebar navigation entry only**, no persistent indicator on other views.

C) **A sidebar expander** in the existing Data block rather than a full page.

D) Other (please describe after the `[Answer]:` tag below)

[Answer]: A

---

## Section 6 — Scope, Quality & Extensions

## Question 14
No SAP system is reachable from this environment, so the live path cannot be executed end to end here. How should it be verified?

A) **Recorded-fixture tests against a stubbed transport.** Realistic OData V2 JSON payloads (including a `__next` paged response, a 401, a 404, a timeout, and a malformed body) fed through an injected transport, so every branch of the connector and mapper is tested deterministically and offline. Documented plainly as "connector logic verified; live connectivity requires a customer system". *(Recommended — this is genuinely verifiable, unlike anything involving a real endpoint, and it keeps the existing suite fully offline as NFR-3.2 requires.)*

B) **Fixture tests plus an optional live smoke test** that is skipped unless connection environment variables are present, for you to run against a real system later.

C) **Manual verification only**, no automated tests for the connector.

D) Other (please describe after the `[Answer]:` tag below)

[Answer]: A

## Question 15
How should this feature be treated in the AI-DLC workflow? It is a larger change than the recent UI iterations — it adds a component layer, a new dependency, and an external integration boundary.

A) **Full treatment**: Requirements → User Stories → Workflow Planning → Application Design (new components and their boundaries) → Functional Design for the affected units → Code Generation → Build and Test, with approval gates at each stage. Slowest, and it keeps the architecture documents accurate — they are currently the authoritative description of this system. *(Recommended — Application Design in particular, because a second data ingress alongside `loader.py` changes the shape of the engine, and that boundary is worth drawing before code exists.)*

B) **Condensed**: Requirements → Workflow Planning → Functional Design → Code Generation → Build and Test, skipping User Stories and Application Design, with component documentation updated in place afterwards.

C) **Minimal**: implement directly against these answers, as with the earlier post-approval UI changes, and update the affected documents afterwards.

D) Other (please describe after the `[Answer]:` tag below)

[Answer]: A

---

## Extension Opt-Ins (re-asked deliberately)

At inception you answered **No** to all three extensions, on the reasoning that BW-ACE is a demo/PoC rather than a production workload. That reasoning was sound then. It does not carry over unchanged: this feature makes the application handle credentials and open authenticated network connections into a customer system, which is precisely the situation those baselines exist for. Hence the re-ask.

## Question 16
Should security extension rules be enforced for this project?

A) Yes — enforce all SECURITY rules as blocking constraints (recommended for production-grade applications). *Note: even at "No", I will still not log or display secrets, will keep TLS verification on by default, and will keep credentials out of session state — that is baseline competence, not an extension. Answering Yes adds formal, auditable enforcement on top.*

B) No — skip all SECURITY rules (suitable for PoCs, prototypes, and experimental projects).

X) Other (please describe after the `[Answer]:` tag below)

[Answer]: B — carried forward, not recommended by me. See the note below.

## Question 17
Should the resiliency baseline be applied to this project?

**What this extension is.** Enabling it applies a set of **directional, design-time best practices** for building resilient systems, derived from the **AWS Well-Architected Framework (Reliability Pillar)** and resilience-review guidance. It steers requirements, design, and code toward fault tolerance, high availability, observability, and recoverability — covering 15 practice areas across business goals, change management, observability, high availability, disaster recovery, and continuous improvement.

**What this extension is NOT.** Enabling it does **not** make your workload production-ready, nor does it certify or guarantee any availability, RTO, or RPO target. It is a **starting point** that scaffolds good resiliency decisions early — it is not a substitute for a formal **AWS Well-Architected Review** of the built system.

Treat the output as a well-grounded **first draft of your resiliency posture** to build on and validate — not a finished, production-certified result.

A) Yes — apply the resiliency baseline as directional best practices and design-time guidance (recommended for business-critical workloads, as an informed starting point that you can validate and harden before go-live)

B) No — skip the resiliency baseline (suitable for PoCs, prototypes, and experimental projects where rapid iteration matters more than reliability). *Note: timeouts, a retry policy for transient failures, and explicit failure states are part of Q3/Q6/Q11 regardless of this answer — they are requirements of the feature, not extension extras.*

X) Other (please describe after the `[Answer]:` tag below)

[Answer]: B — carried forward, not recommended by me. See the note below.

## Question 18
Should property-based testing (PBT) rules be enforced for this project?

A) Yes — enforce all PBT rules as blocking constraints (recommended for projects with business logic, data transformations, serialization, or stateful components)

B) Partial — enforce PBT rules only for pure functions and serialization round-trips (suitable for projects with limited algorithmic complexity). *Would apply naturally to the OData response mapper, which is exactly a parse-and-transform function.*

C) No — skip all PBT rules (suitable for simple CRUD applications, UI-only projects, or thin integration layers with no significant business logic)

X) Other (please describe after the `[Answer]:` tag below)

[Answer]: C — carried forward, not recommended by me. See the note below.

---

## How these answers were filled in (2026-08-19)

User instruction: *"please use the recommended answers and continue"*.

**Q1-Q15 = A** in every case. Each of those fifteen carried an unambiguous recommendation in its option text, so the instruction maps cleanly onto them.

**Q16-Q18 are a different matter and I am not going to pretend otherwise.** Those three are extension opt-ins whose option text carries only a *conditional* recommendation — A is "recommended for production-grade applications", B is "suitable for PoCs". BW-ACE is a demo/PoC, so "the recommended answer" has no single value; it depends on which clause you think applies. Rather than guess and record the guess as your decision, I have **carried forward the inception answers unchanged** (Security No, Resiliency No, PBT No) and marked them as a carry-forward. The extension configuration in `aidlc-state.md` is therefore unchanged, and no extension rule files were loaded.

This has less practical effect than it might appear, and the requirements record it explicitly so it cannot be mistaken for an omission:

- The security behaviours are written as **binding non-functional requirements** (NFR-9.x in `requirements.md` §10.5) rather than as extension rules: credentials never in session state, never rendered, never logged; TLS verification always on; secrets masked in every error path. Answering "No" to the extension does not weaken any of those — it only means there is no formal extension-rule compliance audit at each stage.
- The resiliency behaviours that actually matter here — per-request timeouts, bounded retries on transient failure, explicit failure states, no partial-landscape replacement — come from Q3, Q10, Q11 and Q12 and are functional requirements of the feature.

**If you want the formal enforcement instead, say so** and I will flip Q16 to A (and optionally Q18 to B, which would put property-based tests on the OData response mapper — a genuinely good fit, since it is a pure parse-and-transform function). It is a cheap change now and a more expensive one after Code Generation.

---

## After you answer

Tell me you are done. I will then:

1. Check every answer for contradictions and ambiguities — particularly Q1 against Q11 (mode semantics against partial-failure semantics), Q4 against Q16 (auth scope against security enforcement), and Q7 against Q11 (hybrid provenance against all-or-nothing replacement), where an inconsistent pairing is easy to pick by accident. If I find one, you get a short clarification round rather than my guess.
2. Record the extension decisions in `aidlc-docs/aidlc-state.md` and load the full rule files for any extension you enable.
3. Write the requirements into `aidlc-docs/inception/requirements/requirements.md` as a new section, then stop for your approval.

No code will be touched before then.
