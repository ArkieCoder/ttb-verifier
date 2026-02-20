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

set -euo pipefail

HEALTHY_FILE="/etc/OLLAMA_HEALTHY"
MODEL="${OLLAMA_MODEL:-llama3.2-vision}"
CONTAINER="${OLLAMA_CONTAINER:-ttb-ollama}"
LOG_TAG="ollama-health-cron"

log() { logger -t "$LOG_TAG" "$*"; }

mark_healthy() {
    touch "$HEALTHY_FILE"
    log "OK — model '$MODEL' is in GPU RAM, marked healthy"
}

mark_unhealthy() {
    rm -f "$HEALTHY_FILE"
    log "WARN — $1, marked unhealthy"
}

# ── 1. Is the container running? ────────────────────────────────────────────
if ! docker inspect --format '{{.State.Running}}' "$CONTAINER" 2>/dev/null | grep -q true; then
    mark_unhealthy "container '$CONTAINER' is not running"
    exit 0
fi

# ── 2. Is the model downloaded? (ollama list) ───────────────────────────────
if ! docker exec "$CONTAINER" ollama list 2>/dev/null | awk 'NR>1{print $1}' | grep -q "^${MODEL}"; then
    mark_unhealthy "model '$MODEL' not found in 'ollama list'"
    exit 0
fi

# ── 3. Is the model loaded in GPU RAM? (ollama ps) ──────────────────────────
if docker exec "$CONTAINER" ollama ps 2>/dev/null | awk 'NR>1{print $1}' | grep -q "^${MODEL}"; then
    mark_healthy
    exit 0
fi

# ── 4. Model is downloaded but NOT in GPU — pre-warm it ─────────────────────
log "Model '$MODEL' not in GPU, starting pre-warm..."

# Run a minimal generate request with keep_alive=-1 so the model stays loaded.
# Empty prompt loads weights without running real inference (fast, ~2-5s).
if docker exec "$CONTAINER" ollama run "$MODEL" "" 2>/dev/null; then
    log "Pre-warm complete"
else
    mark_unhealthy "pre-warm command failed"
    exit 0
fi

# ── 5. Re-check after pre-warm ───────────────────────────────────────────────
if docker exec "$CONTAINER" ollama ps 2>/dev/null | awk 'NR>1{print $1}' | grep -q "^${MODEL}"; then
    mark_healthy
else
    mark_unhealthy "model still not in GPU after pre-warm"
fi
