-- LISWMC Database Initialization Script
-- This script sets up the initial database structure for the LISWMC platform

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS zoning;
CREATE SCHEMA IF NOT EXISTS shared;

-- Set search path to include all schemas
ALTER DATABASE liswmc_db SET search_path TO public, analytics, zoning, shared, postgis;

-- Create analytics tables
CREATE TABLE IF NOT EXISTS analytics.companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    unified_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analytics.vehicles (
    id SERIAL PRIMARY KEY,
    plate_number VARCHAR(50) NOT NULL,
    clean_plate VARCHAR(50),
    company_id INTEGER REFERENCES analytics.companies(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analytics.weigh_events (
    id SERIAL PRIMARY KEY,
    vehicle_id INTEGER REFERENCES analytics.vehicles(id),
    weight_in DECIMAL(10,2),
    weight_out DECIMAL(10,2),
    net_weight DECIMAL(10,2),
    event_date TIMESTAMP,
    location VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create zoning tables
CREATE TABLE IF NOT EXISTS zoning.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'planner',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS zoning.zones (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    geometry GEOMETRY(POLYGON, 4326),
    area_sqkm DECIMAL(10,4),
    zone_type VARCHAR(50),
    parent_zone_id INTEGER REFERENCES zoning.zones(id),
    created_by INTEGER REFERENCES zoning.users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    import_source VARCHAR(50),
    import_metadata JSONB,
    original_csv_data TEXT
);

CREATE TABLE IF NOT EXISTS zoning.csv_imports (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255),
    uploaded_by INTEGER REFERENCES zoning.users(id),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_size INTEGER,
    rows_processed INTEGER,
    zones_created INTEGER,
    import_status VARCHAR(50),
    error_log TEXT,
    file_path VARCHAR(500)
);

-- Create shared tables
CREATE TABLE IF NOT EXISTS shared.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_companies_name ON analytics.companies(name);
CREATE INDEX IF NOT EXISTS idx_companies_unified_name ON analytics.companies(unified_name);
CREATE INDEX IF NOT EXISTS idx_vehicles_plate ON analytics.vehicles(plate_number);
CREATE INDEX IF NOT EXISTS idx_vehicles_clean_plate ON analytics.vehicles(clean_plate);
CREATE INDEX IF NOT EXISTS idx_weigh_events_date ON analytics.weigh_events(event_date);
CREATE INDEX IF NOT EXISTS idx_weigh_events_location ON analytics.weigh_events(location);
CREATE INDEX IF NOT EXISTS idx_zones_geometry ON zoning.zones USING GIST(geometry);
CREATE INDEX IF NOT EXISTS idx_zones_type ON zoning.zones(zone_type);
CREATE INDEX IF NOT EXISTS idx_zones_parent ON zoning.zones(parent_zone_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON zoning.users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON zoning.users(email);
CREATE INDEX IF NOT EXISTS idx_shared_users_username ON shared.users(username);
CREATE INDEX IF NOT EXISTS idx_shared_users_email ON shared.users(email);

-- Insert default admin user for zoning system
INSERT INTO zoning.users (username, email, password_hash, role) 
VALUES ('admin', 'admin@liswmc.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewLJyDVLRqrjfTKW', 'admin')
ON CONFLICT (username) DO NOTHING;

-- Insert default admin user for shared system
INSERT INTO shared.users (username, email, password_hash, role) 
VALUES ('admin', 'admin@liswmc.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewLJyDVLRqrjfTKW', 'admin')
ON CONFLICT (username) DO NOTHING;

-- Create sample data for testing
INSERT INTO analytics.companies (name, unified_name) VALUES
('Lusaka Waste Management', 'Lusaka Waste Management'),
('Green City Services', 'Green City Services'),
('Clean Environment Ltd', 'Clean Environment Ltd')
ON CONFLICT DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA analytics TO liswmc_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA zoning TO liswmc_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA shared TO liswmc_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA analytics TO liswmc_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA zoning TO liswmc_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA shared TO liswmc_user;

-- Create functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_companies_updated_at 
    BEFORE UPDATE ON analytics.companies 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vehicles_updated_at 
    BEFORE UPDATE ON analytics.vehicles 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_zones_updated_at 
    BEFORE UPDATE ON zoning.zones 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_zoning_users_updated_at 
    BEFORE UPDATE ON zoning.users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_shared_users_updated_at 
    BEFORE UPDATE ON shared.users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create views for common queries
CREATE OR REPLACE VIEW analytics.weigh_events_with_details AS
SELECT 
    we.id,
    we.weight_in,
    we.weight_out,
    we.net_weight,
    we.event_date,
    we.location,
    v.plate_number,
    v.clean_plate,
    c.name as company_name,
    c.unified_name as company_unified_name
FROM analytics.weigh_events we
JOIN analytics.vehicles v ON we.vehicle_id = v.id
JOIN analytics.companies c ON v.company_id = c.id;

CREATE OR REPLACE VIEW zoning.zones_with_creator AS
SELECT 
    z.id,
    z.name,
    z.description,
    z.geometry,
    z.area_sqkm,
    z.zone_type,
    z.parent_zone_id,
    z.created_at,
    z.updated_at,
    u.username as created_by_username
FROM zoning.zones z
JOIN zoning.users u ON z.created_by = u.id;

-- Grant permissions on views
GRANT SELECT ON analytics.weigh_events_with_details TO liswmc_user;
GRANT SELECT ON zoning.zones_with_creator TO liswmc_user;