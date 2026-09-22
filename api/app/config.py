import os

AIOPS_AGENT_MODE = os.environ.get("AIOPS_AGENT_MODE", "mock")
AIOPS_DB_PATH = os.environ.get("AIOPS_DB_PATH", "/data/aiops.db")
AIOPS_INTERNAL_TOKEN = os.environ.get("AIOPS_INTERNAL_TOKEN", "replace-me")
DEMO_ADMIN_TOKEN = os.environ.get("DEMO_ADMIN_TOKEN", "replace-me")
APPROVAL_SIGNING_SECRET = os.environ.get("APPROVAL_SIGNING_SECRET", "replace-me")
APPROVAL_TTL_SECONDS = int(os.environ.get("APPROVAL_TTL_SECONDS", "300"))
DEMO_APPROVER_NAME = os.environ.get("DEMO_APPROVER_NAME", "Demo Operator")

HERMES_API_URL = os.environ.get("HERMES_API_URL", "http://hermes:8642/v1")
HERMES_API_SERVER_KEY = os.environ.get("HERMES_API_SERVER_KEY", "replace-me")
HERMES_MODEL_NAME = os.environ.get("HERMES_MODEL_NAME", "hermes-agent")

OPS_MCP_URL = os.environ.get("OPS_MCP_URL", "http://ops-mcp:8765/mcp")

DEMO_GATEWAY_URL = os.environ.get("DEMO_GATEWAY_URL", "http://demo-gateway:8080")
DEMO_BACKEND_URL = os.environ.get("DEMO_BACKEND_URL", "http://demo-backend:8080")
NORMAL_BACKEND_URL = os.environ.get("NORMAL_BACKEND_URL", "http://demo-backend:8080")
FAULT_BACKEND_URL = os.environ.get("FAULT_BACKEND_URL", "http://demo-backend:8081")

NORMAL_UPSTREAM = "http://demo-backend:8080"
FAULT_UPSTREAM = "http://demo-backend:8081"
