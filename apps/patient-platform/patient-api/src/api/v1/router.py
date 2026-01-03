"""
Main Router for API Version 1.

This module aggregates all v1 endpoint routers into a single router
that can be included in the main FastAPI application.

Endpoints:
- /health: Health check
- /auth: Authentication (signup, login, logout, password, delete)
- /onboarding: Patient onboarding flow (fax, OCR, welcome, setup)
- /patients: Patient management
- /chat: Symptom checker chat (REST + WebSocket)
- /chemo: Chemotherapy dates
- /diary: Patient diary entries
- /summaries: Conversation summaries
- /profile: Patient profile and configuration

Usage:
    from api.v1 import router as api_v1_router
    
    app.include_router(api_v1_router, prefix="/api/v1")
"""

from fastapi import APIRouter

from .endpoints import auth, chat, patients, profile, health, chemo, diary, summaries, onboarding

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
    onboarding.router,
    tags=["Patient Onboarding"]
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
    chemo.router,
    prefix="/chemo",
    tags=["Chemotherapy"]
)

router.include_router(
    diary.router,
    prefix="/diary",
    tags=["Diary"]
)

router.include_router(
    summaries.router,
    prefix="/summaries",
    tags=["Summaries"]
)

router.include_router(
    profile.router,
    prefix="/profile",
    tags=["Profile"]
)

