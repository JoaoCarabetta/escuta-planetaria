#!/usr/bin/env bash
# Sync web-facing static files to the VPS path for one environment.
# Env: SSH_HOST SSH_USER REMOTE_DIR (e.g. /var/www/escutaplanetaria/prod)
set -euo pipefail

: "${SSH_HOST:?}"
: "${SSH_USER:?}"
: "${REMOTE_DIR:?}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_NAME="$(basename "$REMOTE_DIR")"

RSYNC_SSH=(ssh -o StrictHostKeyChecking=yes)
RSYNC_EXCLUDES=(
  --exclude '.git/'
  --exclude '.github/'
  --exclude 'deploy/'
  --exclude 'arquivo/'
  --exclude 'coleta/'
  --exclude 'moinho/'
  --exclude 'treino/'
  --exclude 'rubrica/'
  --exclude '*.py'
  --exclude '.gitignore'
  --exclude 'README.md'
  --exclude 'nginx/'
)

rsync -az --delete \
  "${RSYNC_EXCLUDES[@]}" \
  -e "${RSYNC_SSH[*]}" \
  "${ROOT}/" \
  "${SSH_USER}@${SSH_HOST}:${REMOTE_DIR}/"

# Environment marker for smoke checks
printf '%s\n' "$ENV_NAME" | ssh "${RSYNC_SSH[@]}" "${SSH_USER}@${SSH_HOST}" \
  "cat > '${REMOTE_DIR}/.deploy-env' && chown www-data:www-data '${REMOTE_DIR}/.deploy-env' 2>/dev/null || true"

echo "Deployed ${ENV_NAME} → ${SSH_USER}@${SSH_HOST}:${REMOTE_DIR}"
