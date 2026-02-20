locals {
  # get_repo_root() finds the .git directory, giving a stable absolute path
  # that works even when Terragrunt evaluates this file from inside the cache.
  _tfvars = file("${get_repo_root()}/infrastructure/terraform.tfvars")

  tfstate_bucket   = regex("tfstate_bucket\\s*=\\s*\"([^\"]+)\"",   local._tfvars)[0]
  github_owner     = regex("github_owner\\s*=\\s*\"([^\"]+)\"",     local._tfvars)[0]
  github_repo_name = regex("github_repo_name\\s*=\\s*\"([^\"]+)\"", local._tfvars)[0]
  domain_name      = regex("domain_name\\s*=\\s*\"([^\"]+)\"",      local._tfvars)[0]
  aws_account_id   = regex("aws_account_id\\s*=\\s*\"([^\"]+)\"",   local._tfvars)[0]
  aws_region       = regex("aws_region\\s*=\\s*\"([^\"]+)\"",       local._tfvars)[0]
  instance_type    = regex("instance_type\\s*=\\s*\"([^\"]+)\"",    local._tfvars)[0]
}

remote_state {
  backend = "s3"

  generate = {
    path      = "backend.tf"
    if_exists = "overwrite"
  }

  config = {
    bucket         = local.tfstate_bucket
    key            = "${path_relative_to_include()}/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = local.tfstate_bucket

    # Terragrunt will auto-create these resources if they don't exist
    skip_bucket_versioning             = false
    skip_bucket_ssencryption           = false
    skip_bucket_root_access            = false
    skip_bucket_enforced_tls           = false
    skip_bucket_public_access_blocking = false

    dynamodb_table_tags = {
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

# Shared inputs for all child configurations.
# All deployment-specific values are read from terraform.tfvars (gitignored)
# via the locals block above — nothing is hardcoded here.
inputs = {
  project_name     = "ttb-verifier"
  environment      = "production"
  root_volume_size = 50

  # From terraform.tfvars
  github_owner     = local.github_owner
  github_repo_name = local.github_repo_name
  domain_name      = local.domain_name
  aws_account_id   = local.aws_account_id
  aws_region       = local.aws_region
  instance_type    = local.instance_type
  tfstate_bucket   = local.tfstate_bucket
}
