"""
Shared Dependencies for API Endpoints.

This module provides common FastAPI dependencies:
- Database session injection
- Authentication/authorization
- Current user retrieval
- Common query parameters

Usage:
    from api.deps import get_current_user, get_patient_db
    
    @router.get("/me")
    async def get_me(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_patient_db)
    ):
        return current_user
"""

from typing import Optional, Generator
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt

from db.session import get_patient_db as _get_patient_db, get_doctor_db as _get_doctor_db
from core import settings
from core.exceptions import AuthenticationException, AuthorizationException
from core.logging import get_logger

logger = get_logger(__name__)

# Security scheme for JWT
security = HTTPBearer(auto_error=False)


# =============================================================================
# DATABASE DEPENDENCIES
# =============================================================================

def get_patient_db() -> Generator[Session, None, None]:
    """
    Dependency to get a patient database session.
    
    Re-exported from db.session for convenience.
    
    Yields:
        SQLAlchemy Session
    """
    yield from _get_patient_db()


def get_doctor_db() -> Generator[Session, None, None]:
    """
    Dependency to get a doctor database session.
    
    Re-exported from db.session for convenience.
    
    Yields:
        SQLAlchemy Session
    """
    yield from _get_doctor_db()


# =============================================================================
# AUTHENTICATION DEPENDENCIES
# =============================================================================

def get_token_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """
    Extract and validate JWT token payload.
    
    Args:
        credentials: Bearer token from Authorization header
    
    Returns:
        Token payload dictionary or None if no token
    
    Raises:
        AuthenticationException: If token is invalid
    """
    if credentials is None:
        return None
    
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationException("Token has expired")
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        raise AuthenticationException("Invalid authentication token")


def get_current_user_uuid(
    payload: Optional[dict] = Depends(get_token_payload)
) -> UUID:
    """
    Get the current user's UUID from the token.
    
    Args:
        payload: JWT token payload
    
    Returns:
        User UUID
    
    Raises:
        AuthenticationException: If not authenticated
    """
    if payload is None:
        raise AuthenticationException("Authentication required")
    
    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        raise AuthenticationException("Invalid token: missing user ID")
    
    try:
        return UUID(user_id)
    except ValueError:
        raise AuthenticationException("Invalid token: malformed user ID")


def get_current_user(
    user_uuid: UUID = Depends(get_current_user_uuid),
    db: Session = Depends(get_patient_db)
) -> dict:
    """
    Get the current authenticated user.
    
    This is a placeholder that returns basic user info.
    In production, this would query the User model.
    
    Args:
        user_uuid: User UUID from token
        db: Database session
    
    Returns:
        User dictionary
    """
    # For now, return a basic dict
    # In production, query User model from database
    return {
        "uuid": user_uuid,
        "is_authenticated": True
    }


def get_current_patient(
    user_uuid: UUID = Depends(get_current_user_uuid),
    db: Session = Depends(get_patient_db)
) -> dict:
    """
    Get the current authenticated patient.
    
    Verifies the user is a patient and returns patient info.
    
    Args:
        user_uuid: User UUID from token
        db: Database session
    
    Returns:
        Patient dictionary
    
    Raises:
        AuthorizationException: If user is not a patient
    """
    # For now, return a basic dict
    # In production, verify user is a patient and return patient data
    return {
        "uuid": user_uuid,
        "is_patient": True
    }


# =============================================================================
# OPTIONAL AUTHENTICATION
# =============================================================================

def get_optional_user(
    payload: Optional[dict] = Depends(get_token_payload)
) -> Optional[dict]:
    """
    Get the current user if authenticated, None otherwise.
    
    Use this for endpoints that work differently for
    authenticated vs anonymous users.
    
    Args:
        payload: JWT token payload (may be None)
    
    Returns:
        User dictionary or None
    """
    if payload is None:
        return None
    
    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        return None
    
    try:
        return {
            "uuid": UUID(user_id),
            "is_authenticated": True
        }
    except ValueError:
        return None


# =============================================================================
# PAGINATION DEPENDENCIES
# =============================================================================

class PaginationParams:
    """
    Common pagination parameters.
    
    Usage:
        @router.get("/items")
        async def list_items(pagination: PaginationParams = Depends()):
            return repo.get_all(
                skip=pagination.skip,
                limit=pagination.limit
            )
    """
    
    def __init__(
        self,
        skip: int = 0,
        limit: int = 20
    ):
        """
        Initialize pagination parameters.
        
        Args:
            skip: Number of items to skip (offset)
            limit: Maximum items to return (1-100)
        """
        self.skip = max(0, skip)
        self.limit = min(100, max(1, limit))


def get_pagination(
    skip: int = 0,
    limit: int = 20
) -> PaginationParams:
    """
    Dependency for pagination parameters.
    
    Args:
        skip: Offset (default 0)
        limit: Max results (default 20, max 100)
    
    Returns:
        PaginationParams instance
    """
    return PaginationParams(skip=skip, limit=limit)





