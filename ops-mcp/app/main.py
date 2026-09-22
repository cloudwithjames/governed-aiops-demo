import os
import json
import logging
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any
import uvicorn

from .config import AIOPS_INTERNAL_TOKEN
from . import tools

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("ops-mcp")

app = FastAPI(title="Ops MCP Server")

TOOL_DEFINITIONS = {
    "check_portal": {
        "description": "Check Customer Portal HTTP status. Read-only.",
        "parameters": {"type": "object", "properties": {"incident_id": {"type": "string"}}, "required": ["incident_id"]},
    },
    "check_backend": {
        "description": "Check backend health endpoint. Read-only.",
        "parameters": {"type": "object", "properties": {"incident_id": {"type": "string"}}, "required": ["incident_id"]},
    },
    "get_gateway_logs": {
        "description": "Get recent gateway error logs. Read-only.",
        "parameters": {"type": "object", "properties": {"incident_id": {"type": "string"}}, "required": ["incident_id"]},
    },
    "get_gateway_config": {
        "description": "Get current gateway upstream configuration. Read-only.",
        "parameters": {"type": "object", "properties": {"incident_id": {"type": "string"}}, "required": ["incident_id"]},
    },
    "get_recent_changes": {
        "description": "Get recent gateway configuration change history. Read-only.",
        "parameters": {"type": "object", "properties": {"incident_id": {"type": "string"}}, "required": ["incident_id"]},
    },
    "apply_gateway_fix": {
        "description": "Apply gateway upstream fix. Requires valid approval token. State-changing.",
        "parameters": {
            "type": "object",
            "properties": {
                "incident_id": {"type": "string"},
                "approval_token": {"type": "string"},
                "expected_current_backend_url": {"type": "string"},
                "target_backend_url": {"type": "string"},
            },
            "required": ["incident_id", "approval_token", "expected_current_backend_url", "target_backend_url"],
        },
    },
    "verify_service": {
        "description": "Verify service health after remediation. Read-only.",
        "parameters": {"type": "object", "properties": {"incident_id": {"type": "string"}}, "required": ["incident_id"]},
    },
}

FORBIDDEN_NAMES = {"shell", "bash", "ssh", "sudo", "docker", "exec", "run_command", "write_file", "delete_file"}


class ToolCallRequest(BaseModel):
    tool: str
    arguments: dict[str, Any]


def _check_internal_token(x_aiops_internal_token: str | None = Header(default=None)):
    if x_aiops_internal_token != AIOPS_INTERNAL_TOKEN:
        raise HTTPException(status_code=403, detail="invalid internal token")


@app.get("/healthz")
async def healthz():
    return {"service": "ops-mcp", "status": "healthy", "tools": list(TOOL_DEFINITIONS.keys())}


@app.get("/mcp/tools")
async def list_tools():
    return {"tools": [{"name": k, **v} for k, v in TOOL_DEFINITIONS.items()]}


@app.post("/mcp/tools/call")
async def call_tool(req: ToolCallRequest, x_aiops_internal_token: str | None = Header(default=None)):
    _check_internal_token(x_aiops_internal_token)
    tool_name = req.tool
    if tool_name in FORBIDDEN_NAMES:
        raise HTTPException(status_code=403, detail="forbidden tool")
    if tool_name not in TOOL_DEFINITIONS:
        raise HTTPException(status_code=404, detail=f"unknown tool: {tool_name}")

    args = req.arguments
    try:
        if tool_name == "check_portal":
            result = await tools.check_portal(args["incident_id"])
        elif tool_name == "check_backend":
            result = await tools.check_backend(args["incident_id"])
        elif tool_name == "get_gateway_logs":
            result = await tools.get_gateway_logs(args["incident_id"])
        elif tool_name == "get_gateway_config":
            result = await tools.get_gateway_config(args["incident_id"])
        elif tool_name == "get_recent_changes":
            result = await tools.get_recent_changes(args["incident_id"])
        elif tool_name == "apply_gateway_fix":
            result = await tools.apply_gateway_fix(
                args["incident_id"],
                args["approval_token"],
                args["expected_current_backend_url"],
                args["target_backend_url"],
            )
        elif tool_name == "verify_service":
            result = await tools.verify_service(args["incident_id"])
        else:
            raise HTTPException(status_code=404, detail=f"unhandled tool: {tool_name}")
        return {"tool": tool_name, "result": result}
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"missing argument: {e}")
    except Exception as e:
        logger.exception("tool execution failed: %s", tool_name)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp")
async def mcp_endpoint(request: Request, x_aiops_internal_token: str | None = Header(default=None)):
    _check_internal_token(x_aiops_internal_token)
    body = await request.json()
    method = body.get("method", "")

    if method == "tools/list":
        return {"tools": [{"name": k, "description": v["description"], "inputSchema": v["parameters"]} for k, v in TOOL_DEFINITIONS.items()]}
    elif method == "tools/call":
        params = body.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        if tool_name in FORBIDDEN_NAMES:
            return {"error": {"code": -32601, "message": "forbidden tool"}}
        if tool_name not in TOOL_DEFINITIONS:
            return {"error": {"code": -32601, "message": f"unknown tool: {tool_name}"}}
        req = ToolCallRequest(tool=tool_name, arguments=arguments)
        return await call_tool(req, x_aiops_internal_token)
    elif method == "initialize":
        return {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}}
    else:
        return {"error": {"code": -32601, "message": f"unknown method: {method}"}}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8765)
