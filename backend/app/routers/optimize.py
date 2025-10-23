"""
Route optimization API endpoints.
"""

import asyncio
import logging
import time
from typing import List
from fastapi import APIRouter, HTTPException, status

from app.models.route import (
    OptimizationRequest,
    OptimizationResponse,
    RouteMetrics,
    Location
)
from app.models.errors import (
    ErrorResponse,
    ErrorCode,
    ErrorDetail,
    create_error_response
)
from app.services.osrm_client import OSRMClient, OSRMClientError, OSRMTimeoutError
from app.services.vrp_solver import ORToolsVRPSolver
from app.services.geocoding_client import GeocodingClient
from app.services.exceptions import (
    GeocodingError,
    GeocodingNotFoundError,
    GeocodingTimeoutError,
    GeocodingServiceError
)
from app.config.settings import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Constants
MAX_STOPS = 100  # Maximum number of stops allowed


@router.post(
    "/optimize",
    response_model=OptimizationResponse,
    status_code=status.HTTP_200_OK,
    summary="Optimize delivery route",
    description="Calculate the optimal route for a list of delivery stops using VRP optimization",
    responses={
        200: {
            "description": "Successful optimization with route and metrics",
            "content": {
                "application/json": {
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
            }
        },
        400: {
            "description": "Bad Request - Invalid input data",
            "content": {
                "application/json": {
                    "example": {
                        "error": True,
                        "code": "INVALID_DEPOT_INDEX",
                        "message": "Depot index 5 is out of bounds for 3 stops",
                        "details": [
                            {
                                "field": "depot_index",
                                "message": "Index 5 is invalid for 3 stops (valid range: 0-2)",
                                "value": 5
                            }
                        ],
                        "suggestion": "Ensure depot_index is between 0 and the number of stops minus 1"
                    }
                }
            }
        },
        500: {
            "description": "Internal Server Error - Solver failure",
            "content": {
                "application/json": {
                    "example": {
                        "error": True,
                        "code": "SOLVER_NO_SOLUTION",
                        "message": "Unable to find optimal route within time limit",
                        "details": [
                            {
                                "field": "solver_timeout",
                                "message": "Solver timed out after 30 seconds",
                                "value": 30
                            }
                        ],
                        "suggestion": "Try reducing the number of stops or increasing the solver timeout"
                    }
                }
            }
        },
        503: {
            "description": "Service Unavailable - OSRM routing service error",
            "content": {
                "application/json": {
                    "example": {
                        "error": True,
                        "code": "ROUTING_SERVICE_TIMEOUT",
                        "message": "Routing service request timed out after 30s",
                        "details": [
                            {
                                "field": "osrm_timeout",
                                "message": "OSRM API request exceeded timeout limit",
                                "value": 30
                            }
                        ],
                        "suggestion": "Try again with fewer stops or check your network connection"
                    }
                }
            }
        }
    }
)
async def optimize_route(request: OptimizationRequest) -> OptimizationResponse:
    """
    Optimize route for given delivery stops.

    This endpoint:
    1. Validates the input stops
    2. Calculates real-world distance matrix using OSRM
    3. Solves VRP using OR-Tools to find optimal route
    4. Compares optimized route against baseline (sequential) route
    5. Returns optimized route with savings metrics

    Args:
        request: Optimization request with stops and depot index

    Returns:
        OptimizationResponse with optimized route and metrics

    Raises:
        HTTPException 400: Invalid request (bad coordinates, depot index, etc.)
        HTTPException 500: Internal server error (OSRM failure, solver failure)
        HTTPException 503: Service temporarily unavailable (OSRM timeout)
    """
    try:
        # Validate number of stops
        if len(request.stops) > MAX_STOPS:
            error = create_error_response(
                code=ErrorCode.TOO_MANY_STOPS,
                message=f"Too many stops: {len(request.stops)} provided, maximum is {MAX_STOPS}",
                details=[ErrorDetail(
                    field="stops",
                    message=f"Received {len(request.stops)} stops, but maximum allowed is {MAX_STOPS}",
                    value=len(request.stops)
                )]
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error.model_dump()
            )

        # Validate depot index
        if request.depot_index >= len(request.stops):
            error = create_error_response(
                code=ErrorCode.INVALID_DEPOT_INDEX,
                message=f"Depot index {request.depot_index} is out of bounds for {len(request.stops)} stops",
                details=[ErrorDetail(
                    field="depot_index",
                    message=f"Index {request.depot_index} is invalid for {len(request.stops)} stops (valid range: 0-{len(request.stops)-1})",
                    value=request.depot_index
                )]
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error.model_dump()
            )

        # Validate coordinates (only for stops that have them - addresses will be geocoded later)
        for i, stop in enumerate(request.stops):
            # Skip validation for stops that will be geocoded
            if stop.needs_geocoding():
                continue

            # Validate latitude if present
            if stop.latitude is not None and not (-90 <= stop.latitude <= 90):
                error = create_error_response(
                    code=ErrorCode.INVALID_COORDINATES,
                    message=f"Invalid latitude at stop {i}: {stop.latitude}",
                    details=[ErrorDetail(
                        field=f"stops[{i}].latitude",
                        message=f"Latitude must be between -90 and 90",
                        value=stop.latitude
                    )]
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error.model_dump()
                )

            # Validate longitude if present
            if stop.longitude is not None and not (-180 <= stop.longitude <= 180):
                error = create_error_response(
                    code=ErrorCode.INVALID_COORDINATES,
                    message=f"Invalid longitude at stop {i}: {stop.longitude}",
                    details=[ErrorDetail(
                        field=f"stops[{i}].longitude",
                        message=f"Longitude must be between -180 and 180",
                        value=stop.longitude
                    )]
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error.model_dump()
                )

        logger.info(f"Optimizing route for {len(request.stops)} stops with depot at index {request.depot_index}")

        # Step 0: Geocode any addresses that don't have coordinates
        locations_to_geocode = [
            (i, stop) for i, stop in enumerate(request.stops)
            if stop.needs_geocoding()
        ]

        if locations_to_geocode:
            logger.info(f"Geocoding {len(locations_to_geocode)} addresses")
            geocoding_start_time = time.time()

            async with GeocodingClient() as geocoding_client:
                # Geocode all addresses in parallel
                geocoding_tasks = [
                    _geocode_single_location(stop, geocoding_client)
                    for _, stop in locations_to_geocode
                ]

                geocoding_results = await asyncio.gather(
                    *geocoding_tasks,
                    return_exceptions=True
                )

            geocoding_time = (time.time() - geocoding_start_time) * 1000

            # Check for geocoding failures
            failed_geocodes = []
            for (idx, stop), result in zip(locations_to_geocode, geocoding_results):
                if isinstance(result, Exception) or result is None:
                    error_msg = str(result) if isinstance(result, Exception) else "Address not found"
                    failed_geocodes.append({
                        "index": idx,
                        "address": stop.address,
                        "error": error_msg
                    })
                    logger.warning(f"Failed to geocode stop {idx} (address: {stop.address}): {error_msg}")

            if failed_geocodes:
                # Return error with details about all failed geocoding attempts
                error = create_error_response(
                    code=ErrorCode.GEOCODING_FAILED,
                    message=f"Failed to geocode {len(failed_geocodes)} address(es)",
                    details=[
                        ErrorDetail(
                            field=f"stops[{f['index']}].address",
                            message=f["error"],
                            value=f["address"]
                        )
                        for f in failed_geocodes
                    ],
                    suggestion="Provide more specific addresses with street, city, state, and ZIP code, or use coordinates directly"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error.model_dump()
                )

            logger.info(
                f"Geocoding completed successfully: {len(locations_to_geocode)} addresses, "
                f"time={geocoding_time:.0f}ms"
            )

        # Validate all stops now have coordinates
        for i, stop in enumerate(request.stops):
            if not stop.has_coordinates():
                error = create_error_response(
                    code=ErrorCode.INVALID_INPUT,
                    message=f"Stop {i} is missing coordinates after geocoding",
                    details=[ErrorDetail(
                        field=f"stops[{i}]",
                        message="Location must have coordinates",
                        value=stop.model_dump()
                    )]
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error.model_dump()
                )

        # Step 1: Get distance matrix from OSRM
        async with OSRMClient(
            base_url=settings.osrm_base_url,
            timeout_seconds=settings.osrm_timeout_seconds
        ) as osrm_client:
            try:
                distances, durations = await osrm_client.get_distance_matrix(request.stops)
            except OSRMTimeoutError as e:
                logger.error(f"OSRM API timeout: {e}")
                error = create_error_response(
                    code=ErrorCode.ROUTING_SERVICE_TIMEOUT,
                    message=f"Routing service request timed out after {settings.osrm_timeout_seconds}s",
                    details=[ErrorDetail(
                        field="osrm_timeout",
                        message=str(e),
                        value=settings.osrm_timeout_seconds
                    )]
                )
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=error.model_dump()
                )
            except OSRMClientError as e:
                logger.error(f"OSRM API error: {e}")
                error = create_error_response(
                    code=ErrorCode.ROUTING_SERVICE_ERROR,
                    message="Unable to calculate route distances",
                    details=[ErrorDetail(
                        field="routing_service",
                        message=str(e)
                    )]
                )
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=error.model_dump()
                )

        # Step 2: Solve VRP using OR-Tools
        solver = ORToolsVRPSolver(time_limit_seconds=settings.solver_time_limit_seconds)

        try:
            result = solver.solve(
                distance_matrix=distances,
                num_vehicles=1,
                depot=request.depot_index
            )

            if result is None:
                logger.warning(f"Solver could not find solution within {settings.solver_time_limit_seconds}s timeout")
                error = create_error_response(
                    code=ErrorCode.SOLVER_NO_SOLUTION,
                    message="Unable to find optimal route within time limit",
                    details=[ErrorDetail(
                        field="solver_timeout",
                        message=f"Solver timed out after {settings.solver_time_limit_seconds} seconds",
                        value=settings.solver_time_limit_seconds
                    )]
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error.model_dump()
                )

            optimized_route_indices, optimized_distance = result

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"VRP solver error: {e}", exc_info=True)
            error = create_error_response(
                code=ErrorCode.SOLVER_FAILED,
                message="Optimization solver encountered an unexpected error",
                details=[ErrorDetail(
                    field="solver",
                    message=str(e)
                )]
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error.model_dump()
            )

        # Step 3: Calculate optimized route metrics
        optimized_duration = _calculate_route_duration(optimized_route_indices, durations)

        # Step 4: Calculate baseline (sequential) route metrics
        baseline_route_indices = list(range(len(request.stops))) + [0]  # 0->1->2->...->n->0
        baseline_distance = _calculate_route_distance(baseline_route_indices, distances)
        baseline_duration = _calculate_route_duration(baseline_route_indices, durations)

        # Step 5: Calculate savings
        distance_saved = baseline_distance - optimized_distance
        time_saved = baseline_duration - optimized_duration
        distance_saved_pct = (distance_saved / baseline_distance * 100) if baseline_distance > 0 else 0
        time_saved_pct = (time_saved / baseline_duration * 100) if baseline_duration > 0 else 0

        # Step 6: Build optimized route with locations
        optimized_route = [request.stops[i] for i in optimized_route_indices]

        # Step 7: Get route geometry from OSRM (road-following path)
        route_geometry = None
        try:
            async with OSRMClient(
                base_url=settings.osrm_base_url,
                timeout_seconds=settings.osrm_timeout_seconds
            ) as osrm_client:
                route_data = await osrm_client.get_route(optimized_route)
                route_geometry = route_data.get("geometry")
                logger.info("Successfully fetched route geometry from OSRM")
        except Exception as e:
            # Don't fail the entire request if route geometry fetch fails
            logger.warning(f"Failed to fetch route geometry: {e}")

        logger.info(
            f"Optimization complete: {distance_saved:.0f}m saved ({distance_saved_pct:.1f}%), "
            f"{time_saved:.0f}s saved ({time_saved_pct:.1f}%)"
        )

        return OptimizationResponse(
            optimized_route=optimized_route,
            optimized_metrics=RouteMetrics(
                total_distance_meters=optimized_distance,
                total_time_seconds=optimized_duration
            ),
            baseline_metrics=RouteMetrics(
                total_distance_meters=baseline_distance,
                total_time_seconds=baseline_duration
            ),
            distance_saved_meters=distance_saved,
            time_saved_seconds=time_saved,
            distance_saved_percentage=distance_saved_pct,
            time_saved_percentage=time_saved_pct,
            route_geometry=route_geometry
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during optimization: {e}")
        error = create_error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message="An unexpected error occurred while processing your request",
            details=[ErrorDetail(
                message="Please try again. If the problem persists, contact support"
            )]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error.model_dump()
        )


def _calculate_route_distance(route_indices: List[int], distance_matrix: List[List[float]]) -> float:
    """
    Calculate total distance for a given route.

    Args:
        route_indices: List of location indices in visit order
        distance_matrix: Distance matrix

    Returns:
        Total distance in meters
    """
    total = 0.0
    for i in range(len(route_indices) - 1):
        from_idx = route_indices[i]
        to_idx = route_indices[i + 1]
        total += distance_matrix[from_idx][to_idx]
    return total


def _calculate_route_duration(route_indices: List[int], duration_matrix: List[List[float]]) -> float:
    """
    Calculate total duration for a given route.

    Args:
        route_indices: List of location indices in visit order
        duration_matrix: Duration matrix

    Returns:
        Total duration in seconds
    """
    total = 0.0
    for i in range(len(route_indices) - 1):
        from_idx = route_indices[i]
        to_idx = route_indices[i + 1]
        total += duration_matrix[from_idx][to_idx]
    return total


async def _geocode_single_location(
    location: Location,
    geocoding_client: GeocodingClient
) -> tuple[float, float] | None:
    """
    Geocode a single location and update its coordinates.

    Args:
        location: Location to geocode
        geocoding_client: Geocoding client instance

    Returns:
        Tuple of (latitude, longitude) or None if geocoding fails

    Raises:
        GeocodingError: If geocoding fails
    """
    try:
        if not location.address:
            raise GeocodingError("Location has no address to geocode")

        # Geocode the address
        lat, lng = await geocoding_client.geocode_address(location.address)

        # Update location with geocoded coordinates
        location.set_geocoded_coordinates(lat, lng, confidence=None)

        logger.debug(f"Geocoded '{location.address}' → ({lat}, {lng})")
        return lat, lng

    except GeocodingNotFoundError as e:
        logger.warning(f"Address not found: {location.address}")
        raise
    except GeocodingTimeoutError as e:
        logger.error(f"Geocoding timeout for address: {location.address}")
        raise
    except GeocodingServiceError as e:
        logger.error(f"Geocoding service error for address: {location.address} - {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected geocoding error for address: {location.address} - {e}", exc_info=True)
        raise GeocodingServiceError(f"Unexpected error: {e}") from e
