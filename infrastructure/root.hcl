# ---------------------------------------------------------------------------
# Configurable locals — edit these to match your deployment
# ---------------------------------------------------------------------------
locals {
  # Prefix used for the Terraform state S3 bucket and DynamoDB lock table.
  # Must be globally unique (S3 bucket names are global).
  # Example: "myorg-ttb"  →  bucket "myorg-ttb-tfstate"
  tfstate_prefix = get_env("TFSTATE_PREFIX", "my-org-ttb")
}

remote_state {
  backend = "s3"
  
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite"
  }
  
  config = {
    bucket         = "${local.tfstate_prefix}-tfstate"
    key            = "${path_relative_to_include()}/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "${local.tfstate_prefix}-tfstate"
    
    # Terragrunt will auto-create these resources if they don't exist
    skip_bucket_versioning         = false
    skip_bucket_ssencryption       = false
    skip_bucket_root_access        = false
    skip_bucket_enforced_tls       = false
    skip_bucket_public_access_blocking = false
    
    # DynamoDB table configuration for state locking
    dynamodb_table_tags = {
      Name      = "${local.tfstate_prefix}-tfstate-lock"
      Project   = "ttb-verifier"
      ManagedBy = "terragrunt"
    }
  }
}

terraform {
  source = "."
}

generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite"
  contents  = <<EOF
terraform {
  required_version = "~> 1.11.5"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

provider "github" {
  owner = var.github_owner
  # Authentication via GITHUB_TOKEN environment variable
}
EOF
}

# Shared inputs for all child configurations
# These values are inherited by both foundation and application layers.
# All deployment-specific values (github_owner, domain_name, aws_account_id,
# instance_type, etc.) should be set in terraform.tfvars, not here.
inputs = {
  project_name = "ttb-verifier"
  aws_region   = "us-east-1"

  # Pass the state bucket name as a Terraform variable so remote_foundation.tf
  # can reference it without hardcoding.
  tfstate_bucket = "${local.tfstate_prefix}-tfstate"

  # Application-specific defaults (can be overridden in terraform.tfvars)
  environment = "production"
}
