#!/usr/bin/env python3
"""
Apply Schema to Supabase - Instructions
"""
import os
from dotenv import load_dotenv
load_dotenv()

def show_instructions():
    url = os.getenv("SUPABASE_URL")
    
    schema_sql = '''-- ============================================
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
    status TEXT DEFAULT 'new',
    follow_up_count INT DEFAULT 0,
    interest_score INT DEFAULT 50,
    last_contact TIMESTAMPTZ,
    next_followup_at TIMESTAMPTZ,
    booked_at TIMESTAMPTZ,
    deal_value DECIMAL(10,2),
    notes TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- CONVERSATIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    channel TEXT,
    strategy TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- EVENTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- INDEXES
-- ============================================
CREATE INDEX IF NOT EXISTS idx_leads_client_status ON leads(client_id, status);
CREATE INDEX IF NOT EXISTS idx_leads_next_followup ON leads(next_followup_at) WHERE status IN ('contacted', 'nurturing');

-- ============================================
-- CREATE TEST CLIENT
-- ============================================
INSERT INTO clients (agency_name, email, config)
VALUES ('Test Marketing Agency', 'test@agency.com', '{"owner_email": "elitesmit@gmail.com"}')
RETURNING id, agency_name;'''
    
    print("=" * 60)
    print("DATABASE SETUP - STEP BY STEP")
    print("=" * 60)
    print()
    print("STEP 1: Open Supabase SQL Editor")
    print(f"   {url}/project/default/sql")
    print()
    print("STEP 2: Copy and paste the SQL below into the editor")
    print("-" * 60)
    print(schema_sql)
    print("-" * 60)
    print()
    print("STEP 3: Click 'Run' button (or Ctrl+Enter)")
    print()
    print("STEP 4: Copy the returned Client ID from the results")
    print()
    print("STEP 5: Test the system with the Client ID")
    print()
    print("=" * 60)
    print("ALTERNATIVE: Use Supabase CLI")
    print("=" * 60)
    print("""
1. Install: npm install -g supabase
2. Login: supabase login
3. Link: supabase link --project-ref ryoaamutexwdtdpxdlll
4. Push: supabase db push
""")

if __name__ == "__main__":
    show_instructions()
