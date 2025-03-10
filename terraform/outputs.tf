output "fastapi_vm_ip" {
  description = "The public IP address of the FastAPI VM"
  value       = google_compute_instance.fastapi_vm.network_interface.0.access_config.0.nat_ip
}

output "telegram_bot_url" {
  description = "The URL of the Telegram Bot Cloud Run service"
  value       = google_cloud_run_service.telegram_bot.status[0].url
}

output "message_broker_url" {
  description = "The URL of the Message Broker Cloud Run service"
  value       = google_cloud_run_service.message_broker.status[0].url
}

output "redis_host" {
  description = "The Redis instance host"
  value       = google_redis_instance.message_broker_redis.host
}

output "redis_port" {
  description = "The Redis instance port"
  value       = google_redis_instance.message_broker_redis.port
}