"""
Confirms the get_llm() abstraction actually works: the same prompt run
through both providers should return a coherent (non-empty) response
with zero code changes, only a provider argument swap. Run before the
demo to confirm the OpenRouter -> Gemini switch is safe.
"""
import pytest
from app.llm.get_llm import get_llm


@pytest.mark.asyncio
async def test_openrouter_provider_responds():
    llm = get_llm(provider="openrouter", temperature=0)
    response = await llm.ainvoke("Say hello in one short sentence.")
    assert response.content


@pytest.mark.asyncio
async def test_gemini_provider_responds():
    llm = get_llm(provider="gemini", temperature=0)
    response = await llm.ainvoke("Say hello in one short sentence.")
    assert response.content
