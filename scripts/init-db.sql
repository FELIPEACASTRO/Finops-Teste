-- FinOps-Teste Database Initialization Script
-- This script creates the initial database schema for the FinOps platform

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create custom types
CREATE TYPE resource_type AS ENUM (
    'ec2', 'rds', 's3', 'lambda', 'elb', 'ebs', 
    'cloudfront', 'route53', 'vpc', 'dynamodb',
    'ecs', 'eks', 'fargate', 'batch', 'lightsail'
);

CREATE TYPE cost_category AS ENUM (
    'compute', 'storage', 'network', 'database', 
    'security', 'monitoring', 'other'
);

CREATE TYPE optimization_status AS ENUM (
    'pending', 'applied', 'rejected', 'expired'
);

-- Cloud Resources Table
CREATE TABLE cloud_resources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resource_id VARCHAR(255) NOT NULL,
    resource_type resource_type NOT NULL,
    name VARCHAR(255) NOT NULL,
    region VARCHAR(50) NOT NULL,
    account_id VARCHAR(20) NOT NULL,
    tags JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for cloud_resources
CREATE INDEX idx_cloud_resources_resource_id ON cloud_resources(resource_id);
CREATE INDEX idx_cloud_resources_type ON cloud_resources(resource_type);
CREATE INDEX idx_cloud_resources_region ON cloud_resources(region);
CREATE INDEX idx_cloud_resources_account ON cloud_resources(account_id);
CREATE INDEX idx_cloud_resources_tags ON cloud_resources USING GIN(tags);
CREATE INDEX idx_cloud_resources_created_at ON cloud_resources(created_at);

-- Cost Entries Table
CREATE TABLE cost_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resource_id UUID NOT NULL REFERENCES cloud_resources(id) ON DELETE CASCADE,
    cost_amount DECIMAL(12, 2) NOT NULL CHECK (cost_amount >= 0),
    cost_currency VARCHAR(3) DEFAULT 'USD',
    category cost_category NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    usage_metrics JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT valid_time_range CHECK (end_time > start_time)
);

-- Create indexes for cost_entries
CREATE INDEX idx_cost_entries_resource_id ON cost_entries(resource_id);
CREATE INDEX idx_cost_entries_time_range ON cost_entries(start_time, end_time);
CREATE INDEX idx_cost_entries_category ON cost_entries(category);
CREATE INDEX idx_cost_entries_amount ON cost_entries(cost_amount);
CREATE INDEX idx_cost_entries_created_at ON cost_entries(created_at);

-- Optimization Recommendations Table
CREATE TABLE optimization_recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resource_id UUID NOT NULL REFERENCES cloud_resources(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    potential_savings_amount DECIMAL(12, 2) NOT NULL CHECK (potential_savings_amount >= 0),
    potential_savings_currency VARCHAR(3) DEFAULT 'USD',
    confidence_score DECIMAL(3, 2) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    status optimization_status DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    applied_at TIMESTAMP WITH TIME ZONE,
    rejected_at TIMESTAMP WITH TIME ZONE,
    rejection_reason TEXT
);

-- Create indexes for optimization_recommendations
CREATE INDEX idx_optimization_recommendations_resource_id ON optimization_recommendations(resource_id);
CREATE INDEX idx_optimization_recommendations_status ON optimization_recommendations(status);
CREATE INDEX idx_optimization_recommendations_savings ON optimization_recommendations(potential_savings_amount);
CREATE INDEX idx_optimization_recommendations_confidence ON optimization_recommendations(confidence_score);
CREATE INDEX idx_optimization_recommendations_created_at ON optimization_recommendations(created_at);

-- Budgets Table
CREATE TABLE budgets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    amount DECIMAL(12, 2) NOT NULL CHECK (amount > 0),
    spent DECIMAL(12, 2) DEFAULT 0 CHECK (spent >= 0),
    currency VARCHAR(3) DEFAULT 'USD',
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    cost_center VARCHAR(100) NOT NULL,
    alert_thresholds DECIMAL[] DEFAULT ARRAY[0.8, 0.9, 1.0],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT valid_date_range CHECK (end_date > start_date)
);

-- Create indexes for budgets
CREATE INDEX idx_budgets_cost_center ON budgets(cost_center);
CREATE INDEX idx_budgets_date_range ON budgets(start_date, end_date);
CREATE INDEX idx_budgets_utilization ON budgets((spent/amount));
CREATE INDEX idx_budgets_created_at ON budgets(created_at);

-- Users Table (for authentication)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active);
CREATE INDEX idx_users_created_at ON users(created_at);

-- Audit Log Table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for audit_logs
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_cloud_resources_updated_at 
    BEFORE UPDATE ON cloud_resources 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_budgets_updated_at 
    BEFORE UPDATE ON budgets 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create views for common queries
CREATE VIEW resource_cost_summary AS
SELECT 
    r.id,
    r.resource_id,
    r.resource_type,
    r.name,
    r.region,
    r.account_id,
    COALESCE(SUM(c.cost_amount), 0) as total_cost,
    COUNT(c.id) as cost_entries_count,
    MAX(c.created_at) as last_cost_update
FROM cloud_resources r
LEFT JOIN cost_entries c ON r.id = c.resource_id
GROUP BY r.id, r.resource_id, r.resource_type, r.name, r.region, r.account_id;

CREATE VIEW budget_utilization AS
SELECT 
    id,
    name,
    amount,
    spent,
    currency,
    cost_center,
    (spent / amount * 100) as utilization_percentage,
    (amount - spent) as remaining_budget,
    CASE 
        WHEN spent / amount >= 1.0 THEN 'over_budget'
        WHEN spent / amount >= 0.9 THEN 'critical'
        WHEN spent / amount >= 0.8 THEN 'warning'
        ELSE 'normal'
    END as status,
    start_date,
    end_date
FROM budgets;

CREATE VIEW optimization_summary AS
SELECT 
    r.resource_type,
    r.region,
    COUNT(o.id) as total_recommendations,
    COUNT(CASE WHEN o.status = 'pending' THEN 1 END) as pending_recommendations,
    COUNT(CASE WHEN o.status = 'applied' THEN 1 END) as applied_recommendations,
    SUM(CASE WHEN o.status = 'pending' THEN o.potential_savings_amount ELSE 0 END) as potential_savings,
    SUM(CASE WHEN o.status = 'applied' THEN o.potential_savings_amount ELSE 0 END) as realized_savings
FROM cloud_resources r
LEFT JOIN optimization_recommendations o ON r.id = o.resource_id
GROUP BY r.resource_type, r.region;

-- Insert sample data for development
INSERT INTO users (email, password_hash, full_name, is_superuser) VALUES
('admin@finops.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj1yFqLgHWCO', 'Admin User', true),
('user@finops.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj1yFqLgHWCO', 'Regular User', false);

-- Insert sample cloud resources
INSERT INTO cloud_resources (resource_id, resource_type, name, region, account_id, tags) VALUES
('i-1234567890abcdef0', 'ec2', 'web-server-01', 'us-east-1', '123456789012', '{"Environment": "production", "Team": "backend", "CostCenter": "engineering"}'),
('i-0987654321fedcba0', 'ec2', 'worker-01', 'us-west-2', '123456789012', '{"Environment": "production", "Team": "data", "CostCenter": "engineering"}'),
('db-instance-1', 'rds', 'main-database', 'us-east-1', '123456789012', '{"Environment": "production", "Team": "backend", "CostCenter": "engineering"}'),
('my-bucket', 's3', 'data-lake-bucket', 'us-east-1', '123456789012', '{"Environment": "production", "Team": "data", "CostCenter": "engineering"}'),
('my-lambda-function', 'lambda', 'data-processor', 'us-east-1', '123456789012', '{"Environment": "production", "Team": "data", "CostCenter": "engineering"}');

-- Insert sample cost entries
INSERT INTO cost_entries (resource_id, cost_amount, category, start_time, end_time, usage_metrics) 
SELECT 
    r.id,
    (random() * 100 + 10)::decimal(12,2),
    CASE r.resource_type 
        WHEN 'ec2' THEN 'compute'
        WHEN 'rds' THEN 'database'
        WHEN 's3' THEN 'storage'
        WHEN 'lambda' THEN 'compute'
        ELSE 'other'
    END::cost_category,
    NOW() - INTERVAL '30 days',
    NOW() - INTERVAL '29 days',
    '{"cpu_utilization": 45.2, "memory_utilization": 67.8}'::jsonb
FROM cloud_resources r;

-- Insert sample budgets
INSERT INTO budgets (name, amount, spent, cost_center, start_date, end_date) VALUES
('Engineering Q4 2024', 10000.00, 7500.00, 'engineering', '2024-10-01', '2024-12-31'),
('Data Team Monthly', 2000.00, 1200.00, 'data', '2024-11-01', '2024-11-30'),
('Infrastructure Annual', 50000.00, 35000.00, 'infrastructure', '2024-01-01', '2024-12-31');

-- Insert sample optimization recommendations
INSERT INTO optimization_recommendations (resource_id, title, description, potential_savings_amount, confidence_score)
SELECT 
    r.id,
    'Downsize ' || r.resource_type || ' instance',
    'Resource shows low utilization and can be downsized to reduce costs',
    (random() * 200 + 50)::decimal(12,2),
    (random() * 0.3 + 0.7)::decimal(3,2)
FROM cloud_resources r
WHERE r.resource_type IN ('ec2', 'rds')
LIMIT 3;

-- Create function to calculate cost trends
CREATE OR REPLACE FUNCTION calculate_cost_trend(
    p_resource_id UUID,
    p_days INTEGER DEFAULT 30
) RETURNS DECIMAL AS $$
DECLARE
    current_period_cost DECIMAL;
    previous_period_cost DECIMAL;
    trend_percentage DECIMAL;
BEGIN
    -- Calculate current period cost
    SELECT COALESCE(SUM(cost_amount), 0) INTO current_period_cost
    FROM cost_entries
    WHERE resource_id = p_resource_id
    AND start_time >= NOW() - INTERVAL '1 day' * p_days;
    
    -- Calculate previous period cost
    SELECT COALESCE(SUM(cost_amount), 0) INTO previous_period_cost
    FROM cost_entries
    WHERE resource_id = p_resource_id
    AND start_time >= NOW() - INTERVAL '1 day' * (p_days * 2)
    AND start_time < NOW() - INTERVAL '1 day' * p_days;
    
    -- Calculate trend percentage
    IF previous_period_cost > 0 THEN
        trend_percentage := ((current_period_cost - previous_period_cost) / previous_period_cost) * 100;
    ELSE
        trend_percentage := 0;
    END IF;
    
    RETURN trend_percentage;
END;
$$ LANGUAGE plpgsql;

-- Create function to get resource utilization
CREATE OR REPLACE FUNCTION get_resource_utilization(
    p_resource_id UUID,
    p_metric_name VARCHAR DEFAULT 'cpu_utilization'
) RETURNS DECIMAL AS $$
DECLARE
    avg_utilization DECIMAL;
BEGIN
    SELECT AVG((usage_metrics->>p_metric_name)::decimal) INTO avg_utilization
    FROM cost_entries
    WHERE resource_id = p_resource_id
    AND usage_metrics ? p_metric_name
    AND start_time >= NOW() - INTERVAL '7 days';
    
    RETURN COALESCE(avg_utilization, 0);
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO finops_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO finops_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO finops_user;

-- Create indexes for performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cost_entries_resource_time 
ON cost_entries(resource_id, start_time DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cost_entries_time_amount 
ON cost_entries(start_time DESC, cost_amount DESC);

-- Analyze tables for better query planning
ANALYZE cloud_resources;
ANALYZE cost_entries;
ANALYZE optimization_recommendations;
ANALYZE budgets;
ANALYZE users;
ANALYZE audit_logs;