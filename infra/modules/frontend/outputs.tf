output "bucket_name" {
  description = "S3 bucket name for frontend static assets."
  value       = aws_s3_bucket.site.bucket
}

output "bucket_arn" {
  description = "S3 bucket ARN."
  value       = aws_s3_bucket.site.arn
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID (use for cache invalidation)."
  value       = aws_cloudfront_distribution.site.id
}

output "cloudfront_domain_name" {
  description = "CloudFront domain name for the site."
  value       = aws_cloudfront_distribution.site.domain_name
}

output "site_url" {
  description = "HTTPS URL for the deployed frontend."
  value       = "https://${aws_cloudfront_distribution.site.domain_name}"
}
