# Services — BW-ACE

**Stage**: INCEPTION — Application Design
**Decision reference**: Q5 = A — a single orchestration service returning one immutable result object

---

## 1. Why a Service Layer Exists Here

The execution plan justified Application Design on NFR-8.1: scoring logic must not live in presentation code. A rule like that is only as good as the mechanism enforcing it.

`AssessmentService` is that mechanism. Views receive a fully computed, immutable `AssessmentResult` and have nothing left to calculate. A view cannot accidentally perform scoring arithmetic because it never holds the inputs required to do so — it holds outputs.

Three further consequences follow, all of which serve approved requirements:

- **Scenario comparison becomes trivial** (FR-9.1, FR-9.2). Two configurations produce two results; diffing them is a comparison of two value objects rather than a re-orchestration of the pipeline.
- **Caching has a single obvious seam** (NFR-5.1, NFR-5.3). Because one component owns sequencing, the split between dataset-dependent and threshold-dependent work is expressed once.
- **The unit boundary is unambiguous.** Unit 2 depends on exactly one Unit 1 interface. Everything else in the engine is an implementation detail.

---

## 2. AssessmentService

### 2.1 Responsibilities

- Sequence the engine pipeline from validated landscape to final result
- Assemble and return the immutable `AssessmentResult`
- Compute landscape KPIs and the classification distribution
- Produce scenario diffs
- Expose the caching seam

### 2.2 Explicit non-responsibilities

- Does not read files. Loading is C3, invoked by C16 before the service is called.
- Does not render, format for display, or construct DataFrames.
- Does not own configuration state. Configuration is passed in; session state belongs to C16.
- Does not implement any scoring, classification, dependency, or wave rule itself. It delegates to C4–C9 and assembles their output.

### 2.3 Interface

| Method | Signature |
|---|---|
| `assess` | `(landscape: Landscape, scoring: ScoringConfig, waves: WaveConfig) -> AssessmentResult` |
| `compute_base` | `(landscape: Landscape) -> BaseScores` |
| `apply_config` | `(base: BaseScores, landscape: Landscape, scoring: ScoringConfig, waves: WaveConfig) -> AssessmentResult` |
| `compare` | `(landscape: Landscape, left: Scenario, right: Scenario) -> ScenarioDiff` |
| `kpis` | `(assessments: tuple[ObjectAssessment, ...], landscape: Landscape) -> LandscapeKpis` |

`assess` is the convenience path: it calls `compute_base` then `apply_config`. Callers wanting the caching benefit call the two separately.

---

## 3. The Result Object

`AssessmentResult` is the entire contract between Unit 1 and Unit 2.

```
AssessmentResult
├── assessments      tuple[ObjectAssessment, ...]   one per object, fully scored,
│                                                   classified, with rationale and
│                                                   resolved dependencies
├── distribution     Mapping[Category, int]         counts per category
├── graph            DependencyGraph                nodes, edges, degrees, area
│                                                   matrix, layout coordinates
├── wave_plan        WavePlan                       waves with risk, plus violations
├── kpis             LandscapeKpis                  headline landscape figures
├── scoring_config   ScoringConfig                  the configuration that produced this
├── wave_config      WaveConfig                     the wave settings that produced this
└── fingerprint      str                            identifies the source dataset
```

**Immutable throughout.** Every field is a frozen dataclass, a tuple, or a mapping treated as read-only. Safe to cache, safe to hold in session state, safe to pass to several views in one render pass.

**Self-describing.** Carrying `scoring_config` and `wave_config` means any result — including an exported one — states the settings that produced it, satisfying FR-10.3 without a separate mechanism.

---

## 4. Orchestration Sequence

### 4.1 Cold start

```
C16 app
  │
  ├─ 1. C3 loader.load_bundled()
  │        └─> LoadOutcome (Landscape + ValidationReport)
  │
  ├─ 2. if report.is_fatal: C14 widgets.validation_panel() and stop
  │
  ├─ 3. C10 service.compute_base(landscape)              [CACHED on fingerprint]
  │        ├─ C7  dependencies.build_graph()
  │        ├─ C4  normalisation.score_* per object per dimension
  │        └─ C5  scoring.business_value() / technical_effort()
  │        └─> BaseScores
  │
  ├─ 4. C10 service.apply_config(base, landscape, scoring, waves)
  │        ├─ C6  classification.classify() per object
  │        ├─ C6  classification.distribution()
  │        ├─ C10 service.kpis()
  │        └─ C8  waves.plan_waves()
  │        └─> AssessmentResult
  │
  └─ 5. C15 views.<selected>.render(result)
           ├─ C12 frames.*   domain objects -> DataFrames
           ├─ C13 charts.*   DataFrames -> Plotly figures
           └─ C14 widgets.*  render fragments
```

### 4.2 Threshold change (the hot path)

A user moves the Value or Effort threshold. Streamlit reruns the script.

```
C16 app
  ├─ 1. C3  loader                      SKIPPED — landscape held in session state
  ├─ 2. C10 compute_base()              CACHE HIT — fingerprint unchanged
  ├─ 3. C10 apply_config()              RECOMPUTED — cheap
  └─ 4. C15 views.render()              re-rendered
```

Steps 1 and 2 are the expensive ones and both are avoided. This is why NFR-5.1's 500 ms target is met by design rather than by the dataset happening to be small, and why NFR-5.3's 1,000-object headroom holds.

**The correctness argument**: `compute_base` takes no `ScoringConfig`. Normalisation bands, weights, and dimension scores are functions of the dataset alone. A threshold cannot change any dimension score — it can only change which side of a boundary a score falls on. Caching `compute_base` is therefore not an approximation; it is exact.

### 4.3 Dataset change

Upload or revert produces a landscape with a different `fingerprint`, so `compute_base` misses cache and recomputes in full. No manual invalidation is required — the key does the work.

### 4.4 Wave configuration change

Wave count, duration, or start date changes re-run `apply_config` only. Classification is unaffected but is recomputed regardless, as it is inexpensive and keeps a single code path.

### 4.5 Scenario comparison

```
C15 scenario_compare.render()
  └─ C10 service.compare(landscape, left, right)
           ├─ C10 compute_base(landscape)              CACHE HIT — shared by both
           ├─ C10 apply_config(base, ..., left)   -> AssessmentResult
           ├─ C10 apply_config(base, ..., right)  -> AssessmentResult
           └─ diff the two -> ScenarioDiff
```

Both scenarios share one cached base, so a comparison costs two cheap classification passes rather than two full pipelines.

---

## 5. Caching Strategy

**Decision reference**: Q4 = B.

| Stage | Cached | Key | Reason |
|---|---|---|---|
| `loader.load_bundled` | Yes | none needed | Bundled files never change during a session |
| `service.compute_base` | Yes | `landscape.fingerprint` | Dataset-dependent only. The primary win. |
| `service.apply_config` | No | — | Cheap, and must reflect live control values |
| `waves.plan_waves` | No | — | Depends on wave configuration, which is live |
| `charts.*` | No | — | Figure construction is cheap; caching figures risks stale rendering |

### 5.1 Why fingerprint rather than hashing the landscape

Streamlit's cache hashes function arguments. `Landscape` contains mappings and nested dataclasses, so hashing it would be both slow and fragile — a hashing failure on an unfamiliar type surfaces as a runtime error rather than a cache miss.

Computing an explicit content fingerprint at load time (C3 `fingerprint`) and keying the cache on that string avoids the problem entirely. The key is cheap, stable, and obviously correct: identical bytes give an identical key.

---

## 6. Session State Ownership

Owned solely by C16 `app`. No other component reads or writes Streamlit session state, which keeps C10–C9 pure and testable.

| Key | Type | Purpose |
|---|---|---|
| `landscape` | `Landscape` | Currently active dataset |
| `scoring_config` | `ScoringConfig` | Live thresholds and guard parameters |
| `wave_config` | `WaveConfig` | Live wave settings |
| `scenarios` | `tuple[Scenario, ...]` | Saved scenarios for comparison |
| `uploads` | `Mapping[str, bytes]` | Uploaded dataset payloads, for revert |
| `active_view` | `str` | Sidebar selection |

---

## 7. Error Propagation

No engine component raises for user-supplied data problems.

| Situation | Handling |
|---|---|
| Malformed upload | C3 returns `ValidationReport` with `is_fatal=True`; C16 shows it via C14 and retains the previous landscape |
| Referential warning | C3 returns `severity=WARNING`; C16 shows it and proceeds |
| Unexpected internal error | C16 boundary handler shows a readable message; no traceback surfaces (NFR-6.4) |

Programming errors — a malformed config constant, for instance — are allowed to raise, because they are defects rather than user input.

---

## 8. Requirement Coverage

| Requirement | How the service layer satisfies it |
|---|---|
| FR-6.1 | `kpis` computes the KPI strip figures |
| FR-9.1, FR-9.2 | `compare` returns a `ScenarioDiff` |
| FR-10.3 | Result carries its own configuration, so exports are self-describing |
| NFR-5.1 | `compute_base` cached; only classification recomputes on a threshold change |
| NFR-5.3 | Same, giving headroom independent of object count |
| NFR-6.4 | Errors returned as reports, never raised |
| NFR-8.1 | Views receive computed output and hold no scoring inputs |
| NFR-7.1 | Service methods are pure given a landscape, so directly unit-testable |
