from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint to verify service availability.

    Returns:
        dict: Service health status and timestamp
    """
    return {
        "status": "healthy",
        "service": "OptiMap Backend",
        "timestamp": datetime.utcnow().isoformat(),
    }
