variable "project_name" {
  description = "Project name used for resource naming and tags."
  type        = string
}

variable "environment" {
  description = "Deployment environment (e.g. dev, prod)."
  type        = string
}

variable "price_class" {
  description = "CloudFront price class. Prefer PriceClass_100 for lowest cost footprint."
  type        = string
  default     = "PriceClass_100"
}

variable "default_root_object" {
  description = "Default object served by CloudFront."
  type        = string
  default     = "index.html"
}

variable "enable_spa_fallback" {
  description = "Route 403/404 responses to index.html for client-side routing."
  type        = bool
  default     = true
}

variable "tags" {
  description = "Additional tags applied to all resources."
  type        = map(string)
  default     = {}
}
