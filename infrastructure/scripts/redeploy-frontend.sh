#!/usr/bin/env bash
set -euo pipefail

# Fly.io deploy for frontend/gateway (root-level toml to ensure correct build context)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

if ! command -v fly >/dev/null 2>&1; then
  echo "flyctl not found. Install from https://fly.io/docs/hands-on/install-flyctl/" >&2
  exit 1
fi

APP_NAME=${FLY_APP_NAME:-oncolife-patient-frontend-gateway}

# Create only if it truly doesn't exist
if fly apps show "$APP_NAME" >/dev/null 2>&1; then
  echo "Using existing app: $APP_NAME"
else
  echo "Creating app: $APP_NAME"
  fly apps create "$APP_NAME"
fi

# Deploy explicitly to the app to avoid name mismatches in TOML
fly deploy --config fly.patient-frontend.toml --app "$APP_NAME" --remote-only --build-only=false --now 