"""
Authentication Service - Doctor API
====================================

Service layer for authentication-related business logic.
Handles AWS Cognito integration for user authentication.

Usage:
    from services import AuthService
    
    auth_service = AuthService(db)
    
    # Login
    response = auth_service.login(email, password)
    
    # Get current user
    user = auth_service.get_current_user_from_token(token)
"""

import os
import hmac
import hashlib
import base64
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
import boto3
from botocore.exceptions import ClientError
import requests

from .base import BaseService
from db.repositories import StaffRepository
from db.models import StaffProfile
from core.config import settings
from core.exceptions import (
    AuthenticationError,
    ExternalServiceError,
    NotFoundError,
)
from core.logging import get_logger

logger = get_logger(__name__)


class AuthService(BaseService):
    """
    Service for authentication operations.
    
    Provides business logic for:
    - User login with AWS Cognito
    - Token validation
    - Password management
    - User lookup
    """
    
    def __init__(self, db: Session):
        """
        Initialize the auth service.
        
        Args:
            db: The database session
        """
        super().__init__(db)
        self.staff_repo = StaffRepository(db)
        self._cognito_client = None
        self._jwks_cache: Dict = {}
    
    # =========================================================================
    # Cognito Client
    # =========================================================================
    
    @property
    def cognito_client(self):
        """Get or create the Cognito client."""
        if self._cognito_client is None:
            self._cognito_client = boto3.client(
                "cognito-idp",
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
            )
        return self._cognito_client
    
    # =========================================================================
    # Authentication
    # =========================================================================
    
    def login(
        self,
        email: str,
        password: str
    ) -> Dict[str, Any]:
        """
        Authenticate a user with email and password.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Dictionary with login result:
            - If successful: {valid: True, tokens: {...}, user_status: "CONFIRMED"}
            - If password change required: {valid: True, session: "...", user_status: "FORCE_CHANGE_PASSWORD"}
            - If failed: {valid: False, message: "..."}
            
        Raises:
            ExternalServiceError: If Cognito service fails
        """
        if not settings.cognito_user_pool_id or not settings.cognito_client_id:
            raise ExternalServiceError(
                message="Cognito is not configured",
                service_name="AWS Cognito"
            )
        
        try:
            auth_params = {
                "USERNAME": email,
                "PASSWORD": password,
            }
            
            # Add secret hash if client secret is configured
            if settings.cognito_client_secret:
                auth_params["SECRET_HASH"] = self._get_secret_hash(email)
            
            response = self.cognito_client.admin_initiate_auth(
                UserPoolId=settings.cognito_user_pool_id,
                ClientId=settings.cognito_client_id,
                AuthFlow="ADMIN_USER_PASSWORD_AUTH",
                AuthParameters=auth_params,
            )
            
            # Successful authentication
            if "AuthenticationResult" in response:
                auth_result = response["AuthenticationResult"]
                self.logger.info(f"Successful login for: {email}")
                
                return {
                    "valid": True,
                    "message": "Login successful",
                    "user_status": "CONFIRMED",
                    "tokens": {
                        "access_token": auth_result["AccessToken"],
                        "refresh_token": auth_result["RefreshToken"],
                        "id_token": auth_result["IdToken"],
                        "token_type": auth_result["TokenType"],
                    }
                }
            
            # Challenge required (e.g., password change)
            if "ChallengeName" in response:
                challenge_name = response["ChallengeName"]
                session = response.get("Session")
                self.logger.info(f"Login for {email} requires challenge: {challenge_name}")
                
                if challenge_name == "NEW_PASSWORD_REQUIRED":
                    return {
                        "valid": True,
                        "message": "Password change required",
                        "user_status": "FORCE_CHANGE_PASSWORD",
                        "session": session,
                    }
                else:
                    return {
                        "valid": True,
                        "message": f"Challenge required: {challenge_name}",
                        "user_status": "CHALLENGE_REQUIRED",
                        "session": session,
                    }
            
            # Unexpected response
            self.logger.warning(f"Unexpected Cognito response for {email}")
            return {
                "valid": False,
                "message": "Unexpected authentication response"
            }
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            
            self.logger.error(f"Cognito error for {email}: {error_code}")
            
            if error_code == "NotAuthorizedException":
                return {"valid": False, "message": "Invalid email or password"}
            elif error_code == "UserNotFoundException":
                return {"valid": False, "message": "User not found"}
            else:
                raise ExternalServiceError(
                    message=f"Authentication failed: {error_message}",
                    service_name="AWS Cognito"
                )
    
    def complete_new_password(
        self,
        email: str,
        new_password: str,
        session: str
    ) -> Dict[str, Any]:
        """
        Complete password setup for a user with a temporary password.
        
        Args:
            email: User's email address
            new_password: The new password to set
            session: Session token from the login challenge
            
        Returns:
            Dictionary with tokens on success
            
        Raises:
            AuthenticationError: If session is invalid or expired
            ExternalServiceError: If Cognito service fails
        """
        try:
            challenge_responses = {
                "USERNAME": email,
                "NEW_PASSWORD": new_password,
            }
            
            if settings.cognito_client_secret:
                challenge_responses["SECRET_HASH"] = self._get_secret_hash(email)
            
            response = self.cognito_client.admin_respond_to_auth_challenge(
                UserPoolId=settings.cognito_user_pool_id,
                ClientId=settings.cognito_client_id,
                ChallengeName="NEW_PASSWORD_REQUIRED",
                Session=session,
                ChallengeResponses=challenge_responses,
            )
            
            if "AuthenticationResult" in response:
                auth_result = response["AuthenticationResult"]
                self.logger.info(f"Password changed successfully for: {email}")
                
                return {
                    "message": "Password changed successfully",
                    "tokens": {
                        "access_token": auth_result["AccessToken"],
                        "refresh_token": auth_result["RefreshToken"],
                        "id_token": auth_result["IdToken"],
                        "token_type": auth_result["TokenType"],
                    }
                }
            
            raise AuthenticationError(
                message="Could not set new password"
            )
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            
            if error_code in ["NotAuthorizedException", "CodeMismatchException", "ExpiredCodeException"]:
                raise AuthenticationError(
                    message="Invalid or expired session. Please try logging in again."
                )
            elif error_code == "InvalidPasswordException":
                raise AuthenticationError(
                    message="New password does not meet requirements"
                )
            else:
                raise ExternalServiceError(
                    message=str(e.response["Error"]["Message"]),
                    service_name="AWS Cognito"
                )
    
    # =========================================================================
    # User Lookup
    # =========================================================================
    
    def get_staff_by_cognito_sub(self, sub: str) -> Optional[StaffProfile]:
        """
        Get a staff profile by Cognito user ID (sub).
        
        Note: This requires the staff_uuid to match the Cognito sub.
        
        Args:
            sub: The Cognito user ID (sub claim)
            
        Returns:
            The StaffProfile instance, or None if not found
        """
        try:
            from uuid import UUID
            staff_uuid = UUID(sub)
            return self.staff_repo.get_by_staff_uuid(staff_uuid)
        except ValueError:
            return None
    
    def get_staff_by_email(self, email: str) -> Optional[StaffProfile]:
        """
        Get a staff profile by email address.
        
        Args:
            email: The staff member's email
            
        Returns:
            The StaffProfile instance, or None if not found
        """
        return self.staff_repo.get_by_email(email)
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _get_secret_hash(self, username: str) -> str:
        """
        Calculate the secret hash for Cognito API calls.
        
        Args:
            username: The username (email)
            
        Returns:
            The calculated secret hash
        """
        message = username + settings.cognito_client_id
        key = settings.cognito_client_secret.encode("utf-8")
        msg = message.encode("utf-8")
        
        digest = hmac.new(key, msg, hashlib.sha256).digest()
        return base64.b64encode(digest).decode()
    
    def get_jwks(self) -> Dict:
        """
        Fetch and cache the JSON Web Key Set from Cognito.
        
        Returns:
            The JWKS containing public keys for token verification
        """
        if self._jwks_cache:
            return self._jwks_cache
        
        if not settings.cognito_jwks_url:
            raise ExternalServiceError(
                message="Cognito JWKS URL not configured",
                service_name="AWS Cognito"
            )
        
        try:
            response = requests.get(settings.cognito_jwks_url)
            response.raise_for_status()
            self._jwks_cache = response.json()
            return self._jwks_cache
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch JWKS: {e}")
            raise ExternalServiceError(
                message="Could not fetch security keys",
                service_name="AWS Cognito"
            )

