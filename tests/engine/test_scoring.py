from bwace.engine.loader import load_bundled
from bwace.engine.dependencies import build_graph
from bwace.engine.scoring import business_value, reference_date, score_all, technical_effort


def _landscape():
    return load_bundled().landscape


def test_axis_totals_within_0_100():
    landscape = _landscape()
    graph = build_graph(landscape.nodes, landscape.edges)
    ref = reference_date(landscape)
    for obj in landscape.objects:
        value = business_value(obj.object_id, landscape, graph, ref)
        effort = technical_effort(obj.object_id, landscape)
        assert 0 <= value.total <= 100
        assert 0 <= effort.total <= 100


def test_reference_date_is_latest_last_run():
    from datetime import date
    landscape = _landscape()
    assert reference_date(landscape) == date(2026, 8, 14)


def test_score_all_covers_every_object():
    landscape = _landscape()
    graph = build_graph(landscape.nodes, landscape.edges)
    scores = score_all(landscape, graph)
    assert set(scores.keys()) == {obj.object_id for obj in landscape.objects}


def test_sc100_worked_example():
    landscape = _landscape()
    graph = build_graph(landscape.nodes, landscape.edges)
    ref = reference_date(landscape)
    value = business_value("SC100", landscape, graph, ref)
    effort = technical_effort("SC100", landscape)
    assert round(value.total, 1) == 86.5
    assert round(effort.total, 1) == 92.0
