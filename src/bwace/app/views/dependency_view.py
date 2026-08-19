"""Dependency view. See business-logic-model.md #3.3."""
from __future__ import annotations

import streamlit as st

from bwace.engine.models import AssessmentResult
from bwace.app import charts, frames, widgets


def render(result: AssessmentResult, landscape) -> None:
    widgets.page_header(
        "Dependencies",
        "How the solution areas depend on one another, and on external and source systems.",
    )

    st.subheader("Dependency Matrix")
    heatmap_df = frames.heatmap_frame(result.graph)
    st.plotly_chart(charts.dependency_heatmap(result.graph, heatmap_df), width='stretch')

    st.divider()
    st.subheader("Dependency Network")
    st.caption("Shape indicates node type; colour is reserved for classification elsewhere in the app.")
    st.plotly_chart(charts.dependency_network(result.graph), width='stretch')

    st.divider()
    st.info(
        "ZMD1 appears as a node in its own right with incoming edges from PR and IN. "
        "Its scoring, however, uses inherited area averages rather than this node's own degree."
    )
