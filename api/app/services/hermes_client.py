import json
import httpx
from ..config import HERMES_API_URL, HERMES_API_SERVER_KEY, HERMES_MODEL_NAME


async def call_hmes(messages: list[dict], tools: list[dict] | None = None) -> dict:
    payload = {
        "model": HERMES_MODEL_NAME,
        "messages": messages,
        "temperature": 0.1,
    }
    if tools:
        payload["tools"] = tools

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{HERMES_API_URL}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {HERMES_API_SERVER_KEY}"},
        )
        resp.raise_for_status()
        return resp.json()


async def check_hermes_health() -> bool:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(
                f"{HERMES_API_URL}/models",
                headers={"Authorization": f"Bearer {HERMES_API_SERVER_KEY}"},
            )
            return resp.status_code == 200
    except Exception:
        return False
