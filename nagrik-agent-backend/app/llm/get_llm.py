"""
THE single entry point for obtaining an LLM anywhere in this codebase.

Rule: no file outside app/llm/ may import ChatOpenAI, ChatGoogleGenerativeAI,
or any other provider SDK directly. Every node/tool calls get_llm().

Swapping providers for the demo = change LLM_PROVIDER (and LLM_MODEL if
needed) in .env. Zero code changes required anywhere else.
"""
from functools import lru_cache
from app.config import settings


def _build_openai(model: str | None, temperature: float):
    from app.llm.providers.openai import build_openai_llm
    return build_openai_llm(model=model, temperature=temperature)


def _build_openrouter(model: str | None, temperature: float):
    from app.llm.providers.openrouter import build_openrouter_llm
    return build_openrouter_llm(model=model, temperature=temperature)


def _build_gemini(model: str | None, temperature: float):
    from app.llm.providers.gemini import build_gemini_llm
    return build_gemini_llm(model=model, temperature=temperature)


_BUILDERS = {
    "openai": _build_openai,
    "openrouter": _build_openrouter,
    "gemini": _build_gemini,
}


def _is_valid_key(key: str | None) -> bool:
    if not key or not key.strip():
        return False
    k = key.strip().lower()
    return not (k.startswith("your_") or "placeholder" in k or k == "none")


@lru_cache(maxsize=8)
def get_llm(model: str | None = None, temperature: float = 0.3, provider: str | None = None):
    """
    Returns a LangChain chat-model instance for the configured provider.
    Primary: OpenAI (gpt-4o-mini). Fallback: Gemini (gemini-2.5-flash).
    """
    provider_name = (provider or settings.llm_provider).lower()

    # Provider key-checking & intelligent fallback logic:
    has_openai = _is_valid_key(settings.openai_api_key)
    has_gemini = _is_valid_key(settings.gemini_api_key)
    has_openrouter = _is_valid_key(settings.openrouter_api_key)

    if provider_name == "openai" and not has_openai:
        if has_gemini:
            provider_name = "gemini"
        elif has_openrouter:
            provider_name = "openrouter"
    elif provider_name == "openrouter" and not has_openrouter:
        if has_openai:
            provider_name = "openai"
        elif has_gemini:
            provider_name = "gemini"
    elif provider_name == "gemini" and not has_gemini:
        if has_openai:
            provider_name = "openai"
        elif has_openrouter:
            provider_name = "openrouter"

    if provider_name not in _BUILDERS:
        if has_openai:
            provider_name = "openai"
        elif has_gemini:
            provider_name = "gemini"
        else:
            provider_name = "openrouter"

    builder = _BUILDERS[provider_name]
    return builder(model=model, temperature=temperature)





def get_vision_llm(temperature: float = 0.2):
    """
    Returns a vision-capable model specifically for image/document understanding.
    """
    return get_llm(
        model="openai/gpt-4o-mini",
        temperature=temperature,
        provider="openrouter",
    )