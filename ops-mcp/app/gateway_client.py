import httpx
import os
import time

DEMO_GATEWAY_URL = os.environ.get("DEMO_GATEWAY_URL", "http://demo-gateway:8080")
DEMO_ADMIN_TOKEN = os.environ.get("DEMO_ADMIN_TOKEN", "replace-me")


async def get_config() -> dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(
            f"{DEMO_GATEWAY_URL}/internal/config",
            headers={"X-Demo-Admin-Token": DEMO_ADMIN_TOKEN},
        )
        return resp.json()


async def set_upstream(url: str, source: str = "mcp-apply-gateway-fix") -> dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.post(
            f"{DEMO_GATEWAY_URL}/internal/config/upstream",
            json={"backend_url": url, "source": source},
            headers={"X-Demo-Admin-Token": DEMO_ADMIN_TOKEN},
        )
        return resp.json()


async def get_logs() -> dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(
            f"{DEMO_GATEWAY_URL}/internal/logs",
            headers={"X-Demo-Admin-Token": DEMO_ADMIN_TOKEN},
        )
        return resp.json()


async def get_changes() -> dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(
            f"{DEMO_GATEWAY_URL}/internal/changes",
            headers={"X-Demo-Admin-Token": DEMO_ADMIN_TOKEN},
        )
        return resp.json()


async def reset_gateway() -> dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.post(
            f"{DEMO_GATEWAY_URL}/internal/reset",
            headers={"X-Demo-Admin-Token": DEMO_ADMIN_TOKEN},
        )
        return resp.json()


async def inject_fault() -> dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.post(
            f"{DEMO_GATEWAY_URL}/internal/inject-fault",
            headers={"X-Demo-Admin-Token": DEMO_ADMIN_TOKEN},
        )
        return resp.json()


async def check_portal_http() -> dict:
    start = time.monotonic()
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(f"{DEMO_GATEWAY_URL}/portal")
            latency_ms = round((time.monotonic() - start) * 1000)
            return {
                "status_code": resp.status_code,
                "healthy": resp.status_code == 200,
                "latency_ms": latency_ms,
                "body": resp.json() if resp.headers.get("content-type", "").startswith("application/json") else None,
            }
        except Exception as e:
            latency_ms = round((time.monotonic() - start) * 1000)
            return {
                "status_code": 0,
                "healthy": False,
                "latency_ms": latency_ms,
                "error": str(e),
            }


async def check_backend_http() -> dict:
    DEMO_BACKEND_URL = os.environ.get("DEMO_BACKEND_URL", "http://demo-backend:8080")
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(f"{DEMO_BACKEND_URL}/api/status")
            body = resp.json() if resp.status_code == 200 else {}
            return {
                "status_code": resp.status_code,
                "healthy": resp.status_code == 200,
                "version": body.get("version", "unknown"),
                "body": body,
            }
        except Exception as e:
            return {
                "status_code": 0,
                "healthy": False,
                "version": "unknown",
                "error": str(e),
            }
