# ====================================
# Application Load Balancer Security Group
# ====================================

resource "aws_security_group" "alb" {
  name        = "ttb-alb-sg"
  description = "Allow HTTP and HTTPS inbound traffic to ALB"

  # Allow HTTP (will redirect to HTTPS)
  ingress {
    description = "HTTP from internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow HTTPS
  ingress {
    description = "HTTPS from internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow all outbound (for health checks to EC2)
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name      = "ttb-alb-sg"
    Project   = "ttb-verifier"
    ManagedBy = "terragrunt"
  }
}

# ====================================
# EC2 Instance Security Group
# ====================================

resource "aws_security_group" "ec2" {
  name        = "ttb-ec2-sg"
  description = "Allow inbound traffic from ALB only, outbound for Docker pulls"

  # Allow port 8000 from ALB only (health checks + traffic)
  ingress {
    description     = "API traffic from ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  # Allow all outbound (for Docker image pulls, SSM agent, package updates)
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name      = "ttb-ec2-sg"
    Project   = "ttb-verifier"
    ManagedBy = "terragrunt"
  }
}
