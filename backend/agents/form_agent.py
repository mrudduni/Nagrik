import google.generativeai as genai
import json
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from backend.core.config import settings
from backend.services.state_manager import StateManager
from backend.db.models import ConversationLog

# Configure Gemini once
if settings.gemini_api_key:
    genai.configure(api_key=settings.gemini_api_key)

class FormAgent:
    def __init__(self, db: Session, session_id: str):
        self.db = db
        self.session_id = session_id
        self.state_manager = StateManager(db, session_id)
        
        # Load conversation history from DB to populate the Gemini ChatSession
        self.history = self.db.query(ConversationLog).filter(
            ConversationLog.session_id == session_id
        ).order_by(ConversationLog.timestamp.asc()).all()

    def process_message(self, user_text: str) -> str:
        schema = self.state_manager.schema_parser.schema
        state_data = self.state_manager.session.state_data
        missing_fields = self.state_manager.get_missing_fields()
        
        # Identify unconfirmed fields
        unconfirmed = [k for k, v in state_data.items() if v.get("status") == "UNCONFIRMED"]

        system_prompt = f"""You are 'Nagrik', a polite conversational AI assistant helping an Indian citizen fill out a government form over a voice call.
Form Name: {schema.get('name')}
Description: {schema.get('description')}

YOUR CAPABILITIES:
1. Extract information from the user's speech and use the `update_form_field` tool.
2. If a field requires confirmation, ask the user to confirm it explicitly. Use `confirm_field` tool when they say yes.
3. Answer questions about the form fields (e.g. "What is an Aadhaar?").
4. If the user corrects themselves, use `update_form_field` to overwrite the value.

CURRENT FORM STATE:
Currently extracted data: {json.dumps(state_data, indent=2)}

WHAT IS MISSING:
Missing fields that still need to be asked: 
{json.dumps([{ 'id': f.get('id', f.get('name')), 'label': f.get('label'), 'type': f.get('type'), 'options': f.get('options') } for f in missing_fields], indent=2)}

UNCONFIRMED FIELDS:
These fields have been recorded but MUST be explicitly confirmed with the user (e.g. "Is your date of birth 1990-01-01?"):
{json.dumps(unconfirmed)}

INSTRUCTIONS:
- You must always converse naturally. Do NOT output JSON directly to the user.
- If there are UNCONFIRMED fields, prioritize asking the user to confirm them first.
- If there are no unconfirmed fields, ask a natural question to gather one of the MISSING fields.
- If the user provides data, CALL THE TOOL, and then immediately ask the next question in the same turn.
- Be concise. Voice responses should be short.
"""

        # Tool definitions
        def update_form_field(field_id: str, value: str):
            """
            Updates a field in the government form with the extracted value.
            Args:
                field_id: The ID of the field to update.
                value: The value to set (use YYYY-MM-DD for dates).
            """
            ok, msg = self.state_manager.update_field(field_id, value)
            return f"Result: {'Success' if ok else 'Error'} - {msg}"
            
        def confirm_field(field_id: str):
            """
            Confirms a field that was previously in the UNCONFIRMED state.
            Args:
                field_id: The ID of the field to confirm.
            """
            ok, msg = self.state_manager.confirm_field(field_id)
            return f"Result: {'Success' if ok else 'Error'} - {msg}"

        if not settings.gemini_api_key:
            return "Error: Gemini API key is not configured in .env"

        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            tools=[update_form_field, confirm_field],
            system_instruction=system_prompt
        )

        # Convert DB history to Gemini history format (simplified for now)
        # To use automatic_function_calling with history is complex because we need to rebuild FunctionCall parts.
        # For this implementation, we will rely heavily on the system prompt containing the CURRENT STATE,
        # which eliminates the strict need for full conversational history just to extract fields.
        
        chat = model.start_chat(enable_automatic_function_calling=True)
        
        # Send the user message
        response = chat.send_message(user_text)
        
        # Save to DB
        self._save_log("user", user_text)
        self._save_log("agent", response.text)
        
        return response.text

    def _save_log(self, role: str, content: str):
        log = ConversationLog(session_id=self.session_id, role=role, content=content)
        self.db.add(log)
        self.db.commit()
