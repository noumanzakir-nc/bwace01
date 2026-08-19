"""Scenario Compare view. See business-logic-model.md #3.5."""
from __future__ import annotations

import streamlit as st

from bwace.engine.models import Landscape, Scenario
from bwace.engine.service import compare


def render(landscape: Landscape) -> None:
    st.header("Scenario Compare")

    st.markdown("**Save Current Configuration**")
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

    names = list(scenarios.keys())
    col1, col2 = st.columns(2)
    with col1:
        left_name = st.selectbox("Left scenario", names, key="scenario-compare-left")
    with col2:
        right_name = st.selectbox("Right scenario", names, index=min(1, len(names) - 1), key="scenario-compare-right")

    diff = compare(landscape, scenarios[left_name], scenarios[right_name])

    st.subheader("Distribution")
    col3, col4 = st.columns(2)
    with col3:
        st.write(f"**{left_name}**")
        st.write({c.value: n for c, n in diff.left_distribution.items()})
    with col4:
        st.write(f"**{right_name}**")
        st.write({c.value: n for c, n in diff.right_distribution.items()})

    st.subheader(f"Changed Objects ({len(diff.changed)})")
    if not diff.changed:
        st.info("No classifications differ between these scenarios.")
    else:
        rows = [
            {"object_id": c.object_id, left_name: c.left_category.value, right_name: c.right_category.value}
            for c in diff.changed
        ]
        st.dataframe(rows, hide_index=True)
