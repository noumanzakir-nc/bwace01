from datetime import date

from bwace.engine.config import BANDS
from bwace.engine.normalisation import apply_band, recency_factor


def test_apply_band_boundaries_inclusive_upper():
    bands = BANDS["usage_frequency"]
    assert apply_band(5, bands) == 0
    assert apply_band(6, bands) == 20
    assert apply_band(25, bands) == 20
    assert apply_band(26, bands) == 40
    assert apply_band(301, bands) == 100
    assert apply_band(1000, bands) == 100


def test_apply_band_below_lowest_scores_zero():
    bands = BANDS["outgoing_dependencies"]
    assert apply_band(0, bands) == 0


def test_recency_factor_tiers():
    reference = date(2026, 8, 14)
    assert recency_factor(date(2026, 8, 1), reference) == 1.00   # 13 days
    assert recency_factor(date(2026, 4, 1), reference) == 0.75   # ~135 days
    assert recency_factor(date(2025, 10, 1), reference) == 0.50  # ~317 days
    assert recency_factor(date(2024, 1, 1), reference) == 0.25   # >366 days


def test_resolve_area_metrics_composite_area_averages():
    from bwace.engine.dependencies import build_graph
    from bwace.engine.models import AreaCriticality, DependencyEdge, DependencyNode, EdgeType, NodeType
    from bwace.engine.normalisation import resolve_area_metrics

    nodes = (
        DependencyNode(node_id="PR", label="Production", node_type=NodeType.SOLUTION_AREA),
        DependencyNode(node_id="IN", label="Inventory Management", node_type=NodeType.SOLUTION_AREA),
    )
    edges = (
        DependencyEdge(source="PR", target="IN", edge_type=EdgeType.LOGICAL),
    )
    graph = build_graph(nodes, edges)
    criticality = {
        "Production": AreaCriticality(solution_area="Production", criticality=85,
                                       migration_priority=3, downtime_tolerance_hours=12),
        "Inventory Management": AreaCriticality(solution_area="Inventory Management", criticality=80,
                                                  migration_priority=3, downtime_tolerance_hours=12),
    }
    metrics = resolve_area_metrics("Production/Inventory Management", criticality, graph)
    assert metrics.criticality == 82.5
