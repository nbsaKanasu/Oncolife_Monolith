"""
Main Router for API Version 1.

This module aggregates all v1 endpoint routers into a single router
that can be included in the main FastAPI application.

Usage:
    from api.v1 import router as api_v1_router
    
    app.include_router(api_v1_router, prefix="/api/v1")
"""

from fastapi import APIRouter

from .endpoints import auth, chat, patients, profile, health

# Create main v1 router
router = APIRouter()

# Include all endpoint routers
router.include_router(
    health.router,
    tags=["Health"]
)

router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

router.include_router(
    patients.router,
    prefix="/patients",
    tags=["Patients"]
)

router.include_router(
    chat.router,
    prefix="/chat",
    tags=["Chat / Symptom Checker"]
)

router.include_router(
    profile.router,
    prefix="/profile",
    tags=["Profile"]
)

