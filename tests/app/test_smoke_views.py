from pathlib import Path

from streamlit.testing.v1 import AppTest

VIEWS = (
    "Dashboard", "Object Detail", "Dependencies", "Wave Planner",
    "Scenario Compare", "Source Data", "Connection Settings",
)

_MAIN_PY = Path(__file__).resolve().parents[2] / "src" / "bwace" / "app" / "main.py"


def _app():
    at = AppTest.from_file(str(_MAIN_PY), default_timeout=30)
    at.run()
    return at


def test_initial_render_has_no_exception():
    at = _app()
    assert not at.exception
    assert not at.get("error")


def test_dashboard_kpis_match_reference():
    at = _app()
    metrics = {m.label: m.value for m in at.get("metric")}
    assert metrics["Total Objects"] == "22"
    assert metrics["Total Storage"] == "604 GB"
    assert metrics["Reclaimable Storage"] == "21 GB"


def test_every_view_renders_without_error():
    at = _app()
    for view in VIEWS:
        radio = at.sidebar.radio(key="sidebar-view-nav")
        radio.set_value(view).run()
        assert not at.exception, f"{view} raised: {list(at.exception)}"
        assert not at.get("error"), f"{view} showed an error box"
        assert at.get("header")[0].value == view


def test_threshold_change_recomputes_without_error():
    at = _app()
    slider = at.sidebar.slider(key="sidebar-effort-threshold")
    slider.set_value(66).run()
    assert not at.exception
    assert not at.get("error")


def test_object_detail_selector_covers_all_22():
    at = _app()
    at.sidebar.radio(key="sidebar-view-nav").set_value("Object Detail").run()
    selector = at.selectbox(key="object-detail-selector")
    assert len(selector.options) == 22


def test_scenario_save_and_compare_flow():
    at = _app()
    at.sidebar.radio(key="sidebar-view-nav").set_value("Scenario Compare").run()
    at.text_input(key="scenario-name-input").set_value("Default").run()
    at.button(key="scenario-save-button").click().run()
    assert not at.exception

    at.sidebar.slider(key="sidebar-effort-threshold").set_value(66).run()
    at.text_input(key="scenario-name-input").set_value("LowerEffort").run()
    at.button(key="scenario-save-button").click().run()
    assert not at.exception

    at.selectbox(key="scenario-compare-left").set_value("Default").run()
    at.selectbox(key="scenario-compare-right").set_value("LowerEffort").run()
    assert not at.exception
    assert not at.get("error")


def test_demo_mode_is_the_startup_default():
    at = _app()
    assert at.session_state["data_mode"] == "demo"
    assert at.session_state["live_payloads"] == {}
    assert at.session_state["odata_tested_ok"] is False


def test_connection_settings_renders_without_credentials():
    at = _app()
    at.sidebar.radio(key="sidebar-view-nav").set_value("Connection Settings").run()
    assert not at.exception
    assert at.get("header")[0].value == "Connection Settings"
    assert at.radio(key="connection-mode-selector").value == "demo"


def test_live_mode_is_refused_without_a_successful_connection_test():
    at = _app()
    at.sidebar.radio(key="sidebar-view-nav").set_value("Connection Settings").run()
    at.radio(key="connection-mode-selector").set_value("live").run()
    assert at.session_state["data_mode"] == "demo"
    assert "connection test" in at.session_state["live_error"]


def test_connection_test_without_credentials_reports_the_missing_variables():
    at = _app()
    at.sidebar.radio(key="sidebar-view-nav").set_value("Connection Settings").run()
    at.button(key="connection-test-button").click().run()
    assert not at.exception
    assert at.session_state["odata_tested_ok"] is False
    assert "BWACE_ODATA_USER" in at.session_state["live_error"]


def test_no_secret_appears_anywhere_in_the_rendered_page(monkeypatch):
    monkeypatch.setenv("BWACE_ODATA_BASE_URL", "https://sapgw.example.test:44300")
    monkeypatch.setenv("BWACE_ODATA_USER", "bwace_reader")
    monkeypatch.setenv("BWACE_ODATA_PASSWORD", "s3cr3t-value")
    at = _app()
    at.sidebar.radio(key="sidebar-view-nav").set_value("Connection Settings").run()

    # Guard against a vacuous assertion: the environment must actually have been read.
    settings = at.session_state["odata_settings"]
    assert settings.user_set and settings.password_set and settings.base_url

    rendered = " ".join(str(e.value) for e in at.get("markdown") + at.get("caption") + at.get("subheader"))
    frame_text = " ".join(str(df.value.to_dict()) for df in at.get("dataframe"))
    haystack = rendered + frame_text
    assert len(haystack) > 500
    assert "s3cr3t-value" not in haystack
    assert "bwace_reader" not in haystack


def test_live_mode_end_to_end_with_a_stubbed_transport(monkeypatch):
    from engine.test_odata import ENV, StubTransport, _full_script

    for key, value in ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(
        "bwace.engine.odata.transport_from_env",
        lambda settings, env=None: StubTransport([("$metadata", b"<edmx/>")] + _full_script()),
    )

    at = _app()
    at.sidebar.radio(key="sidebar-view-nav").set_value("Connection Settings").run()
    at.button(key="connection-test-button").click().run()
    assert at.session_state["odata_tested_ok"] is True

    at.radio(key="connection-mode-selector").set_value("live").run()
    assert at.session_state["data_mode"] == "live"
    assert at.session_state["live_error"] is None
    assert at.session_state["live_fetched_at"] is not None

    sources = at.session_state["landscape"].sources
    assert sources["object_inventory"] == "live"
    assert sources["criticality"] == "bundled"
    assert len(at.session_state["landscape"].objects) == 22

    at.sidebar.radio(key="sidebar-view-nav").set_value("Dashboard").run()
    assert not at.exception
    assert not at.get("error")


def test_reverting_to_demo_data_leaves_live_mode(monkeypatch):
    from engine.test_odata import ENV, StubTransport, _full_script

    for key, value in ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(
        "bwace.engine.odata.transport_from_env",
        lambda settings, env=None: StubTransport([("$metadata", b"<edmx/>")] + _full_script()),
    )
    at = _app()
    at.sidebar.radio(key="sidebar-view-nav").set_value("Connection Settings").run()
    at.button(key="connection-test-button").click().run()
    at.radio(key="connection-mode-selector").set_value("live").run()
    assert at.session_state["data_mode"] == "live"

    at.sidebar.button(key="sidebar-revert-demo").click().run()
    assert at.session_state["data_mode"] == "demo"
    assert all(v == "bundled" for v in at.session_state["landscape"].sources.values())
