# Remote state data source for foundation layer
# Allows application layer to reference protected resources

data "terraform_remote_state" "foundation" {
  backend = "s3"
  
  config = {
    bucket = var.tfstate_bucket
    key    = "foundation/terraform.tfstate"
    region = var.aws_region
  }
}

# Local values for easier reference throughout the application layer
locals {
  # ACM Certificate outputs
  certificate_arn    = data.terraform_remote_state.foundation.outputs.certificate_arn
  certificate_domain = data.terraform_remote_state.foundation.outputs.certificate_domain
  
  # S3 Bucket outputs
  s3_bucket_id  = data.terraform_remote_state.foundation.outputs.s3_bucket_id
  s3_bucket_arn = data.terraform_remote_state.foundation.outputs.s3_bucket_arn
  
  # GitHub Repository outputs
  repository_name      = data.terraform_remote_state.foundation.outputs.repository_name
  repository_full_name = data.terraform_remote_state.foundation.outputs.repository_full_name
}
