# Variables are exported from user_data in instance.tf
# S3_BUCKET - bucket containing Ollama models
# AWS_ACCOUNT_ID - AWS account ID

set -e

echo "========================================="
echo "TTB Verifier EC2 Instance Initialization"
echo "========================================="
echo "S3 Bucket: ${S3_BUCKET:-not set}"
echo ""

# Update system packages
echo "Updating system packages..."
dnf update -y

# Install Docker
echo "Installing Docker..."
dnf install -y docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
echo "Installing Docker Compose..."
DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose

# Verify Docker and Docker Compose installation
docker --version
docker-compose --version

# Verify SSM Agent is running (pre-installed on Amazon Linux 2023)
echo "Verifying SSM Agent..."
systemctl status amazon-ssm-agent
systemctl enable amazon-ssm-agent

# Create application directory
echo "Creating application directory..."
mkdir -p /app
mkdir -p /home/ec2-user/tmp
chown -R ec2-user:ec2-user /app
chown -R ec2-user:ec2-user /home/ec2-user/tmp

# Create production docker-compose.yml
echo "Creating docker-compose configuration..."
cat > /app/docker-compose.yml <<'EOF'
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ttb-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_models:/root/.ollama
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "ollama", "list"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  verifier:
    image: ghcr.io/arkiecoder/ttb-verifier:latest
    container_name: ttb-verifier
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_HOST=http://ollama:11434
      - OLLAMA_MODEL=llama3.2-vision
      - LOG_LEVEL=INFO
      - MAX_FILE_SIZE_MB=10
      - MAX_BATCH_SIZE=50
      - DEFAULT_OCR_BACKEND=tesseract
      - TMPDIR=/app/tmp
      - CORS_ORIGINS=["*"]
    volumes:
      - /home/ec2-user/tmp:/app/tmp
    depends_on:
      - ollama
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 10s

volumes:
  ollama_models:
    driver: local
EOF

chown ec2-user:ec2-user /app/docker-compose.yml

# Create deployment script for GitHub Actions to call
cat > /app/deploy.sh <<'EOFSCRIPT'
#!/bin/bash
set -e

echo "========================================="
echo "Deploying TTB Verifier"
echo "========================================="

cd /app

# Login to GitHub Container Registry (using public access for public repo)
echo "Pulling latest images from GHCR..."
docker-compose pull

# Stop existing containers
echo "Stopping existing containers..."
docker-compose down || true

# Start containers with new images
echo "Starting containers..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 15

# Check Ollama health
echo "Checking Ollama service..."
docker-compose exec -T ollama ollama list

# Check verifier health
echo "Checking verifier service..."
curl -f http://localhost:8000/ || {
  echo "Health check failed!"
  docker-compose logs --tail=50
  exit 1
}

echo "========================================="
echo "Deployment successful!"
echo "========================================="
EOFSCRIPT

chmod +x /app/deploy.sh
chown ec2-user:ec2-user /app/deploy.sh

# Pull and start Ollama service
echo "Starting Ollama service..."
cd /app
docker-compose up -d ollama

# Wait for Ollama to be ready
echo "Waiting for Ollama to start (10 seconds)..."
sleep 10

# Auto-deploy verifier application immediately (fail-open - degraded mode OK)
echo ""
echo "========================================="
echo "Auto-deploying TTB Verifier Application"
echo "========================================="
echo "Deploying application in degraded mode (Tesseract-only)..."
echo "Ollama model will be downloaded in background."

if /app/deploy.sh; then
  echo "✅ Verifier application deployed successfully!"
  echo "   Status: DEGRADED MODE (Tesseract OCR available)"
  echo "   Ollama backend will become available after model download completes."
else
  echo "⚠️  Initial deployment failed, but EC2 is ready for manual deployment"
  echo "   You can manually deploy using:"
  echo "   - GitHub Actions Deploy workflow"
  echo "   - AWS SSM: /app/deploy.sh"
  exit 0  # Don't fail EC2 initialization
fi

# Download llama3.2-vision model from S3 in BACKGROUND (non-blocking)
echo ""
echo "========================================="
echo "Background: Downloading llama3.2-vision model"
echo "========================================="

# Get the S3 bucket name from Terraform/user data (passed as environment variable)
S3_BUCKET="${S3_BUCKET:-ttb-verifier-ollama-models-${AWS_ACCOUNT_ID}}"
MODEL_NAME="llama3.2-vision"

# Run model download in background process
(
  echo "[Background] Starting model download process..."
  
  # Check if model exists in S3, if not fall back to ollama pull
  if aws s3 ls "s3://$S3_BUCKET/models/$MODEL_NAME.tar.gz" >/dev/null 2>&1; then
    echo "[Background] Found model in S3, downloading..."
    
    # Download and extract model (use /home to avoid tmpfs space issues)
    aws s3 cp "s3://$S3_BUCKET/models/$MODEL_NAME.tar.gz" /home/model.tar.gz
    
    # Stop ollama temporarily
    cd /app
    docker-compose stop ollama
    
    # Extract model files into the ollama volume
    docker run --rm \
      -v ollama_models:/root/.ollama \
      -v /home:/backup \
      alpine:latest \
      sh -c "cd /root/.ollama/models && tar xzf /backup/model.tar.gz"
    
    # Clean up
    rm -f /home/model.tar.gz
    
    # Restart ollama
    docker-compose start ollama
    sleep 10
    
    echo "[Background] ✅ Model restored from S3 successfully"
    echo "[Background] Ollama backend is now available for API requests."
  else
    echo "[Background] Model not found in S3, falling back to ollama pull..."
    echo "[Background] This will take 5-15 minutes depending on connection speed..."
    cd /app
    docker-compose exec -T ollama ollama pull llama3.2-vision
    
    echo "[Background] ✅ Model downloaded successfully from Ollama servers."
    echo "[Background] 📦 Exporting model to S3 to speed up future deployments..."
    
    # Self-healing: Export model to S3 for future instances
    # Use /home directory to avoid tmpfs space issues
    docker run --rm \
      --volumes-from ttb-ollama \
      -v /home:/backup \
      alpine:latest \
      tar czf /backup/model.tar.gz -C /root/.ollama models
    
    echo "[Background] Uploading compressed model to S3..."
    aws s3 cp /home/model.tar.gz "s3://$S3_BUCKET/models/$MODEL_NAME.tar.gz"
    
    # Clean up local copy
    rm -f /home/model.tar.gz
    
    echo "[Background] ✅ Model exported to S3 successfully!"
    echo "[Background] Future EC2 instances will download from S3 (1-2 min) instead of Ollama (5-15 min)."
  fi
  
  # Verify model is available
  echo "[Background] Verifying model..."
  cd /app
  docker-compose exec -T ollama ollama list
  
  echo "[Background] ========================================="
  echo "[Background] Model Download Complete!"
  echo "[Background] ========================================="
  echo "[Background] Ollama backend is now fully operational."
  
) >> /var/log/ollama-model-download.log 2>&1 &

# Log background process PID
BACKGROUND_PID=$!
echo "Model download running in background (PID: $BACKGROUND_PID)"
echo "Progress can be monitored: tail -f /var/log/ollama-model-download.log"

echo "========================================="
echo "EC2 Instance Initialization Complete!"
echo "========================================="
echo "Docker: $(docker --version)"
echo "Docker Compose: $(docker-compose --version)"
echo "SSM Agent: Active"
echo "Application: ONLINE (Degraded Mode - Tesseract only)"
echo "Ollama Model: Downloading in background..."
echo "========================================="
echo ""
echo "✅ System is operational and serving traffic!"
echo "   - Tesseract OCR: Available immediately"
echo "   - Ollama OCR: Will be available in ~2-5 minutes"
echo "   - Check status: curl http://localhost:8000/health"
echo "========================================="
