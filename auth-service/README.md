# Auth Service

This service provides authentication and authorization functionality for the application. It uses Supabase for user data storage and implements Role-Based Access Control (RBAC).

## Features

- User registration and login
- JWT-based authentication
- Role-based access control (RBAC)
- Integration with GCP Pub/Sub message broker for event publishing
- Supabase integration for user data storage

## API Endpoints

### Authentication

- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login and get access token

### User Management

- `GET /users/me` - Get current user information
- `GET /users` - Get all users (admin only)
- `PATCH /users/{user_id}` - Update user information

## Environment Variables

The following environment variables are required:

- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase API key
- `JWT_SECRET_KEY` - Secret key for JWT token generation
- `JWT_ALGORITHM` - Algorithm for JWT token generation (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time in minutes (default: 30)
- `BROKER_URL` - URL of the message broker service (default: http://message-broker:8080)
- `GCP_PROJECT_ID` - Google Cloud Project ID
- `GCP_PUBSUB_TOPIC_ID` - Google Cloud Pub/Sub Topic ID
- `GCP_PUBSUB_SUBSCRIPTION_ID` - Google Cloud Pub/Sub Subscription ID

## Development

### Setup

1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Create a `users` table with the following schema:

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT UNIQUE NOT NULL,
  username TEXT NOT NULL,
  password TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'user',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  permissions JSONB DEFAULT '[]'::jsonb
);
```

3. Set up the environment variables in `.env` file
4. Run the service using Docker Compose

### Running Tests

```bash
cd auth-service
pytest
```

## Docker

The service is containerized and can be run using Docker:

```bash
docker build -t auth-service .
docker run -p 8001:8000 --env-file .env auth-service
```

Or using Docker Compose:

```bash
docker-compose up auth-service
``` 