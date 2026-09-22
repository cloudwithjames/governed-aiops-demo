from fastapi import APIRouter
from ..config import AIOPS_AGENT_MODE
from ..services.hermes_client import check_hermes_health

router = APIRouter()


@router.get("/healthz")
async def healthz():
    hermes_ok = True
    if AIOPS_AGENT_MODE == "hermes":
        hermes_ok = await check_hermes_health()
    return {
        "service": "aiops-api",
        "status": "healthy" if hermes_ok else "degraded",
        "mode": AIOPS_AGENT_MODE,
        "hermes_reachable": hermes_ok,
    }
