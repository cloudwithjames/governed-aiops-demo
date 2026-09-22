#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

ENV_FILE="${PROJECT_DIR}/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: .env not found. Run create-env.sh first."
    exit 1
fi

source "$ENV_FILE"

TEMPLATE="${PROJECT_DIR}/hermes/config.yaml.template"
OUTPUT="${PROJECT_DIR}/hermes/config.yaml"

sed \
    -e "s|\${HERMES_MODEL_NAME}|${HERMES_MODEL_NAME}|g" \
    -e "s|\${HERMES_MODEL_BASE_URL}|${HERMES_MODEL_BASE_URL}|g" \
    -e "s|\${HERMES_API_SERVER_KEY}|${HERMES_API_SERVER_KEY}|g" \
    "$TEMPLATE" > "$OUTPUT"

echo "Hermes config rendered to hermes/config.yaml"
echo "WARNING: Model API key is NOT printed for security."
