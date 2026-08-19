"""Wave Planner view. See business-logic-model.md #3.4."""
from __future__ import annotations

import streamlit as st

from bwace.engine.models import AssessmentResult, WaveConfig
from bwace.app import charts, frames, widgets


def render(result: AssessmentResult, landscape) -> WaveConfig:
    st.header("Wave Planner")

    new_wave_config = widgets.wave_controls(result.wave_config)

    gantt_df = frames.gantt_frame(result.wave_plan)
    st.plotly_chart(charts.wave_gantt(gantt_df, _dmk_freeze()), width='stretch')

    st.subheader("Wave Assignments")
    st.dataframe(
        gantt_df[["wave_label", "start_date", "end_date", "object_count", "areas", "risk_band"]],
        hide_index=True,
    )

    st.subheader("Risk Breakdown")
    risk_rows = []
    for wave in result.wave_plan.waves:
        risk_rows.append({
            "Wave": wave.number,
            "Complexity": wave.risk.complexity_contribution,
            "Cross-wave dependency": wave.risk.dependency_contribution,
            "Downtime": wave.risk.downtime_contribution,
            "DMK": wave.risk.dmk_contribution,
            "Total score": wave.risk.score,
            "Band": wave.risk.band.value,
        })
    st.dataframe(risk_rows, hide_index=True)

    st.subheader(f"Dependency Violations ({len(result.wave_plan.violations)})")
    if result.wave_plan.violations:
        for v in result.wave_plan.violations:
            st.warning(v.description)
    else:
        st.success("No dependency violations detected.")

    return new_wave_config


def _dmk_freeze():
    from bwace.engine.config import DMK_FREEZE_UNTIL
    return DMK_FREEZE_UNTIL
