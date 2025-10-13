"""
Unit tests for Pydantic models.

Tests validation, serialization, and deserialization of data models.
"""

import pytest
from pydantic import ValidationError

from app.models.route import (
    Location,
    OptimizationRequest,
    RouteMetrics,
    OptimizationResponse
)


# ===== Location Model Tests =====

@pytest.mark.unit
@pytest.mark.models
def test_location_valid_coordinates():
    """Test Location with valid coordinates."""
    location = Location(
        latitude=40.7128,
        longitude=-74.0060,
        address="New York, NY"
    )

    assert location.latitude == 40.7128
    assert location.longitude == -74.0060
    assert location.address == "New York, NY"


@pytest.mark.unit
@pytest.mark.models
def test_location_without_address():
    """Test Location without optional address."""
    location = Location(latitude=40.7128, longitude=-74.0060)

    assert location.latitude == 40.7128
    assert location.longitude == -74.0060
    assert location.address is None


@pytest.mark.unit
@pytest.mark.models
def test_location_invalid_latitude_too_high():
    """Test Location with latitude > 90."""
    with pytest.raises(ValidationError) as exc_info:
        Location(latitude=95.0, longitude=-74.0060)

    errors = exc_info.value.errors()
    assert any('latitude' in str(error) for error in errors)


@pytest.mark.unit
@pytest.mark.models
def test_location_invalid_latitude_too_low():
    """Test Location with latitude < -90."""
    with pytest.raises(ValidationError) as exc_info:
        Location(latitude=-95.0, longitude=-74.0060)

    errors = exc_info.value.errors()
    assert any('latitude' in str(error) for error in errors)


@pytest.mark.unit
@pytest.mark.models
def test_location_invalid_longitude_too_high():
    """Test Location with longitude > 180."""
    with pytest.raises(ValidationError) as exc_info:
        Location(latitude=40.7128, longitude=185.0)

    errors = exc_info.value.errors()
    assert any('longitude' in str(error) for error in errors)


@pytest.mark.unit
@pytest.mark.models
def test_location_invalid_longitude_too_low():
    """Test Location with longitude < -180."""
    with pytest.raises(ValidationError) as exc_info:
        Location(latitude=40.7128, longitude=-185.0)

    errors = exc_info.value.errors()
    assert any('longitude' in str(error) for error in errors)


@pytest.mark.unit
@pytest.mark.models
def test_location_boundary_values():
    """Test Location with boundary coordinate values."""
    # Maximum valid values
    location_max = Location(latitude=90.0, longitude=180.0)
    assert location_max.latitude == 90.0
    assert location_max.longitude == 180.0

    # Minimum valid values
    location_min = Location(latitude=-90.0, longitude=-180.0)
    assert location_min.latitude == -90.0
    assert location_min.longitude == -180.0


@pytest.mark.unit
@pytest.mark.models
def test_location_serialization():
    """Test Location model serialization."""
    location = Location(
        latitude=40.7128,
        longitude=-74.0060,
        address="New York, NY"
    )

    data = location.model_dump()

    assert data['latitude'] == 40.7128
    assert data['longitude'] == -74.0060
    assert data['address'] == "New York, NY"


@pytest.mark.unit
@pytest.mark.models
def test_location_deserialization():
    """Test Location model deserialization."""
    data = {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "address": "New York, NY"
    }

    location = Location(**data)

    assert location.latitude == 40.7128
    assert location.longitude == -74.0060
    assert location.address == "New York, NY"


# ===== OptimizationRequest Model Tests =====

@pytest.mark.unit
@pytest.mark.models
def test_optimization_request_valid(sample_locations):
    """Test OptimizationRequest with valid data."""
    request = OptimizationRequest(
        stops=sample_locations,
        depot_index=0
    )

    assert len(request.stops) == 4
    assert request.depot_index == 0


@pytest.mark.unit
@pytest.mark.models
def test_optimization_request_default_depot():
    """Test OptimizationRequest with default depot index."""
    request = OptimizationRequest(
        stops=[
            Location(latitude=40.7128, longitude=-74.0060),
            Location(latitude=40.7589, longitude=-73.9851)
        ]
    )

    assert request.depot_index == 0  # Default value


@pytest.mark.unit
@pytest.mark.models
def test_optimization_request_custom_depot(sample_locations):
    """Test OptimizationRequest with custom depot index."""
    request = OptimizationRequest(
        stops=sample_locations,
        depot_index=2
    )

    assert request.depot_index == 2


@pytest.mark.unit
@pytest.mark.models
def test_optimization_request_insufficient_stops():
    """Test OptimizationRequest with too few stops."""
    with pytest.raises(ValidationError) as exc_info:
        OptimizationRequest(
            stops=[Location(latitude=40.7128, longitude=-74.0060)]
        )

    errors = exc_info.value.errors()
    assert any('stops' in str(error) for error in errors)


@pytest.mark.unit
@pytest.mark.models
def test_optimization_request_negative_depot():
    """Test OptimizationRequest with negative depot index."""
    with pytest.raises(ValidationError) as exc_info:
        OptimizationRequest(
            stops=[
                Location(latitude=40.7128, longitude=-74.0060),
                Location(latitude=40.7589, longitude=-73.9851)
            ],
            depot_index=-1
        )

    errors = exc_info.value.errors()
    assert any('depot_index' in str(error) for error in errors)


# ===== RouteMetrics Model Tests =====

@pytest.mark.unit
@pytest.mark.models
def test_route_metrics_valid():
    """Test RouteMetrics with valid data."""
    metrics = RouteMetrics(
        total_distance_meters=8420.5,
        total_time_seconds=1245.8
    )

    assert metrics.total_distance_meters == 8420.5
    assert metrics.total_time_seconds == 1245.8


@pytest.mark.unit
@pytest.mark.models
def test_route_metrics_zero_values():
    """Test RouteMetrics with zero values."""
    metrics = RouteMetrics(
        total_distance_meters=0.0,
        total_time_seconds=0.0
    )

    assert metrics.total_distance_meters == 0.0
    assert metrics.total_time_seconds == 0.0


@pytest.mark.unit
@pytest.mark.models
def test_route_metrics_serialization():
    """Test RouteMetrics serialization."""
    metrics = RouteMetrics(
        total_distance_meters=8420.5,
        total_time_seconds=1245.8
    )

    data = metrics.model_dump()

    assert data['total_distance_meters'] == 8420.5
    assert data['total_time_seconds'] == 1245.8


# ===== OptimizationResponse Model Tests =====

@pytest.mark.unit
@pytest.mark.models
def test_optimization_response_valid(sample_locations):
    """Test OptimizationResponse with valid data."""
    response = OptimizationResponse(
        optimized_route=sample_locations,
        optimized_metrics=RouteMetrics(
            total_distance_meters=8420.5,
            total_time_seconds=1245.8
        ),
        baseline_metrics=RouteMetrics(
            total_distance_meters=10850.2,
            total_time_seconds=1580.4
        ),
        distance_saved_meters=2429.7,
        time_saved_seconds=334.6,
        distance_saved_percentage=22.4,
        time_saved_percentage=21.2
    )

    assert len(response.optimized_route) == 4
    assert response.optimized_metrics.total_distance_meters == 8420.5
    assert response.baseline_metrics.total_distance_meters == 10850.2
    assert response.distance_saved_meters == 2429.7
    assert response.time_saved_seconds == 334.6


@pytest.mark.unit
@pytest.mark.models
def test_optimization_response_no_improvement():
    """Test OptimizationResponse when optimization matches baseline."""
    response = OptimizationResponse(
        optimized_route=[
            Location(latitude=40.7128, longitude=-74.0060),
            Location(latitude=40.7589, longitude=-73.9851)
        ],
        optimized_metrics=RouteMetrics(
            total_distance_meters=5000.0,
            total_time_seconds=600.0
        ),
        baseline_metrics=RouteMetrics(
            total_distance_meters=5000.0,
            total_time_seconds=600.0
        ),
        distance_saved_meters=0.0,
        time_saved_seconds=0.0,
        distance_saved_percentage=0.0,
        time_saved_percentage=0.0
    )

    assert response.distance_saved_meters == 0.0
    assert response.distance_saved_percentage == 0.0


@pytest.mark.unit
@pytest.mark.models
def test_optimization_response_serialization(sample_locations):
    """Test OptimizationResponse serialization."""
    response = OptimizationResponse(
        optimized_route=sample_locations,
        optimized_metrics=RouteMetrics(
            total_distance_meters=8420.5,
            total_time_seconds=1245.8
        ),
        baseline_metrics=RouteMetrics(
            total_distance_meters=10850.2,
            total_time_seconds=1580.4
        ),
        distance_saved_meters=2429.7,
        time_saved_seconds=334.6,
        distance_saved_percentage=22.4,
        time_saved_percentage=21.2
    )

    data = response.model_dump()

    assert 'optimized_route' in data
    assert 'optimized_metrics' in data
    assert 'baseline_metrics' in data
    assert data['distance_saved_meters'] == 2429.7


@pytest.mark.unit
@pytest.mark.models
def test_optimization_response_json_serialization(sample_locations):
    """Test OptimizationResponse JSON serialization."""
    response = OptimizationResponse(
        optimized_route=sample_locations[:2],
        optimized_metrics=RouteMetrics(
            total_distance_meters=8420.5,
            total_time_seconds=1245.8
        ),
        baseline_metrics=RouteMetrics(
            total_distance_meters=10850.2,
            total_time_seconds=1580.4
        ),
        distance_saved_meters=2429.7,
        time_saved_seconds=334.6,
        distance_saved_percentage=22.4,
        time_saved_percentage=21.2
    )

    json_str = response.model_dump_json()

    assert isinstance(json_str, str)
    assert "optimized_route" in json_str
    assert "8420.5" in json_str


# ===== Edge Cases and Integration =====

@pytest.mark.unit
@pytest.mark.models
def test_full_request_response_cycle(sample_locations):
    """Test complete request -> response cycle."""
    # Create request
    request = OptimizationRequest(
        stops=sample_locations,
        depot_index=0
    )

    # Simulate processing
    request_data = request.model_dump()
    assert len(request_data['stops']) == 4

    # Create response
    response = OptimizationResponse(
        optimized_route=sample_locations,
        optimized_metrics=RouteMetrics(
            total_distance_meters=8420.5,
            total_time_seconds=1245.8
        ),
        baseline_metrics=RouteMetrics(
            total_distance_meters=10850.2,
            total_time_seconds=1580.4
        ),
        distance_saved_meters=2429.7,
        time_saved_seconds=334.6,
        distance_saved_percentage=22.4,
        time_saved_percentage=21.2
    )

    # Verify response
    assert len(response.optimized_route) == len(request.stops)
    assert response.distance_saved_meters > 0
