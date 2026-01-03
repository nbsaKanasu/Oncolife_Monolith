"""
OncoLife Patient API - Main Application Entry Point.

This module initializes the FastAPI application with:
- Middleware configuration
- API routing (versioned)
- Logging setup
- Error handling

Architecture:
    The application follows a layered architecture:
    
    ┌─────────────────────────────────────────────┐
    │              API Layer (api/v1/)            │
    │  Routes, Request/Response handling          │
    ├─────────────────────────────────────────────┤
    │            Service Layer (services/)         │
    │  Business logic, orchestration              │
    ├─────────────────────────────────────────────┤
    │          Repository Layer (db/repositories/) │
    │  Data access, queries                       │
    ├─────────────────────────────────────────────┤
    │            Database Layer (db/models/)       │
    │  ORM models, schema                         │
    └─────────────────────────────────────────────┘

Usage:
    # Development
    uvicorn main:app --reload --port 8000
    
    # Production
    uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

Environment:
    See core/config.py for all configuration options.
    Configuration is loaded from environment variables and .env file.
"""

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Core infrastructure
from core import settings, get_logger
from core.logging import setup_logging
from core.middleware import setup_middleware

# API routers - Modular v1 architecture only
from api.v1 import router as api_v1_router

# NOTE: Legacy routers have been removed.
# All endpoints are now served through /api/v1/
# See api/v1/router.py for the complete API structure.


# =============================================================================
# LOGGING SETUP
# =============================================================================

# Configure logging before anything else
setup_logging(
    level=settings.log_level,
    format_type=settings.log_format,
    app_name=settings.app_name
)

logger = get_logger(__name__)


# =============================================================================
# APPLICATION LIFECYCLE
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle handler.
    
    Runs on startup and shutdown. Use for:
    - Database connection setup/teardown
    - Cache initialization
    - Background task setup
    """
    # Startup
    logger.info(
        f"Starting {settings.app_name}",
        extra={
            "version": settings.app_version,
            "environment": settings.environment,
            "debug": settings.debug
        }
    )
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.app_name}")


# =============================================================================
# APPLICATION FACTORY
# =============================================================================

def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    This factory function creates the app with all middleware,
    routes, and configuration applied.
    
    Returns:
        Configured FastAPI application
    """
    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="OncoLife Patient API - Symptom Tracking and Patient Care",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Setup custom middleware (error handling, logging, correlation IDs)
    setup_middleware(app)
    
    # =========================================================================
    # API VERSION 1 (Primary modular structure)
    # =========================================================================
    # 
    # This is the main API with the new modular architecture:
    # - /api/v1/auth     - Authentication (signup, login, logout)
    # - /api/v1/chat     - Symptom checker chat (REST + WebSocket)
    # - /api/v1/chemo    - Chemotherapy dates
    # - /api/v1/diary    - Patient diary entries
    # - /api/v1/profile  - Patient profile
    # - /api/v1/summaries - Conversation summaries
    # - /api/v1/health   - Health checks
    #
    app.include_router(
        api_v1_router,
        prefix=settings.api_v1_prefix
    )
    
    # =========================================================================
    # LEGACY ROUTES - REMOVED
    # =========================================================================
    # 
    # All legacy routes have been migrated to /api/v1/
    # 
    # Migration complete:
    # - /auth/*      -> /api/v1/auth/*
    # - /chat/*      -> /api/v1/chat/*
    # - /chemo/*     -> /api/v1/chemo/*
    # - /diary/*     -> /api/v1/diary/*
    # - /profile/*   -> /api/v1/profile/*
    # - /summaries/* -> /api/v1/summaries/*
    # - /patient/*   -> /api/v1/patients/*
    #
    
    # =========================================================================
    # ROOT ENDPOINTS
    # =========================================================================
    
    @app.get("/", include_in_schema=False)
    async def root():
        """Root endpoint - redirects to docs or returns API info."""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs" if settings.is_development else None,
            "api": settings.api_v1_prefix
        }
    
    @app.get("/health", tags=["Health"])
    async def health():
        """
        Basic health check endpoint.
        
        Returns simple status for load balancer health checks.
        For detailed health info, use /api/v1/health/ready
        """
        return {"status": "ok"}
    
    return app


# =============================================================================
# APPLICATION INSTANCE
# =============================================================================

# Create the application instance
app = create_application()


# =============================================================================
# DEVELOPMENT SERVER
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.log_level.lower()
    )
