"""
Geocoding client for converting addresses to coordinates.

Supports multiple geocoding providers (Nominatim, Google Maps, Mapbox).
"""

import asyncio
import logging
import time
from typing import Tuple, Optional, Dict, Any
from urllib.parse import urlencode

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from app.config.settings import settings
from app.services.exceptions import (
    GeocodingError,
    GeocodingNotFoundError,
    GeocodingTimeoutError,
    GeocodingServiceError
)
from app.utils.geocoding_cache import GeocodingCache

logger = logging.getLogger(__name__)


class GeocodingClient:
    """
    Client for geocoding addresses to coordinates.

    Supports multiple providers:
    - Nominatim (OpenStreetMap, free)
    - Google Maps Geocoding API (paid)
    - Mapbox Geocoding API (paid)
    """

    def __init__(
        self,
        provider: str | None = None,
        api_url: str | None = None,
        api_key: str | None = None,
        timeout_seconds: float | None = None,
        max_retries: int | None = None,
        rate_limit_seconds: float | None = None
    ):
        """
        Initialize geocoding client.

        Args:
            provider: Geocoding provider (nominatim, google, mapbox)
            api_url: Base URL for geocoding API
            api_key: API key for paid providers
            timeout_seconds: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            rate_limit_seconds: Minimum seconds between requests (for rate limiting)
        """
        self.provider = provider or settings.geocoding_provider
        self.api_url = api_url or settings.geocoding_api_url
        self.api_key = api_key or settings.geocoding_api_key
        self.timeout_seconds = timeout_seconds or settings.geocoding_timeout_seconds
        self.max_retries = max_retries or settings.geocoding_max_retries
        self.rate_limit_seconds = rate_limit_seconds or settings.geocoding_rate_limit_seconds

        self._client: Optional[httpx.AsyncClient] = None
        self._last_request_time: float = 0

        # Initialize cache if enabled
        self._cache: Optional[GeocodingCache] = None
        if settings.geocoding_cache_enabled:
            self._cache = GeocodingCache(
                maxsize=settings.geocoding_cache_size,
                ttl_days=settings.geocoding_cache_ttl_days
            )

        logger.info(
            f"Initialized GeocodingClient: provider={self.provider}, "
            f"url={self.api_url}, timeout={self.timeout_seconds}s, "
            f"rate_limit={self.rate_limit_seconds}s, "
            f"cache_enabled={settings.geocoding_cache_enabled}"
        )

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=self.timeout_seconds)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    async def _enforce_rate_limit(self):
        """Enforce rate limiting between requests."""
        if self.rate_limit_seconds > 0:
            time_since_last_request = time.time() - self._last_request_time
            if time_since_last_request < self.rate_limit_seconds:
                sleep_time = self.rate_limit_seconds - time_since_last_request
                logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
        self._last_request_time = time.time()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
    async def _make_request(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make HTTP request to geocoding API with retry logic.

        Args:
            url: API endpoint URL
            params: Query parameters

        Returns:
            JSON response data

        Raises:
            GeocodingTimeoutError: Request timed out
            GeocodingServiceError: API returned error
        """
        if not self._client:
            raise GeocodingError("Client not initialized. Use async context manager.")

        try:
            # Enforce rate limiting
            await self._enforce_rate_limit()

            # Add required headers
            headers = self._get_headers()

            logger.debug(f"Making geocoding request: {url}?{urlencode(params)}")
            start_time = time.time()

            response = await self._client.get(url, params=params, headers=headers)
            request_time = (time.time() - start_time) * 1000

            logger.info(
                f"Geocoding API request completed: status={response.status_code}, "
                f"response_time={request_time:.0f}ms"
            )

            response.raise_for_status()
            return response.json()

        except httpx.TimeoutException as e:
            logger.error(f"Geocoding API timeout after {self.timeout_seconds}s: {e}")
            raise GeocodingTimeoutError("", self.timeout_seconds) from e
        except httpx.HTTPStatusError as e:
            logger.error(f"Geocoding API error: status={e.response.status_code}, {e}")
            raise GeocodingServiceError(
                f"Geocoding API returned error: {e.response.status_code}",
                status_code=e.response.status_code
            ) from e
        except Exception as e:
            logger.error(f"Unexpected geocoding error: {e}", exc_info=True)
            raise GeocodingServiceError(f"Unexpected error: {e}") from e

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for geocoding request based on provider."""
        headers = {}

        if self.provider == "nominatim":
            # Nominatim requires User-Agent header
            headers["User-Agent"] = "OptiMap-RouteOptimizer/1.0 (https://github.com/yourusername/optimap-route-optimizer)"

        return headers

    async def geocode_address(
        self,
        address: str
    ) -> Tuple[float, float]:
        """
        Convert address to coordinates.

        Checks cache first, then calls geocoding API if needed.

        Args:
            address: Street address to geocode

        Returns:
            Tuple of (latitude, longitude)

        Raises:
            GeocodingNotFoundError: Address not found
            GeocodingTimeoutError: Request timed out
            GeocodingServiceError: API error
        """
        if not address or not address.strip():
            raise GeocodingError("Address cannot be empty")

        address = address.strip()

        # Check cache first
        if self._cache is not None:
            cached_result = self._cache.get(address)
            if cached_result is not None:
                lat, lng = cached_result
                logger.debug(f"Cache hit for address: {address} → ({lat}, {lng})")
                return cached_result

        logger.info(f"Geocoding address: {address}")

        try:
            # Geocode based on provider
            if self.provider == "nominatim":
                result = await self._geocode_nominatim(address)
            elif self.provider == "google":
                result = await self._geocode_google(address)
            elif self.provider == "mapbox":
                result = await self._geocode_mapbox(address)
            else:
                raise GeocodingError(f"Unsupported geocoding provider: {self.provider}")

            # Cache the successful result
            if self._cache is not None:
                lat, lng = result
                self._cache.set(address, lat, lng)

            return result

        except GeocodingNotFoundError:
            logger.warning(f"Address not found: {address}")
            raise
        except (GeocodingTimeoutError, GeocodingServiceError):
            raise
        except Exception as e:
            logger.error(f"Geocoding failed for address '{address}': {e}", exc_info=True)
            raise GeocodingServiceError(f"Failed to geocode address: {e}") from e

    async def _geocode_nominatim(self, address: str) -> Tuple[float, float]:
        """
        Geocode address using Nominatim (OpenStreetMap).

        Args:
            address: Address to geocode

        Returns:
            Tuple of (latitude, longitude)

        Raises:
            GeocodingNotFoundError: Address not found
        """
        url = f"{self.api_url}/search"
        params = {
            "q": address,
            "format": "json",
            "limit": 1,
            "addressdetails": 1
        }

        data = await self._make_request(url, params)

        if not data or len(data) == 0:
            raise GeocodingNotFoundError(address)

        result = data[0]
        lat = float(result["lat"])
        lon = float(result["lon"])

        logger.info(f"Geocoded '{address}' → ({lat}, {lon})")
        return lat, lon

    async def _geocode_google(self, address: str) -> Tuple[float, float]:
        """
        Geocode address using Google Maps Geocoding API.

        Args:
            address: Address to geocode

        Returns:
            Tuple of (latitude, longitude)

        Raises:
            GeocodingNotFoundError: Address not found
            GeocodingError: API key missing
        """
        if not self.api_key:
            raise GeocodingError("Google Maps API key is required")

        url = f"{self.api_url}/maps/api/geocode/json"
        params = {
            "address": address,
            "key": self.api_key
        }

        data = await self._make_request(url, params)

        if data.get("status") != "OK":
            status = data.get("status", "UNKNOWN")
            if status == "ZERO_RESULTS":
                raise GeocodingNotFoundError(address)
            else:
                raise GeocodingServiceError(f"Google Maps API error: {status}")

        result = data["results"][0]
        location = result["geometry"]["location"]
        lat = float(location["lat"])
        lon = float(location["lng"])

        logger.info(f"Geocoded '{address}' → ({lat}, {lon}) via Google Maps")
        return lat, lon

    async def _geocode_mapbox(self, address: str) -> Tuple[float, float]:
        """
        Geocode address using Mapbox Geocoding API.

        Args:
            address: Address to geocode

        Returns:
            Tuple of (latitude, longitude)

        Raises:
            GeocodingNotFoundError: Address not found
            GeocodingError: API key missing
        """
        if not self.api_key:
            raise GeocodingError("Mapbox API key is required")

        url = f"{self.api_url}/geocoding/v5/mapbox.places/{address}.json"
        params = {
            "access_token": self.api_key,
            "limit": 1
        }

        data = await self._make_request(url, params)

        features = data.get("features", [])
        if not features:
            raise GeocodingNotFoundError(address)

        result = features[0]
        coordinates = result["geometry"]["coordinates"]
        lon = float(coordinates[0])  # Mapbox returns [lon, lat]
        lat = float(coordinates[1])

        logger.info(f"Geocoded '{address}' → ({lat}, {lon}) via Mapbox")
        return lat, lon

    async def geocode_batch(
        self,
        addresses: list[str]
    ) -> list[Tuple[float, float] | None]:
        """
        Geocode multiple addresses in parallel.

        Args:
            addresses: List of addresses to geocode

        Returns:
            List of (latitude, longitude) tuples or None for failed geocoding
        """
        if not addresses:
            return []

        logger.info(f"Batch geocoding {len(addresses)} addresses")

        # Geocode all addresses in parallel
        tasks = [self._geocode_address_safe(address) for address in addresses]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        successful = sum(1 for r in results if r is not None)
        logger.info(
            f"Batch geocoding complete: {successful}/{len(addresses)} successful"
        )

        return results

    async def _geocode_address_safe(
        self,
        address: str
    ) -> Tuple[float, float] | None:
        """
        Geocode address with error handling (returns None on failure).

        Args:
            address: Address to geocode

        Returns:
            (latitude, longitude) or None if geocoding fails
        """
        try:
            return await self.geocode_address(address)
        except GeocodingError as e:
            logger.warning(f"Failed to geocode address '{address}': {e}")
            return None

    async def reverse_geocode(
        self,
        latitude: float,
        longitude: float
    ) -> str | None:
        """
        Convert coordinates to address (reverse geocoding).

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate

        Returns:
            Address string or None if not found

        Note:
            This is a placeholder for future implementation (OMAP-T17).
            Currently returns None.
        """
        # TODO: Implement reverse geocoding in OMAP-T17
        logger.info(
            f"Reverse geocoding not yet implemented: ({latitude}, {longitude})"
        )
        return None

    def get_cache_stats(self) -> dict | None:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics or None if caching is disabled
        """
        if self._cache is None:
            return None

        return self._cache.get_stats()

    def log_cache_stats(self) -> None:
        """Log cache statistics if caching is enabled."""
        if self._cache is not None:
            self._cache.log_stats()
