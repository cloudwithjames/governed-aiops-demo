import os

DEMO_GATEWAY_URL = os.environ.get("DEMO_GATEWAY_URL", "http://demo-gateway:8080")
DEMO_BACKEND_URL = os.environ.get("DEMO_BACKEND_URL", "http://demo-backend:8080")
NORMAL_BACKEND_URL = os.environ.get("NORMAL_BACKEND_URL", "http://demo-backend:8080")
FAULT_BACKEND_URL = os.environ.get("FAULT_BACKEND_URL", "http://demo-backend:8081")

DEMO_ADMIN_TOKEN = os.environ.get("DEMO_ADMIN_TOKEN", "replace-me")
AIOPS_INTERNAL_TOKEN = os.environ.get("AIOPS_INTERNAL_TOKEN", "replace-me")
AIOPS_API_URL = os.environ.get("AIOPS_API_URL", "http://aiops-api:8000")

APPROVAL_SIGNING_SECRET = os.environ.get("APPROVAL_SIGNING_SECRET", "replace-me")
APPROVAL_TTL_SECONDS = int(os.environ.get("APPROVAL_TTL_SECONDS", "300"))

ALLOWED_TARGET_URLS = {
    NORMAL_BACKEND_URL,
    "http://demo-backend:8080",
}
