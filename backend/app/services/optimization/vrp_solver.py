"""Google OR-Tools VRP solver for municipal fogging routes — Module 9."""

from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from app.api.v1.endpoints.spray import OptimizeSprayRequest, OptimizeSprayResponse


def solve_spray_vrp(request: OptimizeSprayRequest) -> OptimizeSprayResponse:
    """
    Simplified VRP: depot → ward centroids → depot.
    Production: integrate PostGIS ward centroids + road network graph.
    """
    depot = request.depot_location
    # Placeholder: one node per ward + depot
    num_vehicles = len(request.vehicles)
    num_locations = len(request.ward_ids) + 1

    manager = pywrapcp.RoutingIndexManager(num_locations, num_vehicles, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return abs(from_node - to_node) * 1000  # placeholder metres

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    solution = routing.SolveWithParameters(search_parameters)
    status = "OPTIMAL" if solution else "INFEASIBLE"

    routes = []
    if solution:
        for vehicle_idx in range(num_vehicles):
            index = routing.Start(vehicle_idx)
            route_nodes = []
            while not routing.IsEnd(index):
                route_nodes.append(manager.IndexToNode(index))
                index = solution.Value(routing.NextVar(index))
            routes.append({"vehicle_id": request.vehicles[vehicle_idx].id, "nodes": route_nodes})

    est_fuel = len(request.ward_ids) * 2.5 * num_vehicles  # placeholder L/ward

    return OptimizeSprayResponse(
        routes=routes,
        total_fuel_liters=est_fuel,
        estimated_cost_inr=est_fuel * 95.0,
        solver_status=status,
    )
