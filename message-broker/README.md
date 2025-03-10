# Message Broker Service

This service acts as a message broker using Google Cloud Pub/Sub. It provides an API for sending messages and handles the publishing and subscribing to Pub/Sub topics.

## Features

- Send messages via REST API
- Publish messages to Google Cloud Pub/Sub
- Subscribe to messages from Google Cloud Pub/Sub
- Forward messages to the Telegram Bot service

## Requirements

- Python 3.11+
- Google Cloud Platform account with Pub/Sub enabled
- Google Cloud credentials

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| GCP_PROJECT_ID | Google Cloud Project ID | (required) |
| GCP_PUBSUB_TOPIC_ID | Pub/Sub Topic ID | messages |
| GCP_PUBSUB_SUBSCRIPTION_ID | Pub/Sub Subscription ID | messages-sub |
| TELEGRAM_BOT_URL | URL of the Telegram Bot service | http://localhost:8080 |

## Authentication

To authenticate with Google Cloud, you need to set up credentials. There are several ways to do this:

1. Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the path of your service account key file.
2. Use Google Cloud SDK to authenticate (`gcloud auth application-default login`).
3. If running on Google Cloud (GKE, Cloud Run, etc.), use the default service account.

## API Endpoints

### Send Message

```
POST /send
```

Request body:
```json
{
  "user_id": "string",
  "content": "string",
  "service": "string" (optional)
}
```

Response:
```json
{
  "status": "sent",
  "message_id": "string"
}
```

### Health Check

```
GET /health
```

Response:
```json
{
  "status": "healthy"
}
```

## Running Locally

1. Set up the required environment variables.
2. Install dependencies: `pip install -r requirements.txt`
3. Run the FastAPI server: `uvicorn app.main:app --host 0.0.0.0 --port 8080`
4. Run the subscriber in a separate terminal: `python -m app.subscriber`

## Running with Docker

```bash
docker build -t message-broker .
docker run -p 8080:8080 \
  -e GCP_PROJECT_ID=your-project-id \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json \
  -v /path/to/credentials.json:/app/credentials.json \
  message-broker
``` 