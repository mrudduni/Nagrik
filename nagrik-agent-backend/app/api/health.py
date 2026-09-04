from fastapi import APIRouter
from app.config import settings

router = APIRouter()


@router.get("/health")
async def health():
    from app.graph.nodes.responder import ALL_TOOLS
    return {
        "status": "ok",
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "mock_backends": settings.use_mock_backends,
        "registered_tools": [t.name for t in ALL_TOOLS],
        "rag_top_k": settings.rag_top_k,
        "checkpointer": settings.checkpointer_backend,
    }
