"""
Pytest configuration and fixtures for OptiMap backend tests.

This file contains shared fixtures and configuration for all tests.
"""

import pytest
from typing import List, AsyncGenerator
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.main import app
from app.models.route import Location, OptimizationRequest
from app.services.osrm_client import OSRMClient
from app.services.vrp_solver import ORToolsVRPSolver


# ===== Test Data Fixtures =====

@pytest.fixture
def sample_locations() -> List[Location]:
    """Sample locations for testing (NYC landmarks)."""
    return [
        Location(latitude=40.7128, longitude=-74.0060, address="New York, NY"),
        Location(latitude=40.7589, longitude=-73.9851, address="Times Square, NY"),
        Location(latitude=40.7614, longitude=-73.9776, address="Central Park, NY"),
        Location(latitude=40.7484, longitude=-73.9857, address="Empire State Building, NY"),
    ]


@pytest.fixture
def sample_locations_two_stops() -> List[Location]:
    """Minimum two stops for testing."""
    return [
        Location(latitude=40.7128, longitude=-74.0060, address="Location A"),
        Location(latitude=40.7589, longitude=-73.9851, address="Location B"),
    ]


@pytest.fixture
def sample_optimization_request(sample_locations) -> OptimizationRequest:
    """Sample optimization request for testing."""
    return OptimizationRequest(
        stops=sample_locations,
        depot_index=0
    )


@pytest.fixture
def sample_distance_matrix() -> List[List[float]]:
    """
    Sample distance matrix for testing (4x4).

    Represents distances in meters between 4 locations.
    """
    return [
        [0, 2000, 3000, 2500],
        [2000, 0, 1500, 1800],
        [3000, 1500, 0, 2200],
        [2500, 1800, 2200, 0],
    ]


@pytest.fixture
def sample_duration_matrix() -> List[List[float]]:
    """
    Sample duration matrix for testing (4x4).

    Represents travel times in seconds between 4 locations.
    """
    return [
        [0, 300, 450, 375],
        [300, 0, 225, 270],
        [450, 225, 0, 330],
        [375, 270, 330, 0],
    ]


# ===== Service Fixtures =====

@pytest.fixture
def vrp_solver() -> ORToolsVRPSolver:
    """VRP solver instance for testing."""
    return ORToolsVRPSolver(time_limit_seconds=10)


@pytest.fixture
def osrm_client() -> OSRMClient:
    """OSRM client instance for testing (mocked in most tests)."""
    return OSRMClient(
        base_url="http://router.project-osrm.org",
        timeout_seconds=30.0
    )


# ===== API Test Fixtures =====

@pytest.fixture
def test_client() -> TestClient:
    """
    FastAPI test client for synchronous API testing.

    Use this for simple API tests that don't require async.
    """
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP client for asynchronous API testing.

    Use this for tests that need to test async endpoints properly.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# ===== Mock Data Generators =====

def create_mock_distance_matrix(size: int, base_distance: float = 1000.0) -> List[List[float]]:
    """
    Create a mock distance matrix of given size.

    Args:
        size: Number of locations (matrix will be size x size)
        base_distance: Base distance value in meters

    Returns:
        Distance matrix with 0 on diagonal, symmetric values elsewhere
    """
    matrix = [[0.0] * size for _ in range(size)]

    for i in range(size):
        for j in range(i + 1, size):
            # Create some variation in distances
            distance = base_distance * (1 + abs(i - j) * 0.5)
            matrix[i][j] = distance
            matrix[j][i] = distance  # Symmetric matrix

    return matrix


def create_mock_duration_matrix(size: int, base_duration: float = 150.0) -> List[List[float]]:
    """
    Create a mock duration matrix of given size.

    Args:
        size: Number of locations (matrix will be size x size)
        base_duration: Base duration value in seconds

    Returns:
        Duration matrix with 0 on diagonal, symmetric values elsewhere
    """
    matrix = [[0.0] * size for _ in range(size)]

    for i in range(size):
        for j in range(i + 1, size):
            # Create some variation in durations
            duration = base_duration * (1 + abs(i - j) * 0.4)
            matrix[i][j] = duration
            matrix[j][i] = duration  # Symmetric matrix

    return matrix


@pytest.fixture
def large_distance_matrix() -> List[List[float]]:
    """Large distance matrix (20x20) for performance testing."""
    return create_mock_distance_matrix(20, base_distance=5000.0)


@pytest.fixture
def large_duration_matrix() -> List[List[float]]:
    """Large duration matrix (20x20) for performance testing."""
    return create_mock_duration_matrix(20, base_duration=300.0)


# ===== Helper Functions =====

def assert_valid_route(route: List[int], num_stops: int, depot: int = 0) -> None:
    """
    Assert that a route is valid.

    Args:
        route: Route indices
        num_stops: Expected number of stops
        depot: Depot index

    Raises:
        AssertionError: If route is invalid
    """
    assert len(route) == num_stops + 1, f"Route should have {num_stops + 1} locations (including return to depot)"
    assert route[0] == depot, f"Route should start at depot {depot}"
    assert route[-1] == depot, f"Route should end at depot {depot}"
    assert len(set(route[:-1])) == num_stops, "Route should visit each stop exactly once"


def assert_route_improvement(optimized_distance: float, baseline_distance: float, min_improvement: float = 0.0) -> None:
    """
    Assert that optimized route is better than or equal to baseline.

    Args:
        optimized_distance: Distance of optimized route
        baseline_distance: Distance of baseline route
        min_improvement: Minimum improvement percentage required (default: 0%)

    Raises:
        AssertionError: If optimization didn't meet improvement threshold
    """
    assert optimized_distance <= baseline_distance, (
        f"Optimized route ({optimized_distance}) should not be worse than baseline ({baseline_distance})"
    )

    if min_improvement > 0:
        improvement_pct = ((baseline_distance - optimized_distance) / baseline_distance) * 100
        assert improvement_pct >= min_improvement, (
            f"Improvement ({improvement_pct:.1f}%) should be at least {min_improvement}%"
        )


# ===== Pytest Hooks =====

def pytest_configure(config):
    """Pytest configuration hook."""
    # Add custom markers
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config, items):
    """Modify test items after collection."""
    # Auto-mark tests based on their location
    for item in items:
        # Mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        # Mark as unit test if in unit test directory
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
