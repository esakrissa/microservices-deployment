# Deployment Guide

This guide provides step-by-step instructions for deploying the microservices project to Google Cloud Platform.

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Development Environment](#development-environment)
  - [Development Prerequisites](#development-prerequisites)
  - [Development Setup](#development-setup)
  - [Development Workflow](#development-workflow)
  - [Testing in Development](#testing-in-development)
  - [Troubleshooting Development Setup](#troubleshooting-development-setup)
- [Local Deployment](#local-deployment)
  - [Local Prerequisites](#local-prerequisites)
  - [Quick Start (Local)](#quick-start-local)
  - [How Local Deployment Works](#how-local-deployment-works)
  - [Testing the Local Setup](#testing-the-local-setup)
  - [Local Environment Variables](#local-environment-variables)
  - [Managing the Local Environment](#managing-the-local-environment)
  - [Local Troubleshooting](#local-troubleshooting)
  - [Differences from Production](#differences-from-production)
- [Deployment Process](#deployment-process)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Set Up Workload Identity Federation](#2-set-up-workload-identity-federation)
  - [3. Set Up Google Cloud Pub/Sub](#3-set-up-google-cloud-pubsub)
  - [4. Configure GitHub Secrets](#4-configure-github-secrets)
  - [5. Initial Terraform Deployment](#5-initial-terraform-deployment)
  - [6. Update GitHub Secrets](#6-update-github-secrets-with-deployment-information)
  - [7. Update Terraform Variables](#7-update-terraform-variables)
  - [8. Set Up SSH Access to VM](#8-set-up-ssh-access-to-vm)
  - [9. Trigger CI/CD Pipeline](#9-push-code-to-github-to-trigger-cicd)
  - [10. Configure Telegram Webhook](#10-configure-telegram-webhook)
  - [11. Verify Deployment](#11-verify-deployment)
- [Continuous Deployment](#continuous-deployment)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)
- [Security Considerations](#security-considerations)

## Overview

**Infrastructure Automation**: Terraform automatically provisions all required infrastructure:
- ✅ VM instance for API Gateway
- ✅ Cloud Run services for Telegram Bot and Message Broker
- ✅ Google Cloud Pub/Sub for the message broker
- ✅ Artifact Registry repository
- ✅ Service accounts and IAM permissions

> **Note**: You do not need to manually create VMs or Cloud Run services. Terraform handles the creation of all infrastructure components.

## Prerequisites

Before starting, ensure you have:

| Requirement | Description |
|-------------|-------------|
| GCP Account | Active Google Cloud Platform account |
| Telegram Bot | Bot token from BotFather |
| Git | Version control system |
| Terraform | Infrastructure as Code tool (v1.0.0+) |
| Google Cloud SDK | Command-line interface for GCP |
| Docker | Container platform |
| GitHub Account | For hosting code repository |

## Development Environment

This section explains how to set up a local development environment for working on the project without deploying to Google Cloud Platform.

### Development Prerequisites

- Docker and Docker Compose installed
- Git installed
- Telegram Bot Token (from @BotFather)
- ngrok account and ngrok installed (for Telegram webhook)

### Development Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

3. Edit the `.env` file with your values:
   - Add your Telegram Bot Token (`TELEGRAM_BOT_TOKEN`)
   - Other values can remain at their defaults for development

4. Make the development scripts executable:
   ```bash
   chmod +x scripts/*.sh
   ```

5. Start the development environment:
   ```bash
   ./scripts/setup-dev.sh
   ```

6. In a separate terminal, start ngrok to expose your local Telegram bot:
   ```bash
   ngrok http 8080
   ```

7. Add the ngrok URL to your `.env` file:
   ```
   NGROK_URL=your-ngrok-url
   ```

8. Set up the Telegram webhook:
   ```bash
   ./scripts/setup-telegram-webhook-dev.sh
   ```

For detailed step-by-step instructions, see [step-by-step.txt](step-by-step.txt).

### Development Workflow

The development environment uses Docker Compose with:
- Hot-reload enabled for all services
- Local Pub/Sub emulator
- Volume mounts for live code changes
- Test endpoints for debugging

Available services:
- API Gateway: http://localhost:8000
- Telegram Bot: http://localhost:8080
- Message Broker: http://localhost:8081
- Pub/Sub Emulator: http://localhost:8085

Common development tasks:

1. View logs:
   ```bash
   docker-compose logs -f
   ```

2. Rebuild a specific service:
   ```bash
   docker-compose up -d --build service-name
   ```

3. Rebuild Telegram bot and update webhook:
   ```bash
   docker-compose up -d --build telegram-bot webhook-setup
   ```

4. Stop all services:
   ```bash
   docker-compose down
   ```

### Testing in Development

The development environment includes special test endpoints:

- Health Check: http://localhost:8000/test/health
- Send Test Message: http://localhost:8000/test/send-message (POST)
- Pub/Sub Info: http://localhost:8000/test/pubsub-info

Example test command:
```bash
curl -X POST http://localhost:8000/test/send-message \
  -H "Content-Type: application/json" \
  -d '{"content": "Test message", "user_id": "test-user"}'
```

### Troubleshooting Development Setup

1. If webhook not working:
   - Check ngrok is running
   - Verify NGROK_URL in .env
   - Run webhook setup script again

2. If services not starting:
   - Check docker-compose logs
   - Verify all ports are available
   - Check .env configuration

3. If changes not reflecting:
   - Rebuild the specific service
   - Check volume mounts
   - Verify hot-reload is working

## Local Deployment

This section explains how to deploy and test the entire microservices project locally using Docker Compose, including a Pub/Sub emulator for local testing.

### Local Prerequisites

- Docker and Docker Compose installed on your machine
- Git (to clone the repository)
- Bash shell (for running the setup script)

### Quick Start (Local)

1. Clone the repository (if you haven't already):
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Run the local setup script:
   ```bash
   ./scripts/local-setup.sh
   ```
   
   This script will:
   - Check for a `.env` file and create one from `.env.example` if it doesn't exist
   - Load environment variables from the `.env` file
   - Start all services using Docker Compose

3. If this is your first time running the setup, edit the `.env` file with your actual values:
   ```bash
   # Edit the .env file with your preferred editor
   nano .env
   
   # Restart the services after editing
   docker-compose down
   docker-compose up -d
   ```

4. The services will be available at:
   - API Gateway: http://localhost:8000
   - Telegram Bot: http://localhost:8080
   - Message Broker: http://localhost:8081

### How Local Deployment Works

The local deployment uses Docker Compose to create and connect the following services:

1. **Pub/Sub Emulator**: A local emulator for Google Cloud Pub/Sub
2. **API Gateway**: The main application that processes messages
3. **Telegram Bot**: The bot that interacts with Telegram
4. **Message Broker**: The service that handles message queuing using the Pub/Sub emulator

All services are configured to work together in a local environment, with the Pub/Sub emulator replacing the actual Google Cloud Pub/Sub service.

### Testing the Local Setup

1. Test the API Gateway app:
   ```bash
   curl -X POST http://localhost:8000/process \
     -H "Content-Type: application/json" \
     -d '{"content": "Test message", "user_id": "test-user"}'
   ```

2. Check the logs to verify the message flow:
   ```bash
   docker-compose logs -f
   ```

### Local Environment Variables

The project uses a `.env` file for local development. The following variables can be configured:

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `GCP_PROJECT_ID` | Project ID for the Pub/Sub emulator | local-project |
| `GCP_PUBSUB_TOPIC_ID` | Pub/Sub topic name | messages |
| `GCP_PUBSUB_SUBSCRIPTION_ID` | Pub/Sub subscription name | messages-sub |
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | *Required* |
| `BROKER_URL` | URL of the message broker service | http://message-broker:8080 |
| `API_GATEWAY_URL` | URL of the API Gateway service | http://api-gateway:8000 |
| `TELEGRAM_BOT_URL` | URL of the Telegram bot service | http://telegram-bot:8080 |
| `NGROK_URL` | Your ngrok URL for Telegram webhook | *Required for development* |

To set these variables:
1. Copy `.env.example` to `.env`
2. Edit the `.env` file with your actual values
3. Restart the services if they're already running

### Managing the Local Environment

To stop all services:
```bash
docker-compose down
```

To stop and remove all containers, networks, and volumes:
```bash
docker-compose down -v
```

### Local Troubleshooting

#### Pub/Sub Emulator Issues

If you encounter issues with the Pub/Sub emulator:

1. Check if the emulator is running:
   ```bash
   docker-compose ps pubsub-emulator
   ```

2. View the emulator logs:
   ```bash
   docker-compose logs pubsub-emulator
   ```

3. Restart the emulator:
   ```bash
   docker-compose restart pubsub-emulator
   ```

#### Service Connection Issues

If services can't connect to each other:

1. Make sure all services are running:
   ```bash
   docker-compose ps
   ```

2. Check the network configuration:
   ```bash
   docker network inspect deploy-test_default
   ```

3. Restart the affected services:
   ```bash
   docker-compose restart <service-name>
   ```

### Differences from Production

This local setup differs from the production deployment in the following ways:

1. Uses a Pub/Sub emulator instead of actual Google Cloud Pub/Sub
2. Runs all services on a single machine instead of distributed cloud services
3. Uses Docker Compose instead of Terraform for orchestration
4. Doesn't require Google Cloud authentication
5. Doesn't use Workload Identity Federation

These differences make it easier to test the application locally while still maintaining a similar architecture to the production environment.

## Deployment Process

### 1. Clone the Repository

Run this in your terminal:

```bash
git clone <your-repository-url>
cd deploy-test
```

### 2. Set Up Workload Identity Federation

Run the setup script to configure secure authentication between GitHub Actions and Google Cloud:

```bash
./scripts/setup-workload-identity.sh
```

The script will guide you through:
- Google Cloud login
- Project selection
- API enablement
- Artifact Registry creation
- Service account setup
- Workload Identity Federation configuration

> **Important**: Note the output values for GitHub secrets needed in the next step.

### 3. Set Up Google Cloud Pub/Sub

Run the setup script to configure Pub/Sub for the message broker:

```bash
export GCP_PROJECT_ID=your-project-id
./scripts/setup-pubsub.sh
```

This will:
- Enable the Pub/Sub API
- Create a topic for messages
- Create a subscription for processing messages

### 4. Configure GitHub Secrets

Add these initial secrets to your GitHub repository (Settings > Secrets and variables > Actions):

| Secret | Description |
|--------|-------------|
| `WORKLOAD_IDENTITY_PROVIDER` | Workload Identity Provider resource name |
| `SERVICE_ACCOUNT` | Service account email |
| `GCP_PROJECT_ID` | Your Google Cloud project ID |
| `GCP_REGION` | Your preferred GCP region (e.g., us-central1) |
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token |

### 5. Initial Terraform Deployment

The first deployment needs to be done manually to set up the infrastructure:

```bash
cd terraform
terraform init
terraform plan -var="project_id=YOUR_PROJECT_ID" \
  -var="region=YOUR_REGION" \
  -var="telegram_token=YOUR_TELEGRAM_TOKEN" \
  -var="broker_url=placeholder-will-update-later"
```

Review the plan to ensure it will create the expected resources, then apply it:

```bash
terraform apply -var="project_id=YOUR_PROJECT_ID" \
  -var="region=YOUR_REGION" \
  -var="telegram_token=YOUR_TELEGRAM_TOKEN" \
  -var="broker_url=placeholder-will-update-later"
```

This will create all the infrastructure components. Note the outputs, which include:
- `api_gateway_vm_ip`: The public IP of your VM
- `telegram_bot_url`: The URL of your Telegram bot service
- `message_broker_url`: The URL of your message broker service
- `GCP_PUBSUB_TOPIC_ID` and `GCP_PUBSUB_SUBSCRIPTION_ID`: Pub/Sub topic and subscription IDs

### 6. Update GitHub Secrets with Deployment Information

Add these additional secrets to your GitHub repository:

| Secret | Description |
|--------|-------------|
| `VM_HOST` | The `api_gateway_vm_ip` value from Terraform output |
| `VM_USERNAME` | The username for SSH access to the VM |
| `VM_SSH_KEY` | Your private SSH key for VM access |
| `BROKER_URL` | The `message_broker_url` value from Terraform output |
| `API_GATEWAY_URL` | `http://<api_gateway_vm_ip>:80` |
| `GCP_PUBSUB_TOPIC_ID` | The Pub/Sub topic ID (default: messages) |
| `GCP_PUBSUB_SUBSCRIPTION_ID` | The Pub/Sub subscription ID (default: messages-sub) |
| `TELEGRAM_BOT_URL` | The `telegram_bot_url` value from Terraform output |

### 7. Update Terraform Variables

Now that you have the actual message broker URL, update the Terraform configuration:

```bash
terraform apply -var="project_id=YOUR_PROJECT_ID" \
  -var="region=YOUR_REGION" \
  -var="telegram_token=YOUR_TELEGRAM_TOKEN" \
  -var="broker_url=YOUR_BROKER_URL"
```

### 8. Set Up SSH Access to VM

Generate an SSH key if you don't already have one:

```bash
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

Add your public key to the VM's metadata in the Google Cloud Console:
1. Go to Compute Engine > VM instances
2. Click on your VM instance
3. Click Edit
4. Under SSH Keys, click Add item
5. Paste your public key content
6. Save

### 9. Push Code to GitHub to Trigger CI/CD

```bash
git add .
git commit -m "Initial deployment"
git push origin main
```

This will trigger the GitHub Actions workflows, which will:
1. Build and test each service
2. Push Docker images to Artifact Registry
3. Deploy the services to their respective environments

### 10. Configure Telegram Webhook

Set up the webhook for your Telegram bot:

```bash
curl -F "url=<telegram_bot_url>/webhook" https://api.telegram.org/bot<TELEGRAM_TOKEN>/setWebhook
```

Replace `<telegram_bot_url>` with your actual Telegram bot URL and `<TELEGRAM_TOKEN>` with your Telegram bot token.

### 11. Verify Deployment

1. Check that all services are running:
   - VM: SSH into the VM and run `docker ps` to verify the API Gateway container is running
   - Cloud Run: Check the Cloud Run console to verify the Telegram bot and message broker services are deployed

2. Check Docker containers:
   ```bash
   docker ps -a
   ```

3. Check container logs:
   ```bash
   docker logs <container_id>
   ```

## Continuous Deployment

After the initial setup, the CI/CD pipeline will automatically:
- Build and deploy the API Gateway when changes are made to the `api-gateway` directory
- Build and deploy the Telegram bot when changes are made to the `telegram-bot` directory
- Build and deploy the message broker when changes are made to the `message-broker` directory
- Apply Terraform changes when modifications are made to the `terraform` directory

## Troubleshooting

### VM Deployment Issues

If the API Gateway app isn't running on the VM:

1. SSH into the VM:
   ```bash
   ssh <VM_USERNAME>@<VM_HOST>
   ```

2. Check Docker containers:
   ```bash
   docker ps -a
   ```

3. Check container logs:
   ```bash
   docker logs <container_id>
   ```

### Cloud Run Deployment Issues

1. Check the Cloud Run service logs in the Google Cloud Console
2. Verify the service account has the necessary permissions
3. Check that environment variables are correctly set

### Terraform Issues

1. Run `terraform plan` to see what changes would be applied
2. Check for error messages in the Terraform output
3. Verify that your GCP credentials are correctly configured

## Maintenance

### Updating Services

Make changes to the service code in the respective directories, commit, and push. The CI/CD pipeline will automatically deploy the changes.

### Scaling

- VM: To change the VM size, update the `machine_type` in `terraform/main.tf`
- Cloud Run: Cloud Run automatically scales based on load. You can adjust the maximum instances in the annotations in `terraform/main.tf`

### Monitoring

- Set up Cloud Monitoring for all services
- Configure alerts for critical metrics
- Regularly check logs for errors or unusual activity

## Security Considerations

- Rotate the Telegram bot token periodically
- Keep all dependencies updated
- Review IAM permissions regularly to ensure least privilege
- Enable VPC Service Controls for additional security