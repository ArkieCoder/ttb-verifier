# EC2 instance running TTB Label Verifier in Docker containers
resource "aws_instance" "ttb" {
  ami           = data.aws_ami.amazon_linux_2023.id
  instance_type = "t3.medium"

  # Use default VPC security groups
  security_groups = [
    aws_security_group.ec2.name
  ]

  user_data = <<-EOF
    #!/bin/bash
    export S3_BUCKET="${aws_s3_bucket.ollama_models.id}"
    export AWS_ACCOUNT_ID="${var.aws_account_id}"
    
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
