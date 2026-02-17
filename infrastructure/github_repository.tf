# GitHub Repository for TTB Verifier
resource "github_repository" "ttb_verifier" {
  name        = var.github_repo_name
  description = "AI-powered alcohol beverage label verification system for U.S. Treasury Department TTB"
  visibility  = "public"

  has_issues      = true
  has_wiki        = false
  has_projects    = false
  has_discussions = false

  allow_merge_commit     = true
  allow_squash_merge     = true
  allow_rebase_merge     = true
  allow_auto_merge       = false
  delete_branch_on_merge = true

  # Security settings
  vulnerability_alerts   = true
  archive_on_destroy     = false
  
  # Default branch protection will be handled separately
  auto_init = false  # We'll push code manually

  topics = [
    "ai",
    "label-verification",
    "ttb",
    "treasury",
    "fastapi",
    "docker",
    "terraform"
  ]
}

# Branch protection for master branch
resource "github_branch_protection" "master" {
  repository_id = github_repository.ttb_verifier.node_id
  pattern       = "master"

  required_pull_request_reviews {
    required_approving_review_count = 0  # Allow self-merge for solo developer
    dismiss_stale_reviews           = true
  }

  required_status_checks {
    strict = true
    contexts = [
      "test"  # Must pass tests before merge
    ]
  }

  enforce_admins = false  # Allow admin override if needed
}
