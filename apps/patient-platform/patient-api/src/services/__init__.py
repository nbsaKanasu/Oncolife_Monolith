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
    ├── auth_service.py      # Authentication logic
    ├── patient_service.py   # Patient operations
    └── conversation_service.py  # Symptom checker logic

Principles:
    - Services should be stateless
    - Services orchestrate, repositories persist
    - Services handle business rules and validation
    - Services are easily testable

Usage:
    from services import PatientService, ConversationService
    
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
from .conversation_service import ConversationService

__all__ = [
    "BaseService",
    "PatientService",
    "ConversationService",
]

