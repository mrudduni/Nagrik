"""
Gemini provider — used for the final demo. Swapping to this from
OpenRouter requires ONLY an env var change (LLM_PROVIDER=gemini),
never a code change in any agent/node.
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings


def build_gemini_llm(model: str | None = None, **kwargs):
    return ChatGoogleGenerativeAI(
        model=model or settings.llm_model,
        google_api_key=settings.gemini_api_key,
        **kwargs,
    )
