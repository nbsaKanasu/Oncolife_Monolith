"""
Authentication Endpoints - Doctor API
=====================================

Handles user authentication using AWS Cognito.

Endpoints:
- POST /auth/login: Authenticate with email/password
- POST /auth/logout: Logout (client-side token removal)
- POST /auth/complete-new-password: Set new password after temp password

Note: User signup is typically handled by administrators,
not self-registration for the doctor portal.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Optional

from api.deps import get_doctor_db_session
from services import AuthService
from core.exceptions import AuthenticationError, ExternalServiceError
from core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================

class LoginRequest(BaseModel):
    """Login request with email and password."""
    email: EmailStr
    password: str


class AuthTokens(BaseModel):
    """JWT tokens returned after successful authentication."""
    access_token: str
    refresh_token: str
    id_token: str
    token_type: str = "Bearer"


class LoginResponse(BaseModel):
    """Login response with success status and optional tokens."""
    valid: bool
    message: str
    user_status: Optional[str] = None
    session: Optional[str] = None  # For password change flow
    tokens: Optional[AuthTokens] = None


class CompletePasswordRequest(BaseModel):
    """Request to complete new password setup."""
    email: EmailStr
    new_password: str
    session: str


class CompletePasswordResponse(BaseModel):
    """Response after setting new password."""
    message: str
    tokens: AuthTokens


class LogoutResponse(BaseModel):
    """Logout response."""
    message: str


# =============================================================================
# Endpoints
# =============================================================================

@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login",
    description="Authenticate a user with email and password.",
)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_doctor_db_session),
):
    """
    Authenticate a user.
    
    Returns JWT tokens on success, or challenge info if password
    change is required (for users with temporary passwords).
    """
    auth_service = AuthService(db)
    
    try:
        result = auth_service.login(
            email=request.email,
            password=request.password,
        )
        
        # Build response
        response = LoginResponse(
            valid=result["valid"],
            message=result.get("message", ""),
            user_status=result.get("user_status"),
            session=result.get("session"),
        )
        
        # Add tokens if present
        if result.get("tokens"):
            response.tokens = AuthTokens(**result["tokens"])
        
        return response
        
    except ExternalServiceError as e:
        logger.error(f"Login failed for {request.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e.message),
        )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout",
    description="Logout the current user.",
)
async def logout():
    """
    Logout the current user.
    
    Note: This is primarily a client-side operation. The client
    should delete the stored tokens. This endpoint provides a
    consistent API response.
    """
    return LogoutResponse(message="Logout successful")


@router.post(
    "/complete-new-password",
    response_model=CompletePasswordResponse,
    summary="Complete Password Setup",
    description="Set a new password for a user with a temporary password.",
)
async def complete_new_password(
    request: CompletePasswordRequest,
    db: Session = Depends(get_doctor_db_session),
):
    """
    Complete password setup for users with temporary passwords.
    
    This is called after login returns a FORCE_CHANGE_PASSWORD status.
    The session token from the login response must be provided.
    """
    auth_service = AuthService(db)
    
    try:
        result = auth_service.complete_new_password(
            email=request.email,
            new_password=request.new_password,
            session=request.session,
        )
        
        return CompletePasswordResponse(
            message=result["message"],
            tokens=AuthTokens(**result["tokens"]),
        )
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )
    except ExternalServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=e.message,
        )

