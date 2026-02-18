# EC2 instance running TTB Label Verifier in Docker containers
resource "aws_instance" "ttb" {
  ami           = data.aws_ami.amazon_linux_2023.id
  instance_type = "t3.medium"

  # NOTE: This instance gets a public IP from the default VPC (MapPublicIpOnLaunch=true)
  # While the security group restricts access (only ALB can reach port 8000), this is
  # not ideal for production. See infrastructure/FUTURE_ENHANCEMENTS.md for remediation
  # options (VPC endpoints + NAT Gateway). Acceptable for demo/dev environments.
  # To disable: add `associate_public_ip_address = false` and deploy NAT Gateway.

  # Use default VPC security groups
  security_groups = [
    aws_security_group.ec2.name
  ]

  user_data = <<-EOF
    #!/bin/bash
    export S3_BUCKET="${local.s3_bucket_id}"
    export AWS_ACCOUNT_ID="${var.aws_account_id}"
    export DOMAIN_NAME="${var.domain_name}"
    
    # Source the main init script
    ${file("${path.module}/instance_init.sh")}
  EOF
  
  iam_instance_profile = aws_iam_instance_profile.ssm.name

  # Storage for Docker images + Ollama models + temp space for S3 export
  root_block_device {
    volume_size = 50  # Increased from 30 to allow model export to S3
    volume_type = "gp3"
  }

  tags = {
    Name        = "ttb-verifier"
    Project     = "ttb-verifier"
    Environment = "production"
    ManagedBy   = "terragrunt"
  }
}
