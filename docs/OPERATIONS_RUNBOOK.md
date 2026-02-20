# Operations Runbook

## Table of Contents
1. [System Status Checks](#system-status-checks)
2. [Common Operations](#common-operations)
3. [Troubleshooting](#troubleshooting)

## System Status Checks

### Quick Health Check

**Check overall system health:**
```bash
curl https://ttb-verifier.unitedentropy.com/health | jq .
```

**Expected responses:**

**Healthy (all backends available):**
```json
{
  "status": "healthy",
  "backends": {
    "ollama": {"available": true, "error": null}
  },
  "capabilities": {
    "ocr_backends": ["ollama"],
    "degraded_mode": false
  }
}
```

**Degraded (Ollama unavailable):**
```json
{
  "status": "degraded",
  "backends": {
    "ollama": {"available": false, "error": "Model 'llama3.2-vision' not found"}
  },
  "capabilities": {
    "ocr_backends": [],
    "degraded_mode": true
  }
}
```

### Detailed Status Checks

**Check EC2 instance:**
```bash
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=ttb-verifier" \
  --query 'Reservations[0].Instances[0].[InstanceId,State.Name,LaunchTime]' \
  --output table
```

**Check container status:**
```bash
INSTANCE_ID=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=ttb-verifier" \
  --query 'Reservations[0].Instances[0].InstanceId' \
  --output text)

aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=["docker ps"]' \
  --query 'Command.CommandId' \
  --output text

# Wait a few seconds, then get output:
aws ssm get-command-invocation \
  --command-id <COMMAND_ID> \
  --instance-id "$INSTANCE_ID" \
  --query 'StandardOutputContent' \
  --output text
```

**Check model download progress (if in degraded mode):**
```bash
aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=["tail -20 /var/log/ollama-model-download.log 2>&1 || echo \"Log not found\""]' \
  --query 'Command.CommandId' \
  --output text
```

## Common Operations

### Restart Application

**Restart just the verifier container:**
```bash
aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=["cd /app && docker-compose restart verifier"]' \
  --query 'Command.CommandId' \
  --output text
```

**Restart all containers:**
```bash
aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=["cd /app && docker-compose restart"]' \
  --query 'Command.CommandId' \
  --output text
```

### View Logs

**Verifier container logs:**
```bash
aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=["docker logs ttb-verifier --tail 50"]' \
  --query 'Command.CommandId' \
  --output text
```

**Ollama container logs:**
```bash
aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=["docker logs ttb-ollama --tail 50"]' \
  --query 'Command.CommandId' \
  --output text
```

### Check Disk Space

```bash
aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=["df -h"]' \
  --query 'Command.CommandId' \
  --output text
```

### Test Endpoints

**Test Ollama backend:**
```bash
curl -X POST https://ttb-verifier.unitedentropy.com/verify \
  -F "image=@test_samples/label_good_001.jpg" \
  -F "ocr_backend=ollama" | jq .
```

## Troubleshooting

### Issue: System in Degraded Mode

**Symptoms:**
- `/health` returns `"status": "degraded"`
- Ollama backend shows `"available": false`
- Requests with `ocr_backend=ollama` return errors

**Diagnosis:**
1. Check how long instance has been running:
   ```bash
   aws ec2 describe-instances \
     --instance-ids "$INSTANCE_ID" \
     --query 'Reservations[0].Instances[0].LaunchTime'
   ```
2. If < 12 minutes: **Expected** - Model still downloading in background
3. If > 12 minutes: **Problem** - Model download may have failed

**Resolution:**

**If < 12 minutes (normal):**
- Wait for background download to complete
- Monitor via health endpoint
- System is operational in degraded mode

**If > 12 minutes (abnormal):**
1. Check model download logs:
   ```bash
   aws ssm send-command \
     --instance-ids "$INSTANCE_ID" \
     --document-name "AWS-RunShellScript" \
     --parameters 'commands=["cat /var/log/ollama-model-download.log"]'
   ```

2. Check for disk space issues:
   ```bash
   aws ssm send-command \
     --instance-ids "$INSTANCE_ID" \
     --document-name "AWS-RunShellScript" \
     --parameters 'commands=["df -h", "du -sh /home /tmp"]'
   ```

3. Check if model file exists:
   ```bash
   aws ssm send-command \
     --instance-ids "$INSTANCE_ID" \
     --document-name "AWS-RunShellScript" \
     --parameters 'commands=["docker exec ttb-ollama ollama list"]'
   ```

4. If model download failed, manually trigger:
   ```bash
   aws ssm send-command \
     --instance-ids "$INSTANCE_ID" \
     --document-name "AWS-RunShellScript" \
     --parameters 'commands=["cd /app && docker-compose exec -T ollama ollama pull llama3.2-vision"]'
   ```

### Issue: Application Not Responding

**Symptoms:**
- ALB health check failing
- 502/503 errors from load balancer
- `/health` endpoint times out

**Diagnosis:**
```bash
# Check container status
aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=["docker ps -a", "docker logs ttb-verifier --tail 50"]'
```

**Resolution:**

**If container stopped:**
```bash
aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=["cd /app && docker-compose up -d"]'
```

**If container running but unhealthy:**
```bash
# Restart container
aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=["cd /app && docker-compose restart verifier"]'
```

**If persistent issues:**
```bash
# Redeploy application
aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=["/app/workflow_deploy.sh"]'
```

### Issue: High Response Times

**Symptoms:**
- Requests taking > 10 seconds
- Timeout errors

**Diagnosis:**
1. Check which backend is being used:
   - Ollama: Expected 30-60 seconds

2. Check system load:
   ```bash
   aws ssm send-command \
     --instance-ids "$INSTANCE_ID" \
     --document-name "AWS-RunShellScript" \
     --parameters 'commands=["uptime", "free -h", "docker stats --no-stream"]'
   ```

**Resolution:**

**If Ollama is slow:**
- Expected behavior - Ollama takes 30-60 seconds per image
- Consider scaling to larger instance type (t3.large)

**If system is slow:**
- Check system resources (CPU, memory)
- Check for concurrent requests overwhelming system
- Consider implementing rate limiting

### Issue: Out of Disk Space

**Symptoms:**
- Container fails to start
- Model download fails
- Application logs show write errors

**Diagnosis:**
```bash
aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=["df -h", "docker system df"]'
```

**Resolution:**

**Clean up Docker:**
```bash
aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=["docker system prune -af"]'
```

**Remove old model files:**
```bash
aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=["rm -f /home/model.tar.gz /tmp/model.tar.gz"]'
```

**If persistent:** Increase root volume size in `infrastructure/instance.tf`

## References

- [Architecture Overview](docs/ARCHITECTURE.md)
- [Deployment Guide](infrastructure/DEPLOYMENT_GUIDE.md)
- [API Documentation](docs/API_README.md)
