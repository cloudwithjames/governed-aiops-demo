#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

ENV_FILE="${PROJECT_DIR}/.env"

if [ -f "$ENV_FILE" ]; then
    echo ".env already exists. Use --force to overwrite."
    if [ "${1:-}" != "--force" ]; then
        exit 0
    fi
fi

cp "${PROJECT_DIR}/.env.example" "$ENV_FILE"

gen_secret() {
    python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || openssl rand -base64 32 2>/dev/null || echo "fallback-$(date +%s)-$RANDOM"
}

INTERNAL_TOKEN=$(gen_secret)
ADMIN_TOKEN=$(gen_secret)
SIGNING_SECRET=$(gen_secret)
HERMES_KEY=$(gen_secret)

sed -i \
    -e "s|AIOPS_INTERNAL_TOKEN=replace-me|AIOPS_INTERNAL_TOKEN=$INTERNAL_TOKEN|" \
    -e "s|DEMO_ADMIN_TOKEN=replace-me|DEMO_ADMIN_TOKEN=$ADMIN_TOKEN|" \
    -e "s|APPROVAL_SIGNING_SECRET=replace-me|APPROVAL_SIGNING_SECRET=$SIGNING_SECRET|" \
    -e "s|HERMES_API_SERVER_KEY=replace-me|HERMES_API_SERVER_KEY=$HERMES_KEY|" \
    "$ENV_FILE"

echo ".env created with generated secrets."
echo "WARNING: You still need to set:"
echo "  HERMES_MODEL_NAME"
echo "  HERMES_MODEL_BASE_URL"
echo "  HERMES_MODEL_API_KEY"
echo ""
echo "Model API key is NOT auto-generated. Set it manually in .env"
