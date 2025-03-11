-- Suppress notices about non-existent objects
SET client_min_messages TO WARNING;

-- Drop policies using DO block to handle non-existent tables
DO $$ 
BEGIN
    -- Drop policies if they exist (wrapped in exception handling)
    BEGIN
        DROP POLICY IF EXISTS "Users can view their own profile" ON users;
        DROP POLICY IF EXISTS "Admins can view all profiles" ON users;
        DROP POLICY IF EXISTS "Users can update their own profile" ON users;
        DROP POLICY IF EXISTS "Admins can update any profile" ON users;
    EXCEPTION
        WHEN undefined_table THEN NULL;
    END;

    BEGIN
        DROP POLICY IF EXISTS "Roles are viewable by all authenticated users" ON roles;
        DROP POLICY IF EXISTS "Only admins can modify roles" ON roles;
    EXCEPTION
        WHEN undefined_table THEN NULL;
    END;

    BEGIN
        DROP POLICY IF EXISTS "Users can view their own telegram accounts" ON telegram_accounts;
        DROP POLICY IF EXISTS "Admins can view all telegram accounts" ON telegram_accounts;
    EXCEPTION
        WHEN undefined_table THEN NULL;
    END;

    BEGIN
        DROP POLICY IF EXISTS "Users can view their own sessions" ON telegram_sessions;
        DROP POLICY IF EXISTS "Admins can view all sessions" ON telegram_sessions;
    EXCEPTION
        WHEN undefined_table THEN NULL;
    END;
END $$;

-- Disable RLS on tables if it exists
ALTER TABLE IF EXISTS users DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS roles DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS telegram_accounts DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS telegram_sessions DISABLE ROW LEVEL SECURITY;

-- Drop all functions with any signature
DO $$ 
DECLARE 
    _sql text;
BEGIN
    FOR _sql IN 
        SELECT 'DROP FUNCTION IF EXISTS ' || oid::regproc || ' CASCADE;'
        FROM pg_proc 
        WHERE proname IN ('link_telegram_account', 'register_telegram_user', 'register_user', 'update_updated_at_column')
    LOOP
        EXECUTE _sql;
    END LOOP;
END $$;

-- Drop tables with CASCADE to handle dependencies
DROP TABLE IF EXISTS telegram_sessions CASCADE;
DROP TABLE IF EXISTS telegram_accounts CASCADE;
DROP TABLE IF EXISTS user_roles CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS roles CASCADE;

-- Reset client message level
SET client_min_messages TO NOTICE;

-- Drop any remaining auth-related types
DROP TYPE IF EXISTS user_role; 