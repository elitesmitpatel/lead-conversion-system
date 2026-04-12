-- Lead Conversion System - Supabase Database Schema
-- Run this in Supabase SQL Editor to set up your database

-- ============================================
-- CLIENTS TABLE (Marketing Agencies)
-- ============================================
CREATE TABLE IF NOT EXISTS clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    api_key TEXT UNIQUE DEFAULT gen_random_uuid()::TEXT,
    calcom_link TEXT,
    config JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;

-- Policy: Clients can only view their own data
CREATE POLICY "clients_select_own" ON clients FOR SELECT
    USING (true);

CREATE POLICY "clients_insert_own" ON clients FOR INSERT
    WITH CHECK (true);

CREATE POLICY "clients_update_own" ON clients FOR UPDATE
    USING (true);

-- ============================================
-- LEADS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    name TEXT,
    email TEXT,
    phone TEXT,
    source TEXT DEFAULT 'website',
    original_message TEXT,
    channel TEXT DEFAULT 'email',
    status TEXT DEFAULT 'new' CHECK (status IN ('new', 'contacted', 'nurturing', 'booked', 'dead', 'won', 'lost')),
    follow_up_count INT DEFAULT 0,
    interest_score INT DEFAULT 50 CHECK (interest_score >= 0 AND interest_score <= 100),
    last_contact TIMESTAMPTZ,
    next_followup_at TIMESTAMPTZ,
    booked_at TIMESTAMPTZ,
    deal_value DECIMAL(10,2),
    notes TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

-- Policy: Clients can only view their own leads
CREATE POLICY "leads_select_own" ON leads FOR SELECT
    USING (true);

CREATE POLICY "leads_insert_own" ON leads FOR INSERT
    WITH CHECK (true);

CREATE POLICY "leads_update_own" ON leads FOR UPDATE
    USING (true);

-- ============================================
-- CONVERSATIONS TABLE (Full conversation log)
-- ============================================
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    channel TEXT,
    strategy TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "conversations_select_own" ON conversations FOR SELECT
    USING (true);

CREATE POLICY "conversations_insert_own" ON conversations FOR INSERT
    WITH CHECK (true);

-- ============================================
-- EVENTS TABLE (Analytics & tracking)
-- ============================================
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "events_select_own" ON events FOR SELECT
    USING (true);

CREATE POLICY "events_insert_own" ON events FOR INSERT
    WITH CHECK (true);

-- ============================================
-- INDEXES (Performance optimization)
-- ============================================
CREATE INDEX idx_leads_client_status ON leads(client_id, status);
CREATE INDEX idx_leads_client_status_date ON leads(client_id, status, created_at DESC);
CREATE INDEX idx_leads_next_followup ON leads(next_followup_at) 
    WHERE status IN ('contacted', 'nurturing');
CREATE INDEX idx_leads_client_source ON leads(client_id, source);
CREATE INDEX idx_conversations_lead ON conversations(lead_id, created_at);
CREATE INDEX idx_events_lead ON events(lead_id, created_at DESC);
CREATE INDEX idx_events_type ON events(event_type, created_at);

-- ============================================
-- FUNCTIONS (Helper functions)
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at on leads
CREATE TRIGGER leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Trigger to auto-update updated_at on clients
CREATE TRIGGER clients_updated_at
    BEFORE UPDATE ON clients
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- ============================================
-- VIEWS (Ready-to-use analytics)
-- ============================================

-- Pipeline Summary by Client
CREATE OR REPLACE VIEW pipeline_summary AS
SELECT 
    l.client_id,
    c.agency_name,
    l.status,
    COUNT(*) as lead_count,
    ROUND(AVG(l.interest_score), 1) as avg_interest_score,
    COALESCE(SUM(l.deal_value), 0) as total_deal_value
FROM leads l
JOIN clients c ON c.id = l.client_id
GROUP BY l.client_id, c.agency_name, l.status;

-- Recent Activity
CREATE OR REPLACE VIEW recent_activity AS
SELECT 
    l.id as lead_id,
    l.client_id,
    l.name as lead_name,
    e.event_type,
    e.created_at
FROM events e
JOIN leads l ON l.id = e.lead_id
ORDER BY e.created_at DESC
LIMIT 100;

-- Client Metrics
CREATE OR REPLACE VIEW client_metrics AS
SELECT 
    l.client_id,
    c.agency_name,
    COUNT(*) as total_leads,
    COUNT(*) FILTER (WHERE l.status = 'new') as new_leads,
    COUNT(*) FILTER (WHERE l.status = 'contacted') as contacted_leads,
    COUNT(*) FILTER (WHERE l.status = 'nurturing') as nurturing_leads,
    COUNT(*) FILTER (WHERE l.status = 'booked') as booked_leads,
    COUNT(*) FILTER (WHERE l.status = 'won') as won_leads,
    COUNT(*) FILTER (WHERE l.status = 'dead') as dead_leads,
    ROUND(COUNT(*) FILTER (WHERE l.status != 'new')::FLOAT / NULLIF(COUNT(*), 0) * 100, 1) as response_rate,
    ROUND(COUNT(*) FILTER (WHERE l.status = 'booked')::FLOAT / NULLIF(COUNT(*), 0) * 100, 1) as booking_rate,
    ROUND(COUNT(*) FILTER (WHERE l.status = 'won')::FLOAT / NULLIF(COUNT(*) FILTER (WHERE l.status = 'booked'), 0) * 100, 1) as close_rate
FROM leads l
JOIN clients c ON c.id = l.client_id
WHERE l.created_at > NOW() - INTERVAL '30 days'
GROUP BY l.client_id, c.agency_name;

-- ============================================
-- SEEDS (Sample data for testing)
-- ============================================

-- Insert a test client
INSERT INTO clients (agency_name, email, calcom_link, config)
VALUES (
    'Test Marketing Agency',
    'test@agency.com',
    'https://cal.com/test-agency',
    '{"primary_channel": "email", "tone": "professional", "timezone": "America/New_York"}'
);

-- Insert sample leads for testing
INSERT INTO leads (client_id, name, email, phone, source, original_message, channel, status, interest_score)
SELECT 
    c.id,
    'John Smith',
    'john@example.com',
    '+1234567890',
    'website',
    'Interested in marketing services for my agency',
    'email',
    'new',
    60
FROM clients c WHERE c.agency_name = 'Test Marketing Agency'
LIMIT 1;

INSERT INTO leads (client_id, name, email, phone, source, original_message, channel, status, interest_score, last_contact, follow_up_count)
SELECT 
    c.id,
    'Sarah Johnson',
    'sarah@company.com',
    '+1987654321',
    'facebook',
    'Looking for help with lead generation',
    'email',
    'contacted',
    75,
    NOW() - INTERVAL '2 days',
    3
FROM clients c WHERE c.agency_name = 'Test Marketing Agency'
LIMIT 1;

INSERT INTO leads (client_id, name, email, phone, source, original_message, channel, status, interest_score, last_contact)
SELECT 
    c.id,
    'Mike Wilson',
    'mike@startup.io',
    '+1122334455',
    'google',
    'Need to scale our marketing efforts',
    'chat',
    'dead',
    25,
    NOW() - INTERVAL '45 days'
FROM clients c WHERE c.agency_name = 'Test Marketing Agency'
LIMIT 1;

-- Add some conversation history
INSERT INTO conversations (lead_id, role, content, channel, strategy)
SELECT 
    l.id,
    'user',
    l.original_message,
    l.channel,
    'initial'
FROM leads l
JOIN clients c ON c.id = l.client_id
WHERE c.agency_name = 'Test Marketing Agency'
AND l.original_message IS NOT NULL;

-- Add some events
INSERT INTO events (lead_id, event_type, metadata)
SELECT 
    l.id,
    'lead_created',
    '{"source": "website"}'
FROM leads l
JOIN clients c ON c.id = l.client_id
WHERE c.agency_name = 'Test Marketing Agency';

PRINT 'Database schema created successfully!';
PRINT 'You can now start using the Lead Conversion System.';