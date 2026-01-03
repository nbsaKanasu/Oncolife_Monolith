"""
Domain-Specific Database Models for OncoLife Patient API.

This module organizes SQLAlchemy models by domain:
- user.py: User authentication and profile models
- patient.py: Patient-specific models
- conversation.py: Chat, messages, and symptom tracking
- medical.py: Medical records, chemo, and clinical data

All models inherit from Base and use appropriate mixins.

Usage:
    from db.models import Patient, Conversation, Message
    from db.models import User, PatientProfile
"""

from .user import User, PatientProfile, StaffProfile
from .patient import Patient
from .conversation import Conversation, Message
from .medical import (
    ChemoSession,
    ChemoSymptom,
    DiaryEntry,
    ConversationSummary,
)

__all__ = [
    # User models
    "User",
    "PatientProfile",
    "StaffProfile",
    # Patient models
    "Patient",
    # Conversation models
    "Conversation",
    "Message",
    # Medical models
    "ChemoSession",
    "ChemoSymptom",
    "DiaryEntry",
    "ConversationSummary",
]

