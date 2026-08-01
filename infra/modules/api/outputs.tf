output "api_endpoint" {
  description = "Invoke URL for the HTTP API."
  value       = aws_apigatewayv2_api.http.api_endpoint
}

output "api_id" {
  description = "HTTP API identifier."
  value       = aws_apigatewayv2_api.http.id
}

output "lambda_function_name" {
  description = "Lambda function name."
  value       = aws_lambda_function.api.function_name
}

output "lambda_function_arn" {
  description = "Lambda function ARN."
  value       = aws_lambda_function.api.arn
}

output "lambda_role_arn" {
  description = "IAM role ARN attached to the Lambda function."
  value       = aws_iam_role.lambda.arn
}
