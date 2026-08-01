output "user_pool_id" {
  description = "Cognito User Pool ID."
  value       = aws_cognito_user_pool.main.id
}

output "user_pool_arn" {
  description = "Cognito User Pool ARN."
  value       = aws_cognito_user_pool.main.arn
}

output "user_pool_endpoint" {
  description = "Cognito User Pool issuer endpoint host."
  value       = aws_cognito_user_pool.main.endpoint
}

output "user_pool_client_id" {
  description = "Cognito SPA app client ID."
  value       = aws_cognito_user_pool_client.spa.id
}

output "hosted_ui_domain" {
  description = "Cognito hosted UI domain prefix (empty when disabled)."
  value       = try(aws_cognito_user_pool_domain.main[0].domain, "")
}

output "hosted_ui_base_url" {
  description = "Full Cognito hosted UI base URL (empty when disabled)."
  value       = local.hosted_ui_base_url
}

output "google_enabled" {
  description = "Whether the Google identity provider is configured."
  value       = nonsensitive(local.google_enabled)
}
