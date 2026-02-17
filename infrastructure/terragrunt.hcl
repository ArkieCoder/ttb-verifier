# Application Layer - Ephemeral Resources
# This layer contains resources that can be destroyed and recreated
# Resources: EC2, ALB, IAM roles, security groups, GitHub secrets

# Include parent configuration for shared settings
include "root" {
  path = "${get_terragrunt_dir()}/root.hcl"
}

# Override source to use current directory
terraform {
  source = "."
}

# Inputs are inherited from parent root.hcl via include
