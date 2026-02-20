# Variables are exported from user_data in instance.tf
# S3_BUCKET - bucket containing Ollama models
# AWS_ACCOUNT_ID - AWS account ID
# DOMAIN_NAME - primary domain name for the application

set -e

echo "========================================="
echo "TTB Verifier EC2 Instance Initialization"
echo "========================================="
echo "S3 Bucket: ${S3_BUCKET:-not set}"
echo "Domain Name: ${DOMAIN_NAME:-not set}"
echo ""

# Update system packages
echo "Updating system packages..."
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get upgrade -y

# Install AWS CLI (not pre-installed on Ubuntu)
echo "Installing AWS CLI..."
apt-get install -y unzip curl
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip"
unzip -q /tmp/awscliv2.zip -d /tmp
/tmp/aws/install
rm -rf /tmp/aws /tmp/awscliv2.zip

# Install SSM Agent (not pre-installed on Ubuntu)
echo "Installing SSM Agent..."
snap install amazon-ssm-agent --classic
systemctl enable snap.amazon-ssm-agent.amazon-ssm-agent.service
systemctl start snap.amazon-ssm-agent.amazon-ssm-agent.service

# Install Docker
echo "Installing Docker..."
apt-get install -y ca-certificates gnupg lsb-release
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl start docker
systemctl enable docker
usermod -a -G docker ubuntu

# Install NVIDIA drivers and Docker GPU support for g4dn instances
echo "Installing NVIDIA GPU support..."

# Ubuntu has excellent NVIDIA driver support via APT
apt-get install -y ubuntu-drivers-common
ubuntu-drivers devices
apt-get install -y nvidia-driver-550 nvidia-dkms-550

# Load NVIDIA kernel modules
modprobe nvidia || echo "Waiting for driver to initialize..."
modprobe nvidia-uvm || echo "Waiting for nvidia-uvm to initialize..."

# Install NVIDIA Container Toolkit
echo "Installing NVIDIA Container Toolkit..."
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
apt-get update
apt-get install -y nvidia-container-toolkit
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker

# Verify GPU is accessible
nvidia-smi || echo "GPU not detected yet, may need reboot"

# Install Docker Compose standalone (for compatibility)
echo "Installing Docker Compose standalone..."
DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Verify Docker and Docker Compose installation
docker --version
docker-compose --version

# Create application directory
echo "Creating application directory..."
mkdir -p /app
mkdir -p /home/ubuntu/tmp
chown -R ubuntu:ubuntu /app
chown -R ubuntu:ubuntu /home/ubuntu/tmp

# Create Ollama entrypoint wrapper
echo "Creating Ollama entrypoint wrapper..."
cat > /app/ollama-entrypoint.sh <<'EOFWRAPPER'
#!/bin/bash
set -e

echo "Starting Ollama server..."
# Start Ollama server in background
/bin/ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "Waiting for Ollama to be ready..."
for i in {1..30}; do
  if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "Ollama is ready!"
    break
  fi
  sleep 1
done

echo "✅ Ollama container is ready!"
echo "   Model will be loaded by the health cron job"

# Keep the script running and forward signals to Ollama
trap "kill $OLLAMA_PID" SIGTERM SIGINT
wait $OLLAMA_PID
EOFWRAPPER

chmod +x /app/ollama-entrypoint.sh
chown ubuntu:ubuntu /app/ollama-entrypoint.sh

# Create healthcheck script that verifies Ollama is running and model is available
echo "Creating Ollama healthcheck script..."
cat > /app/ollama-healthcheck.sh <<'EOFHEALTH'
#!/bin/sh
# Check if Ollama server is responsive and llama3.2-vision model is available
/bin/ollama list | grep -q 'llama3.2-vision' || exit 1
exit 0
EOFHEALTH

chmod +x /app/ollama-healthcheck.sh
chown ubuntu:ubuntu /app/ollama-healthcheck.sh

# Create production docker-compose.yml
echo "Creating docker-compose configuration..."
cat > /app/docker-compose.yml <<'EOF'
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ttb-ollama
    ports:
      - "11434:11434"
    environment:
      - OLLAMA_KEEP_ALIVE=-1
    volumes:
      - ollama_models:/root/.ollama
      - /app/ollama-entrypoint.sh:/usr/local/bin/ollama-entrypoint.sh:ro
      - /app/ollama-healthcheck.sh:/usr/local/bin/ollama-healthcheck.sh:ro
    entrypoint: ["/usr/local/bin/ollama-entrypoint.sh"]
    runtime: nvidia
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "/usr/local/bin/ollama-healthcheck.sh"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 120s

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
      - TMPDIR=/app/tmp
      - CORS_ORIGINS=["*"]
      - DOMAIN_NAME=${DOMAIN_NAME}
      - AWS_REGION=${AWS_REGION:-us-east-1}
      - SESSION_SECRET_KEY=${SESSION_SECRET_KEY}
    volumes:
      - /home/ubuntu/tmp:/app/tmp
      - /etc/OLLAMA_HEALTHY:/etc/OLLAMA_HEALTHY:ro
    depends_on:
      - ollama
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 30s
      retries: 3
      start_period: 10s

volumes:
  ollama_models:
    driver: local
EOF

chown ubuntu:ubuntu /app/docker-compose.yml

# Create .env file with DOMAIN_NAME for docker-compose
echo "Creating .env file..."

# Fetch session secret key from Secrets Manager
echo "Fetching session secret key from AWS Secrets Manager..."
SESSION_SECRET_KEY=$(aws secretsmanager get-secret-value --secret-id TTB_SESSION_SECRET_KEY --query SecretString --output text --region ${AWS_REGION:-us-east-1})

cat > /app/.env <<EOF
DOMAIN_NAME=${DOMAIN_NAME}
AWS_REGION=${AWS_REGION:-us-east-1}
SESSION_SECRET_KEY=${SESSION_SECRET_KEY}
EOF

chown ubuntu:ubuntu /app/.env

# Create deployment script for GitHub Actions to call
cat > /app/deploy.sh <<'EOFSCRIPT'
#!/bin/bash
set -e

echo "========================================="
echo "Deploying TTB Verifier"
echo "========================================="

cd /app

# Check if this is a verifier-only deployment (default: update both)
# Set VERIFIER_ONLY=true to only restart verifier container
VERIFIER_ONLY=${VERIFIER_ONLY:-false}

if [ "$VERIFIER_ONLY" = "true" ]; then
  echo "📦 Verifier-only deployment detected"
  echo "   - Pulling verifier image only"
  echo "   - Ollama will NOT be restarted (keeps model in GPU)"
  
  # Pull only verifier image
  docker-compose pull verifier
  
  # Stop and remove only verifier container
  echo "Stopping verifier container..."
  docker-compose stop verifier
  docker-compose rm -f verifier
  
  # Start verifier with new image (ollama stays running)
  echo "Starting verifier with new image..."
  docker-compose up -d verifier
  
  # Wait for verifier to be ready
  echo "Waiting for verifier to start..."
  sleep 10
  
else
  echo "🔄 Full deployment - updating all containers"
  
  # Pull all images
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
fi

# Check verifier health (always needed)
echo "Checking verifier service..."
curl -f http://localhost:8000/ || {
  echo "Health check failed!"
  docker-compose logs --tail=50 verifier
  exit 1
}

# Install/refresh Ollama health cron script on every deploy.
# Writes /etc/OLLAMA_HEALTHY when model is in GPU; removes it otherwise.
# The FastAPI /health endpoint reads only this file — no blocking network calls.
cat > /usr/local/bin/ollama-health-cron.sh <<'EOFCRON'
#!/bin/bash
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
EOFCRON
chmod +x /usr/local/bin/ollama-health-cron.sh
(crontab -l 2>/dev/null | grep -v ollama-health-cron || true
 echo "*/5 * * * * /usr/local/bin/ollama-health-cron.sh >> /var/log/ollama-health-cron.log 2>&1") | crontab -
echo "Ollama health cron installed"

echo "========================================="
echo "Deployment successful!"
echo "========================================="
EOFSCRIPT

chmod +x /app/deploy.sh
chown ubuntu:ubuntu /app/deploy.sh

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
echo "Deploying application (Ollama backend required)..."
echo "Ollama model will be downloaded in background."

if /app/deploy.sh; then
  echo "✅ Verifier application deployed successfully!"
  echo "   Status: Ollama backend will be available after model download completes."
  echo "   Verification endpoints will return 503 until Ollama is ready."
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
# Model name from environment variable (allows users to specify custom models)
MODEL_NAME="${OLLAMA_MODEL:-llama3.2-vision}"

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
    # Note: docker-compose prefixes volume names with directory name (app_)
    docker run --rm \
      -v app_ollama_models:/root/.ollama \
      -v /home:/backup \
      alpine:latest \
      sh -c "mkdir -p /root/.ollama && cd /root/.ollama && tar xzf /backup/model.tar.gz"
    
    # Clean up
    rm -f /home/model.tar.gz
    
    # Restart ollama
    docker-compose start ollama
    sleep 10
    
    echo "[Background] ✅ Model restored from S3 successfully"
    echo "[Background] Model will be loaded into GPU by the health cron job"
  else
    echo "[Background] Model not found in S3, falling back to ollama pull..."
    echo "[Background] This will take 5-15 minutes depending on connection speed..."
    cd /app
    docker-compose exec -T ollama ollama pull llama3.2-vision
    
    echo "[Background] ✅ Model downloaded successfully from Ollama servers."
    echo "[Background] Model will be loaded into GPU by the health cron job"

    
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
  echo "[Background] Ollama backend is now operational."
    echo "[Background] Model will be loaded into GPU by the health cron job (runs every 5 min)"
  echo "[Background] Subsequent requests will be fast (model stays loaded with keep_alive=-1)."
  
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
echo "Application: ONLINE"
echo "Ollama Model: Downloading in background..."
echo "========================================="
echo ""
echo "✅ System is operational and will serve traffic once Ollama is ready!"
  echo "   - Ollama OCR: Available after cron pre-warms model (~2-5 minutes)"
echo "   - /verify endpoints return 503 until Ollama is available"
echo "   - Check status: curl http://localhost:8000/health"
echo "========================================="
