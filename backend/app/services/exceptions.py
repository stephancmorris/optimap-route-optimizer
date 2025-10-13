"""
Custom exceptions for OptiMap services.

Provides specific exception types for different service failures.
"""


class GeocodingError(Exception):
    """Base exception for geocoding errors."""

    def __init__(self, message: str, address: str | None = None):
        """
        Initialize geocoding error.

        Args:
            message: Error message
            address: Address that caused the error (if applicable)
        """
        self.address = address
        super().__init__(message)


class GeocodingNotFoundError(GeocodingError):
    """Exception raised when an address cannot be geocoded."""

    def __init__(self, address: str):
        """
        Initialize not found error.

        Args:
            address: Address that could not be found
        """
        super().__init__(f"Address not found: {address}", address)


class GeocodingTimeoutError(GeocodingError):
    """Exception raised when geocoding request times out."""

    def __init__(self, address: str, timeout_seconds: float):
        """
        Initialize timeout error.

        Args:
            address: Address being geocoded
            timeout_seconds: Timeout duration
        """
        super().__init__(
            f"Geocoding timeout after {timeout_seconds}s for address: {address}",
            address
        )
        self.timeout_seconds = timeout_seconds


class GeocodingServiceError(GeocodingError):
    """Exception raised when geocoding service returns an error."""

    def __init__(self, message: str, status_code: int | None = None, address: str | None = None):
        """
        Initialize service error.

        Args:
            message: Error message
            status_code: HTTP status code (if applicable)
            address: Address being geocoded (if applicable)
        """
        super().__init__(message, address)
        self.status_code = status_code


class GeocodingAmbiguousError(GeocodingError):
    """Exception raised when geocoding returns ambiguous results."""

    def __init__(self, address: str, confidence: float):
        """
        Initialize ambiguous error.

        Args:
            address: Address with ambiguous results
            confidence: Confidence score (0.0-1.0)
        """
        super().__init__(
            f"Ambiguous geocoding result for address: {address} (confidence: {confidence:.2f})",
            address
        )
        self.confidence = confidence
