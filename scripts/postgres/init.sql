-- ================================
-- PostgreSQL Initialization Script
-- Azure Advisor Reports Platform
-- ================================

-- Create database if not exists (handled by Docker environment)
-- This script runs after the database is created

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create custom types
DO $$
BEGIN
    -- Report status enum
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'report_status') THEN
        CREATE TYPE report_status AS ENUM ('pending', 'processing', 'completed', 'failed');
    END IF;

    -- Client status enum
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'client_status') THEN
        CREATE TYPE client_status AS ENUM ('active', 'inactive', 'suspended');
    END IF;

    -- User role enum
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
        CREATE TYPE user_role AS ENUM ('admin', 'manager', 'analyst', 'viewer');
    END IF;

    -- Report type enum
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'report_type') THEN
        CREATE TYPE report_type AS ENUM ('detailed', 'executive', 'cost', 'security', 'operations');
    END IF;

    -- Business impact enum
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'business_impact') THEN
        CREATE TYPE business_impact AS ENUM ('High', 'Medium', 'Low');
    END IF;

    -- Recommendation category enum
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'recommendation_category') THEN
        CREATE TYPE recommendation_category AS ENUM ('Cost', 'Security', 'Reliability', 'Operational Excellence', 'Performance');
    END IF;
END
$$;

-- Create indexes for performance (will be created by Django migrations, but keeping for reference)
-- These will be created automatically by Django, this is just documentation

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE azure_advisor_reports TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO postgres;

-- Set default search path
ALTER DATABASE azure_advisor_reports SET search_path TO public;

-- Configure PostgreSQL settings for performance
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET pg_stat_statements.track = 'all';
ALTER SYSTEM SET log_statement = 'none';
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries taking more than 1 second
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Create audit log table (for future use)
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(64) NOT NULL,
    record_id UUID,
    action VARCHAR(16) NOT NULL, -- INSERT, UPDATE, DELETE
    old_values JSONB,
    new_values JSONB,
    changed_by VARCHAR(255),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create system configuration table
CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(255) UNIQUE NOT NULL,
    config_value TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default system configuration
INSERT INTO system_config (config_key, config_value, description) VALUES
('max_upload_size', '52428800', 'Maximum file upload size in bytes (50MB)'),
('allowed_file_extensions', 'csv', 'Comma-separated list of allowed file extensions'),
('default_report_type', 'detailed', 'Default report type for new reports'),
('report_retention_days', '365', 'Number of days to retain reports'),
('csv_chunk_size', '1000', 'Chunk size for CSV processing'),
('celery_task_timeout', '300', 'Celery task timeout in seconds'),
('app_version', '1.0.0', 'Current application version'),
('maintenance_mode', 'false', 'Enable maintenance mode')
ON CONFLICT (config_key) DO NOTHING;

-- Create indexes for audit log
CREATE INDEX IF NOT EXISTS idx_audit_log_table_name ON audit_log(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_log_record_id ON audit_log(record_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_changed_at ON audit_log(changed_at DESC);

-- Create indexes for system config
CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(config_key);

COMMIT;