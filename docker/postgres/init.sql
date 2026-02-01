-- Initialize Episodic Memory Database for AI Agent System
-- This stores past tickets, resolutions, and outcomes

CREATE TABLE IF NOT EXISTS past_tickets (
    id SERIAL PRIMARY KEY,
    ticket_id VARCHAR(255) UNIQUE NOT NULL,
    user_input TEXT NOT NULL,
    intent VARCHAR(50),
    category VARCHAR(50),
    urgency VARCHAR(20),
    severity VARCHAR(50),
    team VARCHAR(100),
    resolution TEXT,
    outcome VARCHAR(50),
    confidence DECIMAL(3,2),
    sla_risk BOOLEAN DEFAULT FALSE,
    pattern_detected BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS ticket_interactions (
    id SERIAL PRIMARY KEY,
    ticket_id VARCHAR(255) REFERENCES past_tickets(ticket_id),
    agent_name VARCHAR(100),
    action VARCHAR(100),
    input_data JSONB,
    output_data JSONB,
    execution_time DECIMAL(10,3),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS escalations (
    id SERIAL PRIMARY KEY,
    ticket_id VARCHAR(255) REFERENCES past_tickets(ticket_id),
    reason TEXT,
    escalated_to VARCHAR(100),
    escalated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolution TEXT
);

-- Create indexes for faster queries
CREATE INDEX idx_intent ON past_tickets(intent);
CREATE INDEX idx_category ON past_tickets(category);
CREATE INDEX idx_urgency ON past_tickets(urgency);
CREATE INDEX idx_created_at ON past_tickets(created_at);
CREATE INDEX idx_ticket_id ON ticket_interactions(ticket_id);

-- Insert sample data for testing
INSERT INTO past_tickets (
    ticket_id, user_input, intent, category, urgency, severity, team,
    resolution, outcome, confidence, resolved_at
) VALUES 
(
    'TICKET-001',
    'Payment API returning 500 errors',
    'incident',
    'technical',
    'critical',
    'business_critical',
    'DevOps',
    'Restarted payment service, identified memory leak in v2.3.1. Rolled back to v2.2.5. Monitoring for stability.',
    'success',
    0.95,
    NOW() - INTERVAL '2 days'
),
(
    'TICKET-002',
    'How do I reset my password?',
    'question',
    'security',
    'low',
    'single_user',
    'Support',
    'Sent password reset link to registered email. User successfully reset password.',
    'success',
    0.98,
    NOW() - INTERVAL '5 days'
),
(
    'TICKET-003',
    'Need access to production database',
    'service_request',
    'security',
    'medium',
    'single_user',
    'Security',
    'Verified user role and manager approval. Granted read-only access to prod DB.',
    'success',
    0.92,
    NOW() - INTERVAL '1 day'
);

COMMIT;
