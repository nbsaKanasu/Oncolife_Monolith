"""
Service Layer for Business Logic.

This module provides the service layer that:
- Contains all business logic
- Orchestrates operations across repositories
- Handles complex workflows
- Provides a clean interface for API endpoints

Architecture:
    services/
    ├── base.py              # Base service class
    ├── auth_service.py      # Authentication logic (Cognito)
    ├── patient_service.py   # Patient operations
    ├── chat_service.py      # Symptom checker chat
    ├── chemo_service.py     # Chemotherapy dates
    ├── diary_service.py     # Patient diary entries
    ├── summary_service.py   # Conversation summaries
    └── profile_service.py   # Patient profile

Principles:
    - Services should be stateless
    - Services orchestrate, repositories persist
    - Services handle business rules and validation
    - Services are easily testable

Usage:
    from services import PatientService, ChatService
    
    @app.get("/patients/{patient_id}")
    async def get_patient(
        patient_id: UUID,
        db: Session = Depends(get_patient_db)
    ):
        service = PatientService(db)
        return service.get_patient(patient_id)
"""

from .base import BaseService
from .patient_service import PatientService
from .auth_service import AuthService
from .chat_service import ChatService
from .chemo_service import ChemoService
from .diary_service import DiaryService
from .summary_service import SummaryService
from .profile_service import ProfileService

# Onboarding services
from .ocr_service import OCRService
from .notification_service import NotificationService
from .onboarding_service import OnboardingService
from .fax_service import FaxService

# Keep backward compatibility
from .conversation_service import ConversationService

__all__ = [
    "BaseService",
    "PatientService",
    "AuthService",
    "ChatService",
    "ChemoService",
    "DiaryService",
    "SummaryService",
    "ProfileService",
    "ConversationService",  # For backward compatibility
    # Onboarding services
    "OCRService",
    "NotificationService",
    "OnboardingService",
    "FaxService",
]

