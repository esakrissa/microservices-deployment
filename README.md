# Microservices Deployment Project

A modern microservices architecture with FastAPI, Telegram Bot, and Message Broker services deployed on Google Cloud Platform using Terraform and GitHub Actions with Workload Identity Federation.

## 📋 Project Overview

This project demonstrates a secure, scalable microservices architecture with:

| Service | Technology | Deployment |
|---------|------------|------------|
| FastAPI App | Python/FastAPI | VM Instance (e2-micro) |
| Telegram Bot | Python | Cloud Run |
| Message Broker | Python | Cloud Run + Redis |

All infrastructure is managed as code with Terraform and deployed automatically via GitHub Actions CI/CD pipelines using Workload Identity Federation for secure authentication.

## 🏗️ Architecture

### Key Components

- **FastAPI Application**: REST API for processing messages
- **Telegram Bot**: Handles user interactions via Telegram
- **Message Broker**: Facilitates communication between services using Redis for message queuing
- **Artifact Registry**: Secure storage for container images
- **Workload Identity Federation**: Keyless authentication for GitHub Actions

## 📁 Project Structure

```
/
├── fastapi-app/           # FastAPI application
│   ├── app/               # Application code
│   ├── Dockerfile         # Docker configuration
│   └── requirements.txt   # Python dependencies
├── telegram-bot/          # Telegram bot service
│   ├── app/               # Bot code
│   ├── Dockerfile         # Docker configuration
│   └── requirements.txt   # Python dependencies
├── message-broker/        # Message broker service
│   ├── app/               # Broker code
│   ├── Dockerfile         # Docker configuration
│   └── requirements.txt   # Python dependencies
├── terraform/             # Infrastructure as Code
│   ├── main.tf            # Main Terraform configuration
│   ├── variables.tf       # Variable definitions
│   └── outputs.tf         # Output definitions
├── .github/workflows/     # CI/CD pipelines
│   ├── fastapi.yml        # FastAPI CI/CD workflow
│   ├── telegram-bot.yml   # Telegram bot CI/CD workflow
│   ├── message-broker.yml # Message broker CI/CD workflow
│   └── terraform.yml      # Terraform CI/CD workflow
├── scripts/               # Utility scripts
│   ├── setup.sh           # General setup script
│   └── setup-workload-identity.sh # Script to set up Workload Identity Federation
└── README.md              # Project documentation
```

## 🚀 Getting Started

### Prerequisites

1. Google Cloud Platform account
2. Telegram Bot token (from BotFather)
3. GitHub repository
4. Terraform installed locally (for initial setup)
5. Google Cloud SDK (gcloud) installed
6. Docker installed (for local testing)

### Quick Start

1. Clone this repository
2. Follow the [Deployment Guide](DEPLOY.md) for step-by-step instructions
3. Start interacting with your Telegram bot!

## 🔒 Security Features

### Workload Identity Federation

This project uses Workload Identity Federation instead of service account keys, providing:
- No long-lived credentials to manage or rotate
- Reduced risk of credential exposure
- Fine-grained access control
- Audit trail of all authentications

### Artifact Registry

Modern, secure container registry that offers:
- Vulnerability scanning
- Access control at the repository level
- Regional storage for faster deployments
- Integration with Cloud Build and Cloud Run

### Service Account Principle of Least Privilege

Each service uses a dedicated service account with minimal permissions required for its operation.

## 🛠️ CI/CD Pipeline

Each service has its own CI/CD pipeline that is triggered only when relevant files change:

1. **Build**: Compile code and run tests
2. **Package**: Create Docker images and push to Artifact Registry
3. **Deploy**: Update services with zero downtime

### GitHub Secrets

Set up the following secrets in your GitHub repository:
- `WORKLOAD_IDENTITY_PROVIDER`: The Workload Identity Provider resource name
- `SERVICE_ACCOUNT`: The service account email
- `GCP_PROJECT_ID`: Your Google Cloud project ID
- `GCP_REGION`: GCP region (e.g., us-central1)
- `VM_HOST`: IP address of your VM (after initial deployment)
- `VM_USERNAME`: SSH username for your VM
- `VM_SSH_KEY`: SSH private key for VM access
- `TELEGRAM_TOKEN`: Your Telegram bot token
- `BROKER_URL`: URL of the message broker service (after initial deployment)
- `FASTAPI_URL`: URL of the FastAPI service (after initial deployment)
- `REDIS_HOST`: Redis host (after initial deployment)
- `REDIS_PORT`: Redis port (after initial deployment)
- `REDIS_PASSWORD`: Redis password (if applicable)
- `TELEGRAM_BOT_URL`: URL of the Telegram bot service (after initial deployment)

## 📊 Monitoring and Logging

- **Cloud Monitoring**: Real-time metrics for all services
- **Cloud Logging**: Centralized logs for troubleshooting
- **Error Reporting**: Automatic notification of application errors
- **Uptime Checks**: Continuous verification of service availability

## 🔄 Scaling

- **FastAPI VM**: Manual scaling by changing machine type in Terraform
- **Cloud Run Services**: Automatic scaling based on load
- **Redis**: Scalable memory configuration

## 📝 Development

### Local Setup

1. Install dependencies for each service:
   ```bash
   cd fastapi-app
   pip install -r requirements.txt
   ```

2. Run services locally:
   ```bash
   # FastAPI
   cd fastapi-app
   uvicorn app.main:app --reload

   # Telegram Bot
   cd telegram-bot
   uvicorn app.main:app --port 8080 --reload

   # Message Broker
   cd message-broker
   uvicorn app.main:app --port 8081 --reload
   ```

### Development Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make changes to the relevant service(s)

3. Push changes and create a pull request:
   ```bash
   git push origin feature/your-feature-name
   ```

4. GitHub Actions will run tests on your pull request

5. Once approved and merged, the changes will be automatically deployed

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Terraform Documentation](https://www.terraform.io/docs)
- [Google Cloud Documentation](https://cloud.google.com/docs)

## 📄 License

This project is licensed under the MIT License.