variable "project_id" {
  description = "The ID of the existing project to use"
  type        = string
}

variable "region" {
  description = "The region to create resources in"
  type        = string
  default     = "us-central1"
}

variable "support_email" {
  description = "The email address to use for support contact"
  type        = string
} 