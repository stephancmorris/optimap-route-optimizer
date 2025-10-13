"""
Error models and custom exceptions for OptiMap API.

Provides structured error responses with consistent format and helpful messages.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ErrorCode(str, Enum):
    """Standardized error codes for different failure types."""

    # Client errors (4xx)
    INVALID_INPUT = "INVALID_INPUT"
    INVALID_COORDINATES = "INVALID_COORDINATES"
    INVALID_DEPOT_INDEX = "INVALID_DEPOT_INDEX"
    INSUFFICIENT_STOPS = "INSUFFICIENT_STOPS"
    TOO_MANY_STOPS = "TOO_MANY_STOPS"

    # Geocoding errors (4xx)
    GEOCODING_FAILED = "GEOCODING_FAILED"
    GEOCODING_TIMEOUT = "GEOCODING_TIMEOUT"
    GEOCODING_AMBIGUOUS = "GEOCODING_AMBIGUOUS"
    GEOCODING_SERVICE_ERROR = "GEOCODING_SERVICE_ERROR"

    # Server errors (5xx)
    SOLVER_FAILED = "SOLVER_FAILED"
    SOLVER_TIMEOUT = "SOLVER_TIMEOUT"
    SOLVER_NO_SOLUTION = "SOLVER_NO_SOLUTION"
    INTERNAL_ERROR = "INTERNAL_ERROR"

    # Service errors (503)
    ROUTING_SERVICE_UNAVAILABLE = "ROUTING_SERVICE_UNAVAILABLE"
    ROUTING_SERVICE_TIMEOUT = "ROUTING_SERVICE_TIMEOUT"
    ROUTING_SERVICE_ERROR = "ROUTING_SERVICE_ERROR"


class ErrorDetail(BaseModel):
    """Detailed information about a specific error."""

    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Human-readable error message")
    value: Optional[Any] = Field(None, description="Invalid value that caused the error")


class ErrorResponse(BaseModel):
    """Standardized error response model."""

    error: bool = Field(True, description="Always true for error responses")
    code: ErrorCode = Field(..., description="Error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[List[ErrorDetail]] = Field(None, description="Additional error details")
    suggestion: Optional[str] = Field(None, description="Suggested action to fix the error")

    class Config:
        json_schema_extra = {
            "example": {
                "error": True,
                "code": "INVALID_DEPOT_INDEX",
                "message": "The specified depot index is out of bounds",
                "details": [
                    {
                        "field": "depot_index",
                        "message": "Depot index 5 is out of bounds for 3 stops",
                        "value": 5
                    }
                ],
                "suggestion": "Ensure depot_index is between 0 and the number of stops minus 1"
            }
        }


# Predefined error messages for consistency
ERROR_MESSAGES = {
    ErrorCode.INVALID_INPUT: "The request contains invalid input data",
    ErrorCode.INVALID_COORDINATES: "One or more coordinates are invalid",
    ErrorCode.INVALID_DEPOT_INDEX: "The specified depot index is out of bounds",
    ErrorCode.INSUFFICIENT_STOPS: "At least 2 stops are required for route optimization",
    ErrorCode.TOO_MANY_STOPS: "Too many stops provided - maximum limit exceeded",
    ErrorCode.GEOCODING_FAILED: "Failed to geocode one or more addresses",
    ErrorCode.GEOCODING_TIMEOUT: "Geocoding service request timed out",
    ErrorCode.GEOCODING_AMBIGUOUS: "Geocoding returned ambiguous results",
    ErrorCode.GEOCODING_SERVICE_ERROR: "Geocoding service encountered an error",
    ErrorCode.SOLVER_FAILED: "The optimization solver encountered an error",
    ErrorCode.SOLVER_TIMEOUT: "The optimization solver timed out before finding a solution",
    ErrorCode.SOLVER_NO_SOLUTION: "The optimization solver could not find a valid solution",
    ErrorCode.INTERNAL_ERROR: "An unexpected internal error occurred",
    ErrorCode.ROUTING_SERVICE_UNAVAILABLE: "The routing service is currently unavailable",
    ErrorCode.ROUTING_SERVICE_TIMEOUT: "The routing service request timed out",
    ErrorCode.ROUTING_SERVICE_ERROR: "The routing service returned an error",
}


# Error suggestions for common issues
ERROR_SUGGESTIONS = {
    ErrorCode.INVALID_COORDINATES: "Ensure latitude is between -90 and 90, longitude is between -180 and 180",
    ErrorCode.INVALID_DEPOT_INDEX: "Ensure depot_index is between 0 and the number of stops minus 1",
    ErrorCode.INSUFFICIENT_STOPS: "Provide at least 2 stops in the 'stops' array",
    ErrorCode.TOO_MANY_STOPS: "Reduce the number of stops or contact support for enterprise limits",
    ErrorCode.GEOCODING_FAILED: "Provide a more specific address with street, city, state, and ZIP code",
    ErrorCode.GEOCODING_TIMEOUT: "Try again or provide coordinates directly instead of addresses",
    ErrorCode.GEOCODING_AMBIGUOUS: "Provide a more specific address to get better results",
    ErrorCode.GEOCODING_SERVICE_ERROR: "Try again later or provide coordinates directly",
    ErrorCode.SOLVER_TIMEOUT: "Try reducing the number of stops or increasing the solver timeout",
    ErrorCode.SOLVER_NO_SOLUTION: "Check that all stops are reachable by road and coordinates are valid",
    ErrorCode.ROUTING_SERVICE_UNAVAILABLE: "Try again in a few moments. If the issue persists, the routing service may be down",
    ErrorCode.ROUTING_SERVICE_TIMEOUT: "Try again with fewer stops or check your network connection",
}


def create_error_response(
    code: ErrorCode,
    message: Optional[str] = None,
    details: Optional[List[ErrorDetail]] = None,
    suggestion: Optional[str] = None
) -> ErrorResponse:
    """
    Create a standardized error response.

    Args:
        code: Error code
        message: Custom error message (uses default if not provided)
        details: List of error details
        suggestion: Custom suggestion (uses default if not provided)

    Returns:
        ErrorResponse object
    """
    return ErrorResponse(
        code=code,
        message=message or ERROR_MESSAGES.get(code, "An error occurred"),
        details=details,
        suggestion=suggestion or ERROR_SUGGESTIONS.get(code)
    )
