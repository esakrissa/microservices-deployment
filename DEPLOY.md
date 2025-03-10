# Deployment Guide

This guide provides step-by-step instructions for deploying the microservices project to Google Cloud Platform.

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
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
- ✅ VM instance for FastAPI application
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
| `TELEGRAM_TOKEN` | Your Telegram bot token |

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
- `fastapi_vm_ip`: The public IP of your VM
- `telegram_bot_url`: The URL of your Telegram bot service
- `message_broker_url`: The URL of your message broker service
- `GCP_PUBSUB_TOPIC_ID` and `GCP_PUBSUB_SUBSCRIPTION_ID`: Pub/Sub topic and subscription IDs

### 6. Update GitHub Secrets with Deployment Information

Add these additional secrets to your GitHub repository:

| Secret | Description |
|--------|-------------|
| `VM_HOST` | The `fastapi_vm_ip` value from Terraform output |
| `VM_USERNAME` | The username for SSH access to the VM |
| `VM_SSH_KEY` | Your private SSH key for VM access |
| `BROKER_URL` | The `message_broker_url` value from Terraform output |
| `FASTAPI_URL` | `http://<fastapi_vm_ip>:80` |
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
   - VM: SSH into the VM and run `docker ps` to verify the FastAPI container is running
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
- Build and deploy the FastAPI app when changes are made to the `fastapi-app` directory
- Build and deploy the Telegram bot when changes are made to the `telegram-bot` directory
- Build and deploy the message broker when changes are made to the `message-broker` directory
- Apply Terraform changes when modifications are made to the `terraform` directory

## Troubleshooting

### VM Deployment Issues

If the FastAPI app isn't running on the VM:

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