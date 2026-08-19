"""Dashboard view. See business-logic-model.md #3.1."""
from __future__ import annotations

import streamlit as st

from bwace.engine.models import AssessmentResult, Landscape
from bwace.app import charts, frames, widgets


def render(result: AssessmentResult, landscape: Landscape) -> None:
    st.header("Dashboard")

    widgets.kpi_strip(result.kpis)

    assessments = frames.assessments_frame(result, landscape)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(charts.classification_donut(assessments), width='stretch')
    with col2:
        st.plotly_chart(charts.top_value_bar(assessments, limit=10), width='stretch')

    st.plotly_chart(charts.quadrant_scatter(assessments, result.scoring_config), width='stretch')

    st.subheader("Decommission Candidates")
    candidates = frames.candidates_frame(result, landscape)
    if candidates.empty:
        st.info("No objects are currently classified for decommission.")
    else:
        total_storage = candidates["storage_gb"].sum()
        st.caption(f"Total reclaimable storage: {total_storage} GB")
        st.dataframe(
            candidates[["object_id", "description", "solution_area", "business_owner",
                        "last_run_date", "monthly_executions", "distinct_users",
                        "storage_gb", "rationale"]],
            hide_index=True,
        )

    st.subheader("Dependency Heatmap")
    heatmap_df = frames.heatmap_frame(result.graph)
    st.plotly_chart(charts.dependency_heatmap(result.graph, heatmap_df), width='stretch')
