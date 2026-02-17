#!/bin/bash
set -e

# Export Ollama model from EC2 instance and upload to S3
# This script should be run once to populate the S3 bucket with the model

INSTANCE_ID="${1:-i-00b92bc2cf4161b27}"
MODEL_NAME="${2:-llama3.2-vision}"
S3_BUCKET="${3}"

if [ -z "$S3_BUCKET" ]; then
  echo "Usage: $0 <instance-id> <model-name> <s3-bucket>"
  echo "Example: $0 i-00b92bc2cf4161b27 llama3.2-vision ttb-verifier-ollama-models-253490750467"
  exit 1
fi

echo "========================================="
echo "Exporting Ollama Model to S3"
echo "========================================="
echo "Instance ID: $INSTANCE_ID"
echo "Model: $MODEL_NAME"
echo "S3 Bucket: $S3_BUCKET"
echo ""

# Step 1: Create the model blob on EC2
echo "Step 1: Creating model blob on EC2..."
COMMAND_ID=$(aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=[
    "set -e",
    "echo Creating model blob...",
    "docker exec ttb-ollama ollama show '"$MODEL_NAME"' --modelfile > /tmp/'"$MODEL_NAME"'.modelfile || true",
    "docker exec ttb-ollama sh -c \"cd /root/.ollama/models && tar czf /tmp/'"$MODEL_NAME"'.tar.gz blobs manifests\"",
    "sudo chown ec2-user:ec2-user /tmp/'"$MODEL_NAME"'.tar.gz",
    "ls -lh /tmp/'"$MODEL_NAME"'.tar.gz",
    "echo Model blob created successfully"
  ]' \
  --output text \
  --query "Command.CommandId")

echo "Command ID: $COMMAND_ID"
echo "Waiting for blob creation..."

# Wait for command to complete
sleep 10
for i in {1..30}; do
  STATUS=$(aws ssm get-command-invocation \
    --command-id "$COMMAND_ID" \
    --instance-id "$INSTANCE_ID" \
    --query 'Status' \
    --output text 2>/dev/null || echo "Pending")
  
  if [ "$STATUS" = "Success" ]; then
    echo "✅ Blob creation completed"
    break
  elif [ "$STATUS" = "Failed" ]; then
    echo "❌ Blob creation failed"
    aws ssm get-command-invocation \
      --command-id "$COMMAND_ID" \
      --instance-id "$INSTANCE_ID" \
      --query '[StandardOutputContent,StandardErrorContent]' \
      --output text
    exit 1
  fi
  
  echo "Status: $STATUS (attempt $i/30)"
  sleep 5
done

# Step 2: Copy model blob from EC2 to local via S3 temp location
echo ""
echo "Step 2: Uploading model to S3..."

COMMAND_ID=$(aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=[
    "set -e",
    "echo Uploading to S3...",
    "aws s3 cp /tmp/'"$MODEL_NAME"'.tar.gz s3://'"$S3_BUCKET"'/models/'"$MODEL_NAME"'.tar.gz",
    "echo Upload completed",
    "aws s3 ls s3://'"$S3_BUCKET"'/models/'"$MODEL_NAME"'.tar.gz",
    "rm -f /tmp/'"$MODEL_NAME"'.tar.gz /tmp/'"$MODEL_NAME"'.modelfile",
    "echo Cleanup completed"
  ]' \
  --output text \
  --query "Command.CommandId")

echo "Command ID: $COMMAND_ID"
echo "Waiting for upload..."

# Wait for upload
sleep 5
for i in {1..60}; do
  STATUS=$(aws ssm get-command-invocation \
    --command-id "$COMMAND_ID" \
    --instance-id "$INSTANCE_ID" \
    --query 'Status' \
    --output text 2>/dev/null || echo "Pending")
  
  if [ "$STATUS" = "Success" ]; then
    echo "✅ Upload completed"
    aws ssm get-command-invocation \
      --command-id "$COMMAND_ID" \
      --instance-id "$INSTANCE_ID" \
      --query 'StandardOutputContent' \
      --output text
    break
  elif [ "$STATUS" = "Failed" ]; then
    echo "❌ Upload failed"
    aws ssm get-command-invocation \
      --command-id "$COMMAND_ID" \
      --instance-id "$INSTANCE_ID" \
      --query '[StandardOutputContent,StandardErrorContent]' \
      --output text
    exit 1
  fi
  
  echo "Status: $STATUS (attempt $i/60)"
  sleep 5
done

echo ""
echo "========================================="
echo "✅ Model exported to S3 successfully!"
echo "========================================="
echo "S3 Location: s3://$S3_BUCKET/models/$MODEL_NAME.tar.gz"
echo ""
echo "Verify with:"
echo "  aws s3 ls s3://$S3_BUCKET/models/"
echo ""
