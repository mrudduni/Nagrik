"""
Gemini provider with multi-key rotation across GEMINI_KEYS pool.
"""
import itertools
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings

def _get_key_pool() -> list[str]:
    keys = []
    if getattr(settings, "gemini_keys", None):
        keys = [k.strip() for k in settings.gemini_keys.split(",") if k.strip()]
    if not keys and settings.gemini_api_key:
        keys = [settings.gemini_api_key.strip()]
    return keys or [""]

_key_cycle = None

def get_next_gemini_key() -> str:
    global _key_cycle
    pool = _get_key_pool()
    if not pool:
        return ""
    if _key_cycle is None:
        _key_cycle = itertools.cycle(pool)
    return next(_key_cycle)


def build_gemini_llm(model: str | None = None, **kwargs):
    api_key = kwargs.pop("google_api_key", None) or get_next_gemini_key()
    return ChatGoogleGenerativeAI(
        model=model or settings.llm_model,
        google_api_key=api_key,
        **kwargs,
    )
