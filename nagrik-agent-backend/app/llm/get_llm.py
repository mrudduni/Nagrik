"""
THE single entry point for obtaining an LLM anywhere in this codebase.

Rule: no file outside app/llm/ may import ChatOpenAI, ChatGoogleGenerativeAI,
or any other provider SDK directly. Every node/tool calls get_llm().

Swapping providers for the demo = change LLM_PROVIDER (and LLM_MODEL if
needed) in .env. Zero code changes required anywhere else.
"""
from functools import lru_cache
from app.config import settings


def _build_openrouter(model: str | None, temperature: float):
    from app.llm.providers.openrouter import build_openrouter_llm

    return build_openrouter_llm(model=model, temperature=temperature)


def _build_gemini(model: str | None, temperature: float):
    from app.llm.providers.gemini import build_gemini_llm

    return build_gemini_llm(model=model, temperature=temperature)


_BUILDERS = {
    "openrouter": _build_openrouter,
    "gemini": _build_gemini,
}


@lru_cache(maxsize=8)
def get_llm(model: str | None = None, temperature: float = 0.3, provider: str | None = None):
    """
    Returns a LangChain chat-model instance for the configured provider.

    Args:
        model: override the default model from settings (rarely needed).
        temperature: sampling temperature.
        provider: override the configured provider (used by tests that need
                  to run the same prompt against both providers, e.g.
                  test_provider_swap.py).
    """
    provider_name = provider or settings.llm_provider
    if provider_name not in _BUILDERS:
        raise ValueError(
            f"Unknown LLM_PROVIDER '{provider_name}'. "
            f"Supported: {list(_BUILDERS.keys())}"
        )
    builder = _BUILDERS[provider_name]
    return builder(model=model, temperature=temperature)


def get_vision_llm(temperature: float = 0.2):
    """
    Returns a vision-capable chat model for the doc/image understanding node.
    Both OpenRouter (many routed models support vision) and Gemini support
    multimodal input natively, so this reuses the same provider config.
    """
    return get_llm(temperature=temperature)
