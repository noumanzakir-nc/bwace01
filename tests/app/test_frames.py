from bwace.engine.config import DEFAULT_SCORING, DEFAULT_WAVES
from bwace.engine.loader import load_bundled
from bwace.engine.models import Scenario, ScoringConfig
from bwace.engine.service import assess, compare
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


def test_object_inventory_frame_shape():
    _, landscape = _result_and_landscape()
    frame = frames.object_inventory_frame(landscape)
    assert len(frame) == 22
    assert {"object_id", "object_type", "solution_area", "description"}.issubset(frame.columns)


def test_usage_logs_frame_shape():
    _, landscape = _result_and_landscape()
    frame = frames.usage_logs_frame(landscape)
    assert len(frame) == 22
    assert {"object_id", "last_run_date", "monthly_executions"}.issubset(frame.columns)


def test_criticality_frame_shape():
    _, landscape = _result_and_landscape()
    frame = frames.criticality_frame(landscape)
    assert len(frame) == 12
    assert {"solution_area", "criticality", "migration_priority"}.issubset(frame.columns)


def test_data_volume_frame_shape():
    _, landscape = _result_and_landscape()
    frame = frames.data_volume_frame(landscape)
    assert len(frame) == 22
    assert frame["storage_gb"].sum() == 604


def test_complexity_frame_shape():
    _, landscape = _result_and_landscape()
    frame = frames.complexity_frame(landscape)
    assert len(frame) == 22
    assert {"object_id", "hana_cv_count", "transformation_count"}.issubset(frame.columns)


def test_dependency_nodes_frame_shape():
    _, landscape = _result_and_landscape()
    frame = frames.dependency_nodes_frame(landscape)
    assert len(frame) == 16
    assert {"node_id", "label", "node_type"}.issubset(frame.columns)


def test_dependency_edges_frame_shape():
    _, landscape = _result_and_landscape()
    frame = frames.dependency_edges_frame(landscape)
    assert len(frame) == 21
    assert {"source", "target", "edge_type"}.issubset(frame.columns)


def _diff_and_scenarios():
    landscape = load_bundled().landscape
    left = Scenario(name="Default", scoring_config=DEFAULT_SCORING, wave_config=DEFAULT_WAVES)
    right = Scenario(name="LowerEffort", scoring_config=ScoringConfig(effort_threshold=66), wave_config=DEFAULT_WAVES)
    return compare(landscape, left, right), left, right


def test_distribution_frame_shape_and_totals():
    diff, _, _ = _diff_and_scenarios()
    frame = frames.distribution_frame(diff)
    assert "category" in frame.columns
    assert "Default" in frame.columns
    assert "LowerEffort" in frame.columns
    assert frame["Default"].sum() == 22
    assert frame["LowerEffort"].sum() == 22


def test_scenario_config_frame_shows_differing_effort_threshold():
    _, left, right = _diff_and_scenarios()
    frame = frames.scenario_config_frame(left, right)
    row = frame[frame["parameter"] == "Effort Threshold"].iloc[0]
    assert row["Default"] == "67"
    assert row["LowerEffort"] == "66"
    assert len(frame) == 9


def test_scenario_config_frame_is_arrow_serialisable():
    # Regression: start_date (a datetime.date) previously shared an object-dtype
    # column with int values from other rows, which PyArrow cannot convert.
    import pyarrow as pa

    _, left, right = _diff_and_scenarios()
    frame = frames.scenario_config_frame(left, right)
    pa.Table.from_pandas(frame)  # raises ArrowInvalid on regression
