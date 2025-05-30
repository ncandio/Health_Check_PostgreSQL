-- SQL schema for SiteSentinel with enhanced real-time monitoring capabilities

-- Table to store website configurations
CREATE TABLE IF NOT EXISTS website_configs (
    id SERIAL PRIMARY KEY,
    url VARCHAR(2048) NOT NULL,
    check_interval_seconds INTEGER NOT NULL CHECK (check_interval_seconds BETWEEN 5 AND 300),
    regex_pattern VARCHAR(1024),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Enhanced table to store monitoring results with detailed performance metrics
CREATE TABLE IF NOT EXISTS monitoring_results (
    id SERIAL PRIMARY KEY,
    website_id INTEGER REFERENCES website_configs(id),
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    response_time_ms FLOAT,
    http_status INTEGER,
    success BOOLEAN NOT NULL,
    regex_matched BOOLEAN,
    failure_reason TEXT,
    -- New fields for enhanced monitoring
    content_size_bytes INTEGER,
    dns_lookup_time_ms FLOAT,
    connection_time_ms FLOAT,
    tls_handshake_time_ms FLOAT,
    server_processing_time_ms FLOAT,
    content_transfer_time_ms FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- JSONB field for storing arbitrary details and debugging info
    check_details JSONB
);

-- Proper indexes for PostgreSQL
CREATE INDEX IF NOT EXISTS idx_monitoring_website_id ON monitoring_results(website_id);
CREATE INDEX IF NOT EXISTS idx_monitoring_checked_at ON monitoring_results(checked_at);
CREATE INDEX IF NOT EXISTS idx_monitoring_success ON monitoring_results(success);
CREATE INDEX IF NOT EXISTS idx_monitoring_http_status ON monitoring_results(http_status);
CREATE INDEX IF NOT EXISTS idx_website_configs_is_active ON website_configs(is_active);

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to update the updated_at column
CREATE TRIGGER update_website_configs_updated_at
BEFORE UPDATE ON website_configs
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- View for real-time monitoring dashboard
CREATE OR REPLACE VIEW vw_monitoring_summary AS
SELECT 
    wc.url,
    COUNT(*) AS total_checks,
    SUM(CASE WHEN mr.success THEN 1 ELSE 0 END) AS successful_checks,
    ROUND(AVG(mr.response_time_ms)::numeric, 2) AS avg_response_time_ms,
    MAX(mr.checked_at) AS last_check_time,
    MIN(CASE WHEN NOT mr.success THEN mr.checked_at ELSE NULL END) AS last_failure_time,
    SUM(CASE WHEN NOT mr.success THEN 1 ELSE 0 END) AS failure_count
FROM 
    website_configs wc
JOIN 
    monitoring_results mr ON wc.id = mr.website_id
WHERE 
    mr.checked_at > NOW() - INTERVAL '24 hours'
GROUP BY 
    wc.url
ORDER BY 
    failure_count DESC, avg_response_time_ms DESC;

-- Table for storing daily monitoring statistics for historical tracking
CREATE TABLE IF NOT EXISTS monitoring_stats (
    id SERIAL PRIMARY KEY,
    website_id INTEGER NOT NULL REFERENCES website_configs(id),
    day_date DATE NOT NULL,
    total_checks INTEGER NOT NULL,
    successful_checks INTEGER NOT NULL,
    avg_response_time_ms FLOAT,
    min_response_time_ms FLOAT,
    max_response_time_ms FLOAT,
    failure_count INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(website_id, day_date)
);

CREATE INDEX IF NOT EXISTS idx_monitoring_stats_website_id ON monitoring_stats(website_id);
CREATE INDEX IF NOT EXISTS idx_monitoring_stats_day_date ON monitoring_stats(day_date);

-- Function to clean up old monitoring results and summarize them into statistics
CREATE OR REPLACE FUNCTION cleanup_old_monitoring_results()
RETURNS void AS $$
BEGIN
    -- First, summarize data older than 7 days into monitoring_stats
    INSERT INTO monitoring_stats (
        website_id, 
        day_date,
        total_checks,
        successful_checks,
        avg_response_time_ms,
        min_response_time_ms,
        max_response_time_ms,
        failure_count
    )
    SELECT 
        website_id,
        DATE_TRUNC('day', checked_at)::date AS day_date,
        COUNT(*) AS total_checks,
        SUM(CASE WHEN success THEN 1 ELSE 0 END) AS successful_checks,
        ROUND(AVG(response_time_ms)::numeric, 2) AS avg_response_time_ms,
        MIN(response_time_ms) AS min_response_time_ms,
        MAX(response_time_ms) AS max_response_time_ms,
        SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) AS failure_count
    FROM 
        monitoring_results
    WHERE 
        checked_at < NOW() - INTERVAL '7 days'
        AND checked_at > NOW() - INTERVAL '8 days'
    GROUP BY 
        website_id, DATE_TRUNC('day', checked_at)::date
    ON CONFLICT (website_id, day_date) 
    DO UPDATE SET
        total_checks = monitoring_stats.total_checks + EXCLUDED.total_checks,
        successful_checks = monitoring_stats.successful_checks + EXCLUDED.successful_checks,
        avg_response_time_ms = (monitoring_stats.avg_response_time_ms * monitoring_stats.total_checks + 
                               EXCLUDED.avg_response_time_ms * EXCLUDED.total_checks) / 
                               (monitoring_stats.total_checks + EXCLUDED.total_checks),
        min_response_time_ms = LEAST(monitoring_stats.min_response_time_ms, EXCLUDED.min_response_time_ms),
        max_response_time_ms = GREATEST(monitoring_stats.max_response_time_ms, EXCLUDED.max_response_time_ms),
        failure_count = monitoring_stats.failure_count + EXCLUDED.failure_count;
    
    -- Then delete the old detailed data
    DELETE FROM monitoring_results
    WHERE checked_at < NOW() - INTERVAL '7 days';
    
    RAISE NOTICE 'Cleanup complete: Summarized and removed monitoring results older than 7 days';
END;
$$ LANGUAGE plpgsql;