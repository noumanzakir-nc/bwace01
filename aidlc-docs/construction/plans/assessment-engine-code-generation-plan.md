# Code Generation Plan — Unit 1 `assessment-engine`

**Phase**: 🟢 CONSTRUCTION
**Unit**: `assessment-engine` (components C1–C10, 14 stories, no dependencies on other units)
**Inputs**: `domain-entities.md`, `business-rules.md`, `business-logic-model.md`, `components.md`, `component-methods.md`, `services.md`, `unit-of-work.md`
**Prerequisites confirmed**: Functional Design approved. NFR Requirements, NFR Design, Infrastructure Design all skipped for this unit per the execution plan — no additional inputs from those stages.

---

## 1. Unit Context

**Stories implemented by this unit** (14, from `unit-of-work-story-map.md`): S1.1, S1.2, S1.3a, S2.1, S2.2, S2.3, S2.4a, S5.1, S6.1, S6.2, S6.4, S7.1, S7.2, S8.3a.

**Dependencies on other units/services**: none. This unit has no dependency on Unit 2 and only one external library outside the standard library (`networkx`, used solely in C7).

**Expected interface and contract**: outward `AssessmentResult` (via `AssessmentService.assess` / `compute_base` + `apply_config`); inward `Landscape`, `ScoringConfig`, `WaveConfig`. No component imports Streamlit, Plotly, or pandas.

**Database entities owned**: none — no database. The six bundled JSON datasets in `data/` are the persistent inputs.

**Service boundaries**: this is the entirety of Unit 1. C1–C10 as specified in `components.md` / `component-methods.md`.

---

## 2. Technology Decisions for This Stage (out of scope for Functional Design, in scope here)

| Decision | Choice | Reason |
|---|---|---|
| Python version | 3.11+ target, running on installed 3.14.0 | Adopted in Requirements Analysis §3.10, supersedes Q10=A's "3.12" |
| Package manager / build backend | `pyproject.toml` with `setuptools` build backend, `src/` layout | Q3=A (one project, two packages); standard, stable, no extra tool dependency |
| Test framework | `pytest` (verified 9.1.1 installable on this machine) | Project convention for Python; supports fixtures needed for reference-dataset tests |
| Dependency pinning | Exact versions pinned in `pyproject.toml`: `networkx==3.6.1` (engine), plus `streamlit==1.61.1`, `pandas==3.0.5`, `plotly==6.9.0` reserved for Unit 2 but declared now so one `pyproject.toml` installs everything in one pass | Empirically verified in Requirements Analysis; avoids a second pinning exercise at Unit 2 |
| JSON dataset embedding | Six files under `data/` at workspace root, read by `loader.py` via a path relative to the installed package's working directory | Per `unit-of-work.md` §4.1 — data is user-facing content, not a library resource |
| Immutability mechanism | `@dataclass(frozen=True)` with `tuple` collection fields; `Mapping` fields via `types.MappingProxyType` wrapping a `dict` | Matches Q2=B and the `models.py` C1 responsibility; stdlib only |
| Enum implementation | `enum.Enum` (stdlib) for `Category`, `Determinant`, `RiskBand`, `Severity`, `EdgeType`, `NodeType` | No external dependency needed |

**No hardcoded logic beyond this plan.** All business rule values (bands, weights, thresholds) come from `business-rules.md` and are transcribed into `config.py` / applied in the relevant module — nothing is invented in this plan beyond ordinary software structure (file names, function names matching `component-methods.md` signatures, test file layout).

---

## 3. Steps

### Step 1 — Project Structure Setup
- [x] Create `pyproject.toml` at workspace root: project metadata, `src` layout, pinned dependencies (`networkx==3.6.1`, `streamlit==1.61.1`, `pandas==3.0.5`, `plotly==6.9.0`, dev dependency `pytest`), Python `>=3.11`
- [x] Create `src/bwace/__init__.py`
- [x] Create `src/bwace/engine/__init__.py`
- [x] Create `tests/engine/__init__.py`
- [x] Create `data/` directory with the six bundled datasets, transcribed from requirement-document.txt §3.1–3.6, converted to the loader's expected JSON shape (object inventory, usage logs, criticality, dependencies, volume, complexity)
- [x] Create root `.gitignore` additions for Python artefacts (`__pycache__/`, `*.egg-info/`, `.pytest_cache/`, venv directories) — append to existing `.gitignore` if present

**Story mapping**: infrastructure for all 14 Unit 1 stories.

### Step 2 — Business Logic Generation: `models.py` (C1)
- [x] All frozen dataclasses from `domain-entities.md` §2–9 and `component-methods.md` §1: `BwObject`, `UsageRecord`, `AreaCriticality`, `VolumeMetrics`, `ComplexityMetrics`, `DependencyNode`, `DependencyEdge`, `Landscape`, `ScoringConfig`, `WaveConfig`, `Scenario`, `DimensionScore`, `AxisScore`, `Classification`, `ObjectAssessment`, `LandscapeKpis`, `AssessmentResult`, `DependencyGraph`, `WaveRisk`, `Wave`, `DependencyViolation`, `WavePlan`, `ValidationIssue`, `ValidationReport`, `LoadOutcome`, `ClassificationChange`, `ScenarioDiff`
- [x] Enumerations: `Category`, `Determinant`, `RiskBand`, `Severity`, `EdgeType`, `NodeType`
- [x] `ScoringConfig.__post_init__` asserts `activity_days < dormancy_days` (BR-6.4 invariant)
- [x] Type hints throughout per NFR-8.3; no docstrings beyond what is critical, per NFR-8.4

**Story mapping**: foundation for all 14 stories.

### Step 3 — Business Logic Generation: `config.py` (C2)
- [x] `VALUE_WEIGHTS`, `EFFORT_WEIGHTS` (BR-2, BR-5 axis weights)
- [x] `BANDS` — fixed absolute bands for usage frequency, distinct users, outgoing/incoming dependencies, complexity sub-attributes, volume sub-attributes (BR-2.1, BR-2.2, BR-2.4, BR-2.5, BR-5.1, BR-5.2)
- [x] `COMPLEXITY_SUBWEIGHTS` (40/30/20/10), `VOLUME_SUBWEIGHTS` (40/40/20)
- [x] `RECENCY_TIERS` (BR-3)
- [x] `DEFAULT_SCORING` (`ScoringConfig` defaults: value 33, effort 67, dormancy 180d/5exec, activity 90d/25exec)
- [x] `DEFAULT_WAVES` (`WaveConfig` defaults: 5 waves, 3 months, 2027-01-01)
- [x] `RISK_BANDS` (0–39 Low, 40–69 Medium, 70–100 High)
- [x] `RISK_WEIGHTS` (complexity 40%, cross-wave deps 25%, downtime 25%, DMK 10%)
- [x] `DMK_FREEZE_UNTIL` = 2028-01-01
- [x] `NON_AREA_NODE_TYPES` / area node identification constants for BR-8.4, BR-9.1b

**Story mapping**: S2.1, S2.2, S2.3, S6.1, S6.2, S6.4.

### Step 4 — Business Logic Generation: `loader.py` (C3)
- [x] `parse_dataset`, `validate_objects`, `validate_usage`, `validate_criticality`, `validate_volume`, `validate_complexity`, `validate_dependencies` per BR-11
- [x] `check_referential_integrity` (BR-11.7, BR-11.9, BR-11.10)
- [x] `fingerprint` (content hash of source bytes, used as cache key per Q4=B / services.md §5.1)
- [x] `load_bundled`, `load_with_overrides`
- [x] All failures return `ValidationReport`; never raises for user data problems (BR-11.1)

**Story mapping**: S1.1, S1.2, S1.3a.

### Step 5 — Business Logic Generation: `normalisation.py` (C4)
- [x] `apply_band`, `recency_factor`, `resolve_area_metrics` (composite-area averaging, BR-4.3)
- [x] `score_usage_frequency`, `score_distinct_users`, `score_criticality`, `score_outgoing_dependencies`, `score_incoming_dependencies`, `score_complexity`, `score_volume` per BR-1 through BR-5
- [x] No function accepts `ScoringConfig` (BR-10.1)

**Story mapping**: S2.1.

### Step 6 — Business Logic Generation: `scoring.py` (C5)
- [x] `business_value`, `technical_effort`, `score_all`, `reference_date` per BR-2, BR-5, BR-6.1

**Story mapping**: S2.1.

### Step 7 — Business Logic Generation: `classification.py` (C6)
- [x] `classify_by_score` (BR-6.2 quadrant mapping)
- [x] `is_dormant`, `is_active` (BR-6.3)
- [x] `classify` (full classification with guard rules and BR-6.6 determinant resolution)
- [x] `build_rationale` (BR-12 templates)
- [x] `distribution`

**Story mapping**: S2.2, S2.3, S2.4a.

### Step 8 — Business Logic Generation: `dependencies.py` (C7)
- [x] `expand_wildcards` (BR-7.2, `ALL → DMK` expansion)
- [x] `build_graph` (using `networkx`, BR-7.1, BR-7.3, BR-7.4)
- [x] `area_matrix` (BR-7.5)
- [x] `edges_for_object`, `constituent_areas` (BR-7.6, BR-4.2)
- [x] `compute_layout` (BR-7.7, deterministic — e.g. seeded/fixed layout algorithm, never random without a fixed seed)

**Story mapping**: S5.1.

### Step 9 — Business Logic Generation: `waves.py` (C8)
- [x] `assign_waves` (BR-8.1, BR-8.2 compression formula, BR-8.3 composite-area latest-wave rule)
- [x] `wave_dates` (BR-8.5)
- [x] `detect_violations` (BR-9.1, area-only, same-wave exclusion)
- [x] `wave_risk` (BR-9.2 four contributions), `risk_band` (BR-9.3)
- [x] `plan_waves` (orchestrates the above into a `WavePlan`)

**Story mapping**: S6.1, S6.2, S6.4.

### Step 10 — Business Logic Generation: `export.py` (C9)
- [x] `classification_csv`, `wave_recommendation_json`, `config_summary` per FR-10.1–10.3

**Story mapping**: S7.2.

### Step 11 — Business Logic Generation: `service.py` (C10)
- [x] `compute_base` (Phase A: graph, normalisation, axis scores — BR-10.1)
- [x] `apply_config` (Phase B: classification, distribution, KPIs, wave plan — BR-10.2)
- [x] `assess` (convenience: `compute_base` then `apply_config`)
- [x] `compare` (two `apply_config` calls over one shared `compute_base`, diff into `ScenarioDiff`)
- [x] `kpis` (`LandscapeKpis` computation)
- [x] `BaseScores` intermediate type (if not already in `models.py` — confirm placement, likely `models.py` since it is a data-holding type)

**Story mapping**: S1.1, S1.2, S2.4a, S7.1, S7.2, S8.3a.

### Step 12 — Business Logic Unit Testing
- [x] `tests/engine/test_loader.py` — valid load, each BR-11 validation failure shape, fingerprint stability/change
- [x] `tests/engine/test_normalisation.py` — band boundaries (inclusive-upper per BR-1.3), recency tiers, composite-area averaging
- [x] `tests/engine/test_scoring.py` — axis totals within 0–100, weight sum verification
- [x] `tests/engine/test_classification.py` — quadrant mapping, both guard predicates, mutual exclusivity assertion (BR-6.4), determinant vs predicate-flag distinction (BR-6.6, using `TR200`/`TM100` as the "fires but doesn't change outcome" cases)
- [x] `tests/engine/test_dependencies.py` — `ALL` expansion to 12 edges, degree computation, area matrix, deterministic layout (two calls produce identical coordinates)
- [x] `tests/engine/test_waves.py` — wave assignment at W=5/3/7 (BR-8.2 compression), violation detection (`LC`→`TM` only), risk contributions and banding
- [x] `tests/engine/test_export.py` — CSV row count and headers, JSON structure, config embedding
- [x] `tests/engine/test_service.py` — `compute_base`/`apply_config` split, cache-equivalence (same fingerprint → identical `BaseScores`), `compare` diff correctness
- [x] `tests/engine/test_reference_dataset.py` — the binding assertions from `unit-of-work.md` §2 Definition of Done: 22 objects, distribution 5/13/4, exact Rebuild/Decommission set membership, `IN200`/`IM100` guard overrides, `FI100GC` flip at Effort 66, 12 DMK edges, exactly 1 violation, risk bands 1 Low/3 Medium/1 High

**Story mapping**: NFR-7.1, NFR-7.2, all 14 stories (verification).

### Step 13 — Business Logic Summary
- [x] Write `aidlc-docs/construction/assessment-engine/code/summary.md` — markdown summary of generated modules, test coverage, and how each maps to the functional design documents. No application code in this file.

**No API Layer, Repository Layer, or Frontend Components steps** — Unit 1 is a pure computation library with no API, no persistence beyond JSON file reads, and no UI (confirmed in `application-design.md` and `unit-of-work.md` §2).

**No Database Migration Scripts** — no database exists.

### Step 14 — Documentation Generation
- [x] Add a "Unit 1 — assessment-engine" section to `README.md` at workspace root (created now, extended in Unit 2) covering: what the engine does, how to install (`pip install -e .`), how to run its tests (`pytest tests/engine`)

**Story mapping**: NFR-2.x (documented setup), supports S8.1 (deferred fully to Unit 2 for the run scripts).

### Step 15 — Deployment Artifacts Generation
- [x] None required at this stage. `run.bat` / `run.sh` (S8.1) depend on the Streamlit entry point, which does not exist until Unit 2. `pyproject.toml` (Step 1) is the only deployment-relevant artifact for this unit and is already covered.

---

## 4. Verification Plan (executed after generation, before presenting completion)

1. `pip install -e .` in a clean environment (or the workspace's existing Python) to confirm the package installs
2. `pytest tests/engine -v` — all tests must pass
3. Specifically confirm `test_reference_dataset.py` reproduces: 22 objects, 5/13/4 distribution, exact Rebuild/Decommission membership, `IN200` dormancy ceiling, `IM100` activity floor, `FI100GC` flip at Effort 66, 12 DMK edges, exactly 1 violation (`LC`→`TM`), risk bands 1 Low/3 Medium/1 High
4. If any deviation from the verified figures in `business-rules.md` §13 appears, treat it as a defect in this code generation (not a re-derivation) and fix the implementation to match the approved design

---

## 5. Artifacts

**Application code** (workspace root, never `aidlc-docs/`):
- `pyproject.toml`, `.gitignore` (amended)
- `data/*.json` (6 files)
- `src/bwace/__init__.py`, `src/bwace/engine/__init__.py`
- `src/bwace/engine/{models,config,loader,normalisation,scoring,classification,dependencies,waves,export,service}.py`
- `tests/engine/__init__.py`
- `tests/engine/test_{loader,normalisation,scoring,classification,dependencies,waves,export,service,reference_dataset}.py`
- `README.md` (created, Unit 1 section)

**Documentation** (`aidlc-docs/construction/assessment-engine/code/`):
- `summary.md`

---

## 6. Out of Scope (deferred to Unit 2 or Build & Test)

- Everything under `src/bwace/app/` (C11–C16)
- `run.bat`, `run.sh` (depend on the Unit 2 entry point)
- Integration/smoke tests spanning both units (Build & Test phase)
- Any Streamlit, Plotly, or pandas code
