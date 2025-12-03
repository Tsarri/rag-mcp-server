-- Multi-Agent RAG MCP Server Database Schema
-- PostgreSQL with pgvector extension

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Clients table: Store client information
CREATE TABLE IF NOT EXISTS clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    company TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    active BOOLEAN DEFAULT TRUE
);

-- Documents table: Document metadata and classification (used by DocumentAgent)
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id TEXT NOT NULL UNIQUE,
    filename TEXT NOT NULL,
    doc_type TEXT,
    matter_id TEXT,
    tags TEXT[],
    key_entities JSONB DEFAULT '{}',
    summary TEXT,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    original_metadata JSONB DEFAULT '{}',
    text_preview TEXT,
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Deadline extractions table: Tracks extraction operations
CREATE TABLE IF NOT EXISTS deadline_extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id TEXT,
    text TEXT,
    extracted_count INTEGER DEFAULT 0,
    extraction_timestamp TIMESTAMPTZ DEFAULT NOW(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Deadlines table: Extracted deadlines from legal documents
CREATE TABLE IF NOT EXISTS deadlines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    extraction_id UUID REFERENCES deadline_extractions(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    description TEXT,
    working_days_remaining INTEGER,
    risk_level TEXT CHECK (risk_level IN ('overdue', 'critical', 'high', 'medium', 'low')),
    source_id TEXT,
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Analyses table: Strategic analyses (used by SmartContextAgent)
CREATE TABLE IF NOT EXISTS analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    firm_id TEXT NOT NULL,
    analysis_type TEXT NOT NULL,
    input_data JSONB DEFAULT '{}',
    key_insights TEXT[],
    action_items TEXT[],
    metrics JSONB DEFAULT '{}',
    summary TEXT,
    risk_level TEXT,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_documents_client_id ON documents(client_id);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_doc_type ON documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_documents_matter_id ON documents(matter_id);

CREATE INDEX IF NOT EXISTS idx_deadlines_client_id ON deadlines(client_id);
CREATE INDEX IF NOT EXISTS idx_deadlines_date ON deadlines(date);
CREATE INDEX IF NOT EXISTS idx_deadlines_risk_level ON deadlines(risk_level);
CREATE INDEX IF NOT EXISTS idx_deadlines_extraction_id ON deadlines(extraction_id);

CREATE INDEX IF NOT EXISTS idx_deadline_extractions_client_id ON deadline_extractions(client_id);

CREATE INDEX IF NOT EXISTS idx_analyses_client_id ON analyses(client_id);
CREATE INDEX IF NOT EXISTS idx_analyses_type ON analyses(analysis_type);
CREATE INDEX IF NOT EXISTS idx_analyses_firm_id ON analyses(firm_id);
CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses(created_at DESC);
