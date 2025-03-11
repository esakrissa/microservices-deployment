-- Insert default roles with their permissions
INSERT INTO roles (name, description, permissions) VALUES
(
  'admin',
  'Administrator with full system access',
  '[
    "read:users",
    "write:users",
    "delete:users",
    "manage:roles",
    "manage:system",
    "manage:telegram"
  ]'::jsonb
),
(
  'moderator',
  'Moderator with user management capabilities',
  '[
    "read:users",
    "write:users",
    "manage:content",
    "read:telegram"
  ]'::jsonb
),
(
  'support',
  'Support staff with limited access',
  '[
    "read:users",
    "read:content",
    "read:telegram"
  ]'::jsonb
),
(
  'user',
  'Regular user with basic access',
  '[
    "read:own_profile",
    "write:own_profile",
    "use:telegram"
  ]'::jsonb
);

-- Insert sample users with hashed passwords
-- Note: These are example hashes for 'password123', replace with real hashed passwords in production
INSERT INTO users (email, username, password_hash, role, permissions) VALUES
(
  'admin@example.com',
  'admin',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj2NXFp/XAyS',
  'admin',
  (SELECT permissions FROM roles WHERE name = 'admin')
),
(
  'moderator@example.com',
  'moderator',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj2NXFp/XAyS',
  'moderator',
  (SELECT permissions FROM roles WHERE name = 'moderator')
),
(
  'support@example.com',
  'support',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj2NXFp/XAyS',
  'support',
  (SELECT permissions FROM roles WHERE name = 'support')
),
(
  'user1@example.com',
  'user1',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj2NXFp/XAyS',
  'user',
  (SELECT permissions FROM roles WHERE name = 'user')
),
(
  'user2@example.com',
  'user2',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj2NXFp/XAyS',
  'user',
  (SELECT permissions FROM roles WHERE name = 'user')
);

-- Insert sample telegram accounts
INSERT INTO telegram_accounts (user_id, telegram_id, username, first_name, last_name) VALUES
(
  (SELECT id FROM users WHERE username = 'admin'),
  '123456789',
  'admin_telegram',
  'Admin',
  'User'
),
(
  (SELECT id FROM users WHERE username = 'moderator'),
  '987654321',
  'mod_telegram',
  'Moderator',
  'User'
),
(
  (SELECT id FROM users WHERE username = 'user1'),
  '123123123',
  'user1_telegram',
  'First',
  'User'
);

-- Insert sample telegram sessions
INSERT INTO telegram_sessions (user_id, telegram_id, token, created_at, last_activity, is_active) VALUES
(
  (SELECT id FROM users WHERE username = 'admin'),
  '123456789',
  'sample_token_admin',
  CURRENT_TIMESTAMP,
  CURRENT_TIMESTAMP,
  true
),
(
  (SELECT id FROM users WHERE username = 'user1'),
  '123123123',
  'sample_token_user1',
  CURRENT_TIMESTAMP,
  CURRENT_TIMESTAMP,
  true
),
(
  (SELECT id FROM users WHERE username = 'user1'),
  '123123123',
  'sample_token_user1_old',
  CURRENT_TIMESTAMP - INTERVAL '1 day',
  CURRENT_TIMESTAMP - INTERVAL '1 day',
  false
); 