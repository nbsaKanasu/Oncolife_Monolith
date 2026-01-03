"""
Chat / Symptom Checker Endpoints.

Provides endpoints for:
- Session management
- Message handling
- Symptom tracking
- Triage alerts

These endpoints power the patient-facing symptom checker chatbot.
"""

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from api.deps import get_patient_db, get_current_user, get_pagination, PaginationParams
from services import ConversationService
from core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


# =============================================================================
# SESSION MANAGEMENT
# =============================================================================

@router.get("/session", summary="Get or create chat session")
async def get_or_create_session(
    db: Session = Depends(get_patient_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get active conversation or create a new one.
    
    Returns the current active session for the patient,
    or creates a new one if none exists.
    
    Returns:
        Session info with conversation ID and messages
    """
    patient_uuid = current_user.get("uuid")
    
    service = ConversationService(db)
    conversation, is_new = service.get_or_create_session(patient_uuid)
    
    # Get messages
    messages = service.get_messages(conversation.uuid)
    
    return {
        "conversation_id": str(conversation.uuid),
        "is_new_session": is_new,
        "state": conversation.conversation_state,
        "symptom_list": conversation.symptom_list or [],
        "messages": [
            {
                "id": msg.id,
                "sender": msg.sender,
                "content": msg.content,
                "type": msg.message_type,
                "structured_data": msg.structured_data,
                "created_at": msg.created_at.isoformat() if msg.created_at else None
            }
            for msg in messages
        ]
    }


@router.get("/conversations", summary="Get patient conversations")
async def get_conversations(
    pagination: PaginationParams = Depends(get_pagination),
    db: Session = Depends(get_patient_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get all conversations for the current patient.
    
    Returns:
        List of conversations (newest first)
    """
    patient_uuid = current_user.get("uuid")
    
    service = ConversationService(db)
    conversations = service.get_patient_conversations(
        patient_uuid,
        skip=pagination.skip,
        limit=pagination.limit
    )
    
    return {
        "conversations": [
            {
                "id": str(c.uuid),
                "state": c.conversation_state,
                "triage_level": c.triage_level,
                "symptom_list": c.symptom_list or [],
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "completed_at": c.completed_at.isoformat() if c.completed_at else None
            }
            for c in conversations
        ],
        "count": len(conversations)
    }


# =============================================================================
# MESSAGE HANDLING
# =============================================================================

@router.post("/message", summary="Send a message")
async def send_message(
    message: Dict[str, Any],  # Should be a Pydantic model
    db: Session = Depends(get_patient_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Send a message in the current conversation.
    
    Processes user input through the symptom checker engine
    and returns the assistant's response.
    
    Args:
        message: Message with content and optional type
    
    Returns:
        Assistant response with message and metadata
    """
    patient_uuid = current_user.get("uuid")
    
    service = ConversationService(db)
    
    # Get or create session
    conversation, _ = service.get_or_create_session(patient_uuid)
    
    # Process message
    content = message.get("content", "")
    message_type = message.get("type", "text")
    
    response = service.process_message(
        conversation_id=conversation.uuid,
        user_input=content,
        message_type=message_type
    )
    
    return {
        "conversation_id": str(conversation.uuid),
        "response": response
    }


@router.get("/conversations/{conversation_id}/messages", summary="Get conversation messages")
async def get_messages(
    conversation_id: UUID,
    pagination: PaginationParams = Depends(get_pagination),
    db: Session = Depends(get_patient_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get messages for a specific conversation.
    
    Args:
        conversation_id: Conversation UUID
    
    Returns:
        List of messages
    """
    service = ConversationService(db)
    messages = service.get_messages(
        conversation_id,
        skip=pagination.skip,
        limit=pagination.limit
    )
    
    return {
        "messages": [
            {
                "id": msg.id,
                "sender": msg.sender,
                "content": msg.content,
                "type": msg.message_type,
                "structured_data": msg.structured_data,
                "created_at": msg.created_at.isoformat() if msg.created_at else None
            }
            for msg in messages
        ],
        "count": len(messages)
    }


# =============================================================================
# TRIAGE AND ALERTS (Admin/Staff endpoints)
# =============================================================================

@router.get("/alerts", summary="Get triage alerts")
async def get_triage_alerts(
    hours: int = 24,
    db: Session = Depends(get_patient_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get conversations requiring care team attention.
    
    Returns conversations with notify_care_team or call_911 triage.
    
    Args:
        hours: Look back period in hours (default 24)
    
    Returns:
        List of alert conversations
    """
    since = datetime.utcnow() - timedelta(hours=hours)
    
    service = ConversationService(db)
    alerts = service.get_care_team_alerts(since=since)
    
    return {
        "alerts": [
            {
                "conversation_id": str(c.uuid),
                "patient_id": str(c.patient_uuid),
                "triage_level": c.triage_level,
                "triage_message": c.triage_message,
                "symptoms": c.symptom_list or [],
                "created_at": c.created_at.isoformat() if c.created_at else None
            }
            for c in alerts
        ],
        "count": len(alerts),
        "period_hours": hours
    }


@router.get("/stats", summary="Get triage statistics")
async def get_triage_stats(
    hours: int = 24,
    db: Session = Depends(get_patient_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get conversation statistics by triage level.
    
    Args:
        hours: Look back period in hours (default 24)
    
    Returns:
        Counts by triage level
    """
    since = datetime.utcnow() - timedelta(hours=hours)
    
    service = ConversationService(db)
    stats = service.get_triage_statistics(since=since)
    
    return {
        "statistics": stats,
        "period_hours": hours
    }


# =============================================================================
# WEBSOCKET (For real-time chat)
# =============================================================================

@router.websocket("/ws/{patient_id}")
async def websocket_chat(
    websocket: WebSocket,
    patient_id: UUID,
    db: Session = Depends(get_patient_db)
):
    """
    WebSocket endpoint for real-time chat.
    
    Provides bidirectional communication for the symptom checker.
    
    Note: This is a placeholder. Full implementation requires
    proper connection management and authentication.
    """
    await websocket.accept()
    
    logger.info(f"WebSocket connected for patient {patient_id}")
    
    try:
        service = ConversationService(db)
        conversation, is_new = service.get_or_create_session(patient_id)
        
        # Send initial messages if new session
        if is_new:
            messages = service.get_messages(conversation.uuid)
            for msg in messages:
                await websocket.send_json({
                    "type": "message",
                    "data": {
                        "sender": msg.sender,
                        "content": msg.content,
                        "message_type": msg.message_type,
                        "structured_data": msg.structured_data
                    }
                })
        
        # Message loop
        while True:
            data = await websocket.receive_json()
            
            # Process message
            content = data.get("content", "")
            message_type = data.get("type", "text")
            
            response = service.process_message(
                conversation_id=conversation.uuid,
                user_input=content,
                message_type=message_type
            )
            
            # Send response
            await websocket.send_json({
                "type": "message",
                "data": response
            })
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for patient {patient_id}")
    except Exception as e:
        logger.error(f"WebSocket error for patient {patient_id}: {e}")
        await websocket.close(code=1011)

