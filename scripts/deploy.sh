#!/bin/bash
set -e

echo "========================================="
echo "TTB Verifier Deployment"
echo "========================================="
echo "Timestamp: $(date)"
echo "Host: $(hostname)"
echo ""

cd /app

# Pull latest images
echo "📥 Pulling latest Docker images from GHCR..."
docker-compose pull

# Stop existing containers gracefully
echo "🛑 Stopping existing containers..."
docker-compose down || true

# Start containers with new images
echo "🚀 Starting containers..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 15

# Check Ollama health
echo "🔍 Checking Ollama service..."
if docker-compose exec -T ollama ollama list > /dev/null 2>&1; then
  echo "✅ Ollama is healthy"
else
  echo "⚠️  Ollama health check failed (may still be starting)"
fi

# Check verifier health
echo "🔍 Checking verifier service..."
MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
  if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Verifier is healthy"
    
    # Show backend availability status
    HEALTH_STATUS=$(curl -s http://localhost:8000/health | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    if [ "$HEALTH_STATUS" = "degraded" ]; then
      echo "⚠️  Running in DEGRADED MODE (Tesseract-only)"
      echo "   Ollama backend will be available after model download completes"
    else
      echo "✅ All backends operational"
    fi
    break
  fi
  
  ATTEMPT=$((ATTEMPT+1))
  if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "❌ Health check failed after $MAX_ATTEMPTS attempts"
    echo ""
    echo "Container logs:"
    docker-compose logs --tail=50
    exit 1
  fi
  
  echo "   Attempt $ATTEMPT/$MAX_ATTEMPTS - waiting 2s..."
  sleep 2
done

# Display running containers
echo ""
echo "📦 Running containers:"
docker-compose ps

echo ""
echo "========================================="
echo "✅ Deployment successful!"
echo "========================================="
