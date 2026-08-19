# Build and Test Summary — BW-ACE

**Date**: 2026-08-18
**Scope**: Both units (`assessment-engine`, `presentation-app`), executed together as one deployable

---

## Build Status

- **Build tool**: `pip` + `setuptools`, editable install, single `pyproject.toml`
- **Build status**: **Success**, verified from a completely clean `.venv` (deleted and recreated for this stage, not reused from Code Generation)
- **Build artifacts**: `bwace` package installed in editable mode; no compiled artifacts (pure Python)
- **Build time**: not separately measured — dominated by network-dependent `pip install`, which was intermittent during this session (consistent with the environment's documented network intermittency) but completed successfully after a wait

---

## Test Execution Summary

### Unit Tests

- **Total tests**: 73 (56 `tests/engine`, 17 `tests/app`)
- **Passed**: 73
- **Failed**: 0
- **Coverage**: qualitative rather than a percentage — every pure engine function has direct tests; `test_reference_dataset.py` binds all 13 of Unit 1's Definition-of-Done criteria; every Unit 2 view is exercised via `AppTest`. No numerical line-coverage target was set in requirements.
- **Status**: **Pass**

### Integration Tests

- **Test scenarios**: 4 (Unit 2 consuming a real Unit 1 result across all views; threshold change round-trip; scenario comparison round-trip; export functions against a live result)
- **Passed**: 4 (realised as 6 automated tests, all passing)
- **Failed**: 0
- **Status**: **Pass**

### Performance Tests

| Requirement | Target | Actual | Status |
|---|---|---|---|
| NFR-5.1 (threshold recomputation) | < 500ms | avg 1.55ms, max 10.76ms | **Pass**, ~45x margin |
| NFR-5.2 (startup to first render) | < 10s | 3.04s | **Pass** |
| NFR-5.3 (headroom to ~1,000 objects) | responsive | 98.5ms cold / 94.0ms hot at 1,100 objects | **Pass**, with a caveat about dependency-graph size not scaling with object count in this synthetic test — see `performance-test-instructions.md` |

### Additional Tests

- **Contract tests**: N/A — no service contract exists; the only boundary is a Python function call within one process (`services.md` §1)
- **Security tests**: N/A — explicitly out of scope (requirements §3.9: no auth, no network exposure beyond localhost, opted out at Requirements Analysis)
- **E2E tests**: covered by the integration scenarios above; no separate E2E suite, since there is no multi-service or multi-session workflow to traverse beyond what `AppTest` already exercises
- **Accessibility tests**: `tests/app/test_theme_contrast.py` (6 tests) — WCAG AA contrast ratios recomputed and verified for every palette role, independently of the checks performed during Requirements Analysis and Unit 2 Functional Design

---

## What Was NOT Verified, and Why

Per the verification guideline's requirement to state what could not be checked rather than presenting assumptions as facts:

| Item | Why not verified | Risk if wrong |
|---|---|---|
| `run.sh` execution | This is a Windows machine; no Linux/macOS environment is available to run it | Low — written to the identical specification as `run.bat`, which was verified branch-by-branch (version check, venv-exists, provisioned-marker skip). The commands used (`python3`, POSIX test syntax, `.venv/bin/`) are standard and were checked by inspection, but never executed. |
| Offline / disconnected-network behaviour (NFR-3.1, S8.3b AC1) | This environment's network cannot be selectively disabled for a single process from within the available tooling | Low — the font fallback stack is a static CSS declaration (BR-P2.2) with no JavaScript conditional logic, so its correctness does not depend on runtime network state; verified by reading `theme.py` rather than by disconnecting a network. No other code path in the application makes a network call during rendering. |
| Real browser rendering / visual appearance | `AppTest` runs the Streamlit script without a browser and inspects element values, not pixel output | Low for logic correctness (which is what `AppTest` confirms); unknown for pixel-level polish (font rendering, spacing) — a manual browser check before the actual customer demo is recommended and is a reasonable Operations-phase or pre-demo activity, not a Construction-phase gap |
| A real ~1,000-object BW extract | No such dataset exists; a synthetic repetition of the bundled 22 objects was used instead | Low-Medium — see the caveat in `performance-test-instructions.md` about dependency graph size. The per-object computation that dominates cost was faithfully scaled; the area-level graph was not. |

---

## Overall Status

- **Build**: Success
- **All tests**: Pass (73/73 unit, 6/6 integration scenarios, 3/3 performance targets, 6/6 accessibility)
- **Ready for Operations**: Yes, with the four caveats above noted for anyone preparing the actual customer demo — none of them block readiness, but the browser-visual and `run.sh` items are worth a quick manual pass before presenting live.

## Next Steps

Ready to proceed to the Operations phase (currently a placeholder per the AI-DLC workflow). No blocking failures to address.
