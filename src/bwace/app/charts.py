"""Plotly figure construction. See business-rules.md BR-P6."""
from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.graph_objects as go

from bwace.engine.models import Category, DependencyGraph, Determinant, NodeType, ScoringConfig
from bwace.app.theme import FONT_STACK, category_style, palette

_LAYOUT_TEMPLATE = dict(
    font=dict(family=FONT_STACK, size=13),
    margin=dict(l=40, r=20, t=40, b=40),
    plot_bgcolor="#ffffff",
    paper_bgcolor="#ffffff",
)

_NODE_TYPE_SYMBOL = {
    NodeType.SOLUTION_AREA: "circle",
    NodeType.EXTERNAL: "square",
    NodeType.SOURCE: "square",
    NodeType.CONSTRAINT: "diamond",
    NodeType.SHARED_OBJECT: "triangle-up",
}

_NODE_TYPE_LABEL = {
    NodeType.SOLUTION_AREA: "Solution area",
    NodeType.EXTERNAL: "External system",
    NodeType.SOURCE: "Source system",
    NodeType.CONSTRAINT: "Constraint",
    NodeType.SHARED_OBJECT: "Shared object",
}


def classification_donut(frame: pd.DataFrame) -> go.Figure:
    counts = frame["category"].value_counts()
    labels = [category_style(c).label for c in counts.index]
    colours = [category_style(c).colour for c in counts.index]
    text = [f"{label}: {count}" for label, count in zip(labels, counts.values)]
    fig = go.Figure(data=[go.Pie(
        labels=labels, values=counts.values, hole=0.5,
        marker=dict(colors=colours), text=text, textinfo="text",
        hovertemplate="%{label}: %{value} objects<extra></extra>",
    )])
    fig.update_layout(**_LAYOUT_TEMPLATE, title="Classification Summary", showlegend=True)
    return fig


def top_value_bar(frame: pd.DataFrame, limit: int = 10) -> go.Figure:
    top = frame.sort_values("business_value", ascending=False).head(limit)
    colours = [category_style(c).colour for c in top["category"]]
    fig = go.Figure(data=[go.Bar(
        x=top["object_id"], y=top["business_value"], marker_color=colours,
        text=top["category_label"], hovertemplate="%{x}: Value %{y:.1f}<br>%{text}<extra></extra>",
    )])
    fig.update_layout(
        **_LAYOUT_TEMPLATE, title=f"Top {limit} Objects by Business Value",
        xaxis_title="Object", yaxis_title="Business Value",
    )
    return fig


def quadrant_scatter(frame: pd.DataFrame, cfg: ScoringConfig) -> go.Figure:
    fig = go.Figure()
    for category in Category:
        subset = frame[frame["category"] == category]
        if subset.empty:
            continue
        style = category_style(category)
        marker = dict(
            color=style.colour, size=12,
            line=dict(
                width=[3 if det is not Determinant.SCORE else 0 for det in subset["determinant"]],
                color="#000000",
            ),
        )
        fig.add_trace(go.Scatter(
            x=subset["technical_effort"], y=subset["business_value"], mode="markers",
            marker=marker, name=style.label, text=subset["object_id"],
            customdata=subset["description"],
            hovertemplate="%{text}: %{customdata}<br>Value %{y:.1f}, Effort %{x:.1f}<extra></extra>",
        ))
    fig.add_hline(y=cfg.value_threshold, line_dash="dash", line_color="#666666",
                  annotation_text=f"Value threshold ({cfg.value_threshold})")
    fig.add_vline(x=cfg.effort_threshold, line_dash="dash", line_color="#666666",
                  annotation_text=f"Effort threshold ({cfg.effort_threshold})")
    fig.update_layout(
        **_LAYOUT_TEMPLATE, title="Business Value vs Technical Effort",
        xaxis_title="Technical Effort", yaxis_title="Business Value",
    )
    return fig


def dependency_heatmap(graph: DependencyGraph, heatmap_df: pd.DataFrame) -> go.Figure:
    labels = [n.label for n in graph.nodes if n.node_id in graph.area_order]
    label_order = [next(n.label for n in graph.nodes if n.node_id == area_id) for area_id in graph.area_order]
    pivot = heatmap_df.pivot(index="source_area", columns="target_area", values="value")
    pivot = pivot.reindex(index=label_order, columns=label_order)
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values, x=pivot.columns, y=pivot.index,
        colorscale=[[0, "#ffffff"], [1, "#02462f"]],
        hovertemplate="%{y} -> %{x}: %{z}<extra></extra>",
    ))
    fig.update_layout(
        **_LAYOUT_TEMPLATE, title="Dependency Matrix",
        xaxis_title="Depends on", yaxis_title="Solution area",
    )
    return fig


def dependency_network(graph: DependencyGraph) -> go.Figure:
    fig = go.Figure()
    x_edges, y_edges = [], []
    for edge in graph.edges:
        if edge.source not in graph.layout or edge.target not in graph.layout:
            continue
        x0, y0 = graph.layout[edge.source]
        x1, y1 = graph.layout[edge.target]
        x_edges += [x0, x1, None]
        y_edges += [y0, y1, None]
    fig.add_trace(go.Scatter(
        x=x_edges, y=y_edges, mode="lines", line=dict(width=1, color="#999999"),
        hoverinfo="skip", showlegend=False,
    ))

    for node_type in NodeType:
        nodes = [n for n in graph.nodes if n.node_type is node_type and n.node_id in graph.layout]
        if not nodes:
            continue
        xs = [graph.layout[n.node_id][0] for n in nodes]
        ys = [graph.layout[n.node_id][1] for n in nodes]
        labels = [n.label for n in nodes]
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="markers+text", text=labels, textposition="top center",
            marker=dict(symbol=_NODE_TYPE_SYMBOL[node_type], size=16, color=palette()["header"].hex),
            name=_NODE_TYPE_LABEL[node_type],
            hovertemplate="%{text}<extra></extra>",
        ))

    fig.update_layout(
        **_LAYOUT_TEMPLATE, title="Dependency Network",
        xaxis=dict(visible=False), yaxis=dict(visible=False), showlegend=True,
    )
    return fig


def wave_gantt(gantt_df: pd.DataFrame, freeze_until: date) -> go.Figure:
    fig = go.Figure()
    for _, row in gantt_df.iterrows():
        colour, band_label = _risk_colour_label(row["risk_band"])
        label = f"{row['wave_label']} ({row['object_count']} objects, {band_label})"
        duration_days = (row["end_date"] - row["start_date"]).days + 1
        fig.add_trace(go.Bar(
            x=[pd.Timedelta(days=duration_days)],
            y=[row["wave_label"]], base=[pd.Timestamp(row["start_date"])],
            orientation="h", marker_color=colour, name=label,
            text=label, hovertemplate=f"{label}: {row['start_date']} to {row['end_date']}<extra></extra>",
            showlegend=False,
        ))
    fig.add_vline(x=pd.Timestamp(freeze_until), line_dash="dot", line_color="#9c4f1f",
                  annotation_text="DMK freeze (2028-01-01)")
    fig.update_layout(
        **_LAYOUT_TEMPLATE, title="Migration Wave Timeline",
        xaxis_title="Date", yaxis_title="Wave", barmode="stack",
    )
    return fig


def _risk_colour_label(band) -> tuple[str, str]:
    from bwace.app.theme import risk_style
    return risk_style(band)
