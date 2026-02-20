#!/bin/bash
# ollama-health-cron.sh — run every 5 minutes via cron (root)
#
# Checks whether the Ollama model is downloaded and loaded in GPU RAM.
# If the model has been evicted, fires a pre-warm via `docker exec` and
# waits for it to finish before re-evaluating.
#
# Writes /etc/OLLAMA_HEALTHY when everything is good.
# Removes /etc/OLLAMA_HEALTHY when Ollama is unhealthy.
#
# The FastAPI /health endpoint reads only this file — no blocking network
# calls inside the app event loop.
#
# Installed by deploy.sh on every deployment. The canonical copy lives in
# scripts/ollama-health-cron.sh; deploy.sh embeds an identical copy.

set -euo pipefail

HEALTHY_FILE="/etc/OLLAMA_HEALTHY"
MODEL="${OLLAMA_MODEL:-llama3.2-vision}"
CONTAINER="${OLLAMA_CONTAINER:-ttb-ollama}"

log() { logger -t "ollama-health-cron" "$*"; }
mark_healthy()   { touch "$HEALTHY_FILE";  log "OK model in GPU"; }
mark_unhealthy() { rm -f "$HEALTHY_FILE";  log "WARN $1"; }

if ! docker inspect --format '{{.State.Running}}' "$CONTAINER" 2>/dev/null | grep -q true; then
  mark_unhealthy "container not running"; exit 0
fi

if ! docker exec "$CONTAINER" ollama list 2>/dev/null | awk 'NR>1{print $1}' | grep -q "^${MODEL}"; then
  mark_unhealthy "model not in ollama list"; exit 0
fi

if docker exec "$CONTAINER" ollama ps 2>/dev/null | awk 'NR>1{print $1}' | grep -q "^${MODEL}"; then
  mark_healthy; exit 0
fi

log "Model not in GPU, pre-warming..."
if docker exec "$CONTAINER" ollama run "$MODEL" "" 2>/dev/null; then
  log "Pre-warm complete"
else
  mark_unhealthy "pre-warm failed"; exit 0
fi

if docker exec "$CONTAINER" ollama ps 2>/dev/null | awk 'NR>1{print $1}' | grep -q "^${MODEL}"; then
  mark_healthy
else
  mark_unhealthy "still not in GPU after pre-warm"
fi
