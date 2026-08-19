from bwace.engine.dependencies import build_graph
from bwace.engine.loader import load_bundled


def _graph():
    landscape = load_bundled().landscape
    return build_graph(landscape.nodes, landscape.edges)


def test_all_wildcard_expands_to_12_edges():
    graph = _graph()
    dmk_edges = [e for e in graph.edges if e.target == "DMK"]
    assert len(dmk_edges) == 12
    assert graph.in_degree["DMK"] == 12


def test_area_matrix_is_square_over_12_areas():
    graph = _graph()
    assert len(graph.area_order) == 12
    assert len(graph.area_matrix) == 12
    assert all(len(row) == 12 for row in graph.area_matrix)


def test_layout_is_deterministic():
    landscape = load_bundled().landscape
    graph_a = build_graph(landscape.nodes, landscape.edges)
    graph_b = build_graph(landscape.nodes, landscape.edges)
    assert graph_a.layout == graph_b.layout


def test_outgoing_degree_range():
    graph = _graph()
    area_out_degrees = [graph.out_degree[node_id] for node_id in graph.area_order]
    assert min(area_out_degrees) >= 1
    assert max(area_out_degrees) <= 6
