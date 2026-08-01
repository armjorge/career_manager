variable "project_name" {
  description = "Project name used for resource naming and tags."
  type        = string
}

variable "environment" {
  description = "Deployment environment (e.g. dev, prod)."
  type        = string
}

variable "callback_urls" {
  description = "Allowed OAuth callback URLs for the SPA app client."
  type        = list(string)
  default     = ["http://localhost:5173/auth/callback"]
}

variable "logout_urls" {
  description = "Allowed OAuth logout URLs for the SPA app client."
  type        = list(string)
  default     = ["http://localhost:5173/"]
}

variable "enable_hosted_ui" {
  description = "Create a Cognito hosted UI domain and enable the authorization-code OAuth flow (required for social IdPs)."
  type        = bool
  default     = false
}

variable "google_client_id" {
  description = "Google OAuth client ID. Leave empty to skip the Google identity provider."
  type        = string
  default     = ""
}

variable "google_client_secret" {
  description = "Google OAuth client secret. Leave empty to skip the Google identity provider."
  type        = string
  default     = ""
  sensitive   = true
}

variable "password_minimum_length" {
  description = "Minimum password length for the user pool."
  type        = number
  default     = 12
}

variable "tags" {
  description = "Additional tags applied to all resources."
  type        = map(string)
  default     = {}
}
