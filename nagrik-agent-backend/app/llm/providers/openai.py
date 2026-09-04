"""
OpenAI provider — configured to default to gpt-4o-mini (least credit usage).
"""
from langchain_openai import ChatOpenAI
from app.config import settings


def build_openai_llm(model: str | None = None, **kwargs):
    model_name = model or settings.llm_model
    if not model_name or "gemini" in model_name.lower():
        model_name = "gpt-4o-mini"
    return ChatOpenAI(
        model=model_name,
        api_key=settings.openai_api_key,
        **kwargs,
    )
