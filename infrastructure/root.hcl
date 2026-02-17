remote_state {
  backend = "s3"
  
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite"
  }
  
  config = {
    bucket         = "unitedentropy-ttb-tfstate"
    key            = "${path_relative_to_include()}/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "unitedentropy-ttb-tfstate"
    
    # Terragrunt will auto-create these resources if they don't exist
    skip_bucket_versioning         = false
    skip_bucket_ssencryption       = false
    skip_bucket_root_access        = false
    skip_bucket_enforced_tls       = false
    skip_bucket_public_access_blocking = false
    
    # DynamoDB table configuration for state locking
    dynamodb_table_tags = {
      Name      = "unitedentropy-ttb-tfstate-lock"
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
# These values are inherited by both foundation and application layers
inputs = {
  github_owner    = "ArkieCoder"
  github_repo_name = "ttb-verifier"
  project_name    = "ttb-verifier"
  domain_name     = "ttb-verifier.unitedentropy.com"
  aws_region      = "us-east-1"
  aws_account_id  = "253490750467"
  
  # Application-specific defaults (used by application layer)
  instance_type     = "t3.medium"
  root_volume_size  = 50
  environment       = "production"
}
