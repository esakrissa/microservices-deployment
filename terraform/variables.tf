variable "project_id" {
  description = "The Google Cloud project ID"
  type        = string
}

variable "region" {
  description = "The Google Cloud region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "The Google Cloud zone"
  type        = string
  default     = "us-central1-a"
}

variable "telegram_token" {
  description = "The Telegram Bot API token"
  type        = string
  sensitive   = true
}

variable "broker_url" {
  description = "URL for the message broker service"
  type        = string
}