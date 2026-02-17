# EC2 instance running TTB Label Verifier in Docker containers
resource "aws_instance" "ttb" {
  ami           = data.aws_ami.amazon_linux_2023.id
  instance_type = "t3.medium"

  # Use default VPC security groups
  security_groups = [
    aws_security_group.ec2.name
  ]

  user_data            = file("${path.module}/instance_init.sh")
  iam_instance_profile = aws_iam_instance_profile.ssm.name

  # Storage for Docker images + Ollama models
  root_block_device {
    volume_size = 30
    volume_type = "gp3"
  }

  tags = {
    Name        = "ttb-verifier"
    Project     = "ttb-verifier"
    Environment = "production"
    ManagedBy   = "terragrunt"
  }
}
