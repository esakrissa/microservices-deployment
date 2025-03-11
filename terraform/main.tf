provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

terraform {
  backend "gcs" {
    bucket = "travel-agency-448103-terraform-state"
    prefix = "terraform/state"
  }
}

# Use existing Artifact Registry repository
data "google_artifact_registry_repository" "app_repo" {
  location      = var.region
  repository_id = "app-images"
}

# VM Instance for API Gateway
resource "google_compute_instance" "api_gateway_vm" {
  name         = "api-gateway-vm"
  machine_type = "e2-micro"
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 30  # 30GB disk to stay within free tier
      type  = "pd-standard"  # Standard persistent disk for free tier
    }
  }

  network_interface {
    network = "default"
    access_config {
      // Ephemeral IP
    }
  }

  metadata_startup_script = <<-EOF
    #!/bin/bash
    
    # Update package lists
    apt-get update
    
    # Install required packages
    apt-get install -y ca-certificates curl gnupg lsb-release
    
    # Add Docker's official GPG key
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Set up the Docker repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Update package lists again
    apt-get update
    
    # Install Docker Engine, containerd, and Docker Compose
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Enable Docker to start on boot
    systemctl enable docker
    systemctl start docker
    
    # Pull and run the API Gateway container
    docker pull ${var.region}-docker.pkg.dev/${var.project_id}/app-images/api-gateway:latest
    docker run -d -p 80:8000 \
      -e BROKER_URL=${var.broker_url} \
      --restart always \
      --name api-gateway \
      ${var.region}-docker.pkg.dev/${var.project_id}/app-images/api-gateway:latest
  EOF

  tags = ["api-gateway", "http-server"]
}

# Firewall rule to allow HTTP traffic
resource "google_compute_firewall" "allow_http" {
  name    = "allow-http"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["80", "8000"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["http-server"]
}

# Cloud Run service for Telegram Bot with Workload Identity Federation
resource "google_cloud_run_service" "telegram_bot" {
  name     = "telegram-bot"
  location = var.region

  template {
    spec {
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/app-images/telegram-bot:latest"
        
        env {
          name  = "TELEGRAM_TOKEN"
          value = var.telegram_token
        }
        
        env {
          name  = "API_GATEWAY_URL"
          value = "http://${google_compute_instance.api_gateway_vm.network_interface.0.access_config.0.nat_ip}:80"
        }
        
        ports {
          container_port = 8080
        }
      }
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "5"
        "run.googleapis.com/client-name"   = "terraform"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

# Allow unauthenticated access to Cloud Run service
resource "google_cloud_run_service_iam_member" "telegram_bot_public" {
  service  = google_cloud_run_service.telegram_bot.name
  location = google_cloud_run_service.telegram_bot.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Cloud Run service for Message Broker with Workload Identity Federation
resource "google_cloud_run_service" "message_broker" {
  name     = "message-broker"
  location = var.region

  template {
    spec {
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/app-images/message-broker:latest"
        
        env {
          name  = "GCP_PROJECT_ID"
          value = var.project_id
        }
        
        env {
          name  = "GCP_PUBSUB_TOPIC_ID"
          value = "messages"
        }
        
        env {
          name  = "GCP_PUBSUB_SUBSCRIPTION_ID"
          value = "messages-sub"
        }
        
        env {
          name  = "TELEGRAM_BOT_URL"
          value = google_cloud_run_service.telegram_bot.status[0].url
        }
        
        ports {
          container_port = 8080
        }
      }
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "5"
        "run.googleapis.com/client-name"   = "terraform"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
  
  depends_on = [
    google_cloud_run_service.telegram_bot
  ]
}

# Allow unauthenticated access to Message Broker service
resource "google_cloud_run_service_iam_member" "message_broker_public" {
  service  = google_cloud_run_service.message_broker.name
  location = google_cloud_run_service.message_broker.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Service account for Cloud Run services
resource "google_service_account" "cloud_run_sa" {
  account_id   = "cloud-run-service-account"
  display_name = "Cloud Run Service Account"
}

# Grant necessary permissions to the service account
resource "google_project_iam_member" "cloud_run_sa_roles" {
  for_each = toset([
    "roles/artifactregistry.reader",
    "roles/logging.logWriter",
    "roles/cloudtrace.agent"
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}