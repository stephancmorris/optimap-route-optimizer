"""
OSRM (Open Source Routing Machine) API client for distance matrix calculation.

This module provides HTTP client functionality to interact with OSRM routing APIs
to obtain real-world road distances and travel times between locations.
"""

import asyncio
import logging
from typing import List, Tuple, Optional
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from app.models.route import Location

logger = logging.getLogger(__name__)


class OSRMClientError(Exception):
    """Base exception for OSRM client errors."""
    pass


class OSRMTimeoutError(OSRMClientError):
    """Raised when OSRM API request times out."""
    pass


class OSRMAPIError(OSRMClientError):
    """Raised when OSRM API returns an error response."""
    pass


class OSRMClient:
    """
    HTTP client for OSRM routing API.

    Handles distance matrix calculations with proper error handling,
    timeouts, and retry logic.
    """

    def __init__(
        self,
        base_url: str = "http://router.project-osrm.org",
        timeout_seconds: float = 30.0,
        max_retries: int = 3
    ):
        """
        Initialize OSRM client.

        Args:
            base_url: Base URL for OSRM API
            timeout_seconds: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url.rstrip('/')
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=self.timeout_seconds)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    def _format_coordinates(self, locations: List[Location]) -> str:
        """
        Format locations as coordinate string for OSRM API.

        Args:
            locations: List of locations

        Returns:
            Semicolon-separated coordinate string (lon,lat;lon,lat;...)
        """
        coords = [f"{loc.longitude},{loc.latitude}" for loc in locations]
        return ";".join(coords)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        reraise=True
    )
    async def _make_request(self, url: str) -> dict:
        """
        Make HTTP request to OSRM API with retry logic.

        Args:
            url: Full API URL

        Returns:
            JSON response as dictionary

        Raises:
            OSRMTimeoutError: If request times out
            OSRMAPIError: If API returns error
        """
        if not self._client:
            self._client = httpx.AsyncClient(timeout=self.timeout_seconds)

        import time
        start_time = time.time()

        try:
            logger.info(f"Requesting OSRM API: {url}")
            response = await self._client.get(url)
            response.raise_for_status()
            data = response.json()

            request_time = (time.time() - start_time) * 1000  # Convert to milliseconds

            if data.get("code") != "Ok":
                error_message = data.get("message", "Unknown OSRM API error")
                logger.error(
                    f"OSRM API error: {error_message} (response_time={request_time:.0f}ms)"
                )
                raise OSRMAPIError(f"OSRM API error: {error_message}")

            logger.info(
                f"OSRM API request successful: "
                f"status={response.status_code}, response_time={request_time:.0f}ms"
            )

            return data

        except httpx.TimeoutException as e:
            request_time = (time.time() - start_time) * 1000
            logger.error(
                f"OSRM API timeout after {request_time:.0f}ms: {e}"
            )
            raise OSRMTimeoutError(f"Request timed out after {self.timeout_seconds}s")
        except httpx.HTTPStatusError as e:
            request_time = (time.time() - start_time) * 1000
            logger.error(
                f"OSRM HTTP error: status={e.response.status_code}, "
                f"response_time={request_time:.0f}ms"
            )
            raise OSRMAPIError(f"HTTP error: {e.response.status_code}")
        except httpx.NetworkError as e:
            request_time = (time.time() - start_time) * 1000
            logger.error(
                f"OSRM network error after {request_time:.0f}ms: {str(e)}"
            )
            raise OSRMAPIError(f"Network error: {str(e)}")

    async def get_distance_matrix(
        self,
        locations: List[Location]
    ) -> Tuple[List[List[float]], List[List[float]]]:
        """
        Calculate distance matrix for given locations.

        Uses OSRM table service to get distances and durations between all
        location pairs.

        Args:
            locations: List of locations to calculate matrix for

        Returns:
            Tuple of (distance_matrix, duration_matrix)
            - distance_matrix: 2D list of distances in meters
            - duration_matrix: 2D list of durations in seconds

        Raises:
            OSRMClientError: If API request fails
            ValueError: If locations list is invalid
        """
        if not locations or len(locations) < 2:
            raise ValueError("At least 2 locations required for distance matrix")

        import time
        start_time = time.time()
        n = len(locations)

        logger.info(f"Calculating distance matrix for {n} locations via OSRM")

        # Format coordinates for OSRM
        coords_string = self._format_coordinates(locations)

        # Build OSRM table API URL
        # Format: /table/v1/{profile}/{coordinates}?annotations=distance,duration
        url = (
            f"{self.base_url}/table/v1/driving/{coords_string}"
            f"?annotations=distance,duration"
        )

        # Make API request
        data = await self._make_request(url)

        # Extract distance and duration matrices
        distances = data.get("distances", [])
        durations = data.get("durations", [])

        if not distances or not durations:
            raise OSRMAPIError("Invalid response: missing distance or duration data")

        # Validate matrix dimensions
        if len(distances) != n or len(durations) != n:
            raise OSRMAPIError(
                f"Matrix dimension mismatch: expected {n}x{n}, "
                f"got {len(distances)}x{len(durations)}"
            )

        total_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        logger.info(
            f"Successfully calculated {n}x{n} distance matrix: "
            f"total_time={total_time:.0f}ms"
        )

        return distances, durations

    async def get_route(
        self,
        locations: List[Location]
    ) -> dict:
        """
        Get route geometry and metadata for given locations in order.

        Args:
            locations: List of locations in visit order

        Returns:
            Route data with geometry and metadata

        Raises:
            OSRMClientError: If API request fails
        """
        if not locations or len(locations) < 2:
            raise ValueError("At least 2 locations required for route")

        coords_string = self._format_coordinates(locations)

        # Build OSRM route API URL
        url = (
            f"{self.base_url}/route/v1/driving/{coords_string}"
            f"?overview=full&geometries=geojson"
        )

        data = await self._make_request(url)

        if "routes" not in data or not data["routes"]:
            raise OSRMAPIError("Invalid response: missing route data")

        return data["routes"][0]


async def create_osrm_client(base_url: str) -> OSRMClient:
    """
    Factory function to create and initialize OSRM client.

    Args:
        base_url: OSRM API base URL

    Returns:
        Initialized OSRMClient instance
    """
    return OSRMClient(base_url=base_url)
