"""Source Data view. Read-only display of the six raw datasets exactly as loaded."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from bwace.engine.models import Landscape
from bwace.app import frames, widgets

DATASET_LABELS = {
    "object_inventory": "Object Inventory",
    "usage_logs": "Usage Logs",
    "criticality": "Criticality Matrix",
    "dependencies": "Dependency Map",
    "data_volume": "Data Volume Metrics",
    "complexity": "Complexity Scores",
}


def _dependency_tables(landscape: Landscape) -> dict[str, pd.DataFrame]:
    return {
        "Nodes": frames.dependency_nodes_frame(landscape),
        "Edges": frames.dependency_edges_frame(landscape),
    }


def render(landscape: Landscape) -> None:
    widgets.page_header(
        "Source Data",
        "Read-only view of the six datasets exactly as loaded (bundled or uploaded).",
    )

    dataset_name = st.selectbox(
        "Dataset", list(DATASET_LABELS.keys()), format_func=lambda k: DATASET_LABELS[k],
        key="source-data-dataset-selector",
    )
    source = landscape.sources.get(dataset_name, "bundled")
    st.caption(f"Source: {source}")

    if dataset_name == "dependencies":
        tables = _dependency_tables(landscape)
        tab_names = list(tables.keys())
        tabs = st.tabs(tab_names)
        for tab, name in zip(tabs, tab_names):
            with tab:
                frame = tables[name]
                st.dataframe(frame, hide_index=True, key=f"source-data-table-{name.lower()}")
                st.download_button(
                    f"Download {name} as CSV", frame.to_csv(index=False),
                    file_name=f"dependencies_{name.lower()}.csv",
                    key=f"source-data-download-{name.lower()}",
                )
        return

    builders = {
        "object_inventory": frames.object_inventory_frame,
        "usage_logs": frames.usage_logs_frame,
        "criticality": frames.criticality_frame,
        "data_volume": frames.data_volume_frame,
        "complexity": frames.complexity_frame,
    }
    frame = builders[dataset_name](landscape)
    st.dataframe(frame, hide_index=True, key=f"source-data-table-{dataset_name}")
    st.download_button(
        f"Download {DATASET_LABELS[dataset_name]} as CSV", frame.to_csv(index=False),
        file_name=f"{dataset_name}.csv", key=f"source-data-download-{dataset_name}",
    )
