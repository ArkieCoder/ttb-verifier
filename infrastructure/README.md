# TTB Verifier Infrastructure

This directory contains OpenTofu/Terraform code managed by Terragrunt to provision AWS infrastructure for the TTB Label Verifier API.

## 📖 Complete Deployment Guide

**👉 For full deployment instructions, see [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)**

The deployment guide includes:
- Detailed prerequisite installation steps
- Complete configuration instructions  
- Step-by-step deployment process
- DNS configuration details
- Security considerations

## Quick Overview

This infrastructure is fully configurable and can be deployed to any AWS account and GitHub organization by editing `terraform.tfvars` and `root.hcl`.

## Two-Layer Architecture

The infrastructure is separated into **two independent layers** with separate Terraform state files:

### Foundation Layer (`foundation/`)
**Protected, long-lived resources deployed once:**
- ACM Certificate (HTTPS/TLS)
- GitHub Repository (code + settings)
- S3 Bucket for Ollama models (performance optimization)
- State: `s3://<tfstate_bucket>/foundation/terraform.tfstate`

**Key Features:**
- All resources have `prevent_destroy = true` lifecycle protection
- Rarely modified after initial deployment
- Preserves critical resources during application layer updates

### Application Layer (`.`)
**Ephemeral resources that can be destroyed/recreated:**
- EC2 instance (Docker host with GPU)
- Application Load Balancer + listeners
- CloudFront distribution (HTTPS, caching, DDoS protection)
- IAM roles and policies
- Security groups
- GitHub Actions secrets
- State: `s3://<tfstate_bucket>/infrastructure/terraform.tfstate`

**Key Features:**
- References foundation via Terraform remote state
- Can be destroyed with `terragrunt destroy` (no targeting required)

### Cross-Layer Communication

Application layer accesses foundation resources via remote state data source:
```hcl
data "terraform_remote_state" "foundation" {
  backend = "s3"
  config = {
    bucket = var.tfstate_bucket
    key    = "foundation/terraform.tfstate"
    region = "us-east-1"
  }
}

# Example usage
locals {
  certificate_arn = data.terraform_remote_state.foundation.outputs.certificate_arn
  s3_bucket_id    = data.terraform_remote_state.foundation.outputs.s3_bucket_id
}
```

## Application Architecture Overview

```
Internet (HTTPS)
    ↓
CloudFront Distribution
  (HTTPS termination, caching, DDoS protection, custom error pages)
    ↓ (HTTP, port 80)
Application Load Balancer
    ↓ (HTTP, port 8000)
EC2 g4dn.2xlarge (Docker, GPU)
    ├─ ttb-verifier container (FastAPI)
    └─ ttb-ollama container (AI OCR)
```

**Key Features:**
- ✅ CloudFront CDN in front of the ALB (HTTPS termination, caching, error pages)
- ✅ HTTPS with auto-renewing ACM certificate
- ✅ SSM-based deployment (no SSH keys)
- ✅ OIDC authentication for GitHub Actions (no long-lived credentials)
- ✅ Subnets configurable via `tfvars` (works with default VPC or any existing VPC)
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
- CloudFront distributions
- ACM certificates
- S3 buckets (for Terragrunt state)
- DynamoDB tables (for state locking)

Recommended: Use `AdministratorAccess` policy for initial setup, then restrict.

### DNS Access

You'll need access to your **DNS provider** to add:
1. CNAME for ACM certificate validation (temporary)
2. CNAME for the application pointing to the **CloudFront** distribution (permanent)

## Deployment Order

### First-Time Setup (Both Layers)

**1. Configure your deployment:**

Edit `terraform.tfvars` with your values (GitHub owner, domain name, AWS account ID, subnet IDs).
Also update the bucket name in `root.hcl` if deploying to a new account.

**2. Deploy Foundation Layer:**
```bash
cd infrastructure/foundation
terragrunt init
terragrunt plan
terragrunt apply
```

**Time:** ~5 minutes  
**Creates:** ACM certificate, GitHub repository, S3 model bucket

**3. Deploy Application Layer:**
```bash
cd infrastructure  # parent directory
terragrunt init
terragrunt plan
terragrunt apply
```

**Time:** ~8-15 minutes (includes EC2 initialization + model download)  
**Creates:** EC2, ALB, CloudFront, IAM roles, security groups, GitHub secrets

### Day-to-Day Operations

**For most infrastructure changes**, you'll only work in the application layer:

```bash
cd infrastructure
terragrunt plan
terragrunt apply
```

**Foundation layer** is only modified when:
- Changing the domain name (ACM certificate)
- Modifying repository settings
- Updating S3 bucket configuration

## Quick Start (Existing Infrastructure)

If the infrastructure already exists and you just need to make changes:

### Step 1: Initialize Terragrunt (Application Layer)

```bash
cd infrastructure  # application layer
terragrunt init
```

**What happens:**
- Connects to existing S3 backend
- Downloads AWS provider plugins
- Generates `backend.tf` and `provider.tf`

**Time:** ~30 seconds

### Step 2: Plan Infrastructure Changes

```bash
terragrunt plan
```

**Review the plan:**
- Shows what will be added, changed, or destroyed
- Includes references to foundation resources via remote state

**Time:** ~1 minute

### Step 3: Apply Infrastructure Changes

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
   - CloudFront distribution created

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

After `terragrunt apply` completes, get the CloudFront distribution domain:

```bash
terragrunt output cloudfront_domain_name
```

**Add CNAME to your DNS provider:**
- **Hostname:** Your application domain (e.g., `ttb-verifier.yourdomain.com`)
- **Type:** CNAME
- **Value:** `<cloudfront-domain from output>` (e.g., `d1bmuzubpqmnvs.cloudfront.net`)
- **TTL:** 300 (or default)

**⚠️ IMPORTANT:** Point to CloudFront, NOT the ALB!
- CloudFront provides custom error pages during downtime
- CloudFront provides caching and DDoS protection
- CloudFront handles HTTPS termination efficiently

**Wait 5-10 minutes for DNS propagation.**

### Step 5: Verify Infrastructure

```bash
# Test DNS resolution (should show CloudFront domain)
nslookup <your-domain>

# Test application (will show error until application deployed)
curl https://<your-domain>/health

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
   **Example:** `arn:aws:iam::<account-id>:role/ttb-github-actions-role`

2. **Name:** `EC2_INSTANCE_ID`  
   **Value:** Output from `ec2_instance_id`  
   **Example:** `i-0abc123def456789`

3. **Name:** `AWS_REGION` (optional, can use workflow env var)  
   **Value:** `us-east-1`

## Resources Created

### Compute
- **EC2 Instance:** g4dn.2xlarge, Ubuntu 22.04, 50GB gp3
- **IAM Instance Profile:** Attached to EC2 for SSM access

### Networking
- **CloudFront Distribution:** HTTPS termination, caching, DDoS protection
- **Application Load Balancer:** Internet-facing, HTTP (CloudFront origin)
- **Target Group:** Routes to EC2 port 8000
- **Security Groups:**
  - ALB: Allow 80/443 from internet
  - EC2: Allow 8000 from ALB only

### Security & Identity
- **IAM Role (EC2):** `ttb-ssm-role` with `AmazonSSMManagedInstanceCore`
- **IAM Role (GitHub Actions):** `ttb-github-actions-role` with SSM SendCommand permissions
- **OIDC Provider:** GitHub Actions authentication (no long-lived credentials)

### SSL/TLS
- **ACM Certificate:** Your configured domain (auto-renewing, DNS validated)

### State Management
- **S3 Bucket:** value of `tfstate_bucket` in `terraform.tfvars` (auto-created by Terragrunt)
- **DynamoDB Table:** same name as the S3 bucket (state locking)

## Configuration Details

### EC2 Instance

**Specifications:**
- Type: g4dn.2xlarge (8 vCPU, 32GB RAM, 1× NVIDIA T4 GPU)
- AMI: Ubuntu 22.04 LTS (latest)
- Storage: 50GB gp3 (for Docker images + Ollama models)
- Network: Configured subnets via `alb_subnet_ids` in `terraform.tfvars`

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
  - Port 80 from 0.0.0.0/0 (HTTP, CloudFront origin protocol)
  - Port 443 from 0.0.0.0/0 (HTTPS)
- Outbound: All (for health checks to EC2)

**EC2 Security Group (`ttb-ec2-sg`):**
- Inbound:
  - Port 8000 from ALB security group only
  - NO SSH access (SSM only)
- Outbound: All (for Docker pulls, SSM agent communication)

### Load Balancer Configuration

**Listener:**
- HTTP (80): Forwards to target group (CloudFront handles HTTPS)

**Target Group Health Checks:**
- Path: `/`
- Protocol: HTTP
- Port: 8000
- Interval: 30 seconds
- Timeout: 5 seconds
- Healthy threshold: 2 consecutive successes
- Unhealthy threshold: 3 consecutive failures

### CloudFront Configuration

CloudFront sits in front of the ALB and is the only public HTTPS entry point:
- HTTPS termination with ACM certificate
- Custom error pages (503 during maintenance)
- Caching for static assets
- DDoS protection via AWS Shield Standard

**DNS:** Your domain CNAME must point to the CloudFront distribution domain, not the ALB.

## Updating Infrastructure

### Making Changes

1. Edit `.tf` files as needed
2. Run `terragrunt plan` to preview changes
3. Run `terragrunt apply` to apply changes

### Common Updates

**Scale instance size:**
```hcl
# In terraform.tfvars
instance_type = "g4dn.4xlarge"
```

**Update ALB subnets:**
```hcl
# In terraform.tfvars
alb_subnet_ids = ["subnet-aaa", "subnet-bbb", "subnet-ccc"]
```

**Update security group rules:**
```hcl
# In security_groups.tf
# Add/modify ingress/egress rules
```

## Destroying Infrastructure

⚠️ **WARNING:** This will delete all resources including the EC2 instance.

```bash
terragrunt destroy
```

**What gets deleted:**
- EC2 instance (application lost!)
- Load balancer
- CloudFront distribution
- Security groups
- IAM roles and policies

**What remains:**
- S3 state bucket (Terragrunt won't delete)
- DynamoDB table (Terragrunt won't delete)
- Foundation layer resources (protected by `prevent_destroy = true`)
- DNS records (manual removal required)

## File Reference

| File | Purpose |
|------|---------|
| `root.hcl` | Terragrunt configuration, backend setup |
| `terraform.tfvars` | Deployment-specific values (owner, domain, subnets, etc.) |
| `ami.tf` | Data source for Ubuntu 22.04 AMI |
| `instance.tf` | EC2 instance resource |
| `instance_init.sh` | User data script (runs on first boot) |
| `roles.tf` | IAM roles for EC2 and GitHub Actions |
| `oidc.tf` | GitHub OIDC provider |
| `security_groups.tf` | Security groups for ALB and EC2 |
| `load_balancers.tf` | ALB and listeners |
| `target_groups.tf` | ALB target group |
| `cloudfront.tf` | CloudFront distribution |
| `remote_foundation.tf` | Remote state reference to foundation layer |
| `outputs.tf` | Output values for GitHub configuration |

## Notes

### Subnet Configuration

ALB subnets must be set in `terraform.tfvars` via `alb_subnet_ids`. They must span at least two Availability Zones. Any existing subnets work — default VPC subnets, or subnets from a custom VPC.

To list your default VPC subnets:
```bash
aws ec2 describe-subnets \
  --filters "Name=default-for-az,Values=true" \
  --query "Subnets[*].{ID:SubnetId,AZ:AvailabilityZone}" \
  --output table
```

### Security Posture

**Encrypted in Transit:**
- ✅ HTTPS enforced via CloudFront (ACM certificate, TLS 1.2+)
- ✅ ALB accepts HTTP from CloudFront only (origin protocol)

**Access Control:**
- ✅ No SSH access (SSM Session Manager only)
- ✅ EC2 port 8000 accessible only from ALB
- ✅ GitHub Actions uses OIDC (no AWS access keys)
- ✅ IAM roles follow least privilege

**Audit & Compliance:**
- ✅ All SSM commands logged to CloudTrail
- ✅ All API requests logged by ALB and CloudFront
- ✅ Infrastructure changes tracked in Terragrunt state

**Known Security Considerations:**
- ⚠️ **Public IP on EC2 Instance:** The EC2 instance may have a public IP depending on your subnet configuration. The security group restricts access (only the ALB can reach port 8000), but removing the public IP requires either a NAT Gateway or VPC endpoints for SSM/Docker Hub access.

## Next Steps

After infrastructure is deployed:

1. ✅ Configure GitHub repository secrets
2. ✅ Create GitHub Actions workflows (see `../.github/workflows/`)
3. ✅ Push code to trigger first deployment
4. ✅ Test HTTPS endpoint via your configured domain

See parent repository's CI/CD documentation for GitHub Actions setup.
