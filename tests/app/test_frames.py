from bwace.engine.config import DEFAULT_SCORING, DEFAULT_WAVES
from bwace.engine.loader import load_bundled
from bwace.engine.service import assess
from bwace.app import frames


def _result_and_landscape():
    landscape = load_bundled().landscape
    return assess(landscape, DEFAULT_SCORING, DEFAULT_WAVES), landscape


def test_assessments_frame_shape():
    result, landscape = _result_and_landscape()
    frame = frames.assessments_frame(result, landscape)
    assert len(frame) == 22
    expected_columns = {
        "object_id", "object_type", "solution_area", "description", "business_value",
        "technical_effort", "category", "category_label", "determinant", "is_dormant",
        "is_active", "monthly_executions", "distinct_users", "last_run_date",
        "business_owner", "storage_gb",
    }
    assert expected_columns.issubset(set(frame.columns))
    assert frame["storage_gb"].sum() == 604


def test_derivation_frame_shape():
    result, _ = _result_and_landscape()
    assessment = next(a for a in result.assessments if a.object_id == "SC100")
    frame = frames.derivation_frame(assessment)
    assert len(frame) == 7
    assert set(frame["axis"]) == {"business_value", "technical_effort"}


def test_gantt_frame_one_row_per_wave():
    result, _ = _result_and_landscape()
    frame = frames.gantt_frame(result.wave_plan)
    assert len(frame) == 5


def test_heatmap_frame_144_rows():
    result, _ = _result_and_landscape()
    frame = frames.heatmap_frame(result.graph)
    assert len(frame) == 144


def test_candidates_frame_matches_decommission_set():
    result, landscape = _result_and_landscape()
    frame = frames.candidates_frame(result, landscape)
    assert set(frame["object_id"]) == {"IN200", "TR100", "TR200", "TM100"}
    assert frame["storage_gb"].sum() == 21
