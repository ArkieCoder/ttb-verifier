# TTB Verifier Infrastructure Deployment Guide

## Overview

This infrastructure deploys the TTB Verifier application to AWS with full CI/CD automation using GitHub Actions. The deployment is fully configurable to work with any GitHub organization and AWS account.

## Prerequisites

### Required Tools

1. **Terragrunt** (v0.45+)
   ```bash
   # macOS
   brew install terragrunt
   
   # Linux
   wget https://github.com/gruntwork-io/terragrunt/releases/download/v0.67.0/terragrunt_linux_amd64
   sudo mv terragrunt_linux_amd64 /usr/local/bin/terragrunt
   sudo chmod +x /usr/local/bin/terragrunt
   ```

2. **OpenTofu** (v1.11.5+)
   ```bash
   # macOS
   brew install opentofu
   
   # Linux
   snap install opentofu --classic
   ```

3. **AWS CLI** (v2+)
   ```bash
   # macOS
   brew install awscli
   
   # Linux
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip
   sudo ./aws/install
   ```

4. **GitHub CLI** (`gh`)
   ```bash
   # macOS
   brew install gh
   
   # Linux
   type -p curl >/dev/null || (sudo apt update && sudo apt install curl -y)
   curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
   sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
   sudo apt update
   sudo apt install gh -y
   ```

### AWS Configuration

1. **Configure AWS credentials:**
   ```bash
   aws configure
   # Enter your AWS Access Key ID, Secret Access Key, and default region (us-east-1)
   ```

2. **Verify AWS access:**
   ```bash
   aws sts get-caller-identity
   # Should show your AWS account ID
   ```

### GitHub Configuration

1. **Authenticate with GitHub CLI:**
   ```bash
   gh auth login
   # Follow prompts:
   # - Select GitHub.com
   # - HTTPS protocol
   # - Authenticate via browser or token
   # - Required scopes: repo, admin:public_key, read:org
   ```

2. **Verify authentication:**
   ```bash
   gh auth status
   # Should show "Logged in to github.com"
   ```

## Configuration

### 1. Copy and customize the configuration file

```bash
cd infrastructure
cp terraform.tfvars.example terraform.tfvars
```

### 2. Edit `terraform.tfvars` with your settings

```hcl
# Required: Your GitHub organization or username
github_owner = "YourGitHubOrg"

# Required: Repository name (will be created if doesn't exist)
github_repo_name = "ttb-verifier"

# Required: Full domain name for your deployment
domain_name = "ttb-verifier.yourdomain.com"

# Required: Your AWS account ID
aws_account_id = "123456789012"

# Optional: AWS region (default: us-east-1)
aws_region = "us-east-1"

# Optional: EC2 instance type (default: t3.medium)
# instance_type = "t3.medium"

# Optional: Root volume size in GB (default: 30)
# root_volume_size = 30

# Optional: Environment tag (default: production)
# environment = "production"

# Optional: Additional tags
# tags = {
#   Owner      = "Your Name"
#   CostCenter = "Engineering"
# }
```

### 3. Find your AWS account ID

```bash
aws sts get-caller-identity --query Account --output text
```

## Deployment Steps

### 1. Initialize Terragrunt

```bash
cd infrastructure
export GITHUB_TOKEN=$(gh auth token)
terragrunt init --backend-bootstrap
```

This will:
- Create S3 bucket for Terraform state
- Create DynamoDB table for state locking
- Download required provider plugins

### 2. Review the plan

```bash
terragrunt plan
```

Review the resources that will be created (~17 AWS resources + 3-5 GitHub resources).

### 3. Apply the infrastructure

```bash
terragrunt apply
```

**Important:** This will pause during ACM certificate validation. Follow the prompts to add the DNS CNAME record to your DNS provider.

#### ACM Certificate Validation

When the apply pauses, you'll see output like:

```
ACTION REQUIRED: DNS Validation
=========================================

Add the following CNAME record to your DNS provider:

Record Type: CNAME
Name:  _abc123def456.ttb-verifier.yourdomain.com
Value: _xyz789abc.acm-validations.aws.

=========================================
Waiting for DNS propagation and ACM validation...
```

1. Add the CNAME record to your DNS provider
2. Wait for DNS propagation (5-30 minutes)
3. The script will automatically poll ACM and continue once validated

**Note:** After the certificate is issued, you can remove this validation CNAME record from your DNS. It's only needed during initial certificate creation. ACM will auto-renew without needing the validation record.

### 4. Configure DNS CNAME for your application

After `apply` completes, you'll see instructions to add a CNAME record pointing your domain to the ALB:

```bash
# From the outputs
Hostname: ttb-verifier.yourdomain.com
Type: CNAME
Value: ttb-verifier-alb-XXXXXXXX.us-east-1.elb.amazonaws.com
```

Add this CNAME to your DNS provider. This record should remain in place permanently.

### 5. Monitor EC2 initialization

The EC2 instance will take 15-20 minutes to fully initialize (Docker, Ollama model download):

```bash
# Get instance ID from outputs
export INSTANCE_ID=$(terragrunt output -raw ec2_instance_id)

# Connect via SSM
aws ssm start-session --target $INSTANCE_ID

# Check Docker containers
docker ps

# Check Ollama model
docker exec ttb-ollama ollama list

# Exit SSM session
exit
```

### 6. Verify GitHub configuration

```bash
# Check that secrets were created
gh secret list --repo ${github_owner}/${github_repo_name}

# Should show:
# AWS_REGION
# AWS_ROLE_TO_ASSUME
# EC2_INSTANCE_ID
```

## Post-Deployment

### Push application code to GitHub

The infrastructure creates an empty repository. You need to push your application code:

```bash
# In the application root directory (not infrastructure/)
cd ..

# Initialize git if not already done
git init
git branch -M master

# Add GitHub remote
git remote add origin git@github.com:${github_owner}/${github_repo_name}.git

# Push code
git add .
git commit -m "Initial commit"
git push -u origin master
```

### Test the deployment

After DNS propagates (5-10 minutes):

```bash
# Health check
curl https://ttb-verifier.yourdomain.com/

# API docs
curl https://ttb-verifier.yourdomain.com/docs

# Test label verification
curl -X POST "https://ttb-verifier.yourdomain.com/verify" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/label.jpg"
```

## Troubleshooting

### Certificate validation timeout

If certificate validation times out (>30 minutes):

1. Verify the CNAME record is correct in your DNS
2. Check DNS propagation: `dig _abc123def456.ttb-verifier.yourdomain.com`
3. Re-run `terragrunt apply` - it will continue from where it left off

### GitHub secrets not created

If secrets fail to create due to repository timing issues:

```bash
# Simply re-run apply
terragrunt apply
```

The `depends_on` directives ensure proper ordering on subsequent runs.

### EC2 instance not responding

Check EC2 initialization logs:

```bash
# Connect via SSM
aws ssm start-session --target $(terragrunt output -raw ec2_instance_id)

# Check cloud-init logs
sudo cat /var/log/cloud-init-output.log

# Check Docker
sudo docker ps
sudo docker logs ttb-ollama
sudo docker logs ttb-verifier
```

### Cannot access via SSM

Verify IAM instance profile and SSM agent:

```bash
# Check IAM instance profile
aws ec2 describe-instances --instance-ids $(terragrunt output -raw ec2_instance_id) \
  --query 'Reservations[0].Instances[0].IamInstanceProfile'

# Should show: ttb-ssm-instance-profile
```

## Updating Infrastructure

### Modify configuration

1. Edit `terraform.tfvars` with your changes
2. Run `terragrunt plan` to review changes
3. Run `terragrunt apply` to apply changes

### Update to new instance type

```hcl
# terraform.tfvars
instance_type = "t3.large"
```

```bash
terragrunt apply
```

**Warning:** Changing instance type will cause instance replacement and downtime.

## Destroying Infrastructure

### Full teardown

```bash
cd infrastructure
export GITHUB_TOKEN=$(gh auth token)
terragrunt destroy
```

This will:
- Destroy all AWS resources
- Delete GitHub secrets (repository remains)
- Preserve Terraform state in S3

### Cleanup state backend

If you want to remove the S3 bucket and DynamoDB table:

```bash
aws s3 rm s3://unitedentropy-ttb-tfstate --recursive
aws s3 rb s3://unitedentropy-ttb-tfstate
aws dynamodb delete-table --table-name unitedentropy-ttb-tfstate
```

## Cost Estimate

Monthly costs (us-east-1):
- EC2 t3.medium: ~$30
- EBS 30GB gp3: ~$2.40
- ALB: ~$16
- Data transfer: ~$2
- S3/DynamoDB: ~$0.11
- **Total: ~$54/month**

## Security Considerations

### Secrets Management

- GitHub Actions uses OIDC (no long-lived AWS credentials)
- IAM roles follow least-privilege principle
- GitHub secrets are encrypted at rest
- SSM is used instead of SSH for server access

### Network Security

- EC2 security group only allows traffic from ALB
- ALB security group allows public HTTPS (443) only
- No direct SSH access - use SSM Session Manager

### Certificate Management

- ACM certificates auto-renew before expiration
- No need to maintain validation CNAME after initial creation
- TLS 1.2+ enforced on ALB

## Support

For issues specific to infrastructure deployment:
1. Check troubleshooting section above
2. Review Terragrunt/OpenTofu logs
3. Verify AWS and GitHub permissions

For application issues:
- See main README.md
- Check API documentation at `/docs`
