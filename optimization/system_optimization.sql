-- FACT System Database Optimization
-- Advanced indexing, query optimization, and performance enhancements
-- for PostgreSQL and SQLite compatibility

-- =======================
-- INDEX OPTIMIZATIONS
-- =======================

-- Advanced text search indexes for knowledge base
CREATE INDEX IF NOT EXISTS idx_knowledge_base_question_gin 
    ON knowledge_base USING GIN (to_tsvector('english', question));

CREATE INDEX IF NOT EXISTS idx_knowledge_base_answer_gin 
    ON knowledge_base USING GIN (to_tsvector('english', answer));

CREATE INDEX IF NOT EXISTS idx_knowledge_base_combined_text_gin 
    ON knowledge_base USING GIN (to_tsvector('english', question || ' ' || answer));

-- Multi-column indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_knowledge_base_category_state_priority 
    ON knowledge_base (category, state, priority);

CREATE INDEX IF NOT EXISTS idx_knowledge_base_state_category_difficulty 
    ON knowledge_base (state, category, difficulty);

CREATE INDEX IF NOT EXISTS idx_knowledge_base_priority_updated 
    ON knowledge_base (priority, updated_at DESC);

-- Partial indexes for high-priority content
CREATE INDEX IF NOT EXISTS idx_knowledge_base_high_priority 
    ON knowledge_base (question, answer) 
    WHERE priority = 'high';

CREATE INDEX IF NOT EXISTS idx_knowledge_base_critical_priority 
    ON knowledge_base (question, answer) 
    WHERE priority = 'critical';

-- State-specific indexes for geographic queries
CREATE INDEX IF NOT EXISTS idx_knowledge_base_georgia 
    ON knowledge_base (question, answer, category) 
    WHERE state = 'GA';

CREATE INDEX IF NOT EXISTS idx_knowledge_base_california 
    ON knowledge_base (question, answer, category) 
    WHERE state = 'CA';

CREATE INDEX IF NOT EXISTS idx_knowledge_base_florida 
    ON knowledge_base (question, answer, category) 
    WHERE state = 'FL';

-- Performance indexes for benchmarks and metrics
CREATE INDEX IF NOT EXISTS idx_benchmarks_test_date_desc 
    ON benchmarks (test_date DESC);

CREATE INDEX IF NOT EXISTS idx_benchmarks_duration_performance 
    ON benchmarks (duration_ms, cache_hit_rate, success_rate);

-- Covering indexes for common queries
CREATE INDEX IF NOT EXISTS idx_knowledge_base_search_cover 
    ON knowledge_base (category, state, priority) 
    INCLUDE (question, answer, tags, difficulty);

-- =======================
-- QUERY OPTIMIZATIONS
-- =======================

-- Create materialized view for popular queries (PostgreSQL only)
-- Uncomment for PostgreSQL deployment
/*
CREATE MATERIALIZED VIEW IF NOT EXISTS popular_knowledge_queries AS
SELECT 
    category,
    state,
    COUNT(*) as query_count,
    AVG(LENGTH(answer)) as avg_answer_length,
    MIN(updated_at) as earliest_update,
    MAX(updated_at) as latest_update
FROM knowledge_base 
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY category, state
HAVING COUNT(*) > 5
ORDER BY query_count DESC;

CREATE INDEX ON popular_knowledge_queries (category, state);
*/

-- Function for intelligent text search ranking
-- SQLite compatible version
CREATE TABLE IF NOT EXISTS search_rankings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_pattern TEXT NOT NULL,
    knowledge_id INTEGER NOT NULL,
    relevance_score REAL DEFAULT 1.0,
    query_count INTEGER DEFAULT 1,
    success_rate REAL DEFAULT 1.0,
    avg_response_time_ms REAL DEFAULT 100.0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (knowledge_id) REFERENCES knowledge_base (id)
);

CREATE INDEX IF NOT EXISTS idx_search_rankings_pattern 
    ON search_rankings (query_pattern);

CREATE INDEX IF NOT EXISTS idx_search_rankings_score 
    ON search_rankings (relevance_score DESC, success_rate DESC);

-- =======================
-- PERFORMANCE MONITORING
-- =======================

-- Query performance tracking table
CREATE TABLE IF NOT EXISTS query_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_hash TEXT NOT NULL,
    query_pattern TEXT NOT NULL,
    execution_time_ms REAL NOT NULL,
    cache_hit BOOLEAN DEFAULT FALSE,
    success BOOLEAN DEFAULT TRUE,
    confidence_score REAL DEFAULT 0.0,
    result_count INTEGER DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_query_performance_hash 
    ON query_performance (query_hash);

CREATE INDEX IF NOT EXISTS idx_query_performance_pattern 
    ON query_performance (query_pattern, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_query_performance_time 
    ON query_performance (execution_time_ms DESC);

-- Cache performance tracking
CREATE TABLE IF NOT EXISTS cache_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_operation TEXT NOT NULL, -- 'hit', 'miss', 'store', 'evict'
    query_hash TEXT,
    operation_time_ms REAL,
    cache_size_bytes INTEGER,
    hit_rate REAL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cache_performance_timestamp 
    ON cache_performance (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_cache_performance_operation 
    ON cache_performance (cache_operation, timestamp DESC);

-- =======================
-- DATA OPTIMIZATION
-- =======================

-- Optimize storage for text fields
-- Add compression hints for large text fields (PostgreSQL)
-- ALTER TABLE knowledge_base ALTER COLUMN answer SET STORAGE EXTERNAL;
-- ALTER TABLE knowledge_base ALTER COLUMN question SET STORAGE EXTERNAL;

-- Update statistics for better query planning
-- ANALYZE knowledge_base;
-- ANALYZE benchmarks;
-- ANALYZE search_rankings;

-- =======================
-- MAINTENANCE PROCEDURES
-- =======================

-- Cleanup old performance data (keep last 30 days)
DELETE FROM query_performance 
WHERE timestamp < datetime('now', '-30 days');

DELETE FROM cache_performance 
WHERE timestamp < datetime('now', '-30 days');

-- Update search rankings based on query performance
INSERT OR REPLACE INTO search_rankings (
    query_pattern, 
    knowledge_id, 
    relevance_score, 
    query_count, 
    success_rate, 
    avg_response_time_ms,
    last_updated
)
SELECT 
    qp.query_pattern,
    kb.id as knowledge_id,
    -- Calculate relevance score based on success rate and response time
    CASE 
        WHEN avg_success_rate > 0.8 AND avg_time < 100 THEN 1.0
        WHEN avg_success_rate > 0.6 AND avg_time < 150 THEN 0.8
        WHEN avg_success_rate > 0.4 THEN 0.6
        ELSE 0.4
    END as relevance_score,
    query_count,
    avg_success_rate,
    avg_time,
    CURRENT_TIMESTAMP
FROM (
    SELECT 
        query_pattern,
        COUNT(*) as query_count,
        AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as avg_success_rate,
        AVG(execution_time_ms) as avg_time
    FROM query_performance 
    WHERE timestamp >= datetime('now', '-7 days')
    GROUP BY query_pattern
    HAVING COUNT(*) >= 3
) qp
CROSS JOIN knowledge_base kb
WHERE kb.category IN (
    SELECT DISTINCT category 
    FROM knowledge_base 
    WHERE question LIKE '%' || substr(qp.query_pattern, 1, 20) || '%'
    OR answer LIKE '%' || substr(qp.query_pattern, 1, 20) || '%'
);

-- =======================
-- OPTIMIZATION VIEWS
-- =======================

-- View for query performance analysis
CREATE VIEW IF NOT EXISTS query_performance_summary AS
SELECT 
    query_pattern,
    COUNT(*) as total_queries,
    AVG(execution_time_ms) as avg_response_time,
    AVG(CASE WHEN cache_hit THEN 1.0 ELSE 0.0 END) as cache_hit_rate,
    AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate,
    AVG(confidence_score) as avg_confidence,
    MIN(timestamp) as first_seen,
    MAX(timestamp) as last_seen
FROM query_performance 
GROUP BY query_pattern
ORDER BY total_queries DESC;

-- View for cache efficiency analysis
CREATE VIEW IF NOT EXISTS cache_efficiency_summary AS
SELECT 
    date(timestamp) as date,
    cache_operation,
    COUNT(*) as operation_count,
    AVG(operation_time_ms) as avg_operation_time,
    AVG(hit_rate) as avg_hit_rate
FROM cache_performance
GROUP BY date(timestamp), cache_operation
ORDER BY date DESC, cache_operation;

-- View for knowledge base utilization
CREATE VIEW IF NOT EXISTS knowledge_utilization AS
SELECT 
    kb.id,
    kb.category,
    kb.state,
    kb.priority,
    COALESCE(usage.query_count, 0) as times_accessed,
    COALESCE(usage.avg_confidence, 0) as avg_confidence_when_used,
    COALESCE(usage.last_accessed, kb.created_at) as last_accessed
FROM knowledge_base kb
LEFT JOIN (
    SELECT 
        kb2.id,
        COUNT(*) as query_count,
        AVG(qp.confidence_score) as avg_confidence,
        MAX(qp.timestamp) as last_accessed
    FROM knowledge_base kb2
    JOIN query_performance qp ON (
        qp.query_pattern LIKE '%' || substr(kb2.question, 1, 20) || '%'
        OR qp.query_pattern LIKE '%' || substr(kb2.answer, 1, 20) || '%'
    )
    WHERE qp.success = 1
    GROUP BY kb2.id
) usage ON kb.id = usage.id
ORDER BY times_accessed DESC;

-- =======================
-- AUTOMATED MAINTENANCE
-- =======================

-- Trigger to update search rankings on successful queries
-- Note: Triggers may need adjustment based on specific database engine
CREATE TRIGGER IF NOT EXISTS update_search_rankings_on_success
    AFTER INSERT ON query_performance
    WHEN NEW.success = 1 AND NEW.confidence_score > 0.7
BEGIN
    INSERT OR IGNORE INTO search_rankings (
        query_pattern, 
        knowledge_id, 
        relevance_score,
        query_count,
        success_rate,
        avg_response_time_ms
    )
    SELECT 
        NEW.query_pattern,
        kb.id,
        CASE 
            WHEN NEW.confidence_score > 0.9 THEN 1.0
            WHEN NEW.confidence_score > 0.8 THEN 0.9
            WHEN NEW.confidence_score > 0.7 THEN 0.8
            ELSE 0.6
        END,
        1,
        1.0,
        NEW.execution_time_ms
    FROM knowledge_base kb
    WHERE kb.question LIKE '%' || substr(NEW.query_pattern, 1, 30) || '%'
       OR kb.answer LIKE '%' || substr(NEW.query_pattern, 1, 30) || '%'
    LIMIT 3; -- Limit to top 3 matches
END;

-- =======================
-- OPTIMIZATION SETTINGS
-- =======================

-- SQLite specific optimizations (uncomment for SQLite)
-- PRAGMA journal_mode = WAL;
-- PRAGMA synchronous = NORMAL;
-- PRAGMA cache_size = 10000;
-- PRAGMA temp_store = memory;
-- PRAGMA mmap_size = 268435456; -- 256MB

-- PostgreSQL specific optimizations (uncomment for PostgreSQL)
-- ALTER SYSTEM SET shared_buffers = '256MB';
-- ALTER SYSTEM SET effective_cache_size = '1GB';
-- ALTER SYSTEM SET maintenance_work_mem = '64MB';
-- ALTER SYSTEM SET checkpoint_completion_target = 0.9;
-- ALTER SYSTEM SET wal_buffers = '16MB';
-- ALTER SYSTEM SET default_statistics_target = 100;

-- =======================
-- MONITORING QUERIES
-- =======================

-- Query to check index usage
-- SELECT name, sql FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%';

-- Query to check table sizes
-- SELECT name, COUNT(*) as row_count FROM (
--     SELECT 'knowledge_base' as name UNION ALL
--     SELECT 'query_performance' UNION ALL
--     SELECT 'cache_performance' UNION ALL
--     SELECT 'search_rankings'
-- ) tables 
-- JOIN knowledge_base ON tables.name = 'knowledge_base'
-- GROUP BY name;

-- Performance monitoring query
/*
SELECT 
    'Cache Hit Rate' as metric,
    ROUND(AVG(CASE WHEN cache_hit THEN 100.0 ELSE 0.0 END), 2) || '%' as value
FROM query_performance
WHERE timestamp >= datetime('now', '-1 hour')
UNION ALL
SELECT 
    'Avg Response Time' as metric,
    ROUND(AVG(execution_time_ms), 2) || 'ms' as value
FROM query_performance
WHERE timestamp >= datetime('now', '-1 hour')
UNION ALL
SELECT 
    'Success Rate' as metric,
    ROUND(AVG(CASE WHEN success THEN 100.0 ELSE 0.0 END), 2) || '%' as value
FROM query_performance
WHERE timestamp >= datetime('now', '-1 hour');
*/