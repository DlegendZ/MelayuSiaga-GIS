from datetime import date

import pytest

from km_flood_priority.core.network import build_graph, evaluate_access, multi_source_dijkstra
from km_flood_priority.core.schema import Closure, Origin, Road, SafePoint


@pytest.fixture
def graph():
    return build_graph(
        [
            Road("bridge", ((0, 0), (10, 0)), name="Test Bridge"),
            Road("east", ((10, 0), (20, 0)), name="Test East"),
            Road("north", ((10, 0), (10, 10)), name="Test North"),
        ]
    )


def test_distance_and_path(graph):
    result = multi_source_dijkstra(graph, {"TARGET": (20, 0)})
    assert result.distances[(0, 0)] == 20
    assert result.path((0, 0)) == ((0, 0), (10, 0), (20, 0))


def test_multisource_nearest_and_tie_deterministic(graph):
    result = multi_source_dijkstra(graph, {"EAST": (20, 0), "NORTH": (10, 10)})
    assert result.target_ids[(10, 10)] == "NORTH"
    assert result.target_ids[(10, 0)] == "EAST"
    assert result.path((99, 99)) == ()


def test_vertex_rounding_merges():
    graph = build_graph([Road("a", ((0, 0), (10.001, 0))), Road("b", ((9.999, 0), (20, 0)))])
    assert len(graph.nodes) == 3
    assert multi_source_dijkstra(graph, {"END": (20, 0)}).distances[(0, 0)] == 20


def test_excluded_highways_and_zero_length_edges():
    graph = build_graph(
        [Road("a", ((0, 0), (0, 0), (10, 0))), Road("b", ((10, 0), (20, 0)), highway="motorway")]
    )
    assert len(graph.edges) == 1
    assert (20, 0) not in graph.nodes


@pytest.mark.parametrize(
    "mode,expected,reason",
    [
        ("no_targets", "UNKNOWN", "no_verified_safe_points"),
        ("off_network", "UNKNOWN", "origin_off_network"),
        ("baseline", "UNKNOWN", "baseline_only_closures_not_assessed"),
        ("unverified_closure", "UNKNOWN", "closures_not_verified_for_date"),
        ("reachable", "REACHABLE", "path_after_verified_closures"),
        ("cut_off", "CUT_OFF", "no_path_after_verified_closures"),
    ],
)
def test_every_normative_status_rule(graph, mode, expected, reason):
    origins = [Origin(4, (1000, 0) if mode == "off_network" else (0, 0))]
    targets = [] if mode == "no_targets" else [SafePoint("TEST-SP", (20, 0), "Y")]
    closures = [
        Closure(
            "TEST-C",
            date(2025, 3, 4),
            "OSM_ID",
            "bridge" if mode == "cut_off" else "north",
            "N" if mode == "unverified_closure" else "Y",
        )
    ]
    dates = [] if mode == "baseline" else [date(2025, 3, 4)]
    result = evaluate_access(graph, origins, targets, closures=closures, event_dates=dates)
    row = result.access[0]
    assert (row.access_status, row.status_reason) == (expected, reason)
    assert row.event_date == ("BASELINE" if mode == "baseline" else "2025-03-04")
    if mode == "cut_off":
        assert row.route_length_m is None
        assert row.baseline_length_m == 20
        assert row.removed_edges == 1


def test_unverified_targets_excluded_by_default(graph):
    result = evaluate_access(graph, [Origin(4, (0, 0))], [SafePoint("TEST-SP", (20, 0), "N")])
    assert result.access[0].status_reason == "no_verified_safe_points"


def test_unverified_opt_in_flagged(graph):
    result = evaluate_access(
        graph,
        [Origin(4, (0, 0))],
        [SafePoint("TEST-SP", (20, 0), "N")],
        use_unverified_safe_points=True,
    )
    row = result.access[0]
    assert row.targets_verified == "N"
    assert row.status_reason.endswith(";unverified_targets")
    assert row.baseline_length_m == 20


def test_off_network_target_skipped(graph):
    result = evaluate_access(graph, [Origin(4, (0, 0))], [SafePoint("TEST-SP", (200, 0), "Y")])
    assert result.access[0].status_reason == "no_verified_safe_points"
    assert result.graph_stats["unsnapped_safe_points"] == ["TEST-SP"]


def test_name_closure_normalization(graph):
    result = evaluate_access(
        graph,
        [Origin(4, (0, 0))],
        [SafePoint("TEST-SP", (20, 0), "Y")],
        closures=[Closure("TEST-C", date(2025, 3, 4), "NAME", " test  bridge ", "Y")],
        event_dates=[date(2025, 3, 4)],
    )
    assert result.access[0].access_status == "CUT_OFF"


def test_closures_isolated_by_date(graph):
    result = evaluate_access(
        graph,
        [Origin(4, (0, 0))],
        [SafePoint("TEST-SP", (20, 0), "Y")],
        closures=[Closure("TEST-C", date(2025, 3, 4), "OSM_ID", "bridge", "Y")],
        event_dates=[date(2025, 3, 4), date(2025, 3, 5)],
    )
    assert [r.access_status for r in result.access] == ["CUT_OFF", "UNKNOWN"]
    assert result.access[1].baseline_length_m == 20
    assert len(graph.edges) == 3


def test_parallel_edges_keep_alternative_path():
    graph = build_graph([Road("a", ((0, 0), (10, 0))), Road("b", ((0, 0), (10, 0)))])
    result = evaluate_access(
        graph,
        [Origin(4, (0, 0))],
        [SafePoint("TEST-SP", (10, 0), "Y")],
        closures=[Closure("TEST-C", date(2025, 3, 4), "OSM_ID", "a", "Y")],
        event_dates=[date(2025, 3, 4)],
    )
    assert result.access[0].access_status == "REACHABLE"
    assert result.access[0].removed_edges == 1


def test_empty_graph_and_negative_tolerance():
    graph = build_graph([])
    result = evaluate_access(graph, [Origin(4, (0, 0))], [SafePoint("TEST-SP", (0, 0), "Y")])
    assert result.graph_stats["connected_components"] == 0
    assert result.access[0].access_status == "UNKNOWN"
    with pytest.raises(ValueError):
        evaluate_access(graph, [], [], snap_tolerance_m=-1)


def test_disconnected_graph_has_two_components():
    graph = build_graph([Road("a", ((0, 0), (10, 0))), Road("b", ((100, 0), (110, 0)))])
    result = evaluate_access(graph, [Origin(4, (0, 0))], [SafePoint("TEST-SP", (110, 0), "Y")])
    assert result.graph_stats["connected_components"] == 2
    assert result.access[0].baseline_length_m is None


def test_same_node_multiple_targets_lexical_tie(graph):
    result = multi_source_dijkstra(graph, {"Z": (20, 0), "A": (20, 0)})
    assert result.target_ids[(0, 0)] == "A"


def test_invalid_network_coordinates_rejected():
    with pytest.raises(ValueError, match="finite"):
        build_graph([Road("a", ((float("nan"), 0), (1, 0)))])
