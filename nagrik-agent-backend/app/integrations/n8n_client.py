"""
n8n webhook trigger — side effects ONLY (e.g. notify citizen after
submission). Never used for decision-making; the graph has already
decided everything by the time this is called.
"""
import httpx
from app.config import settings


async def trigger_n8n_workflow(workflow_name: str, payload: dict) -> None:
    url = f"{settings.n8n_webhook_base}/{workflow_name}"
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(url, json=payload)
    except httpx.HTTPError:
        # Side-effect failures should never break the main conversation flow.
        pass
