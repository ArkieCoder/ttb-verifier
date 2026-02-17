# Operational Runbook

## Table of Contents
1. [System Status Checks](#system-status-checks)
2. [Common Operations](#common-operations)
3. [Troubleshooting](#troubleshooting)
4. [Incident Response](#incident-response)
5. [Maintenance Procedures](#maintenance-procedures)

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
    "tesseract": {"available": true, "error": null},
    "ollama": {"available": true, "error": null}
  },
  "capabilities": {
    "ocr_backends": ["tesseract", "ollama"],
    "degraded_mode": false
  }
}
```

**Degraded (Ollama unavailable):**
```json
{
  "status": "degraded",
  "backends": {
    "tesseract": {"available": true, "error": null},
    "ollama": {"available": false, "error": "Model 'llama3.2-vision' not found"}
  },
  "capabilities": {
    "ocr_backends": ["tesseract"],
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

**Test Tesseract backend:**
```bash
curl -X POST https://ttb-verifier.unitedentropy.com/verify \
  -F "image=@test_samples/label_good_001.jpg" \
  -F "ocr_backend=tesseract" | jq .
```

**Test Ollama backend (may fail in degraded mode):**
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
  --parameters 'commands=["/app/deploy.sh"]'
```

### Issue: High Response Times

**Symptoms:**
- Requests taking > 10 seconds
- Timeout errors

**Diagnosis:**
1. Check which backend is being used:
   - Tesseract: Expected 2-3 seconds
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
- Recommend users use Tesseract backend for faster results
- Consider scaling to larger instance type (t3.large)

**If Tesseract is slow:**
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

## Incident Response

### Severity Levels

**Critical (P1):**
- Complete service outage
- Tesseract backend unavailable
- Data loss or corruption

**High (P2):**
- Degraded performance affecting users
- Ollama backend unavailable > 2 hours
- Error rate > 10%

**Medium (P3):**
- Ollama backend unavailable < 2 hours
- Error rate 5-10%
- Performance degradation < 2x normal

**Low (P4):**
- Cosmetic issues
- Documentation errors
- Minor bugs not affecting core functionality

### Response Procedures

#### P1: Critical Outage

**Immediate actions (< 5 minutes):**
1. Verify outage scope via health endpoint
2. Check EC2 instance status
3. Check container status
4. Notify stakeholders

**Recovery actions (< 15 minutes):**
1. Attempt container restart
2. If failed, redeploy application
3. If failed, recreate EC2 instance:
   ```bash
   cd infrastructure
   terragrunt destroy
   terragrunt apply
   ```
4. Monitor recovery via health endpoint

**Post-incident:**
1. Document timeline and actions taken
2. Review logs for root cause
3. Update runbook with lessons learned

#### P2: High Severity

**Immediate actions (< 15 minutes):**
1. Assess impact and scope
2. Determine if degradation is acceptable
3. If Ollama unavailable, check background download status

**Recovery actions (< 30 minutes):**
1. Follow troubleshooting procedures above
2. If unresolvable quickly, escalate to P1

**Post-incident:**
1. Document issue and resolution
2. Consider if monitoring/alerting needs improvement

## Maintenance Procedures

### Planned Deployment

**Before deployment:**
1. Announce maintenance window
2. Verify backup procedures
3. Review changes in staging

**Deployment process:**
1. Merge code to master branch
2. GitHub Actions automatically:
   - Runs tests
   - Builds Docker image
   - Deploys to EC2
3. Monitor deployment via workflow logs
4. Verify health endpoint post-deployment

**Rollback (if needed):**
```bash
# Revert git commit
git revert HEAD
git push origin master

# GitHub Actions will automatically deploy previous version
```

### Instance Recreation

**When to do this:**
- Infrastructure updates (instance_init.sh changes)
- Instance type changes
- Disk space expansion
- Regular maintenance (monthly recommended)

**Procedure:**
```bash
cd infrastructure

# Destroy current instance
terragrunt destroy

# Recreate with latest configuration
terragrunt apply

# Monitor deployment
watch -n 5 'curl -s https://ttb-verifier.unitedentropy.com/health | jq .'
```

**Expected timeline:**
- Destroy: 2-3 minutes
- Apply (degraded): 2-3 minutes
- Full capability: 10-12 minutes

### Model Cache Update

**When S3 model is corrupted or outdated:**

```bash
# Delete S3 model
aws s3 rm s3://ttb-verifier-ollama-models-<ACCOUNT_ID>/models/llama3.2-vision.tar.gz

# Recreate instance (will download fresh and re-export)
cd infrastructure
terragrunt destroy
terragrunt apply
```

### Certificate Renewal

**ACM certificates auto-renew.** No action required.

**To verify certificate status:**
```bash
aws acm describe-certificate \
  --certificate-arn $(terragrunt output -raw certificate_arn) \
  --query 'Certificate.[DomainName,Status,NotAfter]' \
  --output table
```

## Monitoring Best Practices

### Regular Checks (Daily)
- [ ] Health endpoint status
- [ ] Error rates
- [ ] Response times
- [ ] Disk space usage

### Regular Checks (Weekly)
- [ ] Review CloudWatch logs
- [ ] Review ALB access logs
- [ ] Check for security updates
- [ ] Verify backups/exports working

### Regular Checks (Monthly)
- [ ] Review incident log
- [ ] Update runbooks based on incidents
- [ ] Test disaster recovery procedures
- [ ] Review and optimize costs

## Emergency Contacts

*[Add your team's contact information here]*

- On-call engineer: 
- Engineering lead:
- DevOps team:
- Escalation path:

## References

- Architecture Overview: `docs/ARCHITECTURE.md`
- Deployment Guide: `infrastructure/DEPLOYMENT_GUIDE.md`
- API Documentation: `docs/API_README.md`
