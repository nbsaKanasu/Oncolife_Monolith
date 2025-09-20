import os
import json
import uuid
from typing import Dict, Any, List, Tuple, AsyncGenerator
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime, time
import pytz

from .models import (
    WebSocketMessageIn, WebSocketMessageOut,
    ConnectionEstablished, Message, ProcessResponse
)
from .constants import ConversationState
from .llm.gpt import GPT4oProvider
from .llm.groq import GroqProvider
from .llm.cerebras import CerebrasProvider
from db.patient_models import Conversations as ChatModel, Messages as MessageModel

LLM_PROVIDER = "groq"  # Options: "gpt4o", "groq", "cerebras"

def get_llm_provider():
    """Factory function to get the configured LLM provider."""
    if LLM_PROVIDER == "gpt4o":
        return GPT4oProvider()
    elif LLM_PROVIDER == "groq":
        return GroqProvider()
    elif LLM_PROVIDER == "cerebras":
        return CerebrasProvider()
    else:
        raise ValueError(f"Unknown LLM provider: {LLM_PROVIDER}")


# ===============================================================================
# Core Conversation Logic (with real database queries)
# ===============================================================================

class ConversationService:
    def __init__(self, db: Session):
        self.db = db

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
        return

    def create_chat(self, patient_uuid: UUID, commit: bool = True) -> Tuple[ChatModel, Dict[str, Any]]:
        """
        Creates a new chat, saves a system message, and updates the state.
        Can be part of a larger transaction if commit=False.
        """
        # 1. Create the parent Conversation object
        new_chat = ChatModel(
            patient_uuid=patient_uuid,
            conversation_state=ConversationState.CHEMO_CHECK_SENT,
            symptom_list=[],  # Always start with empty symptom list
            alerts=[]
        )
        self.db.add(new_chat)
        
        if commit:
            self.db.commit()
            self.db.refresh(new_chat)
            
        initial_question = {
            "text": "Did you get chemotherapy today?",
            "type": "single_select",  # Database format (underscore)
            "frontend_type": "single-select",  # Frontend format (hyphen)
            "options": ["Yes", "No", "I had it recently, but didn't record it"],
        }
        return new_chat, initial_question

    def _determine_next_state_and_response(self, chat: ChatModel, message: WebSocketMessageIn) -> Tuple[str, WebSocketMessageOut]:
        """The main state machine for the conversation."""
        current_state = chat.conversation_state
        next_state = current_state
        response_content = "I'm not sure how to respond to that. Can you try again?"
        response_options = []
        response_type = "text"

        if current_state == ConversationState.COMPLETED:
            response_content = "This conversation has ended. Please start a new one if you need assistance."
        
        elif current_state == ConversationState.CHEMO_CHECK_SENT:
            next_state = ConversationState.SYMPTOM_SELECTION_SENT
            response_content = "Please select any symptoms you're experiencing today."
            response_type = "multi_select"
            response_options = [
                "Fever",
                "Diarrhea",
                "Pain",
                "Nausea",
                "Vomiting",
                "Cough",
                "Fatigue",
                "Bruising",
                "Bleeding",
                "Swelling",
                "Numbness or Tingling",
                "Constipation",
                "Mouth or Throat Sores",
                "Rash",
                "Urinary Issues",
                "Other",
                "None"
            ]

        elif current_state == ConversationState.SYMPTOM_SELECTION_SENT:
            next_state = ConversationState.FOLLOWUP_QUESTIONS
            # Parse symptoms from multi-select response
            symptoms = [s.strip() for s in message.content.split(',') if s.strip()]
            # Filter out "None" if it's selected
            symptoms = [s for s in symptoms if s.lower() != "none"]
            # Normalize any legacy combined option into discrete symptoms
            expanded: List[str] = []
            for s in symptoms:
                if s.lower() in ["bruising / bleeding", "bruising/bleeding", "bruising or bleeding"]:
                    expanded.extend(["Bruising", "Bleeding"])
                else:
                    expanded.append(s)
            symptoms = expanded
            
            # Update the chat's symptom list in the database
            if symptoms:
                chat.symptom_list = list(set((chat.symptom_list or []) + symptoms))
                print(f"Updated symptom list in database: {chat.symptom_list}")
                self.db.commit()
            
            context = {"patient_state": {"current_symptoms": chat.symptom_list}}
            response_content = self._query_knowledge_base_with_rag(chat, context)

        elif current_state == ConversationState.FOLLOWUP_QUESTIONS:
            chat_history = self.db.query(MessageModel).filter(MessageModel.chat_uuid == chat.uuid).order_by(MessageModel.id.desc()).limit(20).all()
            context = {
                "patient_state": {"current_symptoms": chat.symptom_list},
                "latest_input": message.content,
                "history": [Message.from_orm(m).model_dump(mode='json') for m in reversed(chat_history)]
            }
            
            llm_response = self._query_knowledge_base_with_rag(chat, context)

            if "DONE" in llm_response:
                response_content = "DONE"
            else:
                # Check if the LLM is asking the user to add more symptoms
                if "anything else you would like to discuss" in llm_response.lower():
                    response_type = "button_prompt"
                    response_options = ["Yes", "No"]
                
                response_content = llm_response

            next_state = ConversationState.FOLLOWUP_QUESTIONS
        
        assistant_response = WebSocketMessageOut(
            type="assistant_message",
            message_type=response_type,
            content=response_content,
            options=response_options,
        )
        return next_state, assistant_response

    def _query_knowledge_base_with_rag(self, chat: ChatModel, context: Dict[str, Any]) -> str:
        """
        Query the LLM using ONLY the model instructions file as the system prompt.
        All other RAG/context sources are disabled.
        """
        print(f"MODEL_INSTRUCTIONS_ONLY: Querying {LLM_PROVIDER.upper()} with model_instructions.txt...")

        # 1) Load ONLY the model instructions file
        model_inputs_path = "/app/model_inputs"
        if not os.path.exists(model_inputs_path):
            model_inputs_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'model_inputs'))
        instructions_path = os.path.join(model_inputs_path, 'model_instructions.txt')
        try:
            with open(instructions_path, 'r') as f:
                system_prompt = f.read()
            print(f"Loaded model_instructions.txt (chars={len(system_prompt)})")
        except Exception as e:
            print(f"ERROR: Failed to load model_instructions.txt from {instructions_path}: {e}")
            system_prompt = "You are a helpful assistant. Respond in JSON."

        # 2) Construct the user prompt for the LLM (conversation state/history only)
        user_prompt_parts = [
            "### Conversation Context ###",
            f"Current Symptoms: {context.get('patient_state', {}).get('current_symptoms', [])}",
            f"Chat History (most recent messages): {json.dumps(context.get('history', []), indent=2)}",
            f"\n### User's Latest Message ###",
            f"User: \"{context.get('latest_input', '')}\"",
            "\n### Instructions ###",
            "Follow the conversation workflow defined in your system instructions. Remember to respond with valid JSON only.",
            "IMPORTANT: If you detect new symptoms in the user's message, include them in the 'new_symptoms' field of your JSON response.",
            "IMPORTANT: If any alerts/triggers are hit this turn, include descriptive strings in the 'new_alerts' array of your JSON response.",
            "IMPORTANT: Unless response_type is 'summary' or 'end', your 'content' must ask a question (not a standalone statement)."
        ]
        user_prompt = "\n".join(user_prompt_parts)

        # 3) Call the LLM provider
        llm_provider = get_llm_provider()
        response_generator = llm_provider.query(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )

        # 4) Consume the streaming generator to get a single string response
        full_response = "".join([chunk for chunk in response_generator])

        print(f"MODEL_INSTRUCTIONS_ONLY: Received response from {LLM_PROVIDER.upper()}: '{full_response[:100]}...'")
        return full_response if full_response else "I'm not sure what to ask next. Can you tell me more?"

    def _extract_json_from_response(self, text: str) -> Dict[str, Any]:
        """
        Extracts JSON from the LLM response, handling various formats.
        """
        print(f"🔍 [JSON] Extracting JSON from response...")
        print(f"🔍 [JSON] Response text length: {len(text)}")
        print(f"🔍 [JSON] Response text preview: {text[:300]}...")
        
        try:
            # Try to find JSON in the response
            start_idx = text.find('{')
            end_idx = text.rfind('}')
            
            print(f"🔍 [JSON] Found JSON markers: start_idx={start_idx}, end_idx={end_idx}")
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = text[start_idx:end_idx + 1]
                print(f"🔍 [JSON] Extracted JSON string: {json_str}")
                
                parsed_json = json.loads(json_str)
                print(f"✅ [JSON] Successfully parsed JSON with keys: {list(parsed_json.keys())}")
                return parsed_json
            else:
                print(f"❌ [JSON] Could not find JSON markers in response")
                print(f"❌ [JSON] Full response text: {text}")
                return {}
        except json.JSONDecodeError as e:
            print(f"❌ [JSON] JSON decode error: {e}")
            print(f"❌ [JSON] Response text: {text}")
            return {}
        except Exception as e:
            print(f"❌ [JSON] Unexpected error during JSON extraction: {e}")
            print(f"❌ [JSON] Response text: {text}")
            return {}

    async def process_message_stream(self, chat_uuid: UUID, message: WebSocketMessageIn) -> AsyncGenerator[Any, None]:
        """
        Processes a message and streams the response back to the client.
        """
        print(f"🔍 Processing message for chat {chat_uuid}: {message.content}")
        chat = self.db.query(ChatModel).filter(ChatModel.uuid == chat_uuid).first()
        if not chat: 
            print(f"Chat {chat_uuid} not found")
            return

        # 1. Save and yield the user's message
        user_msg = MessageModel(chat_uuid=chat_uuid, sender="user", message_type=message.message_type, content=message.content)
        self.db.add(user_msg)
        self.db.commit()
        self.db.refresh(user_msg)
        yield Message.from_orm(user_msg)

        # 2. If we are in an early deterministic state, use the state machine
        # Only CHEMO_CHECK_SENT is deterministic. SYMPTOM_SELECTION_SENT should fall through to LLM after updating symptoms.
        if chat.conversation_state in [
            ConversationState.CHEMO_CHECK_SENT,
        ]:
            try:
                next_state, assistant_response = self._determine_next_state_and_response(chat, message)
            except Exception as e:
                # Fail safe: do not drop the socket; provide a simple fallback response
                print(f"State machine error: {e}")
                next_state = ConversationState.FOLLOWUP_QUESTIONS
                assistant_response = WebSocketMessageOut(
                    type="assistant_message",
                    message_type="button_prompt",
                    content="I understand. Would you like to discuss any other health-related concerns?",
                    options=["Yes", "No"],
                )
            # Persist next state
            chat.conversation_state = next_state
            self.db.commit()

            # Normalize and save assistant message
            db_message_type = assistant_response.message_type.replace('-', '_')
            assistant_msg = MessageModel(
                chat_uuid=chat_uuid,
                sender="assistant",
                message_type=db_message_type,
                content=assistant_response.content,
                structured_data={"options": assistant_response.options} if getattr(assistant_response, 'options', None) else None,
            )
            self.db.add(assistant_msg)
            self.db.commit()
            self.db.refresh(assistant_msg)

            # Yield with frontend message type preserved
            frontend_message = Message.from_orm(assistant_msg)
            frontend_message.message_type = assistant_response.message_type
            yield frontend_message
            return

        # 2b. If we are expecting symptom selection, update the symptom list and advance state, then continue to LLM
        if chat.conversation_state == ConversationState.SYMPTOM_SELECTION_SENT and message.message_type == 'multi_select_response':
            # Parse selections (comma separated string)
            selections = [s.strip() for s in (message.content or '').split(',') if s.strip()]
            selections = [s for s in selections if s.lower() != 'none']
            if selections:
                chat.symptom_list = list(set((chat.symptom_list or []) + selections))
                print(f"[SYMPTOMS] Updated symptom_list after multi-select: {chat.symptom_list}")
            # Advance state to follow-up
            chat.conversation_state = ConversationState.FOLLOWUP_QUESTIONS
            self.db.commit()

        # 3. Get the full conversation history to send to the LLM
        chat_history = self.db.query(MessageModel).filter(MessageModel.chat_uuid == chat.uuid).order_by(MessageModel.id.asc()).all()
        history_for_llm = [Message.from_orm(m).model_dump(mode='json') for m in chat_history]
        # Debug: print history size and preview last few messages
        try:
            print(f"[HISTORY] messages_in_history={len(history_for_llm)}")
        except Exception:
            pass

        context = {
            "patient_state": {"current_symptoms": chat.symptom_list},
            "latest_input": message.content,
            "history": history_for_llm
        }

        print(f"📝 [CONTEXT] Context prepared for LLM:")
        print(f"📝 [CONTEXT] patient_state.current_symptoms: {context.get('patient_state')}")
        print(f"📝 [CONTEXT] latest_input: {context.get('latest_input')}")
        print(f"📝 [CONTEXT] history length: {len(history_for_llm)}")
        print(f"📝 [CONTEXT] history preview: {[m.get('content', '')[:50] + '...' for m in history_for_llm[:3]]}")

        print(f"📝 [CONTEXT] Context prepared: patient_state={context.get('patient_state')} history_len={len(history_for_llm)}")

        # 4. Get LLM response (non-streaming)
        try:
            print("🤖 Starting LLM processing...")
            llm_response_text = self._query_knowledge_base_with_rag(chat, context)
            print(f"📄 Full LLM response: {llm_response_text}")
        except Exception as e:
            print(f"❌ LLM processing error: {e}")
            # Yield a fallback error message
            yield Message(
                id=-1,
                chat_uuid=chat_uuid,
                sender="assistant",
                message_type="text",
                content="I'm sorry, I encountered an error processing your message. Please try again.",
                created_at=datetime.utcnow()
            )
            return
            
        # 5. Parse the complete JSON response
        print(f"🔍 [LLM] Parsing LLM response for JSON...")
        print(f"🔍 [LLM] Raw LLM response length: {len(llm_response_text)}")
        print(f"🔍 [LLM] Raw LLM response preview: {llm_response_text[:200]}...")
        
        llm_json = self._extract_json_from_response(llm_response_text)

        if not llm_json:
            print(f"❌ [LLM] ERROR: Could not parse JSON from LLM response: {llm_response_text}")
            # Yield a fallback error message
            yield Message(
                id=-1,
                chat_uuid=chat_uuid,
                sender="assistant",
                message_type="text",
                content="I'm sorry, I encountered an error. Please try again.",
                created_at=datetime.utcnow()
            )
            return
        
        print(f"✅ [LLM] Successfully parsed JSON response")
        print(f"✅ [LLM] JSON response keys: {list(llm_json.keys())}")
        print(f"✅ [LLM] response_type: {llm_json.get('response_type')}")
        print(f"✅ [LLM] Has summary_data: {'summary_data' in llm_json}")
        
        if 'summary_data' in llm_json:
            summary_data = llm_json.get('summary_data', {})
            print(f"📊 [LLM] summary_data keys: {list(summary_data.keys()) if summary_data else 'None'}")
            print(f"📊 [LLM] summary_data content: {summary_data}")
            
        # 6. Process the structured response
        response_type = llm_json.get("response_type", "text")
        content = llm_json.get("content", "I'm not sure how to respond.")
        options = llm_json.get("options")
        new_symptoms_from_model = llm_json.get("new_symptoms", [])
        new_alerts_from_model = llm_json.get("new_alerts", [])
        
        print(f"🎯 [RESPONSE] Processing response_type: {response_type}")
        print(f"🎯 [RESPONSE] Current chat.conversation_state: {chat.conversation_state}")
        print(f"🎯 [RESPONSE] Will trigger summary/end processing: {response_type in ['summary', 'end']}")

        # Check for new symptoms returned by the model and update the symptom list
        if new_symptoms_from_model:
            print(f"🆕 [SYMPTOMS] New symptoms detected by model: {new_symptoms_from_model}")
            print(f"🆕 [SYMPTOMS] Current chat.symptom_list: {chat.symptom_list}")
            
            # Add new symptoms to the chat's symptom list
            chat.symptom_list = list(set((chat.symptom_list or []) + new_symptoms_from_model))
            
            print(f"🆕 [SYMPTOMS] Updated symptom list: {chat.symptom_list}")
            print(f"🆕 [SYMPTOMS] About to commit symptom update to database...")
            
            self.db.commit()
            print(f"✅ [SYMPTOMS] Successfully committed symptom update to database")
            print(f"✅ [SYMPTOMS] Final chat.symptom_list after commit: {chat.symptom_list}")
        else:
            print(f"ℹ️ [SYMPTOMS] No new symptoms detected by model")

        # Check for new alerts returned by the model and update the chat alerts list
        if new_alerts_from_model:
            try:
                print(f"🚩 [ALERTS] New alerts detected by model: {new_alerts_from_model}")
                current_alerts = chat.alerts or []
                print(f"🚩 [ALERTS] Current chat.alerts: {current_alerts}")
                # Merge uniquely while preserving order preference for new alerts last
                merged = list(dict.fromkeys((current_alerts or []) + new_alerts_from_model))
                chat.alerts = merged
                print(f"🚩 [ALERTS] Updated chat.alerts: {chat.alerts}")
                self.db.commit()
                print(f"✅ [ALERTS] Successfully committed alerts update to database")
            except Exception as e:
                print(f"❌ [ALERTS] Failed to update alerts: {e}")
                self.db.rollback()
        else:
            print(f"ℹ️ [ALERTS] No new alerts detected by model")

        # If the user is responding with their feeling, save it to the chat
        if message.message_type == 'feeling_response':
            print(f"😊 [FEELING] Processing feeling response: {message.content}")
            print(f"😊 [FEELING] Current chat.overall_feeling: {chat.overall_feeling}")
            
            chat.overall_feeling = message.content
            
            print(f"😊 [FEELING] Updated chat.overall_feeling: {chat.overall_feeling}")
            print(f"😊 [FEELING] About to commit feeling update to database...")
            
            self.db.commit()
            print(f"✅ [FEELING] Successfully committed feeling update to database")
            print(f"✅ [FEELING] Final chat.overall_feeling after commit: {chat.overall_feeling}")

        # Normalize message type for database storage (convert hyphenated to underscore)
        db_message_type = response_type.replace('-', '_')
        if response_type.lower() in ["summary", "end"]:
            db_message_type = 'text'

        # 7. Save and yield the assistant's message
        # If this is the summary, format the content for the user
        if response_type.lower() == "summary":
            print(f"📝 [SUMMARY] Processing summary response_type...")
            summary_data = llm_json.get("summary_data", {})
            bulleted_summary = summary_data.get("bulleted_summary", "No summary available.")
            
            print(f"📝 [SUMMARY] Extracted bulleted_summary: {bulleted_summary}")
            print(f"📝 [SUMMARY] bulleted_summary type: {type(bulleted_summary)}")
            
            # Format the bulleted summary with proper bullet points, removing any pre-existing bullets/dashes/numbers
            if bulleted_summary and bulleted_summary != "No summary available.":
                # Handle both string and list formats
                if isinstance(bulleted_summary, list):
                    bullet_lines = bulleted_summary
                    print(f"📝 [SUMMARY] bulleted_summary is already a list with {len(bullet_lines)} items")
                else:
                    bullet_lines = bulleted_summary.split('\n')
                    print(f"📝 [SUMMARY] Split bulleted_summary string into {len(bullet_lines)} lines")

                def normalize_line(raw_line):
                    text = str(raw_line or '').strip()
                    if not text:
                        return ''
                    # Remove common bullet characters, dashes, and numbering at the start
                    # Bullets: • ‣ ◦ – — -
                    prefixes = ["•", "‣", "◦", "–", "—", "-"]
                    for p in prefixes:
                        if text.startswith(p):
                            text = text[len(p):].lstrip()
                    # Remove numbered list like `1. ` or `2) `
                    i = 0
                    while i < len(text) and text[i].isdigit():
                        i += 1
                    if i > 0 and i < len(text) and text[i] in ".)":
                        text = text[i+1:].lstrip()
                    return text

                formatted_bullets = []
                for line in bullet_lines:
                    normalized = normalize_line(line)
                    if normalized:
                        formatted_bullets.append(f"• {normalized}")

                bullet_text = '<br>'.join(formatted_bullets) if formatted_bullets else "• No summary available."
                print(f"📝 [SUMMARY] Formatted bullet_text: {bullet_text}")
            else:
                bullet_text = "• No summary available."
                print(f"📝 [SUMMARY] Using default bullet_text: {bullet_text}")
            
            content = f"<b>Thank you for completing this chat!</b><br><br>Here is your conversation summary:<br><br>{bullet_text}"
            # Append abnormal alerts notice if any alerts were recorded this conversation
            try:
                if chat.alerts and len(chat.alerts) > 0:
                    content = content + "<br><br>We noticed a few symptoms that may be considered abnormal. Please contact your care team if you believe something is urgent."
                    print(f"🚩 [SUMMARY] Appended abnormal alerts notice. alerts_count={len(chat.alerts)}")
            except Exception:
                # Be resilient if alerts is unexpectedly not iterable
                pass
            print(f"📝 [SUMMARY] Final formatted content: {content}")

        assistant_msg = MessageModel(
            chat_uuid=chat_uuid,
            sender="assistant",
            message_type=db_message_type,
            content=content,
            structured_data={"options": options} if options else None
        )
        self.db.add(assistant_msg)
        self.db.commit()
        self.db.refresh(assistant_msg)
        
        # Create the frontend message with the original response type
        frontend_message = Message.from_orm(assistant_msg)
        frontend_message.message_type = response_type if response_type != 'summary' else 'text'
        
        yield frontend_message

        # 8. If the conversation is done, update the chat with the summary and mark as completed
        if response_type.lower() in ["summary", "end"]:
            print(f"🎯 [SUMMARY] Processing {response_type} response for chat {chat_uuid}")
            summary_data = llm_json.get("summary_data", {})
            
            print(f"📊 [SUMMARY] Raw summary_data from LLM: {summary_data}")
            print(f"📊 [SUMMARY] summary_data keys: {list(summary_data.keys()) if summary_data else 'None'}")
            
            # Log each field before updating
            print(f"🏥 [SUMMARY] Current chat.symptom_list: {chat.symptom_list}")
            print(f"🏥 [SUMMARY] Current chat.severity_list: {chat.severity_list}")
            print(f"🏥 [SUMMARY] Current chat.medication_list: {chat.medication_list}")
            print(f"🏥 [SUMMARY] Current chat.longer_summary: {chat.longer_summary}")
            print(f"🏥 [SUMMARY] Current chat.bulleted_summary: {chat.bulleted_summary}")
            print(f"🏥 [SUMMARY] Current chat.overall_feeling: {chat.overall_feeling}")
            
            # Extract and log each field from summary_data
            new_symptom_list = summary_data.get("symptom_list", chat.symptom_list)
            new_severity_list = summary_data.get("severity_list", chat.severity_list)
            new_longer_summary = summary_data.get("longer_summary", chat.longer_summary)
            new_medication_list = summary_data.get("medication_list", chat.medication_list)
            new_bulleted_summary = summary_data.get("bulleted_summary", chat.bulleted_summary)
            new_overall_feeling = summary_data.get("overall_feeling", chat.overall_feeling)
            
            print(f"🆕 [SUMMARY] New symptom_list: {new_symptom_list}")
            print(f"🆕 [SUMMARY] New severity_list: {new_severity_list}")
            print(f"🆕 [SUMMARY] New medication_list: {new_medication_list}")
            print(f"🆕 [SUMMARY] New longer_summary: {new_longer_summary}")
            print(f"🆕 [SUMMARY] New bulleted_summary: {new_bulleted_summary}")
            print(f"🆕 [SUMMARY] New overall_feeling: {new_overall_feeling}")
            
            # Update the chat with new data
            chat.symptom_list = new_symptom_list
            chat.severity_list = new_severity_list
            chat.longer_summary = new_longer_summary
            chat.medication_list = new_medication_list
            chat.bulleted_summary = new_bulleted_summary
            chat.overall_feeling = new_overall_feeling

            print(f"💾 [SUMMARY] About to commit to database...")
            print(f"💾 [SUMMARY] Final chat.symptom_list: {chat.symptom_list}")
            print(f"💾 [SUMMARY] Final chat.severity_list: {chat.severity_list}")
            print(f"💾 [SUMMARY] Final chat.medication_list: {chat.medication_list}")
            print(f"💾 [SUMMARY] Final chat.longer_summary: {chat.longer_summary}")
            print(f"💾 [SUMMARY] Final chat.bulleted_summary: {chat.bulleted_summary}")
            print(f"💾 [SUMMARY] Final chat.overall_feeling: {chat.overall_feeling}")

            if response_type == "summary":
                chat.conversation_state = ConversationState.COMPLETED
                print(f"✅ [SUMMARY] Marked chat as COMPLETED")
            elif response_type == "end":
                chat.conversation_state = ConversationState.EMERGENCY
                print(f"🚨 [SUMMARY] Marked chat as EMERGENCY")

            try:
                self.db.commit()
                print(f"💾 [SUMMARY] Successfully committed summary data to database for chat {chat_uuid}")
                
                # Verify the data was actually saved by refreshing from DB
                self.db.refresh(chat)
                print(f"🔍 [SUMMARY] After DB refresh - chat.severity_list: {chat.severity_list}")
                print(f"🔍 [SUMMARY] After DB refresh - chat.medication_list: {chat.medication_list}")
                print(f"🔍 [SUMMARY] After DB refresh - chat.symptom_list: {chat.symptom_list}")
                
            except Exception as e:
                print(f"❌ [SUMMARY] Failed to commit summary data to database: {e}")
                self.db.rollback()
                raise

    def get_connection_ack(self, chat_uuid: UUID) -> ConnectionEstablished:
        """Returns a connection acknowledgment message."""
        return ConnectionEstablished(
            content="Connection established successfully.",
            chat_state={
                "chat_uuid": str(chat_uuid),
                "status": "connected"
            }
        )

    def get_or_create_today_session(self, patient_uuid: UUID, user_timezone: str = "America/Los_Angeles") -> Tuple[ChatModel, List[MessageModel], bool]:
        """
        Gets the most recent chat for today, or creates a new one if none exists.
        Uses user's timezone to determine what "today" means.
        """
        print(f"🔍 [SESSION] Looking for today's chat for patient {patient_uuid} in timezone {user_timezone}")
        
        # Get today's date in user's timezone
        user_tz = pytz.timezone(user_timezone)
        user_now = datetime.now(user_tz)
        today_start = datetime.combine(user_now.date(), time.min)
        today_end = datetime.combine(user_now.date(), time.max)
        
        # Convert to UTC for database query
        utc_today_start = user_tz.localize(today_start).astimezone(pytz.UTC)
        utc_today_end = user_tz.localize(today_end).astimezone(pytz.UTC)
        
        print(f"🔍 [SESSION] Querying for chats between {utc_today_start} and {utc_today_end}")
        
        # Query for today's chat in user's timezone
        today_chat = self.db.query(ChatModel).filter(
            ChatModel.patient_uuid == patient_uuid,
            ChatModel.created_at >= utc_today_start,
            ChatModel.created_at <= utc_today_end
        ).order_by(ChatModel.created_at.desc()).first()
        
        if today_chat:
            print(f"✅ [SESSION] Found existing chat {today_chat.uuid} for today")
            print(f"✅ [SESSION] Chat state: {today_chat.conversation_state}")
            print(f"✅ [SESSION] Chat symptom_list: {today_chat.symptom_list}")
            print(f"✅ [SESSION] Chat severity_list: {today_chat.severity_list}")
            print(f"✅ [SESSION] Chat medication_list: {today_chat.medication_list}")
            print(f"✅ [SESSION] Chat longer_summary: {today_chat.longer_summary}")
            print(f"✅ [SESSION] Chat bulleted_summary: {today_chat.bulleted_summary}")
            print(f"✅ [SESSION] Chat overall_feeling: {today_chat.overall_feeling}")
            
            messages = self.db.query(MessageModel).filter(
                MessageModel.chat_uuid == today_chat.uuid
            ).order_by(MessageModel.created_at).all()
            
            print(f"✅ [SESSION] Found {len(messages)} messages in existing chat")
            return today_chat, messages, False
        else:
            print(f"🆕 [SESSION] No existing chat found, creating new one...")
            # Create new chat for today
            new_chat, initial_question = self.create_chat(patient_uuid, commit=True)  # Commit the chat first
            
            print(f"🆕 [SESSION] Created new chat {new_chat.uuid}")
            print(f"🆕 [SESSION] New chat state: {new_chat.conversation_state}")
            print(f"🆕 [SESSION] New chat symptom_list: {new_chat.symptom_list}")
            print(f"🆕 [SESSION] New chat severity_list: {new_chat.severity_list}")
            print(f"🆕 [SESSION] New chat medication_list: {new_chat.medication_list}")
            
            # Create the first assistant message
            first_message = MessageModel(
                chat_uuid=new_chat.uuid,
                sender="assistant",
                message_type=initial_question["type"],
                content=initial_question["text"],
                structured_data={"options": initial_question["options"]} if initial_question.get("options") else None
            )
            
            print(f"🆕 [SESSION] Creating first assistant message: {first_message.content}")
            
            # Add the message to the database
            self.db.add(first_message)
            self.db.commit()
            self.db.refresh(first_message)
            
            print(f"✅ [SESSION] Successfully created new chat session with {len([first_message])} messages")
            return new_chat, [first_message], True
