"""Dependency view. See business-logic-model.md #3.3."""
from __future__ import annotations

import streamlit as st

from bwace.engine.models import AssessmentResult
from bwace.app import charts, frames


def render(result: AssessmentResult, landscape) -> None:
    st.header("Dependencies")

    heatmap_df = frames.heatmap_frame(result.graph)
    st.plotly_chart(charts.dependency_heatmap(result.graph, heatmap_df), width='stretch')

    st.plotly_chart(charts.dependency_network(result.graph), width='stretch')

    st.info(
        "ZMD1 appears as a node in its own right with incoming edges from PR and IN. "
        "Its scoring, however, uses inherited area averages rather than this node's own degree."
    )
