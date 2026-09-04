import json
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Initialize Gemini client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
else:
    model = None
    print("WARNING: GEMINI_API_KEY not set. Using static fallback questions.")


def load_schema(schema_name: str) -> dict:
    """Load a JSON schema from the schemas directory."""
    path = os.path.join(os.path.dirname(__file__), "schemas", f"{schema_name}.json")
    with open(path, 'r') as f:
        return json.load(f)


def get_missing_fields(schema: dict, current_data: dict) -> list:
    """Return a list of fields from the schema that are not yet in current_data."""
    missing = []
    for field in schema.get("fields", []):
        if field["name"] not in current_data or current_data[field["name"]] is None:
            missing.append(field)
    return missing


def generate_next_question(schema: dict, current_data: dict, missing_fields: list) -> str:
    """
    Use Gemini to generate a natural, conversational question for the next missing field.
    Falls back to a static question if the model is not available.
    """
    if not missing_fields:
        return "Thank you. We have collected all the necessary information. Your form is complete."

    next_field = missing_fields[0]

    # Static fallback (no API key needed)
    static_questions = {
        "complainant_name": "Could you please tell me your full name?",
        "aadhaar_number": "Could you please provide your 12-digit Aadhaar number?",
        "ministry_or_department": "Which government ministry or department is your grievance related to? For example, Railways, Health, or Municipal Corporation.",
        "grievance_description": "Please describe your grievance in detail.",
        "pincode": "What is your 6-digit PIN code?",
    }

    if not model:
        return static_questions.get(
            next_field["name"],
            f"Please provide your {next_field['name'].replace('_', ' ')}."
        )

    prompt = f"""You are a polite government assistant helping a citizen of India fill out a '{schema["name"]}' form over voice call.
Already collected: {json.dumps(current_data) if current_data else "Nothing yet."}
Next field needed: "{next_field['name']}" — {next_field['description']}

Generate a single, short, natural spoken question in English to ask for this field. 
Be concise and conversational. Do NOT repeat what you already have. Only output the question itself, no extra text."""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini question generation error: {e}")
        return static_questions.get(
            next_field["name"],
            f"Please provide your {next_field['name'].replace('_', ' ')}."
        )
