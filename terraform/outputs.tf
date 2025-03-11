output "api_gateway_vm_ip" {
  description = "The public IP address of the API Gateway VM"
  value       = google_compute_instance.api_gateway_vm.network_interface.0.access_config.0.nat_ip
}

output "telegram_bot_url" {
  description = "The URL of the Telegram Bot Cloud Run service"
  value       = google_cloud_run_service.telegram_bot.status[0].url
}

output "message_broker_url" {
  description = "The URL of the Message Broker Cloud Run service"
  value       = google_cloud_run_service.message_broker.status[0].url
}

output "pubsub_topic_id" {
  description = "The Pub/Sub topic ID"
  value       = "messages"
}

output "pubsub_subscription_id" {
  description = "The Pub/Sub subscription ID"
  value       = "messages-sub"
}