# DNS Configuration Reference

## Overview

The TTB Verifier infrastructure requires two DNS records:
1. **Certificate Validation CNAME** (temporary, can be removed after certificate issues)
2. **Application CNAME** (permanent, points traffic to your application)

## 1. Certificate Validation CNAME (Temporary)

### Purpose
AWS Certificate Manager (ACM) requires proof that you own the domain before issuing an SSL/TLS certificate. This is done via a special validation CNAME record.

### When to Add
During initial `terragrunt apply`, the process will pause and display:

```
ACTION REQUIRED: DNS Validation
=========================================

Add the following CNAME record to your DNS provider:

Record Type: CNAME
Name:  _abc123def456.ttb-verifier.yourdomain.com
Value: _xyz789abc.acm-validations.aws.

=========================================
```

### Configuration Example

**Example validation record:**
```
Type: CNAME
Hostname: _abc123def456.ttb-verifier.yourdomain.com
Points to: _xyz789abc.acm-validations.aws.
TTL: 300 (or your default)
```

**Important:** The exact values will be unique to your certificate request and displayed during deployment.

### Can I Remove This Record?

**YES!** You can safely remove the validation CNAME after the certificate is issued.

#### Why it's safe to remove:
- ✅ ACM only needs it once during initial certificate creation
- ✅ ACM will automatically renew the certificate without needing re-validation
- ✅ Renewal happens as long as the certificate is in use (attached to the ALB)
- ✅ No manual intervention needed for renewals

#### When to remove it:
1. Wait for `terragrunt apply` to complete successfully
2. Verify certificate status is "Issued" in AWS Console or via CLI:
   ```bash
   aws acm describe-certificate \
     --certificate-arn $(terragrunt output -raw certificate_arn) \
     --query 'Certificate.Status' \
     --output text
   # Should show: ISSUED
   ```
3. Once you see "ISSUED", you can delete the validation CNAME from your DNS

#### What happens if I keep it?
- No harm! It's just an extra DNS record
- Some organizations prefer to keep it for documentation purposes
- Uses minimal DNS resources

## 2. Application CNAME (Permanent)

### Purpose
Routes traffic from your domain to the AWS CloudFront distribution.

### When to Add
After `terragrunt apply` completes, you'll see:

```
2. Add CNAME record to your DNS provider:
   - Hostname: ttb-verifier.yourdomain.com
   - Type: CNAME
   - Value: d1bmuzubpqmnvs.cloudfront.net
   
   ⚠️  IMPORTANT: Point to CloudFront, NOT the ALB!
```

### Configuration Example

```
Type: CNAME
Hostname: ttb-verifier.yourdomain.com
Points to: d1bmuzubpqmnvs.cloudfront.net
TTL: 300 (or your default)
```

### Must I Keep This Record?

**YES!** This record must remain in place as long as you want the application accessible.

#### What it does:
- Routes all traffic from `ttb-verifier.yourdomain.com` to CloudFront
- CloudFront provides custom error pages during maintenance/downtime
- CloudFront provides caching and DDoS protection
- CloudFront handles HTTPS termination and forwards to ALB via HTTP

#### What happens if I remove it:
- ❌ Application becomes unreachable at `ttb-verifier.yourdomain.com`
- ❌ Users will get DNS resolution errors
- ❌ GitHub Actions deployments will fail health checks

## DNS Propagation Time

After adding or modifying DNS records:
- **Minimum:** 5 minutes (with low TTL)
- **Typical:** 15-30 minutes
- **Maximum:** Up to 48 hours (rare, usually with high TTL)

### Check DNS propagation:

```bash
# Check validation CNAME
dig _abc123def456.ttb-verifier.yourdomain.com CNAME

# Check application CNAME
dig ttb-verifier.yourdomain.com CNAME

# Check from multiple locations
# https://www.whatsmydns.net/
```

## Troubleshooting

### Certificate validation times out

**Symptoms:** `terragrunt apply` waits 30+ minutes and times out

**Solutions:**
1. Verify CNAME record is correct (no typos)
2. Check DNS propagation with `dig`
3. Ensure record is in correct DNS zone
4. Re-run `terragrunt apply` - it will retry validation

### Application not accessible after DNS added

**Symptoms:** Browser shows DNS resolution error

**Solutions:**
1. Wait longer for DNS propagation (try from different network)
2. Verify CNAME points to CloudFront (not ALB):
   ```bash
   dig ttb-verifier.yourdomain.com CNAME
   # Should show CloudFront domain (e.g., d1bmuzubpqmnvs.cloudfront.net)
   ```
3. Check ALB is healthy:
   ```bash
   aws elbv2 describe-target-health \
     --target-group-arn $(terragrunt output -raw target_group_arn)
   ```
4. Flush local DNS cache:
   ```bash
   # macOS
   sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
   
   # Linux
   sudo systemd-resolve --flush-caches
   
   # Windows
   ipconfig /flushdns
   ```

### Certificate shows as pending in AWS Console

**Symptoms:** Certificate status stuck in "Pending validation"

**Solutions:**
1. Check validation CNAME exists in DNS
2. Verify DNS record uses exact values from ACM
3. Wait up to 30 minutes for AWS to detect the record
4. Check ACM validation status:
   ```bash
   aws acm describe-certificate \
     --certificate-arn $(terragrunt output -raw certificate_arn) \
     --query 'Certificate.DomainValidationOptions'
   ```

## Summary

| DNS Record | Purpose | Required During | Can Remove After? |
|------------|---------|-----------------|-------------------|
| Validation CNAME | Prove domain ownership | Initial cert creation | ✅ Yes (once cert issued) |
| Application CNAME | Route traffic to CloudFront | Always (while app running) | ❌ No (app will be unreachable) |

**Note:** The application CNAME must point to CloudFront distribution, not directly to ALB. CloudFront provides custom error pages, caching, and DDoS protection.

## Reference

- [AWS ACM DNS Validation](https://docs.aws.amazon.com/acm/latest/userguide/dns-validation.html)
- [AWS ACM Certificate Renewal](https://docs.aws.amazon.com/acm/latest/userguide/managed-renewal.html)
