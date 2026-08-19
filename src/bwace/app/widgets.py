"""Reusable UI fragments. See business-rules.md BR-P4, BR-P9, BR-P10."""
from __future__ import annotations

from datetime import date

import streamlit as st

from bwace.engine.models import (
    Classification,
    Determinant,
    LandscapeKpis,
    ObjectAssessment,
    ScoringConfig,
    UsageRecord,
    ValidationReport,
    WaveConfig,
)
from bwace.app.theme import category_style


def kpi_strip(kpis: LandscapeKpis) -> None:
    cols = st.columns(4)
    cols[0].metric("Total Objects", kpis.total_objects)
    cols[1].metric("Total Storage", f"{kpis.total_storage_gb} GB")
    cols[2].metric("Decommission %", f"{kpis.decommission_pct:.1f}%")
    cols[3].metric("Reclaimable Storage", f"{kpis.reclaimable_storage_gb} GB")


def classification_badge(classification: Classification) -> None:
    style = category_style(classification.category)
    st.markdown(
        f"<span style='background-color:{style.colour}; color:{style.text_colour_on_fill}; "
        f"padding:4px 10px; border-radius:6px; font-weight:600;'>{style.icon} {style.label}</span>",
        unsafe_allow_html=True,
    )


_GUARD_LABELS = {
    Determinant.DORMANCY_CEILING: "Dormancy Ceiling",
    Determinant.ACTIVITY_FLOOR: "Activity Floor",
}


def guard_rule_badge(classification: Classification) -> None:
    if classification.determinant is Determinant.SCORE:
        return
    label = _GUARD_LABELS[classification.determinant]
    st.markdown(
        f"<span style='background-color:#f6eeee; color:#02462f; border:1px solid #9c4f1f; "
        f"padding:2px 8px; border-radius:4px; font-size:0.85em;'>\u26a0 {label}</span>",
        unsafe_allow_html=True,
    )


def dormancy_note(classification: Classification, usage: UsageRecord, reference: date) -> None:
    elapsed = (reference - usage.last_run_date).days
    if classification.is_dormant:
        st.markdown(
            f"<em>Dormant — last run {elapsed} days ago, {usage.monthly_executions} executions/month</em>",
            unsafe_allow_html=True,
        )
    if classification.is_active:
        st.markdown(
            f"<em>In active use — {usage.monthly_executions} executions/month "
            f"across {usage.distinct_users} users</em>",
            unsafe_allow_html=True,
        )


def derivation_table(assessment: ObjectAssessment) -> None:
    from bwace.app.frames import derivation_frame
    frame = derivation_frame(assessment)

    st.markdown(f"**Business Value — total {assessment.business_value.total:.1f}**")
    value_rows = frame[frame["axis"] == "business_value"]
    st.dataframe(
        value_rows[["dimension_label", "raw_display", "normalised", "weight", "contribution", "inherited_from"]],
        hide_index=True,
    )

    st.markdown(f"**Technical Effort — total {assessment.technical_effort.total:.1f}**")
    effort_rows = frame[frame["axis"] == "technical_effort"]
    st.dataframe(
        effort_rows[["dimension_label", "raw_display", "normalised", "weight", "contribution", "inherited_from"]],
        hide_index=True,
    )


def scoring_controls(current: ScoringConfig) -> ScoringConfig:
    st.markdown("**Scoring Thresholds**")
    value_threshold = st.slider(
        "Value threshold", 0, 100, int(current.value_threshold),
        help="Default: 33", key="sidebar-value-threshold",
    )
    effort_threshold = st.slider(
        "Effort threshold", 0, 100, int(current.effort_threshold),
        help="Default: 67", key="sidebar-effort-threshold",
    )
    with st.expander("Guard Rule Parameters"):
        dormancy_days = st.number_input(
            "Dormancy days", 1, 730, current.dormancy_days,
            help="Default: 180", key="sidebar-dormancy-days",
        )
        dormancy_executions = st.number_input(
            "Dormancy executions", 0, 100, current.dormancy_executions,
            help="Default: 5", key="sidebar-dormancy-executions",
        )
        activity_days = st.number_input(
            "Activity days", 1, max(1, dormancy_days - 1), min(current.activity_days, dormancy_days - 1),
            help="Default: 90", key="sidebar-activity-days",
        )
        activity_executions = st.number_input(
            "Activity executions", 0, 500, current.activity_executions,
            help="Default: 25", key="sidebar-activity-executions",
        )
    return ScoringConfig(
        value_threshold=value_threshold, effort_threshold=effort_threshold,
        dormancy_days=dormancy_days, dormancy_executions=dormancy_executions,
        activity_days=activity_days, activity_executions=activity_executions,
    )


def wave_controls(current: WaveConfig) -> WaveConfig:
    st.markdown("**Wave Configuration**")
    wave_count = st.slider("Wave count", 1, 10, current.wave_count, key="wave-planner-count")
    wave_months = st.slider("Wave duration (months)", 1, 12, current.wave_months, key="wave-planner-months")
    start_date = st.date_input("Start date", current.start_date, key="wave-planner-start-date")
    return WaveConfig(wave_count=wave_count, wave_months=wave_months, start_date=start_date)


def validation_panel(report: ValidationReport) -> None:
    if not report.issues:
        return
    for issue in report.issues:
        location = f"{issue.dataset}"
        if issue.field:
            location += f" / {issue.field}"
        if issue.record:
            location += f" / {issue.record}"
        message = f"**{issue.severity.value}** ({location}): {issue.message}"
        if issue.severity.value == "ERROR":
            st.error(message)
        else:
            st.warning(message)
