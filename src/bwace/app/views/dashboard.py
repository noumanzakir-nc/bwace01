"""Dashboard view. See business-logic-model.md #3.1."""
from __future__ import annotations

import json

import streamlit as st

from bwace.engine.export import classification_csv, wave_recommendation_json
from bwace.engine.models import AssessmentResult, Landscape
from bwace.app import charts, frames, widgets


def _exports(result: AssessmentResult) -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "Download Classification CSV", classification_csv(result),
            file_name="classification_report.csv", key="export-classification-csv",
            width="stretch",
        )
    with col2:
        st.download_button(
            "Download Wave Plan JSON", json.dumps(wave_recommendation_json(result), indent=2),
            file_name="wave_recommendation.json", key="export-wave-json",
            width="stretch",
        )


def render(result: AssessmentResult, landscape: Landscape) -> None:
    widgets.page_header(
        "Dashboard",
        "Portfolio-level view of the BW landscape under the current scoring configuration.",
    )

    widgets.kpi_strip(result.kpis)
    _exports(result)

    assessments = frames.assessments_frame(result, landscape)

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Classification Summary")
        st.plotly_chart(charts.classification_donut(assessments), width='stretch')
    with col2:
        st.subheader("Top 10 by Business Value")
        st.plotly_chart(charts.top_value_bar(assessments, limit=10), width='stretch')

    st.divider()
    st.subheader("Business Value vs Technical Effort")
    st.caption("Thresholds are the dashed lines. Ringed markers were set by a guard rule, not by score.")
    st.plotly_chart(charts.quadrant_scatter(assessments, result.scoring_config), width='stretch')

    st.divider()
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

    st.divider()
    st.subheader("Dependency Matrix")
    heatmap_df = frames.heatmap_frame(result.graph)
    st.plotly_chart(charts.dependency_heatmap(result.graph, heatmap_df), width='stretch')
