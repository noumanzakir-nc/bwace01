"""Scenario Compare view. See business-logic-model.md #3.5."""
from __future__ import annotations

import streamlit as st

from bwace.engine.models import Landscape, Scenario
from bwace.engine.service import compare
from bwace.app import frames, widgets


def render(landscape: Landscape) -> None:
    widgets.page_header(
        "Scenario Compare",
        "Save configurations as named scenarios, then compare their parameters and outcomes side by side.",
    )

    st.subheader("Save Current Configuration")
    name = st.text_input("Scenario name", key="scenario-name-input")
    if st.button("Save Scenario", key="scenario-save-button"):
        if not name.strip():
            st.error("Scenario name must not be empty.")
        else:
            scenarios = dict(st.session_state.get("scenarios", {}))
            replaced = name in scenarios
            scenarios[name] = Scenario(
                name=name,
                scoring_config=st.session_state["scoring_config"],
                wave_config=st.session_state["wave_config"],
            )
            st.session_state["scenarios"] = scenarios
            st.success(f"Scenario '{name}' {'replaced' if replaced else 'saved'}.")

    scenarios = st.session_state.get("scenarios", {})
    if len(scenarios) < 2:
        st.info("Save at least two scenarios to compare them.")
        return

    st.divider()
    names = list(scenarios.keys())
    col1, col2 = st.columns(2)
    with col1:
        left_name = st.selectbox("Left scenario", names, key="scenario-compare-left")
    with col2:
        right_name = st.selectbox("Right scenario", names, index=min(1, len(names) - 1), key="scenario-compare-right")

    diff = compare(landscape, scenarios[left_name], scenarios[right_name])

    st.subheader("Scenario Configuration")
    config_frame = frames.scenario_config_frame(scenarios[left_name], scenarios[right_name])
    st.dataframe(config_frame, hide_index=True, key="scenario-compare-config-table")

    st.subheader("Distribution")
    dist_frame = frames.distribution_frame(diff)
    st.dataframe(dist_frame, hide_index=True, key="scenario-compare-distribution-table")

    st.subheader(f"Changed Objects ({len(diff.changed)})")
    if not diff.changed:
        st.info("No classifications differ between these scenarios.")
    else:
        rows = [
            {"object_id": c.object_id, left_name: c.left_category.value, right_name: c.right_category.value}
            for c in diff.changed
        ]
        st.dataframe(rows, hide_index=True)
