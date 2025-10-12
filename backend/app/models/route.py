"""
Data models for route optimization requests and responses.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class Location(BaseModel):
    """Represents a geographical location with coordinates."""

    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    address: Optional[str] = Field(None, description="Optional human-readable address")

    @field_validator('latitude', 'longitude')
    @classmethod
    def validate_coordinates(cls, v: float) -> float:
        """Ensure coordinates are valid numbers."""
        if not isinstance(v, (int, float)):
            raise ValueError('Coordinates must be numeric values')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "latitude": 40.7128,
                "longitude": -74.0060,
                "address": "New York, NY"
            }
        }


class OptimizationRequest(BaseModel):
    """Request payload for route optimization."""

    stops: List[Location] = Field(
        ...,
        min_length=2,
        description="List of delivery stops to optimize (minimum 2 stops)"
    )
    depot_index: int = Field(
        0,
        ge=0,
        description="Index of the starting/ending depot location (default: first stop)"
    )

    @field_validator('depot_index')
    @classmethod
    def validate_depot_index(cls, v: int, info) -> int:
        """Ensure depot index is within bounds of stops list."""
        # Note: validation against stops length happens in the endpoint
        if v < 0:
            raise ValueError('Depot index must be non-negative')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "stops": [
                    {"latitude": 40.7128, "longitude": -74.0060, "address": "New York, NY"},
                    {"latitude": 40.7589, "longitude": -73.9851, "address": "Times Square, NY"},
                    {"latitude": 40.7614, "longitude": -73.9776, "address": "Central Park, NY"},
                    {"latitude": 40.7484, "longitude": -73.9857, "address": "Empire State Building, NY"}
                ],
                "depot_index": 0
            }
        }


class RouteMetrics(BaseModel):
    """Metrics for a calculated route."""

    total_distance_meters: float = Field(..., description="Total route distance in meters")
    total_time_seconds: float = Field(..., description="Total route time in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "total_distance_meters": 8420.5,
                "total_time_seconds": 1245.8
            }
        }


class OptimizationResponse(BaseModel):
    """Response containing optimized route and metrics."""

    optimized_route: List[Location] = Field(
        ...,
        description="Stops in optimal visit order"
    )
    optimized_metrics: RouteMetrics = Field(
        ...,
        description="Metrics for the optimized route"
    )
    baseline_metrics: RouteMetrics = Field(
        ...,
        description="Metrics for the original (unoptimized) route"
    )
    distance_saved_meters: float = Field(
        ...,
        description="Distance saved compared to baseline"
    )
    time_saved_seconds: float = Field(
        ...,
        description="Time saved compared to baseline"
    )
    distance_saved_percentage: float = Field(
        ...,
        description="Percentage of distance saved"
    )
    time_saved_percentage: float = Field(
        ...,
        description="Percentage of time saved"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "optimized_route": [
                    {"latitude": 40.7128, "longitude": -74.0060, "address": "New York, NY"},
                    {"latitude": 40.7484, "longitude": -73.9857, "address": "Empire State Building, NY"},
                    {"latitude": 40.7589, "longitude": -73.9851, "address": "Times Square, NY"},
                    {"latitude": 40.7614, "longitude": -73.9776, "address": "Central Park, NY"},
                    {"latitude": 40.7128, "longitude": -74.0060, "address": "New York, NY"}
                ],
                "optimized_metrics": {
                    "total_distance_meters": 8420.5,
                    "total_time_seconds": 1245.8
                },
                "baseline_metrics": {
                    "total_distance_meters": 10850.2,
                    "total_time_seconds": 1580.4
                },
                "distance_saved_meters": 2429.7,
                "time_saved_seconds": 334.6,
                "distance_saved_percentage": 22.4,
                "time_saved_percentage": 21.2
            }
        }


class DistanceMatrixResponse(BaseModel):
    """Response from distance matrix calculation."""

    distances: List[List[float]] = Field(
        ...,
        description="Matrix of distances in meters between all location pairs"
    )
    durations: List[List[float]] = Field(
        ...,
        description="Matrix of travel times in seconds between all location pairs"
    )
