# Microservices Deployment Project

A modern microservices architecture with FastAPI, Telegram Bot, and Message Broker services deployed on Google Cloud Platform using Terraform and GitHub Actions with Workload Identity Federation.

## 📋 Project Overview

This project demonstrates a secure, scalable microservices architecture with:

| Service | Technology | Deployment |
|---------|------------|------------|
| API Gateway | Python/FastAPI | VM Instance (e2-micro) |
| Telegram Bot | Python | Cloud Run |
| Message Broker | Python | Cloud Run + Google Cloud Pub/Sub |
| API Gateway | Python | Cloud Run |

All infrastructure is managed as code with Terraform and deployed automatically via GitHub Actions CI/CD pipelines using Workload Identity Federation for secure authentication.

## 🏗️ Architecture

### Key Components

- **API Gateway**: REST API for processing messages
- **Telegram Bot**: Handles user interactions via Telegram
- **Message Broker**: Facilitates communication between services using Google Cloud Pub/Sub for message queuing
- **API Gateway**: Handles incoming requests and routes them to the appropriate service
- **Artifact Registry**: Secure storage for container images
- **Workload Identity Federation**: Keyless authentication for GitHub Actions

## 📁 Project Structure

```
/
├── api-gateway/           # API Gateway service
│   ├── app/               # Application code
│   │   └── utils/         # Utility functions
│   ├── Dockerfile         # Production Docker configuration
│   ├── Dockerfile.dev     # Development Docker configuration
│   └── requirements.txt   # Python dependencies
├── auth-service/          # Authentication service
│   ├── app/               # Application code
│   │   ├── models/        # Data models
│   │   ├── routers/       # API routes
│   │   ├── schemas/       # Pydantic schemas
│   │   └── services/      # Business logic
│   ├── Dockerfile         # Production Docker configuration
│   └── requirements.txt   # Python dependencies
├── message-broker/        # Message broker service
│   ├── app/               # Broker code
│   ├── Dockerfile         # Production Docker configuration
│   ├── Dockerfile.dev     # Development Docker configuration
│   └── requirements.txt   # Python dependencies
├── telegram-bot/          # Telegram bot service
│   ├── app/               # Bot code
│   │   ├── callbacks/     # Callback handlers
│   │   ├── handlers/      # Message handlers
│   │   ├── models/        # Data models
│   │   ├── states/        # State management
│   │   └── utils/         # Utility functions
│   └── requirements.txt   # Python dependencies
├── terraform/             # Infrastructure as Code
│   ├── main.tf           # Main Terraform configuration
│   ├── variables.tf      # Variable definitions
│   └── outputs.tf        # Output definitions
├── sql/                   # SQL scripts
│   ├── auth_setup.sql     # Authentication database setup
│   ├── auth_data.sql     # Initial data
│   └── auth_reset.sql    # Reset scripts
├── scripts/               # Utility scripts
│   ├── setup.sh           # General setup script
│   ├── setup-dev.sh       # Development environment setup
│   ├── init-pubsub-dev.sh # Initialize Pub/Sub for development
│   ├── setup-telegram-webhook-dev.sh # Set up Telegram webhook for development
│   ├── setup-workload-identity.sh # Script to set up Workload Identity Federation
│   ├── test-auth-service.sh    # Test auth service
│   └── test-telegram-auth.sh   # Test telegram auth
├── .github/workflows/     # CI/CD pipelines
│   ├── api-gateway.yml    # API Gateway CI/CD workflow
│   ├── telegram-bot.yml   # Telegram bot CI/CD workflow
│   ├── message-broker.yml # Message broker CI/CD workflow
│   └── terraform.yml      # Terraform CI/CD workflow
├── docker-compose.yml     # Local development orchestration
├── step-by-step.txt      # Detailed setup instructions
├── .env.example          # Example environment variables
└── README.md             # Project documentation
```

## 🚀 Getting Started

### Prerequisites

1. Google Cloud Platform account (for production)
2. Telegram Bot token (from BotFather)
3. GitHub repository (for production CI/CD)
4. Terraform installed locally (for production setup)
5. Google Cloud SDK (gcloud) installed (for production)
6. Docker and Docker Compose installed (for development and testing)
7. ngrok (for local Telegram webhook development)

### Development Environment Setup

For local development, we provide a Docker Compose setup with hot-reloading:

1. Clone this repository
2. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
3. Add your Telegram Bot Token to the `.env` file
4. Start the development environment:
   ```bash
   ./scripts/setup-dev.sh
   ```
5. In a separate terminal, start ngrok to expose your local Telegram bot:
   ```bash
   ngrok http 8080
   ```
6. Add the ngrok URL to your `.env` file:
   ```
   NGROK_URL=your-ngrok-url
   ```
7. Set up the Telegram webhook:
   ```bash
   ./scripts/setup-telegram-webhook-dev.sh
   ```

For detailed development instructions, see [step-by-step.txt](step-by-step.txt).

### Production Deployment

For production deployment:

1. Follow the [Deployment Guide](DEPLOY.md) for step-by-step instructions
2. Start interacting with your Telegram bot!

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

Set up the following secrets in your GitHub repository (Settings > Secrets and variables > Actions):
- `WORKLOAD_IDENTITY_PROVIDER`: The Workload Identity Provider resource name
- `SERVICE_ACCOUNT`: The service account email
- `GCP_PROJECT_ID`: Your Google Cloud project ID
- `GCP_REGION`: GCP region (e.g., us-central1)
- `VM_HOST`: IP address of your VM (after initial deployment)
- `VM_USERNAME`: SSH username for your VM
- `VM_SSH_KEY`: SSH private key for VM access
- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
- `BROKER_URL`: URL of the message broker service (after initial deployment)
- `API_GATEWAY_URL`: URL of the API Gateway service (after initial deployment)
- `GCP_PUBSUB_TOPIC_ID`: Google Cloud Pub/Sub topic ID (default: messages)
- `GCP_PUBSUB_SUBSCRIPTION_ID`: Google Cloud Pub/Sub subscription ID (default: messages-sub)
- `TELEGRAM_BOT_URL`: URL of the Telegram bot service (after initial deployment)

## 📊 Monitoring and Logging

- **Cloud Monitoring**: Real-time metrics for all services
- **Cloud Logging**: Centralized logs for troubleshooting
- **Error Reporting**: Automatic notification of application errors
- **Uptime Checks**: Continuous verification of service availability
- **Local Development**: View logs with `docker-compose logs -f`

## 🔄 Scaling

- **API Gatewau VM**: Manual scaling by changing machine type in Terraform
- **Cloud Run Services**: Automatic scaling based on load
- **Pub/Sub**: Fully managed and automatically scales with your workload

## 📝 Development

### Development Environment Features

- **Hot-reload**: Code changes automatically reload the services
- **Local Pub/Sub Emulator**: No need for a GCP account during development
- **Test Endpoints**: Special endpoints for testing in development mode
- **Docker Compose**: All services orchestrated locally
- **Automatic Webhook Setup**: Script to configure Telegram webhook with ngrok

### Development Workflow

1. Make changes to the code
2. Services automatically reload with changes
3. For larger changes requiring container rebuild:
   ```bash
   docker-compose up -d --build service-name
   ```
4. For Telegram bot changes that require webhook update:
   ```bash
   docker-compose up -d --build telegram-bot webhook-setup
   ```

### Testing

Test endpoints available in development:
- Health Check: http://localhost:8000/test/health
- Send Test Message: http://localhost:8000/test/send-message (POST)
- Pub/Sub Info: http://localhost:8000/test/pubsub-info

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Terraform Documentation](https://www.terraform.io/docs)
- [Google Cloud Documentation](https://cloud.google.com/docs)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [ngrok Documentation](https://ngrok.com/docs)

## 📄 License

This project is licensed under the MIT License.