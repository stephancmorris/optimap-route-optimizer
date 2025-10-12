import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.config.logging_config import setup_logging
from app.middleware import LoggingMiddleware
from app.routers import health, optimize

# Configure logging before any other imports
setup_logging(
    log_level=settings.log_level,
    use_json=settings.log_json_format,
    log_file=settings.log_file
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OptiMap Route Optimizer API",
    description="""
## OptiMap Route Optimizer

A high-performance Vehicle Routing Problem (VRP) solver designed for last-mile logistics optimization.

### Features

* **Real-world routing**: Uses OSRM for accurate road-based distance and time calculations
* **VRP optimization**: Powered by Google OR-Tools for optimal route sequencing
* **Baseline comparison**: Automatically compares optimized routes against sequential routes
* **Detailed metrics**: Provides distance and time savings with percentage improvements

### Workflow

1. Submit a list of delivery stops with coordinates
2. System calculates real-world distance matrix via OSRM
3. OR-Tools VRP solver computes optimal route sequence
4. Returns optimized route with savings metrics

### Rate Limits

* Maximum 100 stops per request
* 30-second solver timeout
* OSRM API timeout configurable (default: 30s)

### Error Handling

All errors follow a consistent format with:
* HTTP status codes (400, 500, 503)
* Structured error responses with error codes
* Detailed error messages and suggestions
* Field-level validation errors

For detailed error documentation, see the `/optimize` endpoint error responses.
    """,
    version="1.0.0",
    contact={
        "name": "OptiMap Support",
        "url": "https://github.com/yourusername/optimap-route-optimizer",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure logging middleware (first for proper request tracking)
app.add_middleware(LoggingMiddleware)

# Configure CORS - MUST be before routes
# Allow frontend to communicate with backend
# Origins are configured via ALLOWED_ORIGINS environment variable
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,  # Specific origins from config
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers
    max_age=600,  # Cache preflight requests for 10 minutes
)

logger.info(f"OptiMap API starting with configuration: OSRM={settings.osrm_base_url}, "
            f"Solver timeout={settings.solver_time_limit_seconds}s, "
            f"Log level={settings.log_level}")

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(optimize.router, tags=["Optimization"])


@app.get(
    "/",
    summary="API Information",
    description="Get basic information about the OptiMap API",
    tags=["Root"],
    responses={
        200: {
            "description": "API information and documentation links",
            "content": {
                "application/json": {
                    "example": {
                        "name": "OptiMap Route Optimizer API",
                        "version": "1.0.0",
                        "docs": "/docs",
                        "redoc": "/redoc",
                        "openapi": "/openapi.json",
                        "status": "operational"
                    }
                }
            }
        }
    }
)
async def root():
    """
    Root endpoint providing API information and documentation links.

    Returns links to:
    - Interactive API documentation (Swagger UI)
    - Alternative documentation (ReDoc)
    - OpenAPI schema
    """
    return {
        "name": "OptiMap Route Optimizer API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "status": "operational"
    }
