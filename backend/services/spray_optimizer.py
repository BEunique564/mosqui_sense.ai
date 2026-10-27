"""
OR-Tools VRP Solver for Municipal Spray/Fogging Route Optimization.

Uses Google OR-Tools to compute optimal fogging vehicle routes
for Sadar Cantt ward centroids.
"""

from dataclasses import dataclass, asdict
from typing import Optional

try:
    from ortools.constraint_solver import pywrapcp, routing_enums_pb2
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False


@dataclass
class VehicleSpec:
    id: str
    capacity_liters: float = 200.0
    fuel_tank: float = 40.0


@dataclass
class RouteResult:
    routes: list[dict]
    total_fuel_liters: float
    estimated_cost_inr: float
    solver_status: str
    total_distance_km: float
    estimated_time_hours: float
    vehicles_used: int


# Sadar Cantt area hotspot locations (real places)
SADAR_CANTT_HOTSPOTS = [
    {"id": "H1", "name": "Sadar Bazaar", "lat": 26.845, "lon": 80.935, "risk_weight": 1.2},
    {"id": "H2", "name": "Nehru Road", "lat": 26.848, "lon": 80.940, "risk_weight": 1.0},
    {"id": "H3", "name": "Cantonment Board Office", "lat": 26.852, "lon": 80.943, "risk_weight": 0.8},
    {"id": "H4", "name": "Kanpur Road Junction", "lat": 26.840, "lon": 80.938, "risk_weight": 1.1},
    {"id": "H5", "name": "Hazratganj Border", "lat": 26.855, "lon": 80.948, "risk_weight": 0.9},
    {"id": "H6", "name": "Alambagh Crossing", "lat": 26.835, "lon": 80.930, "risk_weight": 1.3},
    {"id": "H7", "name": "Charbagh Area", "lat": 26.850, "lon": 80.928, "risk_weight": 0.7},
    {"id": "H8", "name": "Aminabad Market", "lat": 26.858, "lon": 80.942, "risk_weight": 1.0},
]

# Depot location (Sadar Cantt)
DEPOT = {"lat": 26.850, "lon": 80.940, "name": "Sadar Cantt Depot"}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute distance between two GPS points in km."""
    import math
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def solve_spray_vrp(
    hotspot_ids: Optional[list[str]] = None,
    vehicles: Optional[list[VehicleSpec]] = None,
    max_route_hours: float = 8.0,
) -> RouteResult:
    """Solve VRP for spray routes using OR-Tools.

    Args:
        hotspot_ids: Which hotspots to visit (default: all)
        vehicles: Available vehicles (default: 2)
        max_route_hours: Max working hours per vehicle
    """
    if vehicles is None:
        vehicles = [
            VehicleSpec("V1", 200.0, 40.0),
            VehicleSpec("V2", 150.0, 35.0),
        ]

    hotspots = SADAR_CANTT_HOTSPOTS
    if hotspot_ids:
        hotspots = [h for h in SADAR_CANTT_HOTSPOTS if h["id"] in hotspot_ids]

    if not ORTOOLS_AVAILABLE:
        return _fallback_route(hotspots, vehicles)

    # Build distance matrix including depot
    all_locations = [DEPOT] + hotspots
    n = len(all_locations)
    num_vehicles = len(vehicles)

    distance_matrix = []
    for i in range(n):
        row = []
        for j in range(n):
            d = _haversine_km(
                all_locations[i]["lat"], all_locations[i]["lon"],
                all_locations[j]["lat"], all_locations[j]["lon"],
            )
            # Convert to metres and add time penalty for high-risk areas
            weight = all_locations[j].get("risk_weight", 1.0) if j > 0 else 1.0
            row.append(int(d * 1000 * weight))
        distance_matrix.append(row)

    manager = pywrapcp.RoutingIndexManager(n, num_vehicles, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Capacity constraint (fuel tank)
    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        if from_node == 0:
            return 0
        return 1

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,
        [int(v.capacity_liters) for v in vehicles],
        True,
        "Capacity",
    )

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.FromSeconds(5)

    solution = routing.SolveWithParameters(search_parameters)
    status = "OPTIMAL" if solution else "INFEASIBLE"

    routes = []
    total_distance = 0
    if solution:
        for vehicle_idx in range(num_vehicles):
            index = routing.Start(vehicle_idx)
            route_nodes = []
            route_distance = 0
            while not routing.IsEnd(index):
                node = manager.IndexToNode(index)
                if node > 0:
                    route_nodes.append({
                        "hotspot_id": hotspots[node - 1]["id"],
                        "name": hotspots[node - 1]["name"],
                        "lat": hotspots[node - 1]["lat"],
                        "lon": hotspots[node - 1]["lon"],
                    })
                prev_index = index
                index = solution.Value(routing.NextVar(index))
                route_distance += routing.GetArcCostForVehicle(prev_index, index, vehicle_idx)

            if route_nodes:
                routes.append({
                    "vehicle_id": vehicles[vehicle_idx].id,
                    "stops": route_nodes,
                    "distance_km": round(route_distance / 1000, 2),
                })
                total_distance += route_distance / 1000

    fuel_per_km = 0.15  # L/km for fogging vehicle
    total_fuel = total_distance * fuel_per_km
    cost_per_litre = 95.0  # INR per litre diesel
    total_cost = total_fuel * cost_per_litre
    est_time = total_distance / 25  # 25 km/h avg speed

    return RouteResult(
        routes=routes,
        total_fuel_liters=round(total_fuel, 1),
        estimated_cost_inr=round(total_cost, 0),
        solver_status=status,
        total_distance_km=round(total_distance, 2),
        estimated_time_hours=round(est_time, 1),
        vehicles_used=len([r for r in routes if r["stops"]]),
    )


def _fallback_route(hotspots: list[dict], vehicles: list[VehicleSpec]) -> RouteResult:
    """Simple nearest-neighbor fallback when OR-Tools not installed."""
    import math

    unvisited = list(range(len(hotspots)))
    current_lat, current_lon = DEPOT["lat"], DEPOT["lon"]
    routes = []

    for v_idx, vehicle in enumerate(vehicles):
        if not unvisited:
            break
        stops = []
        total_dist = 0
        while unvisited:
            nearest = min(unvisited, key=lambda i: _haversine_km(
                current_lat, current_lon, hotspots[i]["lat"], hotspots[i]["lon"]
            ))
            dist = _haversine_km(current_lat, current_lon, hotspots[nearest]["lat"], hotspots[nearest]["lon"])
            total_dist += dist
            stops.append({
                "hotspot_id": hotspots[nearest]["id"],
                "name": hotspots[nearest]["name"],
                "lat": hotspots[nearest]["lat"],
                "lon": hotspots[nearest]["lon"],
            })
            current_lat, current_lon = hotspots[nearest]["lat"], hotspots[nearest]["lon"]
            unvisited.remove(nearest)
            if total_dist > 15:  # Max ~15km per vehicle
                break
        if stops:
            routes.append({
                "vehicle_id": vehicle.id,
                "stops": stops,
                "distance_km": round(total_dist, 2),
            })

    total_distance = sum(r["distance_km"] for r in routes)
    fuel = total_distance * 0.15

    return RouteResult(
        routes=routes,
        total_fuel_liters=round(fuel, 1),
        estimated_cost_inr=round(fuel * 95, 0),
        solver_status="FALLBACK_NN",
        total_distance_km=round(total_distance, 2),
        estimated_time_hours=round(total_distance / 25, 1),
        vehicles_used=len(routes),
    )
