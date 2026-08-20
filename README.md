# BW Object Assessment & Classification Engine (BW-ACE)

Analyzes BW metadata, usage logs, and dependencies to classify objects as **Decommission**, **Replicate As-Is**, or **Rebuild as Data Product**, and produces a migration wave plan. Demo dataset: 22 simulated BW objects across 12 Acme solution areas.

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

93 tests, including a reference-dataset suite that reproduces the validated classification distribution (5 Rebuild / 13 Replicate As-Is / 4 Decommission) against the bundled Acme data, plus 37 offline tests for the live OData connector.

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

## Live SAP OData mode

The app starts in **Demo Data** mode every time and works with no network, no credentials, and no configuration. Live mode is opt-in, read-only, and reached from the **Connection Settings** view.

### Setup

Copy `.env.example` to `.env` (git-ignored) and fill in your values, or set the same variables in your environment. Environment values always win over the file.

| Variable | Required | Purpose |
|---|---|---|
| `BWACE_ODATA_BASE_URL` | yes | Gateway host, e.g. `https://sapgw.example.corp:44300` |
| `BWACE_ODATA_USER` / `BWACE_ODATA_PASSWORD` | yes | HTTP Basic credentials |
| `BWACE_ODATA_SERVICE_ROOT` | no | Defaults to `/sap/opu/odata/sap` |
| `BWACE_ODATA_SERVICE_*` | no | One per dataset — see below |
| `BWACE_ODATA_CA_BUNDLE` | no | CA bundle path for a private or self-signed certificate authority |
| `BWACE_ODATA_TIMEOUT_SECONDS` | no | Per-request timeout, default 30 |
| `BWACE_ODATA_MAX_RECORDS` | no | Per-dataset retrieval cap, default 5000 |

Then: open **Connection Settings** → **Test Connection** → switch the mode to **Live OData**. The mode chip at the top of every view shows which data you are looking at and when it was fetched.

### The default service paths are placeholders

The paths shipped as defaults (`RSOD_CATALOG_SRV`, `RSOD_ADSO_SRV`, `RSPC_API_SRV`, `RSOD_USAGE_SRV`) came from the original feature request. **No SAP-delivered OData service by those names could be found.** SAP delivers the framework — Gateway services under `/sap/opu/odata/sap/<SERVICE>` with `$metadata` and entity-set collections — and the usual BW pattern is to create and activate such a service over BW metadata or a BW query in your own system. Point the `BWACE_ODATA_SERVICE_*` variables at whatever your Gateway actually exposes.

### What live mode does and does not cover

Five datasets come from OData: object inventory, complexity, data volume, dependencies (from process chains), and usage. The **criticality matrix is never live** — business criticality, migration priority, and downtime tolerance are business judgements rather than BW metadata, so they stay with the bundled or uploaded file. Every dataset's provenance (`live`, `uploaded`, `bundled`) is listed on the Connection Settings view and in the sidebar.

Behaviour worth knowing:

- **All-or-nothing.** If any of the five endpoints fails, the landscape you were looking at is kept and the failure is reported per endpoint. You never see a half-live landscape.
- **Manual refresh only.** Moving a threshold slider or changing view never re-contacts SAP.
- **Paging is followed** to the end of each collection, capped at `BWACE_ODATA_MAX_RECORDS` with a visible warning if the cap is hit.
- **Read-only.** Only HTTP GET is issued; there is no write path.
- **Credentials** are read from the environment, never stored, never displayed, and masked in error messages.
- **TLS verification cannot be disabled.** If the SAP host presents a self-signed or private-CA certificate, supply `BWACE_ODATA_CA_BUNDLE`.

**Verification status**: the connector is covered by 37 offline tests using recorded OData payloads and a stubbed transport, including paged responses, 401/404/500, timeouts, and malformed bodies. End-to-end connectivity against a real SAP system is unverified — expect to adjust the service paths and possibly the property names on first contact.

### Live-mode troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| Live mode cannot be selected | No successful connection test in this session | Use **Test Connection** first |
| `NOT_CONFIGURED` on every endpoint | Base URL or credentials missing | Set `BWACE_ODATA_BASE_URL`, `BWACE_ODATA_USER`, `BWACE_ODATA_PASSWORD`, then **Reload Configuration** |
| `TLS_ERROR` | Self-signed or private-CA certificate | Set `BWACE_ODATA_CA_BUNDLE` to a bundle that trusts the host. Verification cannot be turned off |
| `NOT_FOUND` on one endpoint | Service path does not exist in your Gateway | Correct the matching `BWACE_ODATA_SERVICE_*` variable |
| `UNAUTHORISED` | Wrong credentials, or the user lacks the service authorisation | Check the credentials and the Gateway service authorisations |
| `MALFORMED` | Payload shape or a property name differs from the expected mapping | Compare your entity-set properties with the field maps in `src/bwace/engine/odata.py` |
| Warning about the record cap | A collection is larger than `BWACE_ODATA_MAX_RECORDS` | Raise the cap; the assessment may otherwise be computed over partial data |

## Unit 2 — presentation app

The Streamlit UI: seven views (Dashboard, Object Detail, Dependencies, Wave Planner, Scenario Compare, Source Data, Connection Settings) driven entirely by Unit 1's `AssessmentResult`.

### Run the app tests

```
pytest tests/app
```

40 tests, including a contrast-ratio check against the WCAG AA threshold for every brand colour, smoke tests for every view using Streamlit's `AppTest` harness, and connection-mode tests covering the live path through a stubbed transport.

### Run everything

```
pytest tests
```

133 tests total (93 engine + 40 app). No test touches the network.
