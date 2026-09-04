"""
Gemini provider — used for the final demo. Swapping to this from
OpenRouter requires ONLY an env var change (LLM_PROVIDER=gemini),
never a code change in any agent/node.
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings


def build_gemini_llm(model: str | None = None, **kwargs):
    model_name = model or settings.llm_model
    if not model_name or "gpt" in model_name.lower() or "openai" in model_name.lower():
        model_name = "gemini-2.5-flash"
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=settings.gemini_api_key,
        **kwargs,
    )

