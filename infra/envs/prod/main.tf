/**
 * Prod environment composition — same modules as dev with stricter defaults.
 *
 * CloudFront site URL is merged into API CORS and Cognito callback/logout URLs
 * automatically when enable_frontend = true.
 */

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }

  # Uncomment and configure for remote state (recommended for teams/CI):
  # backend "s3" {
  #   bucket         = "YOUR_TF_STATE_BUCKET"
  #   key            = "career-app/prod/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "YOUR_TF_LOCK_TABLE"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = merge(var.tags, {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "opentofu"
    })
  }
}

module "frontend" {
  count  = var.enable_frontend ? 1 : 0
  source = "../../modules/frontend"

  project_name = var.project_name
  environment  = var.environment
}

locals {
  frontend_site_url = try(module.frontend[0].site_url, null)

  cors_allow_origins = distinct(concat(
    var.cors_allow_origins,
    local.frontend_site_url != null ? [local.frontend_site_url] : [],
  ))

  cognito_callback_urls = distinct(concat(
    var.cognito_callback_urls,
    local.frontend_site_url != null ? ["${local.frontend_site_url}/auth/callback"] : [],
  ))

  cognito_logout_urls = distinct(concat(
    var.cognito_logout_urls,
    local.frontend_site_url != null ? ["${local.frontend_site_url}/"] : [],
  ))
}

module "auth" {
  count  = var.enable_auth ? 1 : 0
  source = "../../modules/auth"

  project_name         = var.project_name
  environment          = var.environment
  callback_urls        = local.cognito_callback_urls
  logout_urls          = local.cognito_logout_urls
  enable_hosted_ui     = var.enable_hosted_ui
  google_client_id     = var.google_client_id
  google_client_secret = var.google_client_secret
}

module "documents" {
  count  = var.enable_documents ? 1 : 0
  source = "../../modules/documents"

  project_name  = var.project_name
  environment   = var.environment
  force_destroy = false
}

module "api" {
  count  = var.enable_api ? 1 : 0
  source = "../../modules/api"

  project_name                = var.project_name
  environment                 = var.environment
  aws_region                  = var.aws_region
  lambda_zip_path             = var.lambda_zip_path
  cors_allow_origins          = local.cors_allow_origins
  enable_cognito_auth         = var.enable_cognito_auth_on_api && var.enable_auth
  cognito_user_pool_id        = try(module.auth[0].user_pool_id, "")
  cognito_user_pool_client_id = try(module.auth[0].user_pool_client_id, "")
  documents_bucket_arn        = try(module.documents[0].bucket_arn, "")
  enable_documents_access     = var.enable_documents

  environment_variables = merge(
    {
      CORS_ALLOW_ORIGINS   = join(",", local.cors_allow_origins)
      COGNITO_USER_POOL_ID = try(module.auth[0].user_pool_id, "")
      COGNITO_CLIENT_ID    = try(module.auth[0].user_pool_client_id, "")
    },
    var.db_postgresql != "" ? { DB_POSTGRESQL = var.db_postgresql } : {},
    length(module.documents) > 0 ? { DOCUMENTS_S3_BUCKET = module.documents[0].bucket_name } : {},
  )
}
