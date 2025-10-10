"""
Route optimization API endpoints.
"""

import logging
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
    description="Calculate the optimal route for a list of delivery stops using VRP optimization"
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

        # Validate coordinates
        for i, stop in enumerate(request.stops):
            if not (-90 <= stop.latitude <= 90):
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
            if not (-180 <= stop.longitude <= 180):
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
            time_saved_percentage=time_saved_pct
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
