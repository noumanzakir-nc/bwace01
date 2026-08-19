"""Streamlit entry point. Sole owner of session state. See business-logic-model.md #1."""
from __future__ import annotations

import streamlit as st

from bwace.engine.config import DEFAULT_SCORING, DEFAULT_WAVES
from bwace.engine.export import classification_csv, wave_recommendation_json
from bwace.engine.loader import DATASET_FILES, load_bundled, load_with_overrides
from bwace.engine.models import ValidationReport
from bwace.engine.service import apply_config, compute_base
from bwace.app import theme, widgets
from bwace.app.views import dashboard, dependency_view, object_detail, scenario_compare, wave_planner

VIEW_NAMES = ("Dashboard", "Object Detail", "Dependencies", "Wave Planner", "Scenario Compare")

DATASET_LABELS = {
    "object_inventory": "Object Inventory",
    "usage_logs": "Usage Logs",
    "criticality": "Criticality Matrix",
    "dependencies": "Dependency Map",
    "data_volume": "Data Volume Metrics",
    "complexity": "Complexity Scores",
}


def _init_session_state() -> None:
    if "scoring_config" not in st.session_state:
        st.session_state["scoring_config"] = DEFAULT_SCORING
        st.session_state["wave_config"] = DEFAULT_WAVES
        st.session_state["scenarios"] = {}
        st.session_state["uploads"] = {}
        st.session_state["active_view"] = "Dashboard"
        st.session_state["last_report"] = ValidationReport()
        outcome = load_bundled()
        st.session_state["landscape"] = outcome.landscape


def _resolve_landscape() -> None:
    uploads = st.session_state["uploads"]
    if uploads:
        outcome = load_with_overrides(uploads)
    else:
        outcome = load_bundled()

    st.session_state["last_report"] = outcome.report
    if outcome.report.is_fatal:
        return
    st.session_state["landscape"] = outcome.landscape


@st.cache_resource(show_spinner=False)
def _cached_compute_base(fingerprint: str, _landscape):
    # cache_resource (not cache_data): BaseScores holds MappingProxyType fields
    # that pickle cannot serialize. The fingerprint string is the real cache
    # key (services.md #5.1); the leading underscore excludes _landscape from hashing.
    return compute_base(_landscape)


def _render_sidebar() -> None:
    with st.sidebar:
        st.title("BW-ACE")
        st.session_state["active_view"] = st.radio(
            "View", VIEW_NAMES, key="sidebar-view-nav",
            index=VIEW_NAMES.index(st.session_state["active_view"]),
        )

        new_scoring = widgets.scoring_controls(st.session_state["scoring_config"])
        st.session_state["scoring_config"] = new_scoring

        if st.button("Reset to Defaults", key="sidebar-reset-defaults"):
            st.session_state["scoring_config"] = DEFAULT_SCORING
            st.rerun()

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
                _resolve_landscape()
                st.rerun()


def main() -> None:
    theme.apply()
    _init_session_state()

    try:
        _render_sidebar()

        report = st.session_state["last_report"]
        widgets.validation_panel(report)

        landscape = st.session_state["landscape"]
        base = _cached_compute_base(landscape.fingerprint, landscape)
        result = apply_config(base, landscape, st.session_state["scoring_config"], st.session_state["wave_config"])

        active_view = st.session_state["active_view"]
        if active_view == "Dashboard":
            dashboard.render(result, landscape)
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "Download Classification CSV", classification_csv(result),
                    file_name="classification_report.csv", key="export-classification-csv",
                )
            with col2:
                import json
                st.download_button(
                    "Download Wave Plan JSON", json.dumps(wave_recommendation_json(result), indent=2),
                    file_name="wave_recommendation.json", key="export-wave-json",
                )
        elif active_view == "Object Detail":
            object_detail.render(result, landscape)
        elif active_view == "Dependencies":
            dependency_view.render(result, landscape)
        elif active_view == "Wave Planner":
            new_wave_config = wave_planner.render(result, landscape)
            st.session_state["wave_config"] = new_wave_config
        elif active_view == "Scenario Compare":
            scenario_compare.render(landscape)

    except Exception as exc:  # noqa: BLE001 - top-level boundary, must not leak a traceback
        st.error(f"Something went wrong: {exc}")


if __name__ == "__main__":
    main()
