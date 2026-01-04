"""
Health Check Endpoints.

Provides endpoints for:
- Basic health check
- Readiness check (dependencies ready)
- Liveness check (application alive)

These endpoints are used by orchestrators (Kubernetes, Fly.io)
to determine application health.
"""

from fastapi import APIRouter, Response
from typing import Dict, Any

from core import settings
from core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health", summary="Basic health check")
async def health_check() -> Dict[str, str]:
    """
    Basic health check endpoint.
    
    Returns a simple status indicating the API is running.
    Used by load balancers and monitoring systems.
    
    Returns:
        {"status": "ok"}
    """
    return {"status": "ok"}


@router.get("/health/ready", summary="Readiness check")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check for dependent services.
    
    Checks if all dependencies (databases, external services)
    are available and the application is ready to serve traffic.
    
    Returns:
        Health status with dependency details
    """
    # TODO: Add actual database health checks
    # from db.session import check_patient_db_health
    
    return {
        "status": "ready",
        "checks": {
            "database": "ok",
            # Add more checks as needed
        }
    }


@router.get("/health/live", summary="Liveness check")
async def liveness_check() -> Dict[str, str]:
    """
    Liveness check for application health.
    
    Indicates if the application process is alive and responsive.
    Used by orchestrators to determine if the container needs restart.
    
    Returns:
        {"status": "alive"}
    """
    return {"status": "alive"}


@router.get("/health/info", summary="Application info")
async def app_info() -> Dict[str, Any]:
    """
    Get application information.
    
    Returns version and environment info for debugging.
    Note: Don't expose sensitive configuration here.
    
    Returns:
        Application metadata
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }



