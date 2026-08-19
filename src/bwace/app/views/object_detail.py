"""Object Detail view. See business-logic-model.md #3.2."""
from __future__ import annotations

import streamlit as st

from bwace.engine.models import AssessmentResult
from bwace.engine.scoring import reference_date
from bwace.app import widgets


def render(result: AssessmentResult, landscape) -> None:
    st.header("Object Detail")

    options = {f"{a.object_id} — {a.bw_object.description}": a.object_id for a in result.assessments}
    selection = st.selectbox("Select an object", list(options.keys()), key="object-detail-selector")
    object_id = options[selection]
    assessment = next(a for a in result.assessments if a.object_id == object_id)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Metadata**")
        st.write(f"ID: {assessment.object_id}")
        st.write(f"Type: {assessment.bw_object.object_type}")
        st.write(f"Solution area: {assessment.bw_object.solution_area}")
        st.write(f"Description: {assessment.bw_object.description}")

    with col2:
        st.markdown("**Classification**")
        widgets.classification_badge(assessment.classification)
        widgets.guard_rule_badge(assessment.classification)
        ref = reference_date(landscape)
        widgets.dormancy_note(assessment.classification, assessment.usage, ref)
        st.write(f"Business Value: {assessment.business_value.total:.1f}")
        st.write(f"Technical Effort: {assessment.technical_effort.total:.1f}")

    st.markdown("**Usage Metrics**")
    st.write(f"Last run: {assessment.usage.last_run_date}")
    st.write(f"Monthly executions: {assessment.usage.monthly_executions}")
    st.write(f"Distinct users: {assessment.usage.distinct_users}")
    st.write(f"Business owner: {assessment.usage.business_owner}")

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("**Incoming Dependencies**")
        if assessment.incoming:
            for edge in assessment.incoming:
                st.write(f"{edge.source} → {edge.target} ({edge.edge_type.value})")
        else:
            st.caption("None")
    with col4:
        st.markdown("**Outgoing Dependencies**")
        if assessment.outgoing:
            for edge in assessment.outgoing:
                st.write(f"{edge.source} → {edge.target} ({edge.edge_type.value})")
        else:
            st.caption("None")

    if "/" in assessment.bw_object.solution_area:
        areas = assessment.bw_object.solution_area.split("/")
        crits = [landscape.criticality[a].criticality for a in areas]
        avg = sum(crits) / len(crits)
        st.info(
            f"This object spans a composite solution area. Its criticality of {avg:.1f} is the "
            f"average of {areas[0]} ({crits[0]}) and {areas[1]} ({crits[1]})."
        )

    st.markdown("**Score Derivation**")
    widgets.derivation_table(assessment)

    st.markdown("**Rationale**")
    st.write(assessment.classification.rationale)
