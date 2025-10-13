"""
Unit tests for OSRM client module.

Tests the OSRM API client for distance matrix calculations.
Uses mocking to avoid real API calls in unit tests.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import List

from app.services.osrm_client import (
    OSRMClient,
    OSRMClientError,
    OSRMTimeoutError,
    OSRMAPIError
)
from app.models.route import Location


# ===== Client Initialization Tests =====

@pytest.mark.unit
def test_osrm_client_initialization():
    """Test OSRM client can be initialized with default parameters."""
    client = OSRMClient()

    assert client.base_url == "http://router.project-osrm.org"
    assert client.timeout_seconds == 30.0
    assert client.max_retries == 3


@pytest.mark.unit
def test_osrm_client_initialization_custom_parameters():
    """Test OSRM client with custom parameters."""
    client = OSRMClient(
        base_url="https://custom-osrm.example.com",
        timeout_seconds=60.0,
        max_retries=5
    )

    assert client.base_url == "https://custom-osrm.example.com"
    assert client.timeout_seconds == 60.0
    assert client.max_retries == 5


@pytest.mark.unit
def test_osrm_client_strips_trailing_slash():
    """Test that trailing slash is removed from base URL."""
    client = OSRMClient(base_url="http://example.com/")

    assert client.base_url == "http://example.com"


# ===== Coordinate Formatting Tests =====

@pytest.mark.unit
def test_format_coordinates(osrm_client, sample_locations_two_stops):
    """Test coordinate formatting for OSRM API."""
    coords_string = osrm_client._format_coordinates(sample_locations_two_stops)

    # OSRM format: longitude,latitude;longitude,latitude
    assert coords_string == "-74.006,40.7128;-73.9851,40.7589"


@pytest.mark.unit
def test_format_coordinates_multiple_locations(osrm_client, sample_locations):
    """Test coordinate formatting with multiple locations."""
    coords_string = osrm_client._format_coordinates(sample_locations)

    # Should have semicolons separating locations
    assert coords_string.count(';') == len(sample_locations) - 1

    # Should have all coordinates
    assert "-74.006,40.7128" in coords_string
    assert "-73.9851,40.7589" in coords_string


# ===== Distance Matrix Tests (Mocked) =====

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_distance_matrix_success(osrm_client, sample_locations_two_stops):
    """Test successful distance matrix calculation."""
    # Mock OSRM API response
    mock_response = {
        "code": "Ok",
        "distances": [
            [0, 2000],
            [2000, 0]
        ],
        "durations": [
            [0, 300],
            [300, 0]
        ]
    }

    with patch.object(osrm_client, '_make_request', new=AsyncMock(return_value=mock_response)):
        distances, durations = await osrm_client.get_distance_matrix(sample_locations_two_stops)

        assert distances == [[0, 2000], [2000, 0]]
        assert durations == [[0, 300], [300, 0]]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_distance_matrix_multiple_locations(osrm_client, sample_locations):
    """Test distance matrix with multiple locations."""
    # Mock 4x4 matrix response
    mock_response = {
        "code": "Ok",
        "distances": [
            [0, 2000, 3000, 2500],
            [2000, 0, 1500, 1800],
            [3000, 1500, 0, 2200],
            [2500, 1800, 2200, 0]
        ],
        "durations": [
            [0, 300, 450, 375],
            [300, 0, 225, 270],
            [450, 225, 0, 330],
            [375, 270, 330, 0]
        ]
    }

    with patch.object(osrm_client, '_make_request', new=AsyncMock(return_value=mock_response)):
        distances, durations = await osrm_client.get_distance_matrix(sample_locations)

        assert len(distances) == 4
        assert len(durations) == 4
        assert all(len(row) == 4 for row in distances)
        assert all(len(row) == 4 for row in durations)


# ===== Error Handling Tests =====

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_distance_matrix_insufficient_locations(osrm_client):
    """Test that single location raises ValueError."""
    single_location = [Location(latitude=40.7128, longitude=-74.0060)]

    with pytest.raises(ValueError, match="At least 2 locations required"):
        await osrm_client.get_distance_matrix(single_location)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_distance_matrix_empty_list(osrm_client):
    """Test that empty location list raises ValueError."""
    with pytest.raises(ValueError, match="At least 2 locations required"):
        await osrm_client.get_distance_matrix([])


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_distance_matrix_missing_data(osrm_client, sample_locations_two_stops):
    """Test handling of missing distance/duration data."""
    # Mock response missing distances
    mock_response = {
        "code": "Ok",
        "distances": [],
        "durations": []
    }

    with patch.object(osrm_client, '_make_request', new=AsyncMock(return_value=mock_response)):
        with pytest.raises(OSRMAPIError, match="missing distance or duration data"):
            await osrm_client.get_distance_matrix(sample_locations_two_stops)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_distance_matrix_dimension_mismatch(osrm_client, sample_locations):
    """Test handling of matrix dimension mismatch."""
    # Mock response with wrong dimensions
    mock_response = {
        "code": "Ok",
        "distances": [[0, 100], [100, 0]],  # 2x2 instead of 4x4
        "durations": [[0, 10], [10, 0]]
    }

    with patch.object(osrm_client, '_make_request', new=AsyncMock(return_value=mock_response)):
        with pytest.raises(OSRMAPIError, match="Matrix dimension mismatch"):
            await osrm_client.get_distance_matrix(sample_locations)


# ===== HTTP Request Tests (Mocked) =====

@pytest.mark.unit
@pytest.mark.asyncio
async def test_make_request_success(osrm_client):
    """Test successful HTTP request."""
    mock_response_data = {"code": "Ok", "message": "success"}

    # Mock httpx response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status = Mock()

    with patch('app.services.osrm_client.httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        osrm_client._client = mock_client
        result = await osrm_client._make_request("http://example.com/test")

        assert result == mock_response_data


@pytest.mark.unit
@pytest.mark.asyncio
async def test_make_request_osrm_error_code(osrm_client):
    """Test handling of OSRM error code in response."""
    mock_response_data = {
        "code": "NoRoute",
        "message": "No route found between points"
    }

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status = Mock()

    with patch('app.services.osrm_client.httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        osrm_client._client = mock_client

        with pytest.raises(OSRMAPIError, match="No route found"):
            await osrm_client._make_request("http://example.com/test")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_make_request_timeout(osrm_client):
    """Test handling of request timeout."""
    import httpx

    with patch('app.services.osrm_client.httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.TimeoutException("Request timeout")
        mock_client_class.return_value = mock_client

        osrm_client._client = mock_client

        with pytest.raises(OSRMTimeoutError, match="timed out"):
            await osrm_client._make_request("http://example.com/test")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_make_request_http_error(osrm_client):
    """Test handling of HTTP status errors."""
    import httpx

    mock_response = Mock()
    mock_response.status_code = 503
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Service unavailable",
        request=Mock(),
        response=mock_response
    )

    with patch('app.services.osrm_client.httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        osrm_client._client = mock_client

        with pytest.raises(OSRMAPIError, match="HTTP error: 503"):
            await osrm_client._make_request("http://example.com/test")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_make_request_network_error(osrm_client):
    """Test handling of network errors."""
    import httpx

    with patch('app.services.osrm_client.httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.NetworkError("Connection refused")
        mock_client_class.return_value = mock_client

        osrm_client._client = mock_client

        with pytest.raises(OSRMAPIError, match="Network error"):
            await osrm_client._make_request("http://example.com/test")


# ===== Context Manager Tests =====

@pytest.mark.unit
@pytest.mark.asyncio
async def test_osrm_client_context_manager():
    """Test OSRM client as async context manager."""
    async with OSRMClient() as client:
        assert client._client is not None

    # Client should be closed after context exit
    # (We can't easily test this without accessing private state)


# ===== Route Geometry Tests (get_route method) =====

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_route_success(osrm_client, sample_locations_two_stops):
    """Test successful route geometry retrieval."""
    mock_response = {
        "code": "Ok",
        "routes": [{
            "geometry": {"type": "LineString", "coordinates": []},
            "distance": 2000,
            "duration": 300
        }]
    }

    with patch.object(osrm_client, '_make_request', new=AsyncMock(return_value=mock_response)):
        route = await osrm_client.get_route(sample_locations_two_stops)

        assert route is not None
        assert 'geometry' in route
        assert 'distance' in route


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_route_insufficient_locations(osrm_client):
    """Test get_route with insufficient locations."""
    single_location = [Location(latitude=40.7128, longitude=-74.0060)]

    with pytest.raises(ValueError, match="At least 2 locations required"):
        await osrm_client.get_route(single_location)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_route_missing_routes(osrm_client, sample_locations_two_stops):
    """Test handling of missing routes in response."""
    mock_response = {
        "code": "Ok",
        "routes": []
    }

    with patch.object(osrm_client, '_make_request', new=AsyncMock(return_value=mock_response)):
        with pytest.raises(OSRMAPIError, match="missing route data"):
            await osrm_client.get_route(sample_locations_two_stops)


# ===== Factory Function Tests =====

@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_osrm_client():
    """Test OSRM client factory function."""
    from app.services.osrm_client import create_osrm_client

    client = await create_osrm_client("http://example.com")

    assert isinstance(client, OSRMClient)
    assert client.base_url == "http://example.com"
