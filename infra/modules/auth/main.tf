/**
 * AWS Cognito user pool + public SPA app client.
 * No persistent application database for users — Cognito is the identity store.
 *
 * Hosted UI / OAuth (authorization code + PKCE) is opt-in via enable_hosted_ui.
 * Google federation is opt-in when google_client_id and google_client_secret are set.
 */

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

data "aws_region" "current" {}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
  tags = merge(var.tags, {
    Project     = var.project_name
    Environment = var.environment
    Module      = "auth"
  })

  google_enabled = var.enable_hosted_ui && var.google_client_id != "" && var.google_client_secret != ""

  identity_providers = concat(
    ["COGNITO"],
    local.google_enabled ? ["Google"] : [],
  )

  # Cognito rejects domain prefixes containing the reserved word "aws".
  hosted_ui_domain_prefix = "${replace(var.project_name, "aws-", "")}-${var.environment}-auth"
  hosted_ui_base_url      = var.enable_hosted_ui ? "https://${local.hosted_ui_domain_prefix}.auth.${data.aws_region.current.region}.amazoncognito.com" : ""
}

resource "aws_cognito_user_pool" "main" {
  name = "${local.name_prefix}-users"

  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  password_policy {
    minimum_length                   = var.password_minimum_length
    require_lowercase                = true
    require_numbers                  = true
    require_symbols                  = true
    require_uppercase                = true
    temporary_password_validity_days = 7
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  schema {
    name                = "email"
    attribute_data_type = "String"
    mutable             = true
    required            = true

    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }

  tags = local.tags
}

resource "aws_cognito_identity_provider" "google" {
  count = local.google_enabled ? 1 : 0

  user_pool_id  = aws_cognito_user_pool.main.id
  provider_name = "Google"
  provider_type = "Google"

  provider_details = {
    client_id        = var.google_client_id
    client_secret    = var.google_client_secret
    authorize_scopes = "profile email openid"
  }

  attribute_mapping = {
    email    = "email"
    username = "sub"
  }
}

resource "aws_cognito_user_pool_client" "spa" {
  name         = "${local.name_prefix}-spa"
  user_pool_id = aws_cognito_user_pool.main.id

  generate_secret               = false
  prevent_user_existence_errors = "ENABLED"
  enable_token_revocation       = true

  # SRP is the default SPA path; OAuth/hosted UI is opt-in via enable_hosted_ui.
  allowed_oauth_flows_user_pool_client = var.enable_hosted_ui
  allowed_oauth_flows                  = var.enable_hosted_ui ? ["code"] : []
  allowed_oauth_scopes                 = var.enable_hosted_ui ? ["email", "openid", "profile"] : []
  callback_urls                        = var.enable_hosted_ui ? var.callback_urls : []
  logout_urls                          = var.enable_hosted_ui ? var.logout_urls : []
  supported_identity_providers         = var.enable_hosted_ui ? local.identity_providers : null

  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_PASSWORD_AUTH",
  ]

  access_token_validity  = 1
  id_token_validity      = 1
  refresh_token_validity = 30

  token_validity_units {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }

  depends_on = [aws_cognito_identity_provider.google]
}

resource "aws_cognito_user_pool_domain" "main" {
  count = var.enable_hosted_ui ? 1 : 0

  domain       = local.hosted_ui_domain_prefix
  user_pool_id = aws_cognito_user_pool.main.id
}
