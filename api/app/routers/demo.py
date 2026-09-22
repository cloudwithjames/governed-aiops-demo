import httpx
from fastapi import APIRouter, Header, HTTPException
from ..config import DEMO_GATEWAY_URL, DEMO_BACKEND_URL, DEMO_ADMIN_TOKEN, AIOPS_INTERNAL_TOKEN

router = APIRouter(prefix="/api/demo", tags=["demo"])


async def _get_portal_status() -> int:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{DEMO_GATEWAY_URL}/portal")
            return resp.status_code
    except Exception:
        return 0


async def _get_backend_status() -> int:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{DEMO_BACKEND_URL}/api/status")
            return resp.status_code
    except Exception:
        return 0


async def _get_gateway_config() -> dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(
            f"{DEMO_GATEWAY_URL}/internal/config",
            headers={"X-Demo-Admin-Token": DEMO_ADMIN_TOKEN},
        )
        return resp.json()


@router.get("/status")
async def demo_status():
    portal = await _get_portal_status()
    backend = await _get_backend_status()
    cfg = await _get_gateway_config()
    return {
        "portal_status": portal,
        "backend_status": backend,
        "gateway_upstream": cfg.get("backend_url"),
        "portal_healthy": portal == 200,
        "backend_healthy": backend == 200,
    }


@router.post("/inject")
async def inject_fault():
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(
            f"{DEMO_GATEWAY_URL}/internal/reset",
            headers={"X-Demo-Admin-Token": DEMO_ADMIN_TOKEN},
        )
        resp = await client.post(
            f"{DEMO_GATEWAY_URL}/internal/inject-fault",
            headers={"X-Demo-Admin-Token": DEMO_ADMIN_TOKEN},
        )
        inject_result = resp.json()

    portal = await _get_portal_status()
    backend = await _get_backend_status()
    cfg = await _get_gateway_config()

    return {
        "status": "injected",
        "inject_result": inject_result,
        "portal_status": portal,
        "backend_status": backend,
        "gateway_upstream": cfg.get("backend_url"),
        "portal_healthy": portal == 200,
        "backend_healthy": backend == 200,
    }


@router.post("/reset")
async def reset_demo():
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{DEMO_GATEWAY_URL}/internal/reset",
            headers={"X-Demo-Admin-Token": DEMO_ADMIN_TOKEN},
        )
        reset_result = resp.json()

    portal = await _get_portal_status()
    backend = await _get_backend_status()
    cfg = await _get_gateway_config()

    return {
        "status": "reset",
        "reset_result": reset_result,
        "portal_status": portal,
        "backend_status": backend,
        "gateway_upstream": cfg.get("backend_url"),
        "portal_healthy": portal == 200,
        "backend_healthy": backend == 200,
    }
