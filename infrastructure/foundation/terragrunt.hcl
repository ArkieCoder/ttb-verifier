# Foundation Layer - Protected Resources
# This layer contains long-lived resources with prevent_destroy lifecycle rules
# Resources: ACM certificate, GitHub repository, S3 model bucket

# Include parent configuration for shared settings
include "root" {
  path = find_in_parent_folders("root.hcl")
}

# Override source to use current directory
terraform {
  source = "."
}

# Inputs are inherited from parent root.hcl via include
