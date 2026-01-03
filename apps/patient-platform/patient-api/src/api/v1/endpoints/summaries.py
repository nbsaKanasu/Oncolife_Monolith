"""
Summaries Endpoints - Patient API
==================================

Endpoints for conversation summary operations:
- GET /{year}/{month}: Get summaries by month
- GET /{conversation_uuid}: Get summary details
- GET /recent: Get recent summaries
"""

from uuid import UUID
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from api.deps import get_patient_db
from services import SummaryService
from core.logging import get_logger
from core.exceptions import NotFoundError, ValidationError

logger = get_logger(__name__)

router = APIRouter()


# =============================================================================
# Request/Response Schemas
# =============================================================================

class ConversationSummarySchema(BaseModel):
    """Response model for conversation summary."""
    uuid: str
    created_at: datetime
    conversation_state: Optional[str] = None
    symptom_list: Optional[List[str]] = None
    severity_list: Optional[dict] = None
    longer_summary: Optional[str] = None
    medication_list: Optional[List] = None
    bulleted_summary: Optional[str] = None
    overall_feeling: Optional[str] = None

    class Config:
        from_attributes = True


class ConversationDetailSchema(BaseModel):
    """Detailed response model for conversation."""
    uuid: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    conversation_state: Optional[str] = None
    symptom_list: Optional[List[str]] = None
    severity_list: Optional[dict] = None
    longer_summary: Optional[str] = None
    medication_list: Optional[List] = None
    bulleted_summary: Optional[str] = None
    overall_feeling: Optional[str] = None

    class Config:
        from_attributes = True


# =============================================================================
# Endpoints
# =============================================================================

@router.get(
    "/{year}/{month}",
    response_model=List[ConversationSummarySchema],
    summary="Get summaries by month",
    description="Get conversation summaries for a specific month."
)
async def get_summaries_by_month(
    year: int,
    month: int,
    db: Session = Depends(get_patient_db),
    patient_uuid: str = Query(..., description="Patient UUID"),
    timezone: str = Query(default="America/Los_Angeles", description="User's timezone"),
):
    """
    Get all conversation summaries for a specific month and year.
    
    Only returns conversations that have been processed
    (have a bulleted_summary).
    """
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Month must be between 1 and 12",
        )
    
    logger.info(f"Get summaries by month: patient={patient_uuid} {year}/{month}")
    
    summary_service = SummaryService(db)
    
    try:
        summaries = summary_service.get_by_month(UUID(patient_uuid), year, month, timezone)
        return [ConversationSummarySchema(**s) for s in summaries]
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/detail/{conversation_uuid}",
    response_model=ConversationDetailSchema,
    summary="Get summary details",
    description="Get detailed information about a specific conversation."
)
async def get_conversation_details(
    conversation_uuid: str,
    db: Session = Depends(get_patient_db),
    patient_uuid: str = Query(..., description="Patient UUID"),
    timezone: str = Query(default="America/Los_Angeles", description="User's timezone"),
):
    """
    Get detailed information about a specific conversation
    that has been processed.
    """
    logger.info(f"Get summary details: conversation={conversation_uuid}")
    
    summary_service = SummaryService(db)
    
    try:
        summary = summary_service.get_by_uuid(
            UUID(conversation_uuid), UUID(patient_uuid), timezone
        )
        return ConversationDetailSchema(**summary)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/recent",
    response_model=List[ConversationSummarySchema],
    summary="Get recent summaries",
    description="Get recent conversation summaries."
)
async def get_recent_summaries(
    db: Session = Depends(get_patient_db),
    patient_uuid: str = Query(..., description="Patient UUID"),
    timezone: str = Query(default="America/Los_Angeles", description="User's timezone"),
    limit: int = Query(default=10, le=50),
):
    """
    Get recent conversation summaries.
    """
    logger.info(f"Get recent summaries: patient={patient_uuid} limit={limit}")
    
    summary_service = SummaryService(db)
    summaries = summary_service.get_recent(UUID(patient_uuid), limit, timezone)
    
    return [ConversationSummarySchema(**s) for s in summaries]


@router.get(
    "/count",
    summary="Count conversations",
    description="Count completed conversations for patient."
)
async def count_conversations(
    db: Session = Depends(get_patient_db),
    patient_uuid: str = Query(..., description="Patient UUID"),
):
    """
    Get count of completed conversations.
    """
    summary_service = SummaryService(db)
    count = summary_service.count_conversations(UUID(patient_uuid))
    
    return {"count": count}

