# TTB Verifier Infrastructure

This directory contains OpenTofu/Terraform code managed by Terragrunt to provision AWS infrastructure for the TTB Label Verifier API.

## 📖 Complete Deployment Guide

**👉 For full deployment instructions, see [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)**

The deployment guide includes:
- Detailed prerequisite installation steps
- Complete configuration instructions  
- Step-by-step deployment process
- DNS configuration details
- Troubleshooting common issues
- Cost estimates and security considerations

## Quick Overview

This infrastructure is fully configurable and can be deployed to any AWS account and GitHub organization by simply editing `terraform.tfvars`.

## Architecture Overview

```
Internet (HTTPS)
    ↓
Application Load Balancer
    ↓ (HTTP, port 8000)
EC2 t3.medium (Docker)
    ├─ ttb-verifier container (FastAPI)
    └─ ttb-ollama container (AI OCR)
```

**Key Features:**
- ✅ HTTPS with auto-renewing ACM certificate
- ✅ SSM-based deployment (no SSH keys)
- ✅ OIDC authentication for GitHub Actions (no long-lived credentials)
- ✅ Default VPC (reuses existing subnets, no custom VPC needed)
- ✅ Automated Ollama model pre-loading during first boot

## Prerequisites

### Required Tools

- **OpenTofu:** v1.11.5+ ([Install](https://opentofu.org/docs/intro/install/))
- **Terragrunt:** Latest version ([Install](https://terragrunt.gruntwork.io/docs/getting-started/install/))
- **AWS CLI:** v2+ configured with credentials ([Install](https://aws.amazon.com/cli/))

### AWS Permissions Required

Your AWS IAM user/role needs permissions to create:
- EC2 instances and security groups
- IAM roles, policies, and OIDC providers
- Application Load Balancers and target groups
- ACM certificates
- S3 buckets (for Terragrunt state)
- DynamoDB tables (for state locking)

Recommended: Use `AdministratorAccess` policy for initial setup, then restrict.

### DNS Access

You'll need access to your **DNS provider** to add:
1. CNAME for ACM certificate validation (temporary)
2. CNAME for the application pointing to the ALB (permanent)

## Quick Start

### Step 1: Initialize Terragrunt

```bash
cd infrastructure
terragrunt init
```

**What happens:**
- Terragrunt auto-creates S3 bucket: `unitedentropy-ttb-tfstate`
- Terragrunt auto-creates DynamoDB table: `unitedentropy-ttb-tfstate`
- Downloads AWS provider plugins
- Generates `backend.tf` and `provider.tf`

**Time:** ~2 minutes

### Step 2: Plan Infrastructure

```bash
terragrunt plan
```

**Review the plan:**
- EC2 t3.medium instance (Amazon Linux 2023, 30GB storage)
- Application Load Balancer (internet-facing)
- ALB target group (port 8000, health checks)
- Security groups (ALB + EC2)
- ACM certificate (pending DNS validation)
- IAM roles (EC2 SSM + GitHub Actions OIDC)
- OIDC provider for GitHub

**Time:** ~1 minute

### Step 3: Apply Infrastructure

```bash
terragrunt apply
```

**What happens:**

1. **Resources Created** (~5 minutes):
   - Security groups
   - IAM roles and policies
   - OIDC provider
   - EC2 instance launched
   - ALB and target group created
   - ACM certificate requested

2. **Interactive Pause** (5-30 minutes):
   - Script outputs DNS validation CNAME record
   - **YOU MUST:** Log into your DNS provider and add the CNAME record
   - Script polls ACM every 30 seconds waiting for validation
   - Continues automatically once certificate is validated

3. **EC2 Initialization** (~15 minutes in background):
   - User data script installs Docker + Docker Compose
   - Pulls Ollama container
   - Downloads llama3.2-vision model (~7.9GB)
   - Creates `/app/` directory and deployment scripts

4. **Completion**:
   - HTTPS listener created (uses validated certificate)
   - EC2 registered with ALB
   - Outputs displayed

**Total Time:** 25-50 minutes (depends on DNS propagation speed)

### Step 4: Configure DNS (Final CNAME)

After `terragrunt apply` completes, get the ALB DNS name:

```bash
terragrunt output alb_dns_name
```

**Add CNAME to your DNS provider:**
- **Hostname:** Your application domain (e.g., `ttb-verifier.yourdomain.com`)
- **Type:** CNAME
- **Value:** `<alb-dns-name from output>` (e.g., `ttb-verifier-alb-123456789.us-east-1.elb.amazonaws.com`)
- **TTL:** 300 (or default)

**Wait 5-10 minutes for DNS propagation.**

### Step 5: Verify Infrastructure

```bash
# Test DNS resolution
nslookup ttb-verifier.unitedentropy.com

# Test ALB (will show error until application deployed)
curl https://ttb-verifier.unitedentropy.com

# Check EC2 via SSM
aws ssm start-session --target $(terragrunt output -raw ec2_instance_id)

# Once in SSM session, verify:
docker ps                  # Should show ollama container
docker-compose -f /app/docker-compose.yml logs
```

### Step 6: Configure GitHub Secrets

Get the outputs:

```bash
terragrunt output ec2_instance_id
terragrunt output github_actions_role_arn
```

**Add to GitHub Repository** (Settings → Secrets and variables → Actions):

1. **Name:** `AWS_ROLE_TO_ASSUME`  
   **Value:** Output from `github_actions_role_arn`  
   **Example:** `arn:aws:iam::253490750467:role/ttb-github-actions-role`

2. **Name:** `EC2_INSTANCE_ID`  
   **Value:** Output from `ec2_instance_id`  
   **Example:** `i-0abc123def456789`

3. **Name:** `AWS_REGION` (optional, can use workflow env var)  
   **Value:** `us-east-1`

## Resources Created

### Compute
- **EC2 Instance:** t3.medium, Amazon Linux 2023, 30GB gp3
- **IAM Instance Profile:** Attached to EC2 for SSM access

### Networking
- **Application Load Balancer:** Internet-facing, HTTPS + HTTP
- **Target Group:** Routes to EC2 port 8000
- **Security Groups:**
  - ALB: Allow 80/443 from internet
  - EC2: Allow 8000 from ALB only

### Security & Identity
- **IAM Role (EC2):** `ttb-ssm-role` with `AmazonSSMManagedInstanceCore`
- **IAM Role (GitHub Actions):** `ttb-github-actions-role` with SSM SendCommand permissions
- **OIDC Provider:** GitHub Actions authentication (no long-lived credentials)

### SSL/TLS
- **ACM Certificate:** `ttb-verifier.unitedentropy.com` (auto-renewing, DNS validated)

### State Management
- **S3 Bucket:** `unitedentropy-ttb-tfstate` (auto-created by Terragrunt)
- **DynamoDB Table:** `unitedentropy-ttb-tfstate` (state locking)

## Configuration Details

### EC2 Instance

**Specifications:**
- Type: t3.medium (2 vCPU, 4GB RAM)
- AMI: Amazon Linux 2023 (latest)
- Storage: 30GB gp3 (for Docker images + Ollama models)
- Network: Default VPC, public subnet (reuses existing infrastructure)

**Installed Software** (via user_data):
- Docker Engine
- Docker Compose
- Amazon SSM Agent (pre-installed, verified)
- Pre-pulled: ollama/ollama:latest
- Pre-downloaded: llama3.2-vision model (~7.9GB)

**Directory Structure:**
```
/app/
├── docker-compose.yml    # Production compose config
└── deploy.sh             # Deployment script called by GitHub Actions
```

### Security Groups

**ALB Security Group (`ttb-alb-sg`):**
- Inbound:
  - Port 80 from 0.0.0.0/0 (HTTP, redirects to HTTPS)
  - Port 443 from 0.0.0.0/0 (HTTPS)
- Outbound: All (for health checks to EC2)

**EC2 Security Group (`ttb-ec2-sg`):**
- Inbound:
  - Port 8000 from ALB security group only
  - NO SSH access (SSM only)
- Outbound: All (for Docker pulls, SSM agent communication)

### Load Balancer Configuration

**Listeners:**
- HTTP (80): Redirects to HTTPS (301)
- HTTPS (443): Forwards to target group (port 8000)

**Target Group Health Checks:**
- Path: `/`
- Protocol: HTTP
- Port: 8000
- Interval: 30 seconds
- Timeout: 5 seconds
- Healthy threshold: 2 consecutive successes
- Unhealthy threshold: 3 consecutive failures

**SSL Policy:** `ELBSecurityPolicy-TLS13-1-2-2021-06` (TLS 1.2+)

## Cost Estimate

| Resource | Monthly Cost |
|----------|--------------|
| EC2 t3.medium (730 hours) | $30.37 |
| EBS gp3 (30GB) | $2.40 |
| Application Load Balancer | $16.20 |
| ALB LCU (low traffic) | ~$3.00 |
| Data transfer | ~$2.00 |
| S3 state storage | $0.01 |
| DynamoDB state locking | $0.10 |
| ACM Certificate | **FREE** |
| **Total** | **~$54/month** |

## Updating Infrastructure

### Making Changes

1. Edit `.tf` files as needed
2. Run `terragrunt plan` to preview changes
3. Run `terragrunt apply` to apply changes

### Common Updates

**Scale instance size:**
```hcl
# In instance.tf
instance_type = "t3.large"  # Change from t3.medium
```

**Update security group rules:**
```hcl
# In security_groups.tf
# Add/modify ingress/egress rules
```

**Change health check settings:**
```hcl
# In target_groups.tf
# Modify health_check block
```

## Destroying Infrastructure

⚠️ **WARNING:** This will delete all resources including the EC2 instance.

```bash
terragrunt destroy
```

**What gets deleted:**
- EC2 instance (application lost!)
- Load balancer
- Security groups
- IAM roles and policies
- ACM certificate

**What remains:**
- S3 state bucket (Terragrunt won't delete)
- DynamoDB table (Terragrunt won't delete)
- DNS records (manual removal required)

## Troubleshooting

### Certificate Validation Hangs

**Symptom:** `terragrunt apply` pauses at certificate validation for >30 minutes

**Cause:** DNS record not added or incorrect

**Solution:**
1. Check the output for the exact CNAME record
2. Verify record added correctly in your DNS provider:
   ```bash
   dig _<random>.yourdomain.com CNAME
   ```
3. Wait for DNS propagation (can take up to 30 mins)
4. If timeout occurs, just run `terragrunt apply` again

### EC2 Not Appearing in SSM

**Symptom:** `aws ssm describe-instance-information` doesn't show instance

**Causes:**
- SSM Agent not running
- IAM instance profile not attached
- Network connectivity issues

**Solution:**
```bash
# Check instance status
aws ec2 describe-instances --instance-ids <instance-id>

# Check IAM role attached
aws ec2 describe-iam-instance-profile-associations

# Check user data logs (via EC2 console → Instance → Actions → Monitor → Get system log)
```

### Health Checks Failing

**Symptom:** ALB target shows "unhealthy"

**Causes:**
- Docker containers not started
- Port 8000 not accessible
- Application returning non-200 status

**Solution:**
```bash
# SSH via SSM
aws ssm start-session --target <instance-id>

# Check Docker status
docker ps
docker-compose -f /app/docker-compose.yml logs

# Check port listening
curl http://localhost:8000

# Check security group rules
```

### Terraform State Lock

**Symptom:** `Error: Error acquiring the state lock`

**Cause:** Previous `terragrunt apply` was interrupted

**Solution:**
```bash
# Force unlock (use lock ID from error message)
terragrunt force-unlock <lock-id>
```

## File Reference

| File | Purpose |
|------|---------|
| `terragrunt.hcl` | Terragrunt configuration, backend setup |
| `ami.tf` | Data source for Amazon Linux 2023 AMI |
| `instance.tf` | EC2 instance resource |
| `instance_init.sh` | User data script (runs on first boot) |
| `roles.tf` | IAM roles for EC2 and GitHub Actions |
| `oidc.tf` | GitHub OIDC provider |
| `security_groups.tf` | Security groups for ALB and EC2 |
| `load_balancers.tf` | ALB and listeners |
| `target_groups.tf` | ALB target group |
| `certificates.tf` | ACM certificate and validation logic |
| `outputs.tf` | Output values for GitHub configuration |

## Notes

### Default VPC Usage

This infrastructure uses the **default VPC** in us-east-1 with existing subnets. No custom VPC, NAT Gateway, or private subnets are created, saving ~$32/month compared to a fully private architecture.

**Subnet IDs** (hardcoded in `load_balancers.tf`):
- subnet-087c34ce6b854b207 (us-east-1a)
- subnet-067659fddc18e6d08 (us-east-1b)
- subnet-0964715de1feee340 (us-east-1c)
- subnet-0e47260fdbba6e0f6 (us-east-1d)
- subnet-08925a7ee9f27c57b (us-east-1e)
- subnet-0b98b5770d8be8909 (us-east-1f)

These subnets are from the AWS default VPC and are reused to avoid infrastructure overhead. The EC2 instance is in a public subnet but secured via security groups (only ALB can access port 8000).

### Security Posture

**Encrypted in Transit:**
- ✅ HTTPS enforced (HTTP redirects to HTTPS)
- ✅ ACM certificate with TLS 1.2+

**Access Control:**
- ✅ No SSH access (SSM Session Manager only)
- ✅ EC2 port 8000 accessible only from ALB
- ✅ GitHub Actions uses OIDC (no AWS access keys)
- ✅ IAM roles follow least privilege

**Audit & Compliance:**
- ✅ All SSM commands logged to CloudTrail
- ✅ All API requests logged by ALB
- ✅ Infrastructure changes tracked in Terragrunt state

## Next Steps

After infrastructure is deployed:

1. ✅ Configure GitHub repository secrets
2. ✅ Create GitHub Actions workflows (see `../.github/workflows/`)
3. ✅ Push code to trigger first deployment
4. ✅ Test HTTPS endpoint: https://ttb-verifier.unitedentropy.com

See parent repository's CI/CD documentation for GitHub Actions setup.
