-- IntentCore Database Schema
-- SQLite database for storing reasoning chains, patterns, and compliance data

-- ===== Reasoning Chains Table =====
-- Complete audit trail of all agent decisions
CREATE TABLE IF NOT EXISTS reasoning_chains (
    -- Primary Key
    chain_id TEXT PRIMARY KEY,

    -- Metadata
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    agent_id TEXT NOT NULL,
    agent_role TEXT NOT NULL,

    -- Task Context
    task TEXT NOT NULL,
    conversation_history JSON,

    -- Reasoning Components (extracted from messages)
    situation TEXT,
    quantitative_analysis JSON,
    options JSON,  -- List of alternatives considered
    selected_action JSON NOT NULL,
    rationale TEXT,
    risks JSON,  -- List of identified risks

    -- Completeness Assessment
    completeness_score REAL DEFAULT 0.0,
    missing_components JSON,

    -- Governance
    policy_results JSON,
    requires_review BOOLEAN DEFAULT FALSE,
    governance_decision TEXT DEFAULT 'pending',  -- pending, approved, rejected, review_required

    -- Human Review
    reviewer_id TEXT,
    review_timestamp TIMESTAMP,
    human_decision TEXT,  -- approved, rejected, modified
    human_rationale TEXT,
    human_modification JSON,

    -- Execution
    execution_status TEXT DEFAULT 'pending',  -- pending, executing, completed, failed
    execution_result JSON,
    execution_timestamp TIMESTAMP,

    -- Learning
    pattern_id TEXT,
    template_id TEXT,
    confidence_score REAL DEFAULT 0.0
);

-- Indexes for reasoning_chains
CREATE INDEX IF NOT EXISTS idx_rc_timestamp ON reasoning_chains(timestamp);
CREATE INDEX IF NOT EXISTS idx_rc_agent_id ON reasoning_chains(agent_id);
CREATE INDEX IF NOT EXISTS idx_rc_governance_decision ON reasoning_chains(governance_decision);
CREATE INDEX IF NOT EXISTS idx_rc_requires_review ON reasoning_chains(requires_review);
CREATE INDEX IF NOT EXISTS idx_rc_human_decision ON reasoning_chains(human_decision);

-- ===== Patterns Table =====
-- Detected recurring reasoning patterns
CREATE TABLE IF NOT EXISTS reasoning_patterns (
    -- Primary Key
    pattern_id TEXT PRIMARY KEY,

    -- Pattern Identity
    pattern_name TEXT NOT NULL,
    description TEXT,

    -- Pattern Signature
    situation_template JSON,
    decision_template JSON,

    -- Metrics
    occurrence_count INTEGER DEFAULT 0,
    approval_rate REAL DEFAULT 0.0,
    modification_rate REAL DEFAULT 0.0,
    avg_review_time REAL,  -- seconds
    confidence REAL DEFAULT 0.0,

    -- Automation
    auto_approve_enabled BOOLEAN DEFAULT FALSE,
    auto_approve_threshold REAL DEFAULT 0.95,
    auto_approve_constraints JSON,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for reasoning_patterns
CREATE INDEX IF NOT EXISTS idx_rp_auto_approve ON reasoning_patterns(auto_approve_enabled);

-- ===== Templates Table =====
-- Reusable reasoning templates
CREATE TABLE IF NOT EXISTS reasoning_templates (
    -- Primary Key
    template_id TEXT PRIMARY KEY,

    -- Template Identity
    template_name TEXT NOT NULL,
    pattern_id TEXT,

    -- Template Structure
    reasoning_structure JSON NOT NULL,

    -- Usage Metrics
    usage_count INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0.0,
    avg_confidence REAL DEFAULT 0.0,

    -- Metadata
    source TEXT DEFAULT 'detected',  -- detected, manual
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (pattern_id) REFERENCES reasoning_patterns(pattern_id)
);

-- ===== Policy Violations Table =====
-- Track policy violations for compliance
CREATE TABLE IF NOT EXISTS policy_violations (
    -- Primary Key
    violation_id TEXT PRIMARY KEY,

    -- Reference
    chain_id TEXT NOT NULL,

    -- Violation Details
    policy_name TEXT NOT NULL,
    severity TEXT NOT NULL,  -- error, warning, info
    message TEXT NOT NULL,
    auto_blocked BOOLEAN DEFAULT FALSE,

    -- Resolution
    resolved BOOLEAN DEFAULT FALSE,
    resolved_by TEXT,
    resolved_at TIMESTAMP,
    resolution_notes TEXT,

    -- Metadata
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (chain_id) REFERENCES reasoning_chains(chain_id)
);

-- Indexes for policy_violations
CREATE INDEX IF NOT EXISTS idx_pv_policy_name ON policy_violations(policy_name);
CREATE INDEX IF NOT EXISTS idx_pv_resolved ON policy_violations(resolved);

-- ===== Review Queue Table =====
-- Track pending human reviews
CREATE TABLE IF NOT EXISTS review_queue (
    -- Primary Key
    queue_id TEXT PRIMARY KEY,

    -- Reference
    chain_id TEXT NOT NULL,

    -- Priority
    priority TEXT DEFAULT 'normal',  -- urgent, high, normal, low
    priority_score REAL DEFAULT 0.0,

    -- Status
    status TEXT DEFAULT 'pending',  -- pending, in_review, completed, expired
    assigned_to TEXT,

    -- Timestamps
    queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- Notifications
    notified BOOLEAN DEFAULT FALSE,
    notification_sent_at TIMESTAMP,

    FOREIGN KEY (chain_id) REFERENCES reasoning_chains(chain_id)
);

-- Indexes for review_queue
CREATE INDEX IF NOT EXISTS idx_rq_status ON review_queue(status);
CREATE INDEX IF NOT EXISTS idx_rq_priority ON review_queue(priority);
CREATE INDEX IF NOT EXISTS idx_rq_assigned_to ON review_queue(assigned_to);

-- ===== Audit Log Table =====
-- Complete audit trail of all system actions
CREATE TABLE IF NOT EXISTS audit_log (
    -- Primary Key
    log_id TEXT PRIMARY KEY,

    -- Event
    event_type TEXT NOT NULL,  -- reasoning_extracted, policy_checked, review_requested, etc.
    event_data JSON,

    -- Context
    chain_id TEXT,
    user_id TEXT,

    -- Metadata
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for audit_log
CREATE INDEX IF NOT EXISTS idx_al_event_type ON audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_al_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_al_chain_id ON audit_log(chain_id);

-- ===== Metrics Table =====
-- System performance metrics
CREATE TABLE IF NOT EXISTS metrics (
    -- Primary Key
    metric_id TEXT PRIMARY KEY,

    -- Metric Identity
    metric_name TEXT NOT NULL,
    metric_type TEXT NOT NULL,  -- counter, gauge, histogram

    -- Value
    value REAL NOT NULL,
    labels JSON,

    -- Metadata
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for metrics
CREATE INDEX IF NOT EXISTS idx_m_metric_name ON metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_m_timestamp ON metrics(timestamp);

-- ===== Views =====

-- Active Review Queue
CREATE VIEW IF NOT EXISTS active_reviews AS
SELECT
    rq.*,
    rc.agent_role,
    rc.task,
    rc.selected_action,
    rc.completeness_score,
    rc.policy_results
FROM review_queue rq
JOIN reasoning_chains rc ON rq.chain_id = rc.chain_id
WHERE rq.status = 'pending'
ORDER BY rq.priority_score DESC, rq.queued_at ASC;

-- Pattern Performance Summary
CREATE VIEW IF NOT EXISTS pattern_performance AS
SELECT
    rp.pattern_id,
    rp.pattern_name,
    rp.occurrence_count,
    rp.approval_rate,
    rp.auto_approve_enabled,
    COUNT(rc.chain_id) as total_uses,
    AVG(rc.completeness_score) as avg_completeness,
    SUM(CASE WHEN rc.human_decision = 'approved' THEN 1 ELSE 0 END) * 1.0 / COUNT(rc.chain_id) as actual_approval_rate
FROM reasoning_patterns rp
LEFT JOIN reasoning_chains rc ON rp.pattern_id = rc.pattern_id
GROUP BY rp.pattern_id;

-- Daily Metrics
CREATE VIEW IF NOT EXISTS daily_metrics AS
SELECT
    DATE(timestamp) as date,
    COUNT(*) as total_decisions,
    SUM(CASE WHEN requires_review THEN 1 ELSE 0 END) as reviews_required,
    SUM(CASE WHEN human_decision = 'approved' THEN 1 ELSE 0 END) as approved,
    SUM(CASE WHEN human_decision = 'rejected' THEN 1 ELSE 0 END) as rejected,
    SUM(CASE WHEN human_decision IS NOT NULL AND human_modification IS NOT NULL THEN 1 ELSE 0 END) as modified,
    AVG(completeness_score) as avg_completeness
FROM reasoning_chains
GROUP BY DATE(timestamp)
ORDER BY date DESC;
