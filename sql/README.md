# Database Setup for Auth Service

This directory contains SQL scripts for setting up the authentication and authorization system in Supabase.

## Scripts

The database setup is split into two main files:

1. `auth_setup.sql`: Contains all the database structure and functionality
   - UUID extension setup
   - Users table creation with indexes
   - Roles table creation
   - Authentication functions
   - Row Level Security (RLS) policies
   - Automatic timestamp updates

2. `auth_data.sql`: Contains seed data for initial setup
   - Default roles (admin, moderator, user)
   - Sample users for each role
   - Default permissions for each role

## Database Schema

### Users Table
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT UNIQUE NOT NULL,
  username TEXT NOT NULL,
  password TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'user',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  permissions JSONB DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  telegram_id TEXT UNIQUE,
  telegram_username TEXT
);
```

### Roles Table
```sql
CREATE TABLE roles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT UNIQUE NOT NULL,
  description TEXT,
  permissions JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

## Default Roles and Permissions

1. **Admin**
   - Permissions: read:users, write:users, delete:users, manage:roles, manage:system
   - Full access to all features and system management

2. **Moderator**
   - Permissions: read:users, write:users, manage:content
   - Can view and update user profiles and manage content

3. **User**
   - Permissions: read:own_profile, write:own_profile
   - Can only view and update their own profile

## Setup Instructions

1. Create a new Supabase project
2. Open the SQL editor in the Supabase dashboard
3. Execute `auth_setup.sql` first to create the database structure
4. Execute `auth_data.sql` to populate the database with initial data
5. Update the sample user passwords in `auth_data.sql` with properly hashed passwords before using in production

## Telegram Integration

The schema includes support for Telegram integration:
- Users can register directly through Telegram
- Existing users can link their Telegram accounts
- Telegram IDs are unique to prevent duplicate accounts

### Integration Flow

1. **User Registration via Telegram**:
   - User initiates registration with `/register` command or "Register" button
   - Bot collects email, username, and password
   - Auth service creates a new user with the Telegram ID linked

2. **User Login via Telegram**:
   - User initiates login with `/login` command or "Login" button
   - Bot collects email and password
   - Auth service authenticates the user and links the Telegram ID

3. **Automatic Authentication**:
   - Once a Telegram ID is linked to a user account, the user is automatically authenticated in future sessions
   - The Telegram ID serves as a unique identifier for the user

### Helper Functions

1. `register_user(email, username, password, role)`: Register a new user
2. `link_telegram_account(email, telegram_id, telegram_username)`: Link Telegram account to existing user
3. `register_telegram_user(email, username, password, telegram_id, telegram_username, role)`: Register directly via Telegram

## Testing the Integration

You can test the integration between the Telegram bot and auth service using the provided script:

```bash
./scripts/test-telegram-auth.sh
```

This script:
1. Registers a test user via the auth service
2. Logs in with the test user
3. Links a test Telegram ID to the user
4. Simulates a Telegram message to test the integration 