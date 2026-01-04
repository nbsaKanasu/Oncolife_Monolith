"""
Health Check Endpoints - Doctor API
===================================

Provides health check endpoints for monitoring and load balancers.

Endpoints:
- GET /health: Basic health check
- GET /health/ready: Readiness check with dependency status
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict
from datetime import datetime

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


# =============================================================================
# Response Models
# =============================================================================

class HealthResponse(BaseModel):
    """Basic health check response."""
    status: str
    service: str
    version: str
    timestamp: str


class ReadinessResponse(BaseModel):
    """Detailed readiness check response."""
    status: str
    service: str
    version: str
    environment: str
    timestamp: str
    checks: Dict[str, bool]


# =============================================================================
# Endpoints
# =============================================================================

@router.get(
    "",
    response_model=HealthResponse,
    summary="Health Check",
    description="Basic health check endpoint for load balancers and monitoring.",
)
async def health_check():
    """
    Basic health check.
    
    Returns a simple status indicating the service is running.
    This endpoint does not check dependencies.
    """
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness Check",
    description="Detailed readiness check including dependency status.",
)
async def readiness_check():
    """
    Detailed readiness check.
    
    Verifies that the service and its dependencies are ready
    to accept traffic. Checks database connections.
    """
    checks = {
        "doctor_db": False,
        "patient_db": False,
    }
    
    # Check doctor database
    try:
        from db.session import doctor_engine
        if doctor_engine:
            with doctor_engine.connect() as conn:
                conn.execute("SELECT 1")
            checks["doctor_db"] = True
    except Exception as e:
        logger.warning(f"Doctor database check failed: {e}")
    
    # Check patient database
    try:
        from db.session import patient_engine
        if patient_engine:
            with patient_engine.connect() as conn:
                conn.execute("SELECT 1")
            checks["patient_db"] = True
    except Exception as e:
        logger.warning(f"Patient database check failed: {e}")
    
    # Determine overall status
    # Service is ready if at least doctor_db is available
    all_healthy = all(checks.values())
    doctor_ready = checks.get("doctor_db", False)
    
    status = "healthy" if all_healthy else ("degraded" if doctor_ready else "unhealthy")
    
    return ReadinessResponse(
        status=status,
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.utcnow().isoformat() + "Z",
        checks=checks,
    )



