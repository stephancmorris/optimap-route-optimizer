"""
Vehicle Routing Problem (VRP) solver using Google OR-Tools.

This module provides utilities for solving the Traveling Salesman Problem (TSP)
and Vehicle Routing Problem (VRP) using Google's OR-Tools optimization library.
"""

from typing import List, Tuple, Optional
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp


class ORToolsVRPSolver:
    """
    Wrapper for Google OR-Tools VRP solver.

    Handles initialization, configuration, and execution of the Vehicle Routing
    Problem algorithm for last-mile route optimization.
    """

    def __init__(self, time_limit_seconds: int = 30):
        """
        Initialize the VRP solver.

        Args:
            time_limit_seconds: Maximum time allowed for solver to find solution
        """
        self.time_limit_seconds = time_limit_seconds

    def create_data_model(
        self,
        distance_matrix: List[List[float]],
        num_vehicles: int = 1,
        depot: int = 0
    ) -> dict:
        """
        Create the data model for the routing problem.

        Args:
            distance_matrix: 2D matrix of distances between all location pairs
            num_vehicles: Number of vehicles (default 1 for TSP)
            depot: Index of starting/ending location

        Returns:
            dict: Data model for OR-Tools solver
        """
        data = {
            'distance_matrix': distance_matrix,
            'num_vehicles': num_vehicles,
            'depot': depot
        }
        return data

    def solve(
        self,
        distance_matrix: List[List[float]],
        num_vehicles: int = 1,
        depot: int = 0
    ) -> Optional[Tuple[List[int], int]]:
        """
        Solve the VRP problem and return optimal route.

        Args:
            distance_matrix: 2D matrix of distances between locations
            num_vehicles: Number of vehicles to optimize for
            depot: Starting depot index

        Returns:
            Tuple of (route_indices, total_distance) or None if no solution found
        """
        # Create data model
        data = self.create_data_model(distance_matrix, num_vehicles, depot)

        # Create the routing index manager
        manager = pywrapcp.RoutingIndexManager(
            len(data['distance_matrix']),
            data['num_vehicles'],
            data['depot']
        )

        # Create routing model
        routing = pywrapcp.RoutingModel(manager)

        # Create distance callback
        def distance_callback(from_index: int, to_index: int) -> int:
            """Returns the distance between the two nodes."""
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return int(data['distance_matrix'][from_node][to_node])

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)

        # Define cost of each arc
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Set search parameters
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.time_limit.seconds = self.time_limit_seconds

        # Solve the problem
        solution = routing.SolveWithParameters(search_parameters)

        if solution:
            return self._extract_solution(manager, routing, solution)
        else:
            return None

    def _extract_solution(
        self,
        manager: pywrapcp.RoutingIndexManager,
        routing: pywrapcp.RoutingModel,
        solution: pywrapcp.Assignment
    ) -> Tuple[List[int], int]:
        """
        Extract route and total distance from solution.

        Args:
            manager: Routing index manager
            routing: Routing model
            solution: Solution from solver

        Returns:
            Tuple of (route_indices, total_distance)
        """
        route = []
        index = routing.Start(0)  # Start at vehicle 0's route

        while not routing.IsEnd(index):
            route.append(manager.IndexToNode(index))
            index = solution.Value(routing.NextVar(index))

        # Add the final depot
        route.append(manager.IndexToNode(index))

        # Get total distance
        total_distance = solution.ObjectiveValue()

        return route, int(total_distance)


def get_solver_info() -> dict:
    """
    Get information about the OR-Tools solver.

    Returns:
        dict: Solver version and configuration info
    """
    import ortools

    return {
        "library": "Google OR-Tools",
        "version": ortools.__version__,
        "solver_type": "Constraint Programming (CP-SAT)",
        "algorithm": "Vehicle Routing Problem (VRP)",
        "python_compatible": True
    }
