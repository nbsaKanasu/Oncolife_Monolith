"""
API V1 Router - Doctor API
==========================

This module assembles all v1 API endpoints into a single router.

All routes are prefixed with /api/v1 when mounted in the main app.

Route structure:
    /api/v1/
    ├── /health         - Health check endpoints
    ├── /auth           - Authentication endpoints
    ├── /clinics        - Clinic management
    ├── /staff          - Staff management
    └── /patients       - Patient data access
"""

from fastapi import APIRouter

from .endpoints import (
    health,
    auth,
    clinics,
    staff,
    patients,
    dashboard,
    registration,
    docs,
)

# Create the main API router for v1
api_router = APIRouter()

# =============================================================================
# Include all endpoint routers
# =============================================================================

# Health check - no authentication required
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["Health"],
)

# Authentication - login, logout, password management
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)

# Clinics - clinic management (protected)
api_router.include_router(
    clinics.router,
    prefix="/clinics",
    tags=["Clinics"],
)

# Staff - staff and physician management (protected)
api_router.include_router(
    staff.router,
    prefix="/staff",
    tags=["Staff"],
)

# Patients - patient data access (protected, read-only)
api_router.include_router(
    patients.router,
    prefix="/patients",
    tags=["Patients"],
)

# Dashboard - analytics and clinical monitoring
api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["Dashboard"],
)

# Registration - admin-controlled physician/staff creation
api_router.include_router(
    registration.router,
    prefix="/registration",
    tags=["Registration"],
)

# Secured API Documentation (production)
api_router.include_router(
    docs.router,
    prefix="/docs",
    tags=["API Documentation"],
    include_in_schema=False,
)



