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

---

## Running with Docker

Docker is the easiest way to run BW-ACE without installing Python or any dependencies locally. It works identically on Windows and Linux.

**Prerequisites**: [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows / macOS) or [Docker Engine](https://docs.docker.com/engine/install/) (Linux).

### Quick start

**Windows** — open a terminal in the project root and run:

```
docker-run.bat
```

**Linux / macOS** — open a terminal in the project root and run:

```
chmod +x docker-run.sh   # first time only
./docker-run.sh
```

Both scripts build the image automatically on first run and start the container. Open **http://localhost:8501** in your browser.

To force a rebuild (e.g. after pulling new source):

```
docker-run.bat --build        # Windows
./docker-run.sh --build       # Linux / macOS
```

### Using Docker Compose

```
docker compose up --build
```

On subsequent runs (no source changes) omit `--build`:

```
docker compose up
```

To stop the container press `Ctrl+C`, or run `docker compose down` from another terminal.

### Environment variables (live OData mode)

Copy `.env.example` to `.env` and fill in your values. Docker Compose and both helper scripts automatically pass the file to the container when it exists. The file is never baked into the image.

```
cp .env.example .env     # Linux / macOS
copy .env.example .env   # Windows
```

### Docker troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| "Docker was not found on PATH" | Docker Desktop is not installed or not running | Install Docker Desktop and start it |
| Port 8501 already in use | Another app is bound to that port | Stop the other app, or change the port: `docker run -p 8502:8501 bwace:latest` |
| Build fails with a pip error | Network issue during image build | Check connectivity and retry; `docker build --no-cache -t bwace:latest .` forces a clean build |
| Container starts but the browser cannot connect | Firewall or VPN blocking 8501 | Allow port 8501 in your firewall rules, or access from the same machine |
| Fonts look different | No internet access to the Google Fonts CDN inside the container | Expected and harmless — the UI falls back to system fonts automatically (NFR-3.2) |

---

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

## Deploy to Streamlit Community Cloud

The app is ready to deploy on [Streamlit Community Cloud](https://share.streamlit.io/) (free tier).

### Steps

1. Push this repository to a public GitHub repo (or a private repo if you have a paid plan).
2. Go to [share.streamlit.io](https://share.streamlit.io/) and sign in with your GitHub account.
3. Click **New app** and select:
   - **Repository**: your GitHub repo
   - **Branch**: `main` (or whichever branch you use)
   - **Main file path**: `src/bwace/app/main.py`
4. Under **Advanced settings**, set the Python version to **3.11**.
5. Click **Deploy**.

The app will install its dependencies from `requirements.txt` and start. The bundled demo data ships with the repo, so the app works immediately with no further configuration.

### Secrets (optional — for live OData mode)

If you want live SAP connectivity on the deployed app, open **App settings → Secrets** and paste TOML-formatted credentials:

```toml
BWACE_ODATA_BASE_URL = "https://sapgw.example.corp:44300"
BWACE_ODATA_USER = "your_user"
BWACE_ODATA_PASSWORD = "your_password"
```

Root-level keys in Streamlit secrets are exposed as environment variables, so the app's existing `os.environ` approach picks them up without code changes. Add any of the optional `BWACE_ODATA_*` variables from `.env.example` as needed.

### Password protection

To restrict access, add an `APP_PASSWORD` secret:

```toml
APP_PASSWORD = "your_chosen_password"
```

When set, visitors see a password prompt before the app loads. Leave it unset or blank for open access. For local development, add `APP_PASSWORD=something` to your `.env` file.

### Notes

- The `.python-version` file (containing `3.11`) hints at the target runtime. You can also select the version in the deploy dialog.
- The `pyproject.toml` at the root is used for local development (`pip install -e .`). Community Cloud uses `requirements.txt` which takes precedence per its dependency resolution order.
- The free tier has resource limits (1 GB RAM, apps sleep after inactivity). The BW-ACE demo dataset is small (22 objects) and well within these limits.
- If the app sleeps, the next visitor sees a brief "waking up" spinner before it resumes.

---

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
