#!/bin/bash
set -e

echo "🔍 Running health checks..."

# Check if verifier container is running
if ! docker ps --filter "name=ttb-verifier" --filter "status=running" --format "{{.Names}}" | grep -q "ttb-verifier"; then
  echo "❌ Verifier container is not running"
  exit 1
fi

echo "✅ Verifier container is running"

# Check HTTP health endpoint
if curl -f -s http://localhost:8000/ > /dev/null; then
  echo "✅ HTTP health check passed"
else
  echo "❌ HTTP health check failed"
  exit 1
fi

# Check if Ollama is accessible
if curl -f -s http://localhost:11434/api/tags > /dev/null; then
  echo "✅ Ollama is accessible"
else
  echo "⚠️  Ollama health check warning (may not be critical)"
fi

echo "✅ All health checks passed!"
