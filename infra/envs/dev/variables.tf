variable "aws_region" {
  description = "AWS region for all resources."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Short project slug used in resource names."
  type        = string
  default     = "career-app"
}

variable "db_postgresql" {
  description = "Neon pooled PostgreSQL connection string for the API Lambda."
  type        = string
  sensitive   = true
  default     = ""
}

variable "enable_documents" {
  description = "Toggle documents S3 bucket module."
  type        = bool
  default     = true
}

variable "environment" {
  description = "Environment name."
  type        = string
  default     = "dev"
}

variable "enable_frontend" {
  description = "Toggle S3 + CloudFront frontend module."
  type        = bool
  default     = true
}

variable "enable_auth" {
  description = "Toggle Cognito auth module."
  type        = bool
  default     = true
}

variable "enable_api" {
  description = "Toggle API Gateway + Lambda module."
  type        = bool
  default     = true
}

variable "enable_cognito_auth_on_api" {
  description = "Require Cognito JWT on API proxy routes."
  type        = bool
  default     = true
}

variable "enable_hosted_ui" {
  description = "Create a Cognito hosted UI domain and enable OAuth (required for Google sign-in)."
  type        = bool
  default     = false
}

variable "google_client_id" {
  description = "Google OAuth client ID for Cognito federation (optional)."
  type        = string
  default     = ""
}

variable "google_client_secret" {
  description = "Google OAuth client secret for Cognito federation (optional)."
  type        = string
  default     = ""
  sensitive   = true
}

variable "lambda_zip_path" {
  description = "Path to the packaged Lambda zip (relative to this env directory)."
  type        = string
  default     = "../../../backend/dist/lambda.zip"
}

variable "cors_allow_origins" {
  description = "Extra CORS origins (localhost / custom domains). CloudFront site URL is appended automatically when the frontend module is enabled."
  type        = list(string)
  default     = ["http://localhost:5173"]
}

variable "cognito_callback_urls" {
  description = "Extra Cognito OAuth callback URLs. CloudFront /auth/callback is appended automatically when the frontend module is enabled."
  type        = list(string)
  default     = ["http://localhost:5173/auth/callback"]
}

variable "cognito_logout_urls" {
  description = "Extra Cognito logout URLs. CloudFront origin is appended automatically when the frontend module is enabled."
  type        = list(string)
  default     = ["http://localhost:5173/"]
}

variable "tags" {
  description = "Extra tags applied to all modules."
  type        = map(string)
  default     = {}
}
