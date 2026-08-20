"""Streamlit entry point. Sole owner of session state. See business-logic-model.md #1."""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure the src/ directory is on sys.path so that `bwace` is importable without
# an editable pip install. Required for Streamlit Community Cloud, which runs
# `pip install -r requirements.txt` but does not install the project itself.
_SRC = str(Path(__file__).resolve().parents[2])
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import streamlit as st

import os

from bwace.engine import odata
from bwace.engine.config import DEFAULT_SCORING, DEFAULT_WAVES
from bwace.engine.loader import DATASET_FILES, load_bundled, load_with_live, load_with_overrides
from bwace.engine.models import ValidationReport
from bwace.engine.service import apply_config, compute_base
from bwace.app import theme, widgets
from bwace.app.frames import DATASET_LABELS
from bwace.app.views import (
    connection_settings,
    dashboard,
    dependency_view,
    object_detail,
    scenario_compare,
    source_data,
    wave_planner,
)

VIEW_NAMES = (
    "Dashboard", "Object Detail", "Dependencies", "Wave Planner",
    "Scenario Compare", "Source Data", "Connection Settings",
)


def _init_session_state() -> None:
    if "scoring_config" not in st.session_state:
        st.session_state["scoring_config"] = DEFAULT_SCORING
        st.session_state["wave_config"] = DEFAULT_WAVES
        st.session_state["scenarios"] = {}
        st.session_state["uploads"] = {}
        st.session_state["active_view"] = "Dashboard"
        st.session_state["last_report"] = ValidationReport()
        # Live OData state. Demo is always the startup mode (FR-13.1), and the
        # fetched payloads are held so no rerun re-hits SAP (FR-14.7).
        st.session_state["data_mode"] = "demo"
        odata.load_env_file()
        st.session_state["odata_settings"] = odata.OdataSettings.from_env()
        st.session_state["odata_endpoints"] = ()
        st.session_state["odata_tested_ok"] = False
        st.session_state["live_payloads"] = {}
        st.session_state["live_fetched_at"] = None
        st.session_state["live_warnings"] = ()
        st.session_state["live_error"] = None
        outcome = load_bundled()
        st.session_state["landscape"] = outcome.landscape


def _resolve_landscape() -> None:
    uploads = st.session_state["uploads"]
    live = st.session_state["live_payloads"]
    if st.session_state["data_mode"] == "live" and live:
        outcome = load_with_live(live, uploads)
    elif uploads:
        outcome = load_with_overrides(uploads)
    else:
        outcome = load_bundled()

    st.session_state["last_report"] = outcome.report
    if outcome.report.is_fatal:
        return
    st.session_state["landscape"] = outcome.landscape


def _transport():
    settings = st.session_state["odata_settings"]
    return odata.transport_from_env(settings), settings


def _run_connection_test() -> None:
    transport, settings = _transport()
    if transport is None:
        st.session_state["odata_endpoints"] = ()
        st.session_state["odata_tested_ok"] = False
        st.session_state["live_error"] = (
            "Credentials are not set. Provide "
            f"{odata.ODATA_ENV_VARS['user']} and {odata.ODATA_ENV_VARS['password']} in the environment."
        )
        return
    results = odata.test_connection(settings, transport, secrets=odata.secret_values())
    st.session_state["odata_endpoints"] = results
    st.session_state["odata_tested_ok"] = all(r.ok for r in results)
    failures = [r for r in results if not r.ok]
    st.session_state["live_error"] = (
        None if not failures
        else f"{len(failures)} of {len(results)} endpoints failed the connection test. See the table below."
    )


def _run_live_fetch() -> None:
    transport, settings = _transport()
    if transport is None:
        st.session_state["live_error"] = "Credentials are not set, so no fetch was attempted."
        return
    outcome = odata.fetch_landscape(
        settings, transport, uploads=st.session_state["uploads"], secrets=odata.secret_values(),
    )
    st.session_state["odata_endpoints"] = outcome.endpoints
    st.session_state["live_warnings"] = outcome.warnings

    if not outcome.ok:
        # FR-14.6 - the working landscape is never partially replaced.
        detail = "; ".join(f"{f.dataset} ({f.status.value})" for f in outcome.failures)
        st.session_state["live_error"] = (
            f"Live fetch failed and the previously loaded data was kept. Failed: {detail}"
            if detail else
            "Live data was retrieved but failed validation; the previously loaded data was kept."
        )
        return

    st.session_state["live_payloads"] = dict(outcome.payloads)
    st.session_state["live_fetched_at"] = outcome.fetched_at
    st.session_state["live_error"] = None
    st.session_state["last_report"] = outcome.load.report
    st.session_state["landscape"] = outcome.load.landscape


def _handle_settings_action(action) -> None:
    if action is None:
        return
    if action.kind == "reload":
        odata.load_env_file()
        st.session_state["odata_settings"] = odata.OdataSettings.from_env()
        st.session_state["odata_tested_ok"] = False
        st.session_state["odata_endpoints"] = ()
    elif action.kind == "test":
        with st.spinner("Testing connection to SAP..."):
            _run_connection_test()
    elif action.kind == "refresh":
        with st.spinner("Fetching from SAP..."):
            _run_live_fetch()
        _resolve_landscape()
    elif action.kind == "set_mode":
        if action.mode == "live":
            if not st.session_state["odata_tested_ok"]:
                st.session_state["live_error"] = (
                    "Live mode needs a successful connection test first. Use Test Connection."
                )
                return
            st.session_state["data_mode"] = "live"
            if not st.session_state["live_payloads"]:
                with st.spinner("Fetching from SAP..."):
                    _run_live_fetch()
        else:
            st.session_state["data_mode"] = "demo"
        _resolve_landscape()
    st.rerun()


@st.cache_resource(show_spinner=False)
def _cached_compute_base(fingerprint: str, _landscape):
    # cache_resource (not cache_data): BaseScores holds MappingProxyType fields
    # that pickle cannot serialize. The fingerprint string is the real cache
    # key (services.md #5.1); the leading underscore excludes _landscape from hashing.
    return compute_base(_landscape)


def _render_sidebar() -> None:
    with st.sidebar:
        st.title("BW-ACE")

        # Three distinct blocks: navigation, global scoring controls, data
        # sources. The thresholds affect every view, so they stay global; the
        # dividers stop them reading as part of the menu.
        st.caption("Navigation")
        st.session_state["active_view"] = st.radio(
            "View", VIEW_NAMES, key="sidebar-view-nav",
            index=VIEW_NAMES.index(st.session_state["active_view"]),
            label_visibility="collapsed",
        )

        widgets.sidebar_section("Scoring")
        new_scoring = widgets.scoring_controls(st.session_state["scoring_config"])
        st.session_state["scoring_config"] = new_scoring

        if st.button("Reset to Defaults", key="sidebar-reset-defaults"):
            st.session_state["scoring_config"] = DEFAULT_SCORING
            st.rerun()

        widgets.sidebar_section("Data")
        with st.expander("Data Sources"):
            for name in DATASET_FILES:
                label = DATASET_LABELS[name]
                source = st.session_state["landscape"].sources.get(name, "bundled")
                st.caption(f"{label}: {source}")
                uploaded = st.file_uploader(
                    f"Replace {label}", type=["csv", "json"], key=f"sidebar-upload-{name}",
                )
                if uploaded is not None:
                    st.session_state["uploads"][name] = uploaded.getvalue()
                    _resolve_landscape()
                    if st.session_state["last_report"].is_fatal:
                        st.session_state["uploads"].pop(name, None)
                    st.rerun()

            if st.button("Revert to Demo Data", key="sidebar-revert-demo"):
                st.session_state["uploads"] = {}
                st.session_state["data_mode"] = "demo"
                _resolve_landscape()
                st.rerun()


def _check_password() -> bool:
    """Gate the app behind a simple password. Returns True if authenticated."""
    password = os.environ.get("APP_PASSWORD", "")
    if not password:
        return True  # No password configured — open access.
    if st.session_state.get("authenticated"):
        return True
    st.title("BW-ACE")
    st.caption("Enter the application password to continue.")
    entered = st.text_input("Password", type="password", key="login-password")
    if st.button("Enter", key="login-submit"):
        if entered == password:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    return False


def main() -> None:
    theme.apply()

    if not _check_password():
        return

    _init_session_state()

    try:
        _render_sidebar()

        mode = st.session_state["data_mode"]
        widgets.mode_indicator(
            mode=mode,
            host=st.session_state["odata_settings"].host or "not configured",
            fetched_at=st.session_state["live_fetched_at"],
            stale=mode == "live" and st.session_state["live_error"] is not None,
        )

        report = st.session_state["last_report"]
        widgets.validation_panel(report)

        landscape = st.session_state["landscape"]
        base = _cached_compute_base(landscape.fingerprint, landscape)
        result = apply_config(base, landscape, st.session_state["scoring_config"], st.session_state["wave_config"])

        active_view = st.session_state["active_view"]
        if active_view == "Dashboard":
            # Exports live inside the Dashboard view, directly under the KPI
            # strip, rather than below the full scroll where they were missable.
            dashboard.render(result, landscape)
        elif active_view == "Object Detail":
            object_detail.render(result, landscape)
        elif active_view == "Dependencies":
            dependency_view.render(result, landscape)
        elif active_view == "Wave Planner":
            new_wave_config = wave_planner.render(result, landscape)
            st.session_state["wave_config"] = new_wave_config
        elif active_view == "Scenario Compare":
            scenario_compare.render(landscape)
        elif active_view == "Source Data":
            source_data.render(landscape)
        elif active_view == "Connection Settings":
            action = connection_settings.render(
                settings=st.session_state["odata_settings"],
                mode=mode,
                endpoints=st.session_state["odata_endpoints"],
                tested_ok=st.session_state["odata_tested_ok"],
                fetched_at=st.session_state["live_fetched_at"],
                landscape=landscape,
                warnings=st.session_state["live_warnings"],
                error=st.session_state["live_error"],
            )
            _handle_settings_action(action)

    except Exception as exc:  # noqa: BLE001 - top-level boundary, must not leak a traceback
        st.error(f"Something went wrong: {exc}")


if __name__ == "__main__":
    main()
