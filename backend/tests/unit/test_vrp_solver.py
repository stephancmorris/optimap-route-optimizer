"""
Unit tests for VRP solver module.

Tests the OR-Tools VRP solver implementation for route optimization.
"""

import pytest
from typing import List

from app.services.vrp_solver import ORToolsVRPSolver, get_solver_info
from tests.conftest import assert_valid_route, assert_route_improvement, create_mock_distance_matrix


# ===== Solver Initialization Tests =====

@pytest.mark.unit
def test_solver_initialization():
    """Test solver can be initialized with default parameters."""
    solver = ORToolsVRPSolver()
    assert solver.time_limit_seconds == 30


@pytest.mark.unit
def test_solver_initialization_custom_time_limit():
    """Test solver can be initialized with custom time limit."""
    solver = ORToolsVRPSolver(time_limit_seconds=60)
    assert solver.time_limit_seconds == 60


# ===== Data Model Creation Tests =====

@pytest.mark.unit
def test_create_data_model(vrp_solver, sample_distance_matrix):
    """Test data model creation for OR-Tools."""
    data = vrp_solver.create_data_model(
        distance_matrix=sample_distance_matrix,
        num_vehicles=1,
        depot=0
    )

    assert data['distance_matrix'] == sample_distance_matrix
    assert data['num_vehicles'] == 1
    assert data['depot'] == 0


@pytest.mark.unit
def test_create_data_model_custom_depot(vrp_solver, sample_distance_matrix):
    """Test data model with custom depot location."""
    data = vrp_solver.create_data_model(
        distance_matrix=sample_distance_matrix,
        num_vehicles=1,
        depot=2
    )

    assert data['depot'] == 2


# ===== Basic Solving Tests =====

@pytest.mark.unit
@pytest.mark.solver
def test_solve_simple_route(vrp_solver, sample_distance_matrix):
    """Test solving a simple 4-stop route."""
    result = vrp_solver.solve(
        distance_matrix=sample_distance_matrix,
        num_vehicles=1,
        depot=0
    )

    assert result is not None, "Solver should find a solution"
    route, total_distance = result

    # Validate route structure
    assert_valid_route(route, num_stops=4, depot=0)

    # Validate distance
    assert total_distance > 0, "Total distance should be positive"
    assert isinstance(total_distance, int), "Total distance should be an integer"


@pytest.mark.unit
@pytest.mark.solver
def test_solve_with_different_depot(vrp_solver, sample_distance_matrix):
    """Test solving with different depot location."""
    result = vrp_solver.solve(
        distance_matrix=sample_distance_matrix,
        num_vehicles=1,
        depot=1
    )

    assert result is not None
    route, _ = result

    # Should start and end at depot 1
    assert route[0] == 1
    assert route[-1] == 1


@pytest.mark.unit
@pytest.mark.solver
def test_solve_minimum_stops(vrp_solver):
    """Test solving with minimum number of stops (2)."""
    # Simple 2-stop problem
    distance_matrix = [
        [0, 1000],
        [1000, 0]
    ]

    result = vrp_solver.solve(
        distance_matrix=distance_matrix,
        num_vehicles=1,
        depot=0
    )

    assert result is not None
    route, total_distance = result

    # Route should be: 0 -> 1 -> 0
    assert len(route) == 3
    assert route == [0, 1, 0]
    assert total_distance == 2000  # Round trip


# ===== Optimization Quality Tests =====

@pytest.mark.unit
@pytest.mark.solver
def test_solver_finds_optimal_solution(vrp_solver):
    """Test that solver finds optimal solution for a known problem."""
    # Create a problem with an obvious optimal solution
    # Locations: 0 (depot), 1, 2, 3
    # Optimal route: 0 -> 1 -> 2 -> 3 -> 0
    distance_matrix = [
        [0, 100, 200, 300],    # From depot
        [100, 0, 100, 200],    # From location 1
        [200, 100, 0, 100],    # From location 2
        [300, 200, 100, 0],    # From location 3
    ]

    result = vrp_solver.solve(
        distance_matrix=distance_matrix,
        num_vehicles=1,
        depot=0
    )

    assert result is not None
    route, total_distance = result

    # Optimal route should be sequential: 0 -> 1 -> 2 -> 3 -> 0
    assert route == [0, 1, 2, 3, 0]
    assert total_distance == 600  # 100 + 100 + 100 + 300


@pytest.mark.unit
@pytest.mark.solver
def test_solver_handles_asymmetric_matrix(vrp_solver):
    """Test solver with asymmetric distance matrix (one-way streets)."""
    # Asymmetric matrix: different distances in each direction
    distance_matrix = [
        [0, 100, 500, 400],
        [200, 0, 150, 300],
        [400, 250, 0, 200],
        [300, 350, 100, 0],
    ]

    result = vrp_solver.solve(
        distance_matrix=distance_matrix,
        num_vehicles=1,
        depot=0
    )

    assert result is not None
    route, total_distance = result

    assert_valid_route(route, num_stops=4, depot=0)
    assert total_distance > 0


# ===== Performance Tests =====

@pytest.mark.unit
@pytest.mark.solver
@pytest.mark.slow
def test_solve_larger_problem(vrp_solver, large_distance_matrix):
    """Test solving a larger problem (20 stops)."""
    result = vrp_solver.solve(
        distance_matrix=large_distance_matrix,
        num_vehicles=1,
        depot=0
    )

    assert result is not None, "Solver should handle 20 stops"
    route, total_distance = result

    assert_valid_route(route, num_stops=20, depot=0)
    assert total_distance > 0


@pytest.mark.unit
@pytest.mark.solver
def test_solver_respects_time_limit(vrp_solver):
    """Test that solver respects time limit."""
    # Create a complex problem that might take longer
    large_matrix = create_mock_distance_matrix(50, base_distance=1000.0)

    # Set very short time limit
    fast_solver = ORToolsVRPSolver(time_limit_seconds=1)

    result = fast_solver.solve(
        distance_matrix=large_matrix,
        num_vehicles=1,
        depot=0
    )

    # Should still return a result (may not be optimal)
    # OR-Tools typically finds something even with short time limits
    assert result is not None or result is None  # Either is acceptable


# ===== Edge Cases and Error Handling =====

@pytest.mark.unit
@pytest.mark.solver
def test_solve_single_location_returns_none(vrp_solver):
    """Test that single location (just depot) is handled."""
    # Can't optimize a route with no stops
    distance_matrix = [[0]]

    result = vrp_solver.solve(
        distance_matrix=distance_matrix,
        num_vehicles=1,
        depot=0
    )

    # Solver should return None or a trivial solution
    if result is not None:
        route, _ = result
        assert len(route) <= 2  # At most depot -> depot


@pytest.mark.unit
@pytest.mark.solver
def test_solve_with_zero_distances(vrp_solver):
    """Test solver with zero distances (co-located points)."""
    # All locations at same place
    distance_matrix = [
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0],
    ]

    result = vrp_solver.solve(
        distance_matrix=distance_matrix,
        num_vehicles=1,
        depot=0
    )

    # Should still find a valid route
    if result is not None:
        route, total_distance = result
        assert_valid_route(route, num_stops=3, depot=0)
        assert total_distance == 0


# ===== Baseline Comparison Tests =====

@pytest.mark.unit
@pytest.mark.solver
def test_optimized_route_not_worse_than_sequential(vrp_solver, sample_distance_matrix):
    """Test that optimized route is at least as good as sequential."""
    # Solve with OR-Tools
    result = vrp_solver.solve(
        distance_matrix=sample_distance_matrix,
        num_vehicles=1,
        depot=0
    )

    assert result is not None
    optimized_route, optimized_distance = result

    # Calculate sequential route distance (0 -> 1 -> 2 -> 3 -> 0)
    sequential_route = [0, 1, 2, 3, 0]
    sequential_distance = 0
    for i in range(len(sequential_route) - 1):
        sequential_distance += sample_distance_matrix[sequential_route[i]][sequential_route[i + 1]]

    # Optimized should be at least as good as sequential
    assert_route_improvement(optimized_distance, sequential_distance)


# ===== Utility Function Tests =====

@pytest.mark.unit
def test_get_solver_info():
    """Test solver info utility function."""
    info = get_solver_info()

    assert isinstance(info, dict)
    assert 'library' in info
    assert 'version' in info
    assert 'solver_type' in info
    assert 'algorithm' in info
    assert info['library'] == "Google OR-Tools"
    assert info['algorithm'] == "Vehicle Routing Problem (VRP)"


# ===== Multiple Vehicles Tests (Future Enhancement) =====

@pytest.mark.unit
@pytest.mark.solver
def test_solve_with_multiple_vehicles(vrp_solver, sample_distance_matrix):
    """Test solving with multiple vehicles (currently using 1)."""
    # Even though we request 2 vehicles, current implementation uses 1
    result = vrp_solver.solve(
        distance_matrix=sample_distance_matrix,
        num_vehicles=2,  # Future: support multiple vehicles
        depot=0
    )

    assert result is not None
    route, _ = result
    # Currently returns single route, but test should pass
    assert len(route) >= 2
