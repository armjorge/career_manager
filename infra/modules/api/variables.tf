variable "project_name" {
  description = "Project name used for resource naming and tags."
  type        = string
}

variable "environment" {
  description = "Deployment environment (e.g. dev, prod)."
  type        = string
}

variable "lambda_zip_path" {
  description = "Absolute or relative path to the packaged Lambda deployment zip."
  type        = string
}

variable "lambda_handler" {
  description = "Lambda handler entrypoint."
  type        = string
  default     = "app.handler.handler"
}

variable "lambda_runtime" {
  description = "Lambda Python runtime."
  type        = string
  default     = "python3.13"
}

variable "lambda_memory_size" {
  description = "Lambda memory (MB). Start small; scale with metrics."
  type        = number
  default     = 256
}

variable "lambda_timeout" {
  description = "Lambda timeout in seconds."
  type        = number
  default     = 29
}

variable "cors_allow_origins" {
  description = "Allowed CORS origins for the HTTP API."
  type        = list(string)
  default     = ["http://localhost:5173"]
}

variable "enable_cognito_auth" {
  description = "Attach a Cognito JWT authorizer to protected routes."
  type        = bool
  default     = true
}

variable "cognito_user_pool_id" {
  description = "Cognito User Pool ID used by the JWT authorizer."
  type        = string
  default     = ""
}

variable "cognito_user_pool_client_id" {
  description = "Cognito app client ID used as an audience claim."
  type        = string
  default     = ""
}

variable "aws_region" {
  description = "AWS region for Cognito issuer URL construction."
  type        = string
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention for the Lambda function."
  type        = number
  default     = 14
}

variable "environment_variables" {
  description = "Additional environment variables for the Lambda function."
  type        = map(string)
  default     = {}
  sensitive   = true
}

variable "documents_bucket_arn" {
  description = "ARN of the documents S3 bucket (grants Lambda read/write)."
  type        = string
  default     = ""
}

variable "enable_documents_access" {
  description = "Attach S3 documents read/write policy to the Lambda role."
  type        = bool
  default     = false
}

variable "tags" {
  description = "Additional tags applied to all resources."
  type        = map(string)
  default     = {}
}
