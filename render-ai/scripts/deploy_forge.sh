#!/usr/bin/env bash
# Sync render.ai LiteLLM fork to forge and (re)start the proxy.
set -euo pipefail

FORGE_HOST="${FORGE_HOST:-vulcan@forge}"
FORGE_PASS="${FORGE_PASS:-vulcan}"
REMOTE_DIR="${REMOTE_DIR:-/home/vulcan/litellm}"
LOCAL_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SERVICE_NAME="${SERVICE_NAME:-render-litellm}"

echo "Syncing $LOCAL_ROOT -> $FORGE_HOST:$REMOTE_DIR"
sshpass -p "$FORGE_PASS" rsync -az --delete \
  --exclude '.git' \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude 'node_modules' \
  "$LOCAL_ROOT/" "$FORGE_HOST:$REMOTE_DIR/"

echo "Installing and restarting on forge..."
sshpass -p "$FORGE_PASS" ssh "$FORGE_HOST" bash -s <<REMOTE
set -euo pipefail
cd "$REMOTE_DIR"
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip wheel
pip install -e ".[proxy]"

if [[ ! -f render-ai/.env ]]; then
  echo "WARNING: $REMOTE_DIR/render-ai/.env missing on forge — copy from .env.example"
fi

# User systemd unit (idempotent)
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/${SERVICE_NAME}.service <<UNIT
[Unit]
Description=render.ai LiteLLM capability gateway
After=network.target

[Service]
WorkingDirectory=$REMOTE_DIR
EnvironmentFile=-$REMOTE_DIR/render-ai/.env
ExecStart=$REMOTE_DIR/.venv/bin/litellm --config $REMOTE_DIR/render-ai/capability_registry.yaml --host 0.0.0.0 --port 4000
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
UNIT

systemctl --user daemon-reload
systemctl --user enable ${SERVICE_NAME}
systemctl --user restart ${SERVICE_NAME}
systemctl --user --no-pager status ${SERVICE_NAME} || true
REMOTE

echo "Done. Probe: curl http://forge:4000/health (from Mac)"