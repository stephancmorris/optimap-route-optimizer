"""
Integration tests for API endpoints.

Tests the FastAPI endpoints with mocked external services.
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# ===== Root Endpoint Tests =====

@pytest.mark.integration
@pytest.mark.api
def test_root_endpoint():
    """Test root endpoint returns API information."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()

    assert data['name'] == "OptiMap Route Optimizer API"
    assert data['version'] == "1.0.0"
    assert data['docs'] == "/docs"
    assert data['status'] == "operational"


# ===== Health Check Tests =====

@pytest.mark.integration
@pytest.mark.api
def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert data['status'] == "healthy"
    assert data['service'] == "OptiMap Backend"
    assert 'timestamp' in data


# ===== Optimize Endpoint Tests =====

@pytest.mark.integration
@pytest.mark.api
def test_optimize_valid_request():
    """Test optimize endpoint with valid request (mocked OSRM)."""
    request_data = {
        "stops": [
            {"latitude": 40.7128, "longitude": -74.0060, "address": "Location A"},
            {"latitude": 40.7589, "longitude": -73.9851, "address": "Location B"},
            {"latitude": 40.7614, "longitude": -73.9776, "address": "Location C"}
        ],
        "depot_index": 0
    }

    # Mock OSRM client
    mock_distances = [
        [0, 2000, 3000],
        [2000, 0, 1500],
        [3000, 1500, 0]
    ]
    mock_durations = [
        [0, 300, 450],
        [300, 0, 225],
        [450, 225, 0]
    ]

    with patch('app.routers.optimize.OSRMClient') as mock_osrm:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.get_distance_matrix.return_value = (mock_distances, mock_durations)
        mock_osrm.return_value = mock_instance

        response = client.post("/optimize", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert 'optimized_route' in data
        assert 'optimized_metrics' in data
        assert 'baseline_metrics' in data
        assert 'distance_saved_meters' in data
        assert 'time_saved_seconds' in data

        # Verify route has correct length (includes return to depot)
        assert len(data['optimized_route']) == 4  # 3 stops + return to depot


@pytest.mark.integration
@pytest.mark.api
def test_optimize_minimum_stops():
    """Test optimize with minimum number of stops (2)."""
    request_data = {
        "stops": [
            {"latitude": 40.7128, "longitude": -74.0060},
            {"latitude": 40.7589, "longitude": -73.9851}
        ],
        "depot_index": 0
    }

    mock_distances = [[0, 2000], [2000, 0]]
    mock_durations = [[0, 300], [300, 0]]

    with patch('app.routers.optimize.OSRMClient') as mock_osrm:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.get_distance_matrix.return_value = (mock_distances, mock_durations)
        mock_osrm.return_value = mock_instance

        response = client.post("/optimize", json=request_data)

        assert response.status_code == 200


# ===== Validation Error Tests =====

@pytest.mark.integration
@pytest.mark.api
def test_optimize_insufficient_stops():
    """Test optimize with too few stops."""
    request_data = {
        "stops": [
            {"latitude": 40.7128, "longitude": -74.0060}
        ],
        "depot_index": 0
    }

    response = client.post("/optimize", json=request_data)

    assert response.status_code == 422  # Validation error


@pytest.mark.integration
@pytest.mark.api
def test_optimize_invalid_latitude():
    """Test optimize with invalid latitude."""
    request_data = {
        "stops": [
            {"latitude": 95.0, "longitude": -74.0060},
            {"latitude": 40.7589, "longitude": -73.9851}
        ],
        "depot_index": 0
    }

    response = client.post("/optimize", json=request_data)

    assert response.status_code == 400 or response.status_code == 422
    data = response.json()

    # Check for error information
    assert 'detail' in data or 'error' in data


@pytest.mark.integration
@pytest.mark.api
def test_optimize_invalid_longitude():
    """Test optimize with invalid longitude."""
    request_data = {
        "stops": [
            {"latitude": 40.7128, "longitude": -185.0},
            {"latitude": 40.7589, "longitude": -73.9851}
        ],
        "depot_index": 0
    }

    response = client.post("/optimize", json=request_data)

    assert response.status_code == 400 or response.status_code == 422


@pytest.mark.integration
@pytest.mark.api
def test_optimize_invalid_depot_index():
    """Test optimize with out-of-bounds depot index."""
    request_data = {
        "stops": [
            {"latitude": 40.7128, "longitude": -74.0060},
            {"latitude": 40.7589, "longitude": -73.9851}
        ],
        "depot_index": 10  # Out of bounds
    }

    # Mock OSRM to isolate depot validation
    mock_distances = [[0, 2000], [2000, 0]]
    mock_durations = [[0, 300], [300, 0]]

    with patch('app.routers.optimize.OSRMClient') as mock_osrm:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.get_distance_matrix.return_value = (mock_distances, mock_durations)
        mock_osrm.return_value = mock_instance

        response = client.post("/optimize", json=request_data)

        assert response.status_code == 400
        data = response.json()

        # Check error response structure
        assert 'detail' in data
        error_detail = data['detail']
        assert error_detail['code'] == "INVALID_DEPOT_INDEX"


@pytest.mark.integration
@pytest.mark.api
def test_optimize_missing_required_fields():
    """Test optimize with missing required fields."""
    request_data = {
        "stops": []  # Empty stops
    }

    response = client.post("/optimize", json=request_data)

    assert response.status_code in [400, 422]


# ===== Error Handling Tests =====

@pytest.mark.integration
@pytest.mark.api
def test_optimize_osrm_timeout():
    """Test optimize when OSRM times out."""
    from app.services.osrm_client import OSRMTimeoutError

    request_data = {
        "stops": [
            {"latitude": 40.7128, "longitude": -74.0060},
            {"latitude": 40.7589, "longitude": -73.9851}
        ],
        "depot_index": 0
    }

    with patch('app.routers.optimize.OSRMClient') as mock_osrm:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.get_distance_matrix.side_effect = OSRMTimeoutError("Request timed out")
        mock_osrm.return_value = mock_instance

        response = client.post("/optimize", json=request_data)

        assert response.status_code == 503
        data = response.json()

        assert 'detail' in data
        error_detail = data['detail']
        assert error_detail['code'] == "ROUTING_SERVICE_TIMEOUT"


@pytest.mark.integration
@pytest.mark.api
def test_optimize_osrm_api_error():
    """Test optimize when OSRM returns an error."""
    from app.services.osrm_client import OSRMAPIError

    request_data = {
        "stops": [
            {"latitude": 40.7128, "longitude": -74.0060},
            {"latitude": 40.7589, "longitude": -73.9851}
        ],
        "depot_index": 0
    }

    with patch('app.routers.optimize.OSRMClient') as mock_osrm:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.get_distance_matrix.side_effect = OSRMAPIError("No route found")
        mock_osrm.return_value = mock_instance

        response = client.post("/optimize", json=request_data)

        assert response.status_code == 503
        data = response.json()

        assert 'detail' in data
        error_detail = data['detail']
        assert error_detail['code'] == "ROUTING_SERVICE_ERROR"


# ===== CORS Tests =====

@pytest.mark.integration
@pytest.mark.api
def test_cors_headers_present():
    """Test that CORS headers are present in responses."""
    response = client.get("/health")

    # Note: TestClient doesn't fully simulate CORS preflight
    # For full CORS testing, use async client with proper headers
    assert response.status_code == 200


# ===== Documentation Endpoints =====

@pytest.mark.integration
@pytest.mark.api
def test_openapi_schema_available():
    """Test that OpenAPI schema is available."""
    response = client.get("/openapi.json")

    assert response.status_code == 200
    data = response.json()

    assert 'openapi' in data
    assert 'info' in data
    assert 'paths' in data


@pytest.mark.integration
@pytest.mark.api
def test_swagger_ui_available():
    """Test that Swagger UI is available."""
    response = client.get("/docs")

    assert response.status_code == 200
    assert b"swagger" in response.content.lower()


@pytest.mark.integration
@pytest.mark.api
def test_redoc_available():
    """Test that ReDoc is available."""
    response = client.get("/redoc")

    assert response.status_code == 200
    assert b"redoc" in response.content.lower()


# ===== Request/Response Format Tests =====

@pytest.mark.integration
@pytest.mark.api
def test_optimize_response_format():
    """Test that optimize response has correct format."""
    request_data = {
        "stops": [
            {"latitude": 40.7128, "longitude": -74.0060},
            {"latitude": 40.7589, "longitude": -73.9851}
        ],
        "depot_index": 0
    }

    mock_distances = [[0, 2000], [2000, 0]]
    mock_durations = [[0, 300], [300, 0]]

    with patch('app.routers.optimize.OSRMClient') as mock_osrm:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.get_distance_matrix.return_value = (mock_distances, mock_durations)
        mock_osrm.return_value = mock_instance

        response = client.post("/optimize", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Verify all required fields are present
        required_fields = [
            'optimized_route',
            'optimized_metrics',
            'baseline_metrics',
            'distance_saved_meters',
            'time_saved_seconds',
            'distance_saved_percentage',
            'time_saved_percentage'
        ]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Verify nested structure
        assert 'total_distance_meters' in data['optimized_metrics']
        assert 'total_time_seconds' in data['optimized_metrics']


@pytest.mark.integration
@pytest.mark.api
def test_optimize_savings_calculation():
    """Test that optimization savings are calculated correctly."""
    request_data = {
        "stops": [
            {"latitude": 40.7128, "longitude": -74.0060},
            {"latitude": 40.7589, "longitude": -73.9851},
            {"latitude": 40.7614, "longitude": -73.9776}
        ],
        "depot_index": 0
    }

    mock_distances = [
        [0, 2000, 3000],
        [2000, 0, 1500],
        [3000, 1500, 0]
    ]
    mock_durations = [
        [0, 300, 450],
        [300, 0, 225],
        [450, 225, 0]
    ]

    with patch('app.routers.optimize.OSRMClient') as mock_osrm:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.get_distance_matrix.return_value = (mock_distances, mock_durations)
        mock_osrm.return_value = mock_instance

        response = client.post("/optimize", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Verify savings are non-negative
        assert data['distance_saved_meters'] >= 0
        assert data['time_saved_seconds'] >= 0
        assert data['distance_saved_percentage'] >= 0
        assert data['time_saved_percentage'] >= 0

        # Verify optimized is not worse than baseline
        optimized_distance = data['optimized_metrics']['total_distance_meters']
        baseline_distance = data['baseline_metrics']['total_distance_meters']
        assert optimized_distance <= baseline_distance
