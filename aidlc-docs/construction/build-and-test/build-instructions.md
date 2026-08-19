# Build Instructions — BW-ACE

## Prerequisites
- **Build tool**: `pip` with `setuptools>=69` (declared in `pyproject.toml`'s `[build-system]`)
- **Python**: 3.11 or newer. Verified on this machine's Python **3.14.0**.
- **Dependencies**: pinned exactly in `pyproject.toml` — `networkx==3.6.1`, `streamlit==1.61.1`, `pandas==3.0.5`, `plotly==6.9.0`; dev extra `pytest==9.1.1`
- **Environment variables**: none required
- **System requirements**: no specific memory/disk constraints beyond a standard Python install; no database, no Docker, no Node.js (NFR-2.3)

## Build Steps

### 1. Create a virtual environment
```
python -m venv .venv
```

### 2. Install dependencies (editable install, both units)
```
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -e ".[dev]"
```
On Linux/macOS, use `.venv/bin/python` in place of `.venv\Scripts\python.exe`.

### 3. Verify the build
```
.venv\Scripts\python.exe -c "import bwace.engine.service, bwace.app.main; print('install OK')"
```

### 4. Verify build success
- **Expected output**: `install OK`, no import errors
- **Build artifacts**: `bwace` package installed in editable mode; `src/bwace.egg-info/` generated locally (not committed — see `.gitignore`)
- **Common warnings**: none observed on a clean install

## Verification Performed for This Document

This build was executed from a **completely clean environment** as part of Build and Test (the previous `.venv` was deleted and recreated) to confirm the recorded steps are sufficient on their own, not merely a description of what had already been set up during Code Generation.

| Step | Result |
|---|---|
| `python -m venv .venv` | Succeeded |
| `pip install -e ".[dev]"` | Succeeded (network was intermittent during this run — see Troubleshooting; the command was simply re-checked after a wait rather than retried, and completed) |
| Import check | `install OK` printed, no errors |

## Troubleshooting

### Build fails with dependency errors
- **Cause**: intermittent network access during `pip install`, or a `pip` version too old to resolve the pinned set
- **Solution**: run `pip install --upgrade pip` first; retry the install command. If a specific package fails to resolve, confirm no stale `pip` cache is forcing an incompatible version with `pip cache purge`.

### Build fails with "Python 3.11+ required" or an import error naming a syntax feature
- **Cause**: an older Python interpreter is first on `PATH`
- **Solution**: install Python 3.11 or newer and either add it to `PATH` ahead of the older version or invoke it explicitly when creating the venv (e.g. `py -3.12 -m venv .venv` on Windows)

### `ModuleNotFoundError: No module named 'bwace'`
- **Cause**: the editable install did not run, or a different Python/venv is active than the one used for install
- **Solution**: re-run step 2 inside the same venv you are invoking Python from
