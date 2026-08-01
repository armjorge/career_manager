output "frontend_site_url" {
  description = "CloudFront URL for the static frontend."
  value       = try(module.frontend[0].site_url, null)
}

output "frontend_bucket_name" {
  description = "S3 bucket for frontend assets."
  value       = try(module.frontend[0].bucket_name, null)
}

output "frontend_distribution_id" {
  description = "CloudFront distribution ID."
  value       = try(module.frontend[0].cloudfront_distribution_id, null)
}

output "api_endpoint" {
  description = "HTTP API invoke URL."
  value       = try(module.api[0].api_endpoint, null)
}

output "cognito_user_pool_id" {
  description = "Cognito User Pool ID for the frontend .env."
  value       = try(module.auth[0].user_pool_id, null)
}

output "cognito_user_pool_client_id" {
  description = "Cognito SPA client ID for the frontend .env."
  value       = try(module.auth[0].user_pool_client_id, null)
}

output "cognito_hosted_ui_domain" {
  description = "Cognito hosted UI domain prefix (if enabled)."
  value       = try(module.auth[0].hosted_ui_domain, null)
}

output "cognito_hosted_ui_base_url" {
  description = "Full Cognito hosted UI base URL (if enabled)."
  value       = try(module.auth[0].hosted_ui_base_url, null)
}

output "cognito_google_enabled" {
  description = "Whether Google sign-in is configured on the user pool."
  value       = try(module.auth[0].google_enabled, false)
}

output "documents_bucket_name" {
  description = "S3 bucket for user document templates and attachments."
  value       = try(module.documents[0].bucket_name, null)
}
