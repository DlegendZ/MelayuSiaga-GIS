"""FR-2 undirected pedestrian routing over metric coordinates using stdlib heapq."""

import heapq
import math
from dataclasses import dataclass
from datetime import date

from .normalize import normalize_name
from .schema import AccessRecord, AccessResult, Route

Node = tuple[float, float]
DEFAULT_EXCLUDED_HIGHWAY = frozenset(
    {
        "motorway",
        "motorway_link",
        "construction",
        "proposed",
        "raceway",
        "bus_guideway",
    }
)


@dataclass(frozen=True)
class Edge:
    start: Node
    end: Node
    length: float
    osm_id: str
    name: str


@dataclass
class Graph:
    nodes: tuple[Node, ...]
    edges: tuple[Edge, ...]
    adjacency: dict[Node, list[tuple[Node, int]]]


@dataclass
class DijkstraResult:
    distances: dict[Node, float]
    target_ids: dict[Node, str]
    next_node: dict[Node, Node]

    def path(self, node: Node) -> tuple[Node, ...]:
        if node not in self.distances:
            return ()
        route = [node]
        while node in self.next_node:
            node = self.next_node[node]
            route.append(node)
        return tuple(route)


def _coordinate(point) -> Node:
    if len(point) < 2 or not all(math.isfinite(v) for v in point[:2]):
        raise ValueError("Network coordinates must be finite x/y values")
    return round(point[0], 2), round(point[1], 2)


def build_graph(roads, excluded_highway=DEFAULT_EXCLUDED_HIGHWAY) -> Graph:
    adjacency, edges = {}, []
    for road in roads:
        if road.highway.strip().lower() in excluded_highway:
            continue
        vertices = [_coordinate(point) for point in road.vertices]
        for start, end in zip(vertices, vertices[1:], strict=False):
            if start == end:
                continue
            index = len(edges)
            edges.append(
                Edge(start, end, math.dist(start, end), str(road.osm_id), normalize_name(road.name))
            )
            adjacency.setdefault(start, []).append((end, index))
            adjacency.setdefault(end, []).append((start, index))
    return Graph(tuple(sorted(adjacency)), tuple(edges), adjacency)


def multi_source_dijkstra(
    graph: Graph, targets: dict[str, Node], removed_edges=()
) -> DijkstraResult:
    distances, target_ids, next_node, queue = {}, {}, {}, []
    removed = set(removed_edges)
    for target_id, node in sorted(targets.items()):
        if node not in graph.adjacency:
            continue
        if node not in distances or target_id < target_ids[node]:
            distances[node], target_ids[node] = 0.0, target_id
            heapq.heappush(queue, (0.0, target_id, node))
    while queue:
        distance, target_id, node = heapq.heappop(queue)
        if (distance, target_id) != (distances[node], target_ids[node]):
            continue
        for neighbor, edge_index in graph.adjacency[node]:
            if edge_index in removed:
                continue
            candidate = distance + graph.edges[edge_index].length
            current = distances.get(neighbor, math.inf), target_ids.get(neighbor, "")
            if (candidate, target_id) < current:
                distances[neighbor], target_ids[neighbor] = candidate, target_id
                next_node[neighbor] = node
                heapq.heappush(queue, (candidate, target_id, neighbor))
    return DijkstraResult(distances, target_ids, next_node)


def _snap(graph, point, tolerance):
    if not graph.nodes:
        return None
    _coordinate(point)
    closest = min(graph.nodes, key=lambda node: (math.dist(point[:2], node), node))
    return closest if math.dist(point[:2], closest) <= tolerance else None


def _components(graph, removed=()):
    remaining, count = set(graph.nodes), 0
    while remaining:
        count += 1
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        while stack:
            for neighbor, index in graph.adjacency[stack.pop()]:
                if index not in removed and neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
    return count


def closure_edges(graph, closures, event_date):
    ids, names = set(), set()
    for closure in closures:
        if closure.event_date != event_date or closure.verified != "Y":
            continue
        if closure.road_ref_type == "OSM_ID":
            ids.add(str(closure.road_ref).strip())
        elif closure.road_ref_type == "NAME" and closure.road_ref.strip():
            names.add(normalize_name(closure.road_ref))
    return {
        index for index, edge in enumerate(graph.edges) if edge.osm_id in ids or edge.name in names
    }


def evaluate_access(
    graph,
    origins,
    safe_points=(),
    *,
    closures=(),
    event_dates=(),
    use_unverified_safe_points=False,
    snap_tolerance_m=50.0,
) -> AccessResult:
    if snap_tolerance_m < 0 or not math.isfinite(snap_tolerance_m):
        raise ValueError("SNAP_TOLERANCE_M must be finite and non-negative")
    closures = list(closures)
    targets, skipped = {}, []
    unverified_used = False
    for point in sorted(safe_points, key=lambda point: point.sp_id):
        if point.verified != "Y" and not use_unverified_safe_points:
            continue
        node = _snap(graph, point.coordinates, snap_tolerance_m)
        if node is None:
            skipped.append(point.sp_id)
            continue
        targets[point.sp_id] = node
        unverified_used = unverified_used or point.verified != "Y"
    target_flag = "N" if unverified_used else "Y"
    baseline = multi_source_dijkstra(graph, targets)
    dates = sorted(set(event_dates)) or [None]
    rows, routes = [], []
    stats = {
        "nodes": len(graph.nodes),
        "edges": len(graph.edges),
        "connected_components": _components(graph),
        "removed_edges": {},
        "components_by_date": {},
        "unsnapped_safe_points": skipped,
    }
    snapped = [
        (origin, _snap(graph, origin.coordinates, snap_tolerance_m))
        for origin in sorted(origins, key=lambda origin: origin.rw_no)
    ]
    for day in dates:
        if day is not None and not isinstance(day, date):
            raise ValueError("Event dates must be datetime.date values")
        date_label = "BASELINE" if day is None else day.isoformat()
        verified_closures = [c for c in closures if c.event_date == day and c.verified == "Y"]
        removed = closure_edges(graph, closures, day)
        after = multi_source_dijkstra(graph, targets, removed) if verified_closures else baseline
        stats["removed_edges"][date_label] = len(removed)
        stats["components_by_date"][date_label] = _components(graph, removed)
        for origin, node in snapped:
            status = "UNKNOWN"
            route_result = baseline
            if not targets:
                reason = "no_verified_safe_points"
            elif node is None:
                reason = "origin_off_network"
            elif day is None:
                reason = "baseline_only_closures_not_assessed"
            elif not verified_closures:
                reason = "closures_not_verified_for_date"
            elif node in after.distances:
                status, reason = "REACHABLE", "path_after_verified_closures"
                route_result = after
            else:
                status, reason = "CUT_OFF", "no_path_after_verified_closures"
                route_result = after
            if unverified_used:
                reason += ";unverified_targets"
            rows.append(
                AccessRecord(
                    origin.rw_no,
                    date_label,
                    status,
                    reason,
                    route_result.target_ids.get(node),
                    route_result.distances.get(node),
                    baseline.distances.get(node),
                    target_flag,
                    len(removed),
                )
            )
            route = route_result.path(node)
            if route:
                routes.append(
                    Route(
                        origin.rw_no,
                        date_label,
                        "REACHABLE" if status == "REACHABLE" else "BASELINE",
                        route,
                    )
                )
    return AccessResult(rows, routes, stats)
