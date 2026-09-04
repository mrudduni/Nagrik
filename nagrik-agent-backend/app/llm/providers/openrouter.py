"""
OpenRouter provider — used mainly during development because it gives
access to many models behind one API key. Talks an OpenAI-compatible API,
so we reuse langchain_openai's ChatOpenAI with a custom base_url.
"""
from langchain_openai import ChatOpenAI
from app.config import settings


def build_openrouter_llm(model: str | None = None, **kwargs):
    return ChatOpenAI(
        model=model or settings.llm_model,
        api_key=settings.openrouter_api_key,
        base_url="https://openrouter.ai/api/v1",
        **kwargs,
    )
