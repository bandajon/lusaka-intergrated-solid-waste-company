-- Migration: 001_create_users_table.sql
-- Description: Create liswmc_users table for dashboard authentication
-- Date: 2025-01-11

CREATE TABLE IF NOT EXISTS liswmc_users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE,
    full_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'user', 'viewer')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE
);

-- Create indexes for performance
CREATE INDEX idx_liswmc_users_username ON liswmc_users(username);
CREATE INDEX idx_liswmc_users_email ON liswmc_users(email);
CREATE INDEX idx_liswmc_users_role ON liswmc_users(role);
CREATE INDEX idx_liswmc_users_is_active ON liswmc_users(is_active);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_liswmc_users_updated_at 
    BEFORE UPDATE ON liswmc_users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insert default admin user (password: 'admin123' - change this immediately!)
-- Password hash for 'admin123' using bcrypt
INSERT INTO liswmc_users (username, password_hash, full_name, email, role) 
VALUES (
    'admin', 
    '$2b$12$LQv3c1yqBw7QtD1YP7Y6oeH.XjZjCZN8YP.K6z8QxLqV3rJp2kXOu', 
    'System Administrator',
    'admin@liswmc.com',
    'admin'
) ON CONFLICT (username) DO NOTHING;

-- Insert default viewer user (password: 'viewer123' - change this immediately!)
-- Password hash for 'viewer123' using bcrypt
INSERT INTO liswmc_users (username, password_hash, full_name, email, role) 
VALUES (
    'viewer', 
    '$2b$12$9XnKhJ4q8bPz1gx7vH2yFuL8rR5nS6mE4wQ2aD3cT9kU0pY5iO6vA', 
    'Dashboard Viewer',
    'viewer@liswmc.com',
    'viewer'
) ON CONFLICT (username) DO NOTHING;

COMMENT ON TABLE liswmc_users IS 'User accounts for dashboard authentication';
COMMENT ON COLUMN liswmc_users.role IS 'User role: admin (full access), user (standard access), viewer (read-only)';
COMMENT ON COLUMN liswmc_users.login_attempts IS 'Number of failed login attempts';
COMMENT ON COLUMN liswmc_users.locked_until IS 'Account locked until this timestamp'; 