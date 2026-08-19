# Performance Test Instructions — BW-ACE

## Purpose

Validate the two performance requirements that carry acceptance criteria: NFR-5.1 (sub-500ms threshold recomputation) and NFR-5.3 (responsive to ~1,000 objects), plus NFR-5.2 (10-second startup). This is a PoC for a customer demo — the performance bar is "feels instant to a presenter," not throughput under concurrent load, since the application has no concurrent-user scenario (NFR §3.9 explicitly excludes multi-user access).

## Performance Requirements

- **NFR-5.1**: full recomputation on a threshold change completes in under 500ms (target: feels instantaneous)
- **NFR-5.2**: application startup to first rendered view completes within 10 seconds
- **NFR-5.3**: the scoring engine remains responsive for datasets up to approximately 1,000 objects

There is no throughput or concurrent-user requirement — single presenter, single session, local process (§3.9).

## Setup Performance Test Environment

No special environment. These are measured directly against the installed package using `time.perf_counter()`, not a load-testing tool — appropriate given there is no concurrency dimension to this requirement.

## Test 1 — Threshold Recomputation (NFR-5.1)

### Method
Call `compute_base` once (simulating Streamlit's cache having already warmed it), then call `apply_config` repeatedly across a spread of Effort threshold values from 50 to 89, timing each call individually.

### Actual Results (executed for this document)

```
apply_config (hot path) over 40 runs:
  min=0.40ms max=10.76ms avg=1.55ms
```

**Result: PASS.** Average 1.55ms, worst case 10.76ms — both far under the 500ms target, with roughly 45x headroom even at the worst observed sample.

## Test 2 — Startup Time (NFR-5.2)

### Method
Time a full `streamlit.testing.v1.AppTest` run from script load through first render, using the actual `main.py` entry point (page config, theme CSS, session state init, bundled data load, `compute_base`, `apply_config`, Dashboard render).

### Actual Results

```
STARTUP_SECONDS=3.04
```

**Result: PASS.** 3.04 seconds against a 10-second target. This measurement includes Python module import time for `streamlit`, `plotly`, `pandas`, and `networkx`, which in a real browser session is paid once per process start — consistent with what NFR-5.2 is measuring.

## Test 3 — Headroom at ~1,000 Objects (NFR-5.3)

### Method
No real 1,000-object BW landscape exists to test against, so a synthetic dataset was constructed by replicating the 22 bundled objects 50 times with distinct IDs (1,100 objects total, same solution areas, dependency graph, and usage patterns repeated), then timing both engine phases.

### Actual Results

```
Synthetic dataset size: 1100 objects
compute_base (cold, ~1100 objects): 98.5ms
apply_config (hot path, ~1100 objects): 94.0ms
```

**Result: PASS.** Even the *cold* full pipeline (`compute_base`, which is the expensive phase and is normally cached) completes in under 100ms at 50x the bundled dataset's size. The *hot path* (`apply_config` alone, what a threshold change actually triggers) is 94ms — under the 500ms target from Test 1 even without caching's help, at a dataset size beyond NFR-5.3's stated ~1,000-object target.

### Caveat

This synthetic dataset repeats the same 12 solution areas and dependency graph 1 (the graph itself does not scale with object count — it is area-level, not object-level, per Unit 1's design). A real 1,000-object extract might have more solution areas and a larger dependency graph, which would affect `compute_base`'s graph-construction and layout-computation substeps more than this synthetic test captures. The per-object normalisation and scoring substeps, which dominate `compute_base`'s cost and do scale with object count, are faithfully represented.

## Performance Optimisation

Not needed — all three measurements pass with substantial margin. If a future real customer extract showed different results, the two-phase cache split (`compute_base` cached on fingerprint, `apply_config` always cheap) is the mechanism already in place to investigate first, per `services.md` §5.

## Out of Scope

- Concurrent user load (no such requirement exists — single local presenter session)
- Network latency (no network calls in the engine; NFR-3.1 requires offline capability, tested separately)
- Long-running stability / memory leak testing (not requested; a demo session is a single short-lived process)
