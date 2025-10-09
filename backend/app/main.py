from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.routers import health, optimize

app = FastAPI(
    title="OptiMap Route Optimizer",
    description="High-performance VRP solver for last-mile logistics optimization",
    version="1.0.0",
)

# Configure CORS - MUST be before routes
# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(optimize.router, tags=["Optimization"])


@app.get("/")
async def root():
    """Root endpoint providing API information."""
    return {
        "name": "OptiMap Route Optimizer API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "operational"
    }
