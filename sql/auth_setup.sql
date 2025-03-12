-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create roles table first
CREATE TABLE IF NOT EXISTS roles (
    name VARCHAR(50) PRIMARY KEY,
    description TEXT,
    permissions JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) REFERENCES roles(name),
    permissions JSONB NOT NULL DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create telegram_accounts table
CREATE TABLE IF NOT EXISTS telegram_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    telegram_id VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create telegram_sessions table
CREATE TABLE IF NOT EXISTS telegram_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    telegram_id VARCHAR(255) NOT NULL,
    token TEXT,
    session_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    UNIQUE(telegram_id, is_active)
);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Function to register a new user
CREATE OR REPLACE FUNCTION register_user(
    p_email TEXT,
    p_username TEXT,
    p_password TEXT,
    p_role TEXT DEFAULT 'user'
)
RETURNS UUID AS $$
DECLARE
    v_user_id UUID;
    v_role_permissions JSONB;
BEGIN
    -- Get permissions for the role
    SELECT permissions INTO v_role_permissions FROM roles WHERE name = p_role;
    
    -- If role doesn't exist, use 'user' role
    IF v_role_permissions IS NULL THEN
        SELECT permissions INTO v_role_permissions FROM roles WHERE name = 'user';
    END IF;
    
    -- Insert the new user
    INSERT INTO users (email, username, password_hash, role, permissions)
    VALUES (p_email, p_username, p_password, p_role, v_role_permissions)
    RETURNING id INTO v_user_id;
    
    RETURN v_user_id;
END;
$$ LANGUAGE plpgsql;

-- Function to link a Telegram account to an existing user
CREATE OR REPLACE FUNCTION link_telegram_account(
    p_user_id UUID,
    p_telegram_id TEXT,
    p_username TEXT,
    p_first_name TEXT DEFAULT NULL,
    p_last_name TEXT DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    v_user_exists BOOLEAN;
BEGIN
    -- Check if user exists
    SELECT EXISTS(SELECT 1 FROM users WHERE id = p_user_id) INTO v_user_exists;
    
    IF v_user_exists THEN
        -- Insert or update telegram account
        INSERT INTO telegram_accounts (
            user_id, 
            telegram_id, 
            username, 
            first_name, 
            last_name
        )
        VALUES (
            p_user_id, 
            p_telegram_id, 
            p_username, 
            p_first_name, 
            p_last_name
        )
        ON CONFLICT (telegram_id) 
        DO UPDATE SET
            username = EXCLUDED.username,
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name,
            updated_at = CURRENT_TIMESTAMP;
        
        RETURN TRUE;
    ELSE
        RETURN FALSE;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to register a user directly from Telegram
CREATE OR REPLACE FUNCTION register_telegram_user(
    p_email TEXT,
    p_username TEXT,
    p_password TEXT,
    p_telegram_id TEXT,
    p_telegram_username TEXT,
    p_first_name TEXT DEFAULT NULL,
    p_last_name TEXT DEFAULT NULL,
    p_role TEXT DEFAULT 'user'
)
RETURNS UUID AS $$
DECLARE
    v_user_id UUID;
BEGIN
    -- Register the user first
    v_user_id := register_user(p_email, p_username, p_password, p_role);
    
    -- Link the telegram account
    PERFORM link_telegram_account(
        v_user_id, 
        p_telegram_id, 
        p_telegram_username,
        p_first_name,
        p_last_name
    );
    
    RETURN v_user_id;
END;
$$ LANGUAGE plpgsql;

-- Create triggers
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_telegram_accounts_updated_at
    BEFORE UPDATE ON telegram_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_roles_updated_at
    BEFORE UPDATE ON roles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_telegram_sessions_updated_at
    BEFORE UPDATE ON telegram_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_telegram_accounts_user_id ON telegram_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_telegram_accounts_telegram_id ON telegram_accounts(telegram_id);
CREATE INDEX IF NOT EXISTS idx_telegram_sessions_user_id ON telegram_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_telegram_sessions_telegram_id ON telegram_sessions(telegram_id);
CREATE INDEX IF NOT EXISTS idx_telegram_sessions_active ON telegram_sessions(telegram_id) WHERE is_active = true;

-- Enable Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE telegram_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE telegram_sessions ENABLE ROW LEVEL SECURITY;

-- Create policies for users table
CREATE POLICY "Users can view their own profile"
    ON users
    FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Admins can view all profiles"
    ON users
    FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM users
        WHERE id = auth.uid()
        AND role = 'admin'
    ));

CREATE POLICY "Users can update their own profile"
    ON users
    FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "Admins can update any profile"
    ON users
    FOR UPDATE
    USING (EXISTS (
        SELECT 1 FROM users
        WHERE id = auth.uid()
        AND role = 'admin'
    ));

-- Create policies for roles table
CREATE POLICY "Roles are viewable by all authenticated users"
    ON roles
    FOR SELECT
    USING (auth.role() IS NOT NULL);

CREATE POLICY "Only admins can modify roles"
    ON roles
    FOR ALL
    USING (EXISTS (
        SELECT 1 FROM users
        WHERE id = auth.uid()
        AND role = 'admin'
    ));

-- Create policies for telegram_accounts table
CREATE POLICY "Users can view their own telegram accounts"
    ON telegram_accounts
    FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "Admins can view all telegram accounts"
    ON telegram_accounts
    FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM users
        WHERE id = auth.uid()
        AND role = 'admin'
    ));

-- Create policies for telegram_sessions table
CREATE POLICY "Users can view their own sessions"
    ON telegram_sessions
    FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "Admins can view all sessions"
    ON telegram_sessions
    FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM users
        WHERE id = auth.uid()
        AND role = 'admin'
    )); 