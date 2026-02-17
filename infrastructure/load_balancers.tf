# Application Load Balancer
resource "aws_lb" "ttb" {
  name               = "ttb-verifier-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]

  # Using default VPC subnets across multiple AZs
  # Note: These are existing subnets, no VPC infrastructure code needed
  subnets = [
    "subnet-087c34ce6b854b207", # us-east-1a
    "subnet-067659fddc18e6d08", # us-east-1b
    "subnet-0964715de1feee340", # us-east-1c
    "subnet-0e47260fdbba6e0f6", # us-east-1d
    "subnet-08925a7ee9f27c57b", # us-east-1e
    "subnet-0b98b5770d8be8909"  # us-east-1f
  ]

  tags = {
    Name      = "ttb-verifier-alb"
    Project   = "ttb-verifier"
    ManagedBy = "terragrunt"
  }
}

# HTTP Listener (redirects to HTTPS)
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.ttb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }

  tags = {
    Name      = "ttb-http-listener"
    Project   = "ttb-verifier"
    ManagedBy = "terragrunt"
  }
}

# HTTPS Listener (requires validated certificate)
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.ttb.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate.ttb.arn

  # Wait for certificate validation before creating listener
  depends_on = [terraform_data.wait_for_certificate_validation]

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ttb.arn
  }

  tags = {
    Name      = "ttb-https-listener"
    Project   = "ttb-verifier"
    ManagedBy = "terragrunt"
  }
}
