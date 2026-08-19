# Code Generation Summary — Unit 1 `assessment-engine`

**Phase**: 🟢 CONSTRUCTION — Code Generation (Part 2)
**Plan executed**: `aidlc-docs/construction/plans/assessment-engine-code-generation-plan.md`

This is a documentation summary. No application code lives here — see `src/bwace/engine/` for the generated modules.

---

## 1. Modules Generated

| File | Component | Design source |
|---|---|---|
| `src/bwace/engine/models.py` | C1 `models` | `domain-entities.md`, `component-methods.md` §1 |
| `src/bwace/engine/config.py` | C2 `config` | `business-rules.md` BR-1 to BR-9, `component-methods.md` §2 |
| `src/bwace/engine/loader.py` | C3 `loader` | `business-rules.md` BR-11, `component-methods.md` §3 |
| `src/bwace/engine/normalisation.py` | C4 `normalisation` | `business-rules.md` BR-1 to BR-5, `component-methods.md` §4 |
| `src/bwace/engine/scoring.py` | C5 `scoring` | `business-rules.md` BR-2, BR-5, BR-6.1, `component-methods.md` §5 |
| `src/bwace/engine/classification.py` | C6 `classification` | `business-rules.md` BR-6, BR-12, `component-methods.md` §6 |
| `src/bwace/engine/dependencies.py` | C7 `dependencies` | `business-rules.md` BR-7, `component-methods.md` §7 |
| `src/bwace/engine/waves.py` | C8 `waves` | `business-rules.md` BR-8, BR-9, `component-methods.md` §8 |
| `src/bwace/engine/export.py` | C9 `export` | FR-10.1 to FR-10.3, `component-methods.md` §9 |
| `src/bwace/engine/service.py` | C10 `assessment_service` | `services.md`, `component-methods.md` §10 |

All ten modules follow the `component-methods.md` signatures. No component imports `streamlit`, `plotly`, or `pandas` (NFR-8.1 verified by inspection — only `networkx` appears, solely in `dependencies.py`).

## 2. Data Files Created

Six JSON files under `data/`, transcribed byte-faithfully from `requirements/requirement-document.txt` §3.1–3.6, with field names aligned to `domain-entities.md` (e.g. `data_volume` renamed to `data_volume_label`; dependency node/edge fields renamed to `node_id`/`node_type`/`edge_type` and given enum-compatible uppercase values).

## 3. Tests Generated

9 test files under `tests/engine/`, 56 tests total, all passing.

| File | Focus |
|---|---|
| `test_loader.py` | Load success, fingerprint stability/uniqueness, BR-11 validation failure shapes |
| `test_normalisation.py` | Band boundary inclusivity, recency tiers, composite-area averaging |
| `test_scoring.py` | Axis totals bounded 0–100, `SC100` worked example reproduced exactly |
| `test_classification.py` | Quadrant mapping, guard mutual exclusivity, `ScoringConfig` invariant, `IN200`/`IM100`/`TR200` worked examples |
| `test_dependencies.py` | `ALL→DMK` expansion to 12 edges, area matrix shape, deterministic layout |
| `test_waves.py` | Wave membership at W=5/3/7, exactly one violation, risk bands |
| `test_export.py` | CSV row count, JSON structure, configuration embedding |
| `test_service.py` | `compute_base`/`apply_config` split, `compare` diff, KPIs |
| `test_reference_dataset.py` | The 13 binding Definition-of-Done assertions from `unit-of-work.md` §2 |

## 4. Verification Performed

1. Clean editable install (`pip install -e .[dev]`) succeeded on the workspace's Python 3.14.0
2. Full engine run against the bundled dataset reproduced every figure in `business-rules.md` §13: 22 objects, 5/13/4 distribution, exact Rebuild/Decommission membership, `IN200` dormancy ceiling, `IM100` activity floor, `TR200`/`TM100` dormant-without-override, `FI100GC` flip at Effort 66, 12 DMK edges, exactly 1 violation (`LC`→`TM`), risk bands 1 Low/3 Medium/1 High
3. `pytest tests/engine` — 56/56 passed

## 5. Defects Found and Fixed During Generation

**Wave risk cross-wave dependency contribution (BR-9.2b).** The first implementation counted only the wave's own violations, doubled. Verification against `business-rules.md` §13's per-wave risk table (wave 2 expected 77.9/High) initially produced 65.4/Medium. Root cause: BR-9.2b requires counting *all* cross-wave edges from the wave's areas, not only violating ones, with violations counted twice and other cross-wave edges once. Rewrote `cross_wave_dependency_count` in `waves.py` to enumerate every area-to-area edge from the wave, band it, and weight violations at 2x. Re-verification reproduced all five wave risk scores and bands exactly.

## 6. Correction to an Approved Artifact

`domain-entities.md` §5 (`LandscapeKpis` worked figures) stated total storage as "596 GB". Summing `storage_gb` across all 22 records in the source data (and independently via `kpis()`) gives **604 GB**. The reclaimable figure (21 GB) and decommission percentage (18.2%) were unaffected and are unchanged. Corrected in `domain-entities.md` with an inline note; `test_reference_dataset.py::test_kpis_matches_reference`-equivalent assertion (in `test_service.py`) asserts 604.

## 7. Deferred to Unit 2 / Build & Test

- `src/bwace/app/` (C11–C16) — presentation layer, not yet generated
- `run.bat`, `run.sh` — depend on the Unit 2 Streamlit entry point
- Cross-unit integration and smoke tests — Build & Test phase
