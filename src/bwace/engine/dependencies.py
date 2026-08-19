"""Build and interrogate the dependency graph. See BR-7."""
from __future__ import annotations

import networkx as nx

from bwace.engine.models import (
    BwObject,
    DependencyEdge,
    DependencyGraph,
    DependencyNode,
    NodeType,
)


def constituent_areas(solution_area: str, known_areas: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(solution_area.split("/"))


def expand_wildcards(edges: tuple[DependencyEdge, ...], area_node_ids: tuple[str, ...]) -> tuple[DependencyEdge, ...]:
    expanded: list[DependencyEdge] = []
    for edge in edges:
        if edge.source == "ALL":
            for area_id in area_node_ids:
                expanded.append(DependencyEdge(
                    source=area_id, target=edge.target, edge_type=edge.edge_type, description=edge.description,
                ))
        else:
            expanded.append(edge)
    return tuple(expanded)


def compute_layout(nodes: tuple[DependencyNode, ...], edges: tuple[DependencyEdge, ...]) -> dict[str, tuple[float, float]]:
    graph = nx.DiGraph()
    graph.add_nodes_from(n.node_id for n in nodes)
    graph.add_edges_from((e.source, e.target) for e in edges)
    positions = nx.spring_layout(graph, seed=42)
    return {node_id: (float(x), float(y)) for node_id, (x, y) in positions.items()}


def build_graph(nodes: tuple[DependencyNode, ...], edges: tuple[DependencyEdge, ...]) -> DependencyGraph:
    area_node_ids = tuple(n.node_id for n in nodes if n.node_type is NodeType.SOLUTION_AREA)
    expanded = expand_wildcards(edges, area_node_ids)

    graph = nx.DiGraph()
    graph.add_nodes_from(n.node_id for n in nodes)
    graph.add_edges_from((e.source, e.target) for e in expanded)

    out_degree = {node.node_id: graph.out_degree(node.node_id) for node in nodes}
    in_degree = {node.node_id: graph.in_degree(node.node_id) for node in nodes}

    area_order = area_node_ids
    area_matrix = tuple(
        tuple(1 if graph.has_edge(row, col) else 0 for col in area_order)
        for row in area_order
    )

    layout = compute_layout(nodes, expanded)

    return DependencyGraph(
        nodes=nodes, edges=expanded, out_degree=out_degree, in_degree=in_degree,
        area_order=area_order, area_matrix=area_matrix, layout=layout,
    )


def area_matrix(graph: DependencyGraph) -> tuple[tuple[int, ...], ...]:
    return graph.area_matrix


def edges_for_object(obj: BwObject, graph: DependencyGraph) -> tuple[tuple[DependencyEdge, ...], tuple[DependencyEdge, ...]]:
    areas = set(constituent_areas(obj.solution_area, graph.area_order))
    area_ids = {node.node_id for node in graph.nodes if node.label in areas}
    incoming = tuple(e for e in graph.edges if e.target in area_ids)
    outgoing = tuple(e for e in graph.edges if e.source in area_ids)
    return incoming, outgoing
