locals {
  # dirname(find_in_parent_folders("root.hcl")) resolves to the infrastructure/
  # directory regardless of which child layer (app or foundation) is calling.
  # That is where terraform.tfvars lives.
  tfstate_bucket = regex("tfstate_bucket\\s*=\\s*\"([^\"]+)\"",
    file("${dirname(find_in_parent_folders("root.hcl"))}/terraform.tfvars")
  )[0]
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
# Deployment-specific values live in terraform.tfvars (gitignored).
inputs = {
  project_name     = "ttb-verifier"
  aws_region       = "us-east-1"
  environment      = "production"
  root_volume_size = 50

  # Pass state bucket to Terraform so remote_foundation.tf can reference it.
  tfstate_bucket = local.tfstate_bucket
}
