from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
from dotenv import load_dotenv
import json
import os

from agent import load_schema, get_missing_fields, generate_next_question

load_dotenv()

# Initialize Twilio Client
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

try:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
except Exception:
    twilio_client = None

app = FastAPI(title="Nagrik Voice Form System")

class ChatRequest(BaseModel):
    session_id: str
    text: str

# In-memory state store for active calls
# Format: { "CallSid": { "schema_name": "public_grievance", "data": {}, "history": [] } }
call_states = {}

def save_submission(schema_name: str, data: dict):
    """Save completed form to local JSON."""
    path = os.path.join(os.path.dirname(__file__), "data", "submissions.json")
    try:
        with open(path, "r") as f:
            submissions = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        submissions = []

    submissions.append({
        "schema_name": schema_name,
        "data": data
    })

    with open(path, "w") as f:
        json.dump(submissions, f, indent=2)


WORD_TO_DIGIT = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
}

def normalize_numbers(text: str, field_type: str) -> str:
    """
    For fields typed as 'number', convert spoken words like 'one two three'
    to digit strings like '123'. Also strips spaces from pure digit strings.
    For string fields, return text as-is.
    """
    if field_type != "number":
        return text
    words = text.lower().split()
    result = "".join(WORD_TO_DIGIT.get(w, w) for w in words)
    # Remove any remaining spaces/punctuation so we get a clean digit string
    return "".join(c for c in result if c.isdigit())

@app.get("/", response_class=HTMLResponse)
def read_root():
    try:
        with open(os.path.join(os.path.dirname(__file__), "templates", "index.html"), "r") as f:
            return f.read()
    except FileNotFoundError:
        return "<html><body><h1>Templates folder not found!</h1></body></html>"

@app.post("/api/chat")
async def chat_api(req: ChatRequest):
    """
    Web API for the conversational agent.
    Uses field-by-field tracking: `current_field_index` points to the field
    currently being asked. The user's answer is stored directly to that field.
    If the user says nothing, we re-ask the same field.
    """
    call_sid = req.session_id

    # Initialize state for a new session
    if call_sid not in call_states:
        schema_name = "public_grievance"
        schema = load_schema(schema_name)
        call_states[call_sid] = {
            "schema_name": schema_name,
            "data": {},
            # Points to the field currently being asked (not yet answered)
            "current_field_index": 0,
        }

    state = call_states[call_sid]
    schema = load_schema(state["schema_name"])
    fields = schema.get("fields", [])
    idx = state["current_field_index"]
    user_text = req.text.strip()

    # If the user provided an answer, store it for the CURRENT field and advance
    if user_text and idx < len(fields):
        current_field = fields[idx]
        # Normalize spoken numbers to digits for numeric fields
        answer = normalize_numbers(user_text, current_field.get("type", "string"))
        state["data"][current_field["name"]] = answer
        idx += 1
        state["current_field_index"] = idx
    # If empty speech AND this is not the very first turn, we re-ask the same field
    # (idx stays the same, so we fall through to ask it again)

    # If all fields are filled, we are done
    if idx >= len(fields):
        save_submission(state["schema_name"], state["data"])
        del call_states[call_sid]
        return {
            "response": "Thank you! We have collected all your information. Your grievance has been successfully registered.",
            "is_complete": True,
            "data": state["data"]
        }

    # Ask for the field at the current index
    next_field = fields[idx]
    # If re-asking after empty speech, prepend a gentle retry prompt
    retry_prefix = ""
    if not user_text and idx > 0:
        retry_prefix = "Sorry, I didn't catch that. "
    next_question = retry_prefix + generate_next_question(schema, state["data"], [next_field])
    return {"response": next_question, "is_complete": False}

@app.post("/voice")
async def voice(request: Request):
    """
    Endpoint triggered by Twilio when a call comes in.
    """
    form_data = await request.form()
    call_sid = form_data.get('CallSid', 'test_sid')
    
    # Initialize state for this call. We default to 'public_grievance' for now.
    schema_name = "public_grievance"
    schema = load_schema(schema_name)
    
    call_states[call_sid] = {
        "schema_name": schema_name,
        "data": {},
        "history": []
    }
    
    missing_fields = get_missing_fields(schema, {})
    first_question = generate_next_question(schema, {}, missing_fields)
    
    response = VoiceResponse()
    gather = Gather(input='speech', action='/gather', speechTimeout='auto')
    gather.say(first_question)
    response.append(gather)
    response.say("We didn't receive any input. Goodbye!")
    
    return str(response)

@app.post("/gather")
async def gather_input(request: Request):
    """
    Endpoint triggered by Twilio when speech is recognized.
    """
    form_data = await request.form()
    speech_result = form_data.get('SpeechResult', '')
    call_sid = form_data.get('CallSid', 'test_sid')

    state = call_states.get(call_sid)
    response = VoiceResponse()
    
    if not state:
        response.say("Sorry, your session has expired. Please call again.")
        response.hangup()
        return str(response)
        
    schema = load_schema(state["schema_name"])
    
    # Extract information from what the user just said
    extracted = extract_information(speech_result, schema, state["data"])
    
    # Update the state data
    state["data"].update(extracted)
    
    # Check what is still missing
    missing_fields = get_missing_fields(schema, state["data"])
    
    if not missing_fields:
        # Form is complete
        response.say("Thank you. We have collected all your information. Your grievance has been registered. Goodbye!")
        save_submission(state["schema_name"], state["data"])
        
        # Optional: Send an SMS confirmation if we have a valid phone number from the caller
        caller_phone = form_data.get('From')
        if twilio_client and caller_phone and TWILIO_PHONE_NUMBER:
            try:
                twilio_client.messages.create(
                    body=f"Your {state['schema_name'].replace('_', ' ')} has been successfully submitted.",
                    from_=TWILIO_PHONE_NUMBER,
                    to=caller_phone
                )
            except Exception as e:
                print(f"Failed to send SMS: {e}")
                
        del call_states[call_sid]
    else:
        # Generate the next question
        next_question = generate_next_question(schema, state["data"], missing_fields)
        
        # Ask it
        gather = Gather(input='speech', action='/gather', speechTimeout='auto')
        gather.say(next_question)
        response.append(gather)
        response.say("We didn't receive any input. Goodbye!")
    
    return str(response)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
