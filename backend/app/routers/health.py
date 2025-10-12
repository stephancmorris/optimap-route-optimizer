from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get(
    "/health",
    summary="Health Check",
    description="Check if the service is running and available",
    responses={
        200: {
            "description": "Service is healthy and operational",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "service": "OptiMap Backend",
                        "timestamp": "2025-10-12T15:30:45.123456"
                    }
                }
            }
        }
    }
)
async def health_check():
    """
    Health check endpoint to verify service availability.

    Use this endpoint to monitor service uptime and confirm the API is responding.
    Returns a timestamp in ISO 8601 format.

    Returns:
        dict: Service health status and timestamp
    """
    return {
        "status": "healthy",
        "service": "OptiMap Backend",
        "timestamp": datetime.utcnow().isoformat(),
    }
