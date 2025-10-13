"""
Caching layer for geocoding results.

Implements LRU cache with TTL to minimize redundant geocoding API calls.
"""

import logging
import re
from datetime import timedelta
from typing import Tuple, Optional, Dict, Any

from cachetools import TTLCache

logger = logging.getLogger(__name__)


class GeocodingCache:
    """
    Cache for geocoding results with LRU eviction and TTL.

    Provides address normalization for consistent cache keys and
    tracks statistics for cache effectiveness monitoring.
    """

    def __init__(self, maxsize: int = 10000, ttl_days: int = 30):
        """
        Initialize geocoding cache.

        Args:
            maxsize: Maximum number of cached addresses
            ttl_days: Time-to-live in days for cached entries
        """
        ttl_seconds = timedelta(days=ttl_days).total_seconds()
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl_seconds)
        self.maxsize = maxsize
        self.ttl_days = ttl_days

        # Statistics
        self.hits = 0
        self.misses = 0

        logger.info(
            f"Initialized GeocodingCache: maxsize={maxsize}, ttl={ttl_days} days"
        )

    def get(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Get cached coordinates for an address.

        Args:
            address: Address to look up

        Returns:
            Tuple of (latitude, longitude) or None if not cached
        """
        if not address or not address.strip():
            return None

        cache_key = self._normalize_address(address)
        result = self.cache.get(cache_key)

        if result is not None:
            self.hits += 1
            logger.debug(f"Cache hit for address: {address}")
        else:
            self.misses += 1
            logger.debug(f"Cache miss for address: {address}")

        return result

    def set(
        self,
        address: str,
        latitude: float,
        longitude: float
    ) -> None:
        """
        Cache geocoding result for an address.

        Args:
            address: Address that was geocoded
            latitude: Latitude coordinate
            longitude: Longitude coordinate
        """
        if not address or not address.strip():
            logger.warning("Cannot cache result for empty address")
            return

        cache_key = self._normalize_address(address)
        self.cache[cache_key] = (latitude, longitude)

        logger.debug(
            f"Cached coordinates for address: {address} → ({latitude}, {longitude})"
        )

    def _normalize_address(self, address: str) -> str:
        """
        Normalize address for consistent cache keys.

        Normalization steps:
        1. Convert to lowercase
        2. Remove extra whitespace
        3. Standardize common abbreviations
        4. Remove punctuation variations

        Args:
            address: Raw address string

        Returns:
            Normalized address string
        """
        # Convert to lowercase
        normalized = address.lower().strip()

        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)

        # Standardize common abbreviations (case-insensitive)
        abbreviations = {
            r'\bstreet\b': 'st',
            r'\bavenue\b': 'ave',
            r'\broad\b': 'rd',
            r'\bdrive\b': 'dr',
            r'\boulevard\b': 'blvd',
            r'\blane\b': 'ln',
            r'\bcourt\b': 'ct',
            r'\bplace\b': 'pl',
            r'\bapartment\b': 'apt',
            r'\bsuite\b': 'ste',
            r'\bnorth\b': 'n',
            r'\bsouth\b': 's',
            r'\beast\b': 'e',
            r'\bwest\b': 'w',
        }

        for full_form, abbrev in abbreviations.items():
            normalized = re.sub(full_form, abbrev, normalized)

        # Remove common punctuation (but keep hyphens in street names)
        normalized = re.sub(r'[,.]', '', normalized)

        return normalized

    def clear(self) -> None:
        """Clear all cached entries."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        logger.info("Geocoding cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics:
            - size: Current number of cached entries
            - maxsize: Maximum cache size
            - hits: Number of cache hits
            - misses: Number of cache misses
            - hit_rate_percent: Cache hit rate percentage
            - total_requests: Total number of cache lookups
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "size": len(self.cache),
            "maxsize": self.maxsize,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests,
            "ttl_days": self.ttl_days
        }

    def log_stats(self) -> None:
        """Log current cache statistics."""
        stats = self.get_stats()
        logger.info(
            f"Geocoding cache stats: {stats['size']}/{stats['maxsize']} entries, "
            f"{stats['hits']} hits, {stats['misses']} misses, "
            f"{stats['hit_rate_percent']}% hit rate"
        )

    def __len__(self) -> int:
        """Get current cache size."""
        return len(self.cache)

    def __contains__(self, address: str) -> bool:
        """Check if address is in cache."""
        cache_key = self._normalize_address(address)
        return cache_key in self.cache
