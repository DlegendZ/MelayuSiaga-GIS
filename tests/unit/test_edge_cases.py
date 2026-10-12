from dataclasses import replace
from datetime import date

from km_flood_priority.core.network import build_graph, multi_source_dijkstra
from km_flood_priority.core.normalize import normalize_name
from km_flood_priority.core.schema import Road


def test_name_alias_does_not_replace_a_longer_word():
    assert normalize_name("KPO TEST") == "KPO TEST"


def test_cross_source_group_preserves_same_source_records(raw_event, importer):
    result = importer(
        [
            raw_event,
            {**raw_event, "event_id": "TEST-D"},
            {**raw_event, "event_id": "OTHER-A", "source_id": "OTHER"},
        ]
    )
    assert [e.duplicate_of for e in result.events] == [None, None, "TEST-A#4"]


def test_looped_grid_chooses_shortest_route():
    graph = build_graph(
        [
            Road("TEST-A", ((0, 0), (10, 0), (20, 0))),
            Road("TEST-B", ((0, 0), (0, 10), (10, 10), (20, 10), (20, 0))),
            Road("TEST-C", ((10, 0), (10, 10))),
        ]
    )
    route = multi_source_dijkstra(graph, {"TEST-SP": (20, 0)})
    assert route.distances[(0, 0)] == 20
    assert route.distances[(0, 10)] == 30
    assert route.path((0, 0)) == ((0, 0), (10, 0), (20, 0))


def test_episode_year_count_does_not_imply_complete_coverage(raw_event, importer):
    from km_flood_priority.core.priority import compute_priority

    normalized = importer([raw_event]).events[0]
    records = [normalized, replace(normalized, event_date=date(2020, 1, 1))]
    row = compute_priority(records, [4], kelurahan="TESTVILLE").polygons[0]
    assert row.n_years == 2
