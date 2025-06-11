-- Rollback Migration: 001_rollback_users_table.sql
-- Description: Drop liswmc_users table and related objects
-- Date: 2025-01-11

-- Drop trigger first
DROP TRIGGER IF EXISTS update_liswmc_users_updated_at ON liswmc_users;

-- Drop function
DROP FUNCTION IF EXISTS update_updated_at_column();

-- Drop indexes
DROP INDEX IF EXISTS idx_liswmc_users_username;
DROP INDEX IF EXISTS idx_liswmc_users_email;
DROP INDEX IF EXISTS idx_liswmc_users_role;
DROP INDEX IF EXISTS idx_liswmc_users_is_active;

-- Drop table
DROP TABLE IF EXISTS liswmc_users; 