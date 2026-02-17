# ====================================
# EC2 Instance IAM Role (for SSM access)
# ====================================

resource "aws_iam_role" "ssm" {
  name = "ttb-ssm-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })

  tags = {
    Name      = "ttb-ssm-role"
    Project   = "ttb-verifier"
    ManagedBy = "terragrunt"
  }
}

# Attach AWS managed policy for SSM
resource "aws_iam_role_policy_attachment" "ssm_policy" {
  role       = aws_iam_role.ssm.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# EC2 Instance Profile (required to attach IAM role to EC2)
resource "aws_iam_instance_profile" "ssm" {
  name = "ttb-ssm-instance-profile"
  role = aws_iam_role.ssm.name

  tags = {
    Name      = "ttb-ssm-instance-profile"
    Project   = "ttb-verifier"
    ManagedBy = "terragrunt"
  }
}

# ====================================
# GitHub Actions IAM Role (via OIDC)
# ====================================

resource "aws_iam_role" "github_actions" {
  name = "ttb-github-actions-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = {
        Federated = data.aws_iam_openid_connect_provider.github.arn
      },
      Action = "sts:AssumeRoleWithWebIdentity",
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        },
        StringLike = {
          # Only allow from specified repo, master branch
          "token.actions.githubusercontent.com:sub" = "repo:${var.github_owner}/${var.github_repo_name}:ref:refs/heads/master"
        }
      }
    }]
  })

  tags = {
    Name      = "ttb-github-actions-role"
    Project   = "ttb-verifier"
    ManagedBy = "terragrunt"
  }
}

# Custom policy for GitHub Actions to trigger SSM commands
resource "aws_iam_policy" "github_actions_ssm" {
  name        = "ttb-github-actions-ssm-policy"
  description = "Allow GitHub Actions to trigger SSM commands on TTB verifier EC2 instance"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "SSMSendCommand",
        Effect = "Allow",
        Action = [
          "ssm:SendCommand"
        ],
        Resource = [
          # Limit to specific EC2 instance
          "arn:aws:ec2:${var.aws_region}:${var.aws_account_id}:instance/${aws_instance.ttb.id}",
          # Allow using AWS-RunShellScript document
          "arn:aws:ssm:${var.aws_region}::document/AWS-RunShellScript"
        ]
      },
      {
        Sid    = "SSMGetCommandStatus",
        Effect = "Allow",
        Action = [
          "ssm:GetCommandInvocation",
          "ssm:ListCommandInvocations"
        ],
        Resource = "*"
      },
      {
        Sid      = "SSMDescribeInstance",
        Effect   = "Allow",
        Action   = "ssm:DescribeInstanceInformation",
        Resource = "*"
      }
    ]
  })

  tags = {
    Name      = "ttb-github-actions-ssm-policy"
    Project   = "ttb-verifier"
    ManagedBy = "terragrunt"
  }
}

# Attach custom policy to GitHub Actions role
resource "aws_iam_role_policy_attachment" "github_actions_ssm" {
  role       = aws_iam_role.github_actions.name
  policy_arn = aws_iam_policy.github_actions_ssm.arn
}
