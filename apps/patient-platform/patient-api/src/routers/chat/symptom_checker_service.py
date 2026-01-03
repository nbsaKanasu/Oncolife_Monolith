"""
Symptom Checker Service.
Provides the main interface for the symptom checker conversation flow.
Replaces the LLM-based chat service with a rule-based approach.
"""
from typing import Dict, Any, List, Tuple, Optional, AsyncGenerator
from uuid import UUID
from datetime import datetime, time
from sqlalchemy.orm import Session
import pytz
import json
import logging

from .symptom_checker import SymptomCheckerEngine, TriageLevel
from .symptom_checker.symptom_engine import ConversationState, EngineResponse
from .models import (
    WebSocketMessageIn, WebSocketMessageOut,
    ConnectionEstablished, Message
)
from db.patient_models import Conversations as ChatModel, Messages as MessageModel

logger = logging.getLogger(__name__)


class SymptomCheckerService:
    """
    Service for managing symptom checker conversations.
    Uses a rule-based engine instead of LLM.
    """

    def __init__(self, db: Session):
        self.db = db
        self.engine = None

    def create_chat(self, patient_uuid: UUID, commit: bool = True) -> Tuple[ChatModel, Dict[str, Any]]:
        """
        Creates a new symptom checker chat session.
        """
        # Create the conversation record
        new_chat = ChatModel(
            patient_uuid=patient_uuid,
            conversation_state="symptom_selection",
            symptom_list=[]
        )
        self.db.add(new_chat)
        
        if commit:
            self.db.commit()
            self.db.refresh(new_chat)

        # Initialize the engine and get the greeting
        engine = SymptomCheckerEngine()
        response = engine.start_conversation()

        # Store engine state in chat metadata
        new_chat.engine_state = response.state.to_dict() if response.state else {}
        self.db.commit()

        initial_message = {
            "text": response.message,
            "type": self._map_message_type(response.message_type),
            "frontend_type": response.message_type,
            "options": [opt['label'] for opt in response.options] if response.options else [],
            "options_data": response.options
        }

        return new_chat, initial_message

    def delete_chat(self, chat_uuid: UUID, patient_uuid: UUID):
        """Deletes a chat conversation after verifying ownership."""
        chat = self.db.query(ChatModel).filter(
            ChatModel.uuid == chat_uuid,
            ChatModel.patient_uuid == patient_uuid
        ).first()

        if not chat:
            raise ValueError("Chat not found or access denied.")
        
        self.db.delete(chat)
        self.db.commit()

    def get_or_create_today_session(
        self, 
        patient_uuid: UUID, 
        user_timezone: str = "America/Los_Angeles"
    ) -> Tuple[ChatModel, List[MessageModel], bool]:
        """
        Gets the most recent chat for today, or creates a new one if none exists.
        """
        # Get today's date in user's timezone
        user_tz = pytz.timezone(user_timezone)
        user_now = datetime.now(user_tz)
        today_start = datetime.combine(user_now.date(), time.min)
        today_end = datetime.combine(user_now.date(), time.max)
        
        # Convert to UTC for database query
        utc_today_start = user_tz.localize(today_start).astimezone(pytz.UTC)
        utc_today_end = user_tz.localize(today_end).astimezone(pytz.UTC)
        
        # Query for today's chat
        today_chat = self.db.query(ChatModel).filter(
            ChatModel.patient_uuid == patient_uuid,
            ChatModel.created_at >= utc_today_start,
            ChatModel.created_at <= utc_today_end
        ).order_by(ChatModel.created_at.desc()).first()
        
        if today_chat:
            messages = self.db.query(MessageModel).filter(
                MessageModel.chat_uuid == today_chat.uuid
            ).order_by(MessageModel.created_at).all()
            return today_chat, messages, False
        else:
            # Create new chat
            new_chat, initial_question = self.create_chat(patient_uuid, commit=True)
            
            # Create the first assistant message
            first_message = MessageModel(
                chat_uuid=new_chat.uuid,
                sender="assistant",
                message_type=initial_question["type"],
                content=initial_question["text"],
                structured_data={
                    "options": initial_question.get("options", []),
                    "options_data": initial_question.get("options_data", []),
                    "frontend_type": initial_question.get("frontend_type", "text")
                }
            )
            
            self.db.add(first_message)
            self.db.commit()
            self.db.refresh(first_message)
            
            return new_chat, [first_message], True

    async def process_message_stream(
        self, 
        chat_uuid: UUID, 
        message: WebSocketMessageIn
    ) -> AsyncGenerator[Any, None]:
        """
        Processes a message using the rule-based symptom checker engine.
        """
        logger.info(f"Processing symptom checker message for chat {chat_uuid}: {message.content}")
        
        chat = self.db.query(ChatModel).filter(ChatModel.uuid == chat_uuid).first()
        if not chat:
            logger.error(f"Chat {chat_uuid} not found")
            return

        # 1. Save the user's message
        user_msg = MessageModel(
            chat_uuid=chat_uuid,
            sender="user",
            message_type=message.message_type,
            content=message.content
        )
        self.db.add(user_msg)
        self.db.commit()
        self.db.refresh(user_msg)
        yield Message.from_orm(user_msg)

        # 2. Load or create the engine with saved state
        engine_state_data = getattr(chat, 'engine_state', None) or {}
        if engine_state_data:
            state = ConversationState.from_dict(engine_state_data)
            engine = SymptomCheckerEngine(state=state)
        else:
            engine = SymptomCheckerEngine()

        # 3. Parse the user's response
        user_response = self._parse_user_response(message)

        # 4. Process the response through the engine
        try:
            engine_response = engine.process_response(user_response)
        except Exception as e:
            logger.error(f"Engine processing error: {e}")
            error_msg = MessageModel(
                chat_uuid=chat_uuid,
                sender="assistant",
                message_type="text",
                content="I'm sorry, I encountered an error. Please try again."
            )
            self.db.add(error_msg)
            self.db.commit()
            self.db.refresh(error_msg)
            yield Message.from_orm(error_msg)
            return

        # 5. Save the engine state
        if engine_response.state:
            chat.engine_state = engine_response.state.to_dict()
            
            # Update chat fields based on state
            chat.symptom_list = engine_response.state.selected_symptoms
            
            if engine_response.is_complete:
                if engine_response.triage_level == TriageLevel.CALL_911:
                    chat.conversation_state = "EMERGENCY"
                else:
                    chat.conversation_state = "COMPLETED"
            else:
                chat.conversation_state = engine_response.state.phase.value
        
        self.db.commit()

        # 6. Create and save the assistant message
        assistant_msg = MessageModel(
            chat_uuid=chat_uuid,
            sender="assistant",
            message_type=self._map_message_type(engine_response.message_type),
            content=engine_response.message,
            structured_data={
                "options": [opt['label'] for opt in engine_response.options] if engine_response.options else None,
                "options_data": engine_response.options,
                "frontend_type": engine_response.message_type,
                "triage_level": engine_response.triage_level.value if engine_response.triage_level else None,
                "is_complete": engine_response.is_complete
            }
        )
        self.db.add(assistant_msg)
        self.db.commit()
        self.db.refresh(assistant_msg)

        # Convert for frontend
        frontend_message = Message.from_orm(assistant_msg)
        frontend_message.message_type = self._map_frontend_type(engine_response.message_type)
        
        yield frontend_message

    def _parse_user_response(self, message: WebSocketMessageIn) -> Any:
        """Parse the user's response based on message type."""
        content = message.content
        msg_type = message.message_type

        # Handle yes/no responses
        if msg_type == 'button_response':
            if content.lower() in ['yes', 'true']:
                return True
            elif content.lower() in ['no', 'false']:
                return False
            return content

        # Handle multi-select responses (comma-separated)
        if msg_type == 'multi_select_response':
            # Parse comma-separated values
            values = [v.strip() for v in content.split(',') if v.strip()]
            
            # Try to get the actual values from structured_data
            if message.structured_data and 'selected_values' in message.structured_data:
                return message.structured_data['selected_values']
            
            return values

        # Handle number responses
        try:
            return float(content)
        except (ValueError, TypeError):
            pass

        return content

    def _map_message_type(self, engine_type: str) -> str:
        """Map engine message types to database message types."""
        mapping = {
            'text': 'text',
            'yes_no': 'single_select',
            'choice': 'single_select',
            'multiselect': 'multi_select',
            'number': 'text',
            'symptom_select': 'multi_select',
            'triage_result': 'text'
        }
        return mapping.get(engine_type, 'text')

    def _map_frontend_type(self, engine_type: str) -> str:
        """Map engine message types to frontend message types."""
        mapping = {
            'text': 'text',
            'yes_no': 'single-select',
            'choice': 'single-select',
            'multiselect': 'multi-select',
            'number': 'text',
            'symptom_select': 'symptom-select',
            'triage_result': 'text'
        }
        return mapping.get(engine_type, 'text')

    def get_connection_ack(self, chat_uuid: UUID) -> ConnectionEstablished:
        """Returns a connection acknowledgment message."""
        return ConnectionEstablished(
            content="Connection established successfully.",
            chat_state={
                "chat_uuid": str(chat_uuid),
                "status": "connected"
            }
        )

