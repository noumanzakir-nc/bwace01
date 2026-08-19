from pathlib import Path

from streamlit.testing.v1 import AppTest

VIEWS = ("Dashboard", "Object Detail", "Dependencies", "Wave Planner", "Scenario Compare", "Source Data")

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
