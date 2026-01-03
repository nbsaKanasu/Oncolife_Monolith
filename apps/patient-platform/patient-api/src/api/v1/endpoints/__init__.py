"""
API V1 Endpoints.

This package contains all endpoint handlers organized by domain.
Each module corresponds to a logical grouping of API endpoints.
"""

from . import auth, chat, patients, profile, health

__all__ = ["auth", "chat", "patients", "profile", "health"]

