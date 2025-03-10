# Scripts Documentation

This document provides an overview of all the scripts in this project and step-by-step instructions on how to use them to set up and run the project.

## Available Scripts

### 1. `setup.sh`

**Purpose**: Initial setup script for the deployment project.

**What it does**:
- Checks for required dependencies (gcloud, terraform, docker)
- Logs you into Google Cloud
- Sets up your Google Cloud project
- Enables necessary Google Cloud APIs (Compute Engine, Cloud Run, Redis, Artifact Registry)
- Creates a service account for GitHub Actions with appropriate permissions
- Downloads a service account key for GitHub Actions
- Initializes Terraform

### 2. `setup-workload-identity.sh`

**Purpose**: Sets up Workload Identity Federation for GitHub Actions.

**What it does**:
- Checks for required dependencies
- Logs you into Google Cloud if not already logged in
- Sets up your Google Cloud project
- Enables necessary Google Cloud APIs
- Creates an Artifact Registry repository
- Sets up Workload Identity Federation for GitHub Actions
- Configures the necessary IAM permissions

### 3. `setup-pubsub.sh`

**Purpose**: Sets up Google Cloud Pub/Sub for the message broker service.

**What it does**:
- Checks if gcloud CLI is installed
- Verifies Google Cloud authentication
- Sets up your Google Cloud project
- Enables the Pub/Sub API if not already enabled
- Creates a Pub/Sub topic if it doesn't exist
- Creates a Pub/Sub subscription if it doesn't exist

## Step-by-Step Setup Instructions

### Prerequisites

Before starting, make sure you have:
- A Google Cloud account
- Google Cloud SDK (gcloud) installed
- Terraform installed
- Docker installed
- Git installed

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <repository-directory>
```

### 2. Initial Project Setup

Run the main setup script:

```bash
./scripts/setup.sh
```

This will:
- Guide you through logging into Google Cloud
- Set up your project
- Create necessary service accounts
- Initialize Terraform

### 3. Set Up Workload Identity (Optional)

If you want to use Workload Identity Federation with GitHub Actions (recommended for production):

```bash
./scripts/setup-workload-identity.sh
```

Follow the prompts to complete the setup.

### 4. Set Up Pub/Sub for Message Broker

```bash
# Set your Google Cloud project ID
export GCP_PROJECT_ID=your-project-id

# Optionally customize topic and subscription names
export GCP_PUBSUB_TOPIC_ID=messages
export GCP_PUBSUB_SUBSCRIPTION_ID=messages-sub

# Run the setup script
./scripts/setup-pubsub.sh
```

### 5. Deploy Infrastructure with Terraform

```bash
cd terraform
terraform apply
```

Review the planned changes and type `yes` to apply them.

### 6. Build and Deploy Services

#### Option 1: Using Docker Compose (Local Development)

```bash
# Set environment variables from Terraform output
export TELEGRAM_TOKEN=your-telegram-token
export GCP_PROJECT_ID=your-project-id

# Build and run services
docker-compose up --build
```

#### Option 2: Using Cloud Run (Production)

The GitHub Actions workflow will automatically deploy to Cloud Run when you push to the main branch.

## Running the Project

After completing the setup, your project should be running with:

1. **FastAPI App**: Processes messages and sends them to the message broker
2. **Message Broker**: Uses Google Cloud Pub/Sub to handle message queuing
3. **Telegram Bot**: Interfaces with Telegram to send and receive messages

### Testing the Setup

1. Send a test message to the FastAPI app:
   ```bash
   curl -X POST http://localhost:8000/process \
     -H "Content-Type: application/json" \
     -d '{"content": "Test message", "user_id": "your-telegram-id"}'
   ```

2. Check the logs to verify the message flow:
   ```bash
   # For local development
   docker-compose logs -f

   # For Cloud Run
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=fastapi-app"
   ```

## Troubleshooting

If you encounter issues:

1. Check that all required APIs are enabled in your Google Cloud project
2. Verify that service accounts have the correct permissions
3. Check the logs for each service
4. Ensure environment variables are correctly set

For more detailed information, refer to the README.md and DEPLOY.md files in the project root. 