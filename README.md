# BW Object Assessment & Classification Engine (BW-ACE)

Analyzes BW metadata, usage logs, and dependencies to classify objects as **Decommission**, **Replicate As-Is**, or **Rebuild as Data Product**, and produces a migration wave plan. Demo dataset: 22 simulated BW objects across 12 Arla solution areas.

## Unit 1 — `assessment-engine`

The scoring, classification, dependency, and wave-planning engine. Pure Python, no UI.

### Install

Requires Python 3.11+.

```
pip install -e .[dev]
```

### Run the engine tests

```
pytest tests/engine
```

56 tests, including a reference-dataset suite that reproduces the validated classification distribution (5 Rebuild / 13 Replicate As-Is / 4 Decommission) against the bundled Arla data.

### Try it

```python
from bwace.engine.loader import load_bundled
from bwace.engine.config import DEFAULT_SCORING, DEFAULT_WAVES
from bwace.engine.service import assess

outcome = load_bundled()
result = assess(outcome.landscape, DEFAULT_SCORING, DEFAULT_WAVES)
print(result.distribution)
```

---

## Running the Application

### Windows

```
run.bat
```

### Linux / macOS

```
chmod +x run.sh   # first time only
./run.sh
```

Either script:
1. Checks for Python 3.11 or newer on `PATH`, and stops with a clear message naming the version found if it is too old
2. Creates a `.venv` virtual environment if one does not already exist
3. Installs pinned dependencies on first run only (a marker file `.venv/.provisioned` skips reinstall on subsequent runs)
4. Launches the Streamlit application

The app opens in your default browser. If it does not, the script prints a local URL to open manually.

### Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| "Python was not found on PATH" | No Python interpreter is installed or discoverable | Install Python 3.11+ and ensure it is on `PATH` |
| "Found Python X.Y, but 3.11+ is required" | An older Python is the one found first on `PATH` | Install a newer Python, or adjust `PATH` ordering |
| Dependency install fails partway | Network issue during `pip install` | Delete `.venv` and re-run the script; check network connectivity |
| App starts but shows stale results after re-running the script | A `.venv` from a previous, incompatible version | Delete `.venv` and re-run to force a clean reinstall |
| Fonts look different from the brand mockup | No internet access to the Google Fonts CDN | Expected and harmless — the UI falls back to system fonts automatically (NFR-3.2) |

## Unit 2 — presentation app

The Streamlit UI: five views (Dashboard, Object Detail, Dependencies, Wave Planner, Scenario Compare) driven entirely by Unit 1's `AssessmentResult`.

### Run the app tests

```
pytest tests/app
```

17 tests, including a contrast-ratio check against the WCAG AA threshold for every brand colour and smoke tests for every view using Streamlit's `AppTest` harness.

### Run everything

```
pytest tests
```

73 tests total (56 engine + 17 app).
