"""
Symptom Checker Engine.
Manages the rule-based conversation flow for symptom triage.
"""
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID
import json
import logging

from .constants import TriageLevel, InputType, ConversationPhase
from .symptom_definitions import (
    SYMPTOMS, SymptomDef, Question, LogicResult,
    get_visible_symptoms, get_symptom_by_id
)

logger = logging.getLogger(__name__)


@dataclass
class ConversationState:
    """Tracks the current state of the symptom checker conversation."""
    phase: ConversationPhase = ConversationPhase.GREETING
    current_symptom_id: Optional[str] = None
    current_question_index: int = 0
    is_follow_up: bool = False
    answers: Dict[str, Any] = field(default_factory=dict)
    selected_symptoms: List[str] = field(default_factory=list)
    completed_symptoms: List[str] = field(default_factory=list)
    triage_results: List[Dict[str, Any]] = field(default_factory=list)
    branch_stack: List[str] = field(default_factory=list)  # Stack for branching
    highest_triage_level: TriageLevel = TriageLevel.NONE

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state to dictionary."""
        return {
            'phase': self.phase.value,
            'current_symptom_id': self.current_symptom_id,
            'current_question_index': self.current_question_index,
            'is_follow_up': self.is_follow_up,
            'answers': self.answers,
            'selected_symptoms': self.selected_symptoms,
            'completed_symptoms': self.completed_symptoms,
            'triage_results': self.triage_results,
            'branch_stack': self.branch_stack,
            'highest_triage_level': self.highest_triage_level.value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationState':
        """Deserialize state from dictionary."""
        return cls(
            phase=ConversationPhase(data.get('phase', 'greeting')),
            current_symptom_id=data.get('current_symptom_id'),
            current_question_index=data.get('current_question_index', 0),
            is_follow_up=data.get('is_follow_up', False),
            answers=data.get('answers', {}),
            selected_symptoms=data.get('selected_symptoms', []),
            completed_symptoms=data.get('completed_symptoms', []),
            triage_results=data.get('triage_results', []),
            branch_stack=data.get('branch_stack', []),
            highest_triage_level=TriageLevel(data.get('highest_triage_level', 'none'))
        )


@dataclass
class EngineResponse:
    """Response from the symptom checker engine."""
    message: str
    message_type: str  # 'text', 'yes_no', 'choice', 'multiselect', 'number', 'symptom_select', 'triage_result'
    options: List[Dict[str, Any]] = field(default_factory=list)
    triage_level: Optional[TriageLevel] = None
    triage_message: Optional[str] = None
    is_complete: bool = False
    state: Optional[ConversationState] = None


class SymptomCheckerEngine:
    """
    Rule-based symptom checker engine.
    Manages the conversation flow and triage logic.
    """

    GREETING_MESSAGE = (
        "Hi! I'm Ruby, your symptom checker assistant. 👋\n\n"
        "I'm here to help you report any symptoms you're experiencing. "
        "Your responses will help your care team understand how you're feeling.\n\n"
        "Let's start by selecting the symptoms you'd like to discuss today."
    )

    def __init__(self, state: Optional[ConversationState] = None):
        """Initialize the engine with optional existing state."""
        self.state = state or ConversationState()

    def start_conversation(self) -> EngineResponse:
        """Start a new symptom checker conversation."""
        self.state = ConversationState(phase=ConversationPhase.SYMPTOM_SELECTION)
        
        symptoms = get_visible_symptoms()
        
        # Group by category
        emergency = [s for s in symptoms if s['category'] == 'emergency']
        common = [s for s in symptoms if s['category'] == 'common']
        other = [s for s in symptoms if s['category'] == 'other']
        
        options = []
        
        # Add emergency symptoms first
        for s in emergency:
            options.append({
                'label': f"🚨 {s['name']}",
                'value': s['id'],
                'category': 'emergency'
            })
        
        # Add common symptoms
        for s in common:
            options.append({
                'label': s['name'],
                'value': s['id'],
                'category': 'common'
            })
        
        # Add other symptoms
        for s in other:
            options.append({
                'label': s['name'],
                'value': s['id'],
                'category': 'other'
            })
        
        options.append({
            'label': "I'm feeling fine today",
            'value': 'none',
            'category': 'none'
        })

        return EngineResponse(
            message=self.GREETING_MESSAGE,
            message_type='symptom_select',
            options=options,
            state=self.state
        )

    def process_response(self, user_response: Any) -> EngineResponse:
        """
        Process a user's response and return the next step.
        
        Args:
            user_response: The user's answer (string, number, list, or bool)
        
        Returns:
            EngineResponse with the next question or triage result
        """
        logger.info(f"Processing response: {user_response}, Phase: {self.state.phase}")

        if self.state.phase == ConversationPhase.SYMPTOM_SELECTION:
            return self._handle_symptom_selection(user_response)
        
        elif self.state.phase == ConversationPhase.SCREENING:
            return self._handle_screening_response(user_response)
        
        elif self.state.phase == ConversationPhase.FOLLOW_UP:
            return self._handle_followup_response(user_response)
        
        elif self.state.phase == ConversationPhase.COMPLETED:
            return self._generate_summary()
        
        elif self.state.phase == ConversationPhase.EMERGENCY:
            return self._generate_emergency_response()
        
        else:
            return self.start_conversation()

    def _handle_symptom_selection(self, user_response: Any) -> EngineResponse:
        """Handle symptom selection from the user."""
        if isinstance(user_response, str):
            if user_response == 'none':
                self.state.phase = ConversationPhase.COMPLETED
                return EngineResponse(
                    message="Great to hear you're feeling fine today! 😊\n\n"
                            "Remember, you can always come back if you start experiencing any symptoms. "
                            "Take care!",
                    message_type='text',
                    is_complete=True,
                    state=self.state
                )
            selected = [user_response]
        elif isinstance(user_response, list):
            selected = [s for s in user_response if s != 'none']
        else:
            selected = []

        if not selected:
            self.state.phase = ConversationPhase.COMPLETED
            return EngineResponse(
                message="Great to hear you're feeling fine today! Take care!",
                message_type='text',
                is_complete=True,
                state=self.state
            )

        self.state.selected_symptoms = selected
        self.state.phase = ConversationPhase.SCREENING
        
        return self._start_next_symptom()

    def _start_next_symptom(self) -> EngineResponse:
        """Start processing the next symptom in the queue."""
        # Check if there are branched symptoms to process first
        if self.state.branch_stack:
            next_symptom_id = self.state.branch_stack.pop(0)
        elif self.state.selected_symptoms:
            # Get next unprocessed symptom
            remaining = [s for s in self.state.selected_symptoms 
                        if s not in self.state.completed_symptoms]
            if not remaining:
                return self._generate_summary()
            next_symptom_id = remaining[0]
        else:
            return self._generate_summary()

        symptom = get_symptom_by_id(next_symptom_id)
        if not symptom:
            logger.error(f"Symptom not found: {next_symptom_id}")
            self.state.completed_symptoms.append(next_symptom_id)
            return self._start_next_symptom()

        self.state.current_symptom_id = next_symptom_id
        self.state.current_question_index = 0
        self.state.is_follow_up = False
        self.state.answers = {}
        self.state.phase = ConversationPhase.SCREENING

        return self._get_next_question(symptom)

    def _get_next_question(self, symptom: SymptomDef) -> EngineResponse:
        """Get the next applicable question for the current symptom."""
        questions = symptom.follow_up_questions if self.state.is_follow_up else symptom.screening_questions
        
        while self.state.current_question_index < len(questions):
            question = questions[self.state.current_question_index]
            
            # Check if question condition is met
            if question.condition is None or question.condition(self.state.answers):
                return self._format_question(question, symptom)
            
            # Skip this question if condition not met
            self.state.current_question_index += 1

        # No more questions in current phase
        return self._evaluate_current_phase(symptom)

    def _format_question(self, question: Question, symptom: SymptomDef) -> EngineResponse:
        """Format a question into an EngineResponse."""
        options = []
        
        if question.input_type == InputType.YES_NO:
            options = [
                {'label': 'Yes', 'value': True},
                {'label': 'No', 'value': False}
            ]
            message_type = 'yes_no'
        
        elif question.input_type == InputType.CHOICE:
            options = [{'label': o.label, 'value': o.value} for o in question.options]
            message_type = 'choice'
        
        elif question.input_type == InputType.MULTISELECT:
            options = [{'label': o.label, 'value': o.value} for o in question.options]
            message_type = 'multiselect'
        
        elif question.input_type == InputType.NUMBER:
            message_type = 'number'
        
        else:  # TEXT
            message_type = 'text'

        # Add symptom context to first question
        prefix = ""
        if self.state.current_question_index == 0 and not self.state.is_follow_up:
            prefix = f"📋 **{symptom.name}**\n\n"

        return EngineResponse(
            message=prefix + question.text,
            message_type=message_type,
            options=options,
            state=self.state
        )

    def _handle_screening_response(self, user_response: Any) -> EngineResponse:
        """Handle a response during the screening phase."""
        symptom = get_symptom_by_id(self.state.current_symptom_id)
        if not symptom:
            return self._start_next_symptom()

        questions = symptom.screening_questions
        if self.state.current_question_index < len(questions):
            question = questions[self.state.current_question_index]
            self.state.answers[question.id] = user_response
            logger.info(f"Stored answer for {question.id}: {user_response}")

        self.state.current_question_index += 1
        return self._get_next_question(symptom)

    def _handle_followup_response(self, user_response: Any) -> EngineResponse:
        """Handle a response during the follow-up phase."""
        symptom = get_symptom_by_id(self.state.current_symptom_id)
        if not symptom:
            return self._start_next_symptom()

        questions = symptom.follow_up_questions
        if self.state.current_question_index < len(questions):
            question = questions[self.state.current_question_index]
            self.state.answers[question.id] = user_response
            logger.info(f"Stored follow-up answer for {question.id}: {user_response}")

        self.state.current_question_index += 1
        return self._get_next_question(symptom)

    def _evaluate_current_phase(self, symptom: SymptomDef) -> EngineResponse:
        """Evaluate the current phase and determine next steps."""
        if self.state.is_follow_up:
            # Evaluate follow-up
            if symptom.evaluate_follow_up:
                result = symptom.evaluate_follow_up(self.state.answers)
                return self._handle_logic_result(result, symptom)
            else:
                return self._complete_symptom(symptom)
        else:
            # Evaluate screening
            result = symptom.evaluate_screening(self.state.answers)
            return self._handle_logic_result(result, symptom)

    def _handle_logic_result(self, result: LogicResult, symptom: SymptomDef) -> EngineResponse:
        """Handle the result of a logic evaluation."""
        # Record triage result if any
        if result.triage_level != TriageLevel.NONE:
            self._record_triage_result(symptom.id, symptom.name, result)

        if result.action == 'stop':
            # Check for emergency
            if result.triage_level == TriageLevel.CALL_911:
                self.state.phase = ConversationPhase.EMERGENCY
                return self._generate_emergency_response(result.triage_message)
            
            return self._complete_symptom(symptom, result.triage_message)

        elif result.action == 'branch':
            # Add branched symptom to stack
            if result.branch_to_symptom_id and result.branch_to_symptom_id not in self.state.completed_symptoms:
                self.state.branch_stack.insert(0, result.branch_to_symptom_id)
            
            return self._complete_symptom(symptom)

        elif result.action == 'continue':
            # Check if there are follow-up questions
            if not self.state.is_follow_up and symptom.follow_up_questions:
                self.state.is_follow_up = True
                self.state.current_question_index = 0
                return self._get_next_question(symptom)
            else:
                return self._complete_symptom(symptom)

        return self._complete_symptom(symptom)

    def _record_triage_result(self, symptom_id: str, symptom_name: str, result: LogicResult):
        """Record a triage result."""
        self.state.triage_results.append({
            'symptom_id': symptom_id,
            'symptom_name': symptom_name,
            'level': result.triage_level.value,
            'message': result.triage_message,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Update highest triage level
        levels = [TriageLevel.NONE, TriageLevel.NOTIFY_CARE_TEAM, TriageLevel.CALL_911]
        if levels.index(result.triage_level) > levels.index(self.state.highest_triage_level):
            self.state.highest_triage_level = result.triage_level

    def _complete_symptom(self, symptom: SymptomDef, message: Optional[str] = None) -> EngineResponse:
        """Complete processing of a symptom and move to the next."""
        self.state.completed_symptoms.append(symptom.id)
        
        # Check if we should show a status message
        if message:
            logger.info(f"Symptom {symptom.name} completed with message: {message}")
        
        return self._start_next_symptom()

    def _generate_emergency_response(self, message: Optional[str] = None) -> EngineResponse:
        """Generate emergency response for 911 situations."""
        emergency_text = (
            "🚨 **EMERGENCY - IMMEDIATE ACTION REQUIRED** 🚨\n\n"
            f"{message or 'Based on your responses, you need immediate medical attention.'}\n\n"
            "**Please call 911 immediately or go to your nearest emergency room.**\n\n"
            "If you cannot call yourself, please ask someone nearby to help you."
        )
        
        return EngineResponse(
            message=emergency_text,
            message_type='triage_result',
            triage_level=TriageLevel.CALL_911,
            triage_message=message,
            is_complete=True,
            state=self.state
        )

    def _generate_summary(self) -> EngineResponse:
        """Generate the final summary of the symptom check."""
        self.state.phase = ConversationPhase.COMPLETED
        
        if not self.state.triage_results:
            summary = (
                "✅ **Summary**\n\n"
                "Thank you for checking in! Based on your responses, no urgent concerns were identified.\n\n"
                "Continue to monitor your symptoms and reach out if anything changes. "
                "Your care team will review this information."
            )
            return EngineResponse(
                message=summary,
                message_type='triage_result',
                triage_level=TriageLevel.NONE,
                is_complete=True,
                state=self.state
            )

        # Generate summary based on highest triage level
        if self.state.highest_triage_level == TriageLevel.CALL_911:
            return self._generate_emergency_response()
        
        elif self.state.highest_triage_level == TriageLevel.NOTIFY_CARE_TEAM:
            alerts = [r for r in self.state.triage_results if r['level'] == 'notify_care_team']
            alert_text = "\n".join([f"• **{r['symptom_name']}**: {r['message']}" for r in alerts])
            
            summary = (
                "⚠️ **Summary - Care Team Notification**\n\n"
                "Based on your responses, the following concerns have been identified:\n\n"
                f"{alert_text}\n\n"
                "**Your care team has been notified and will follow up with you.**\n\n"
                "If your symptoms worsen or you develop new concerning symptoms, "
                "please call your care team or seek emergency care."
            )
            
            return EngineResponse(
                message=summary,
                message_type='triage_result',
                triage_level=TriageLevel.NOTIFY_CARE_TEAM,
                triage_message=alert_text,
                is_complete=True,
                state=self.state
            )
        
        else:
            summary = (
                "✅ **Summary**\n\n"
                "Thank you for checking in! Based on your responses, your symptoms appear manageable.\n\n"
                "Continue to monitor your symptoms and reach out if anything changes. "
                "Your care team will review this information at your next appointment."
            )
            
            return EngineResponse(
                message=summary,
                message_type='triage_result',
                triage_level=TriageLevel.NONE,
                is_complete=True,
                state=self.state
            )

    def get_state(self) -> ConversationState:
        """Get the current conversation state."""
        return self.state

    def set_state(self, state: ConversationState):
        """Set the conversation state."""
        self.state = state

    @staticmethod
    def get_available_symptoms() -> List[Dict[str, Any]]:
        """Get list of available symptoms for selection."""
        return get_visible_symptoms()



