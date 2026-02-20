# Application Load Balancer
resource "aws_lb" "ttb" {
  name               = "ttb-verifier-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]

  # Increase idle timeout for Ollama vision processing (can take 60-120 seconds)
  idle_timeout = 180

  # Subnet IDs are supplied via tfvars (alb_subnet_ids).
  # Must span at least two Availability Zones.
  subnets = var.alb_subnet_ids

  tags = {
    Name      = "ttb-verifier-alb"
    Project   = "ttb-verifier"
    ManagedBy = "terragrunt"
  }
}

# HTTP Listener (forwards to target group for CloudFront origin)
# CloudFront handles HTTPS termination and connects to ALB via HTTP
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.ttb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ttb.arn
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
  certificate_arn   = local.certificate_arn

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
