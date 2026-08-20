"""Connection Settings view. Renders state and returns an action; all I/O stays in main.py."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import streamlit as st

from bwace.engine.config import ODATA_ENV_VARS
from bwace.engine.models import Landscape
from bwace.engine.odata import EndpointResult, OdataSettings, Status
from bwace.app import frames, widgets

MODE_LABELS = {"demo": "Demo Data", "live": "Live OData"}


@dataclass(frozen=True)
class SettingsAction:
    kind: str  # "test" | "refresh" | "reload" | "set_mode"
    mode: str | None = None


def render(
    settings: OdataSettings,
    mode: str,
    endpoints: tuple[EndpointResult, ...],
    tested_ok: bool,
    fetched_at: datetime | None,
    landscape: Landscape,
    warnings: tuple[str, ...],
    error: str | None,
) -> SettingsAction | None:
    widgets.page_header(
        "Connection Settings",
        "Switch between demo data and a live SAP BW OData connection, and verify the connection before using it.",
    )

    action: SettingsAction | None = None

    st.subheader("Data Source Mode")
    options = list(MODE_LABELS.keys())
    chosen = st.radio(
        "Mode", options, index=options.index(mode), format_func=lambda k: MODE_LABELS[k],
        horizontal=True, key="connection-mode-selector",
    )
    if chosen != mode:
        action = SettingsAction(kind="set_mode", mode=chosen)

    if not tested_ok:
        st.info(
            "Live mode becomes available once a connection test succeeds in this session. "
            "Demo mode is always available and needs no network."
        )
    if error:
        st.error(error)
    for warning in warnings:
        st.warning(warning)

    st.divider()
    st.subheader("Credentials and Configuration")
    st.caption(
        "Credentials come from environment variables only and are never stored, displayed, or logged. "
        "Presence is shown; values are not."
    )
    st.dataframe(frames.environment_frame(settings), hide_index=True, key="connection-env-table")

    missing = settings.missing_configuration()
    if missing:
        st.warning("Not yet configured. Set: " + ", ".join(missing))
    st.caption(
        f"Authentication: HTTP Basic over TLS. Certificate verification is always on; supply a CA bundle via "
        f"`{ODATA_ENV_VARS['ca_bundle']}` for a private or self-signed authority. "
        "OAuth 2.0 and client certificates are not implemented in this iteration."
    )

    st.divider()
    st.subheader("Endpoints")
    st.caption(
        "The default service paths are **placeholders**. No SAP-delivered OData service by these names could be "
        "found; point them at the services activated in your own SAP Gateway using the environment variables above."
    )
    st.dataframe(frames.endpoint_config_frame(settings), hide_index=True, key="connection-endpoint-config-table")

    cols = st.columns(3)
    if cols[0].button("Test Connection", key="connection-test-button"):
        action = SettingsAction(kind="test")
    if cols[1].button("Refresh from SAP", key="connection-refresh-button"):
        action = SettingsAction(kind="refresh")
    if cols[2].button("Reload Configuration", key="connection-reload-button"):
        action = SettingsAction(kind="reload")

    if endpoints:
        st.dataframe(frames.endpoint_status_frame(endpoints), hide_index=True, key="connection-endpoint-table")
        failures = [e for e in endpoints if e.status is not Status.OK]
        if failures:
            st.caption(f"{len(failures)} of {len(endpoints)} endpoints reported a problem.")
    else:
        st.caption("No connection attempt has been made in this session.")

    st.divider()
    st.subheader("Data Provenance")
    st.caption(
        "The criticality matrix has no live source. Business criticality, migration priority and downtime "
        "tolerance are business judgements rather than BW metadata, so they stay with the bundled or uploaded file."
    )
    st.dataframe(frames.provenance_frame(landscape), hide_index=True, key="connection-provenance-table")
    if fetched_at is not None:
        st.caption(f"Last successful live fetch: {fetched_at:%Y-%m-%d %H:%M:%S} UTC")

    return action
