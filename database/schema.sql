-- Multi-Agent RAG MCP Server Database Schema
-- PostgreSQL with pgvector extension

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Documents table: Main document storage
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    source TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Document embeddings table: Vector storage for semantic search
CREATE TABLE IF NOT EXISTS document_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    embedding vector(1536),
    chunk_text TEXT,
    chunk_index INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Deadlines table: Extracted deadlines from legal documents
CREATE TABLE IF NOT EXISTS deadlines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    deadline_date DATE NOT NULL,
    deadline_type TEXT,
    description TEXT,
    priority TEXT CHECK (priority IN ('high', 'medium', 'low')),
    status TEXT CHECK (status IN ('pending', 'completed', 'missed')) DEFAULT 'pending',
    extracted_text TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Document classifications table
CREATE TABLE IF NOT EXISTS document_classifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    subcategory TEXT,
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    tags TEXT[],
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Strategic analysis table
CREATE TABLE IF NOT EXISTS strategic_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    analysis_type TEXT NOT NULL,
    insights JSONB,
    key_findings TEXT[],
    recommendations TEXT[],
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_documents_created_at ON documents(created_at DESC);
CREATE INDEX idx_embeddings_document_id ON document_embeddings(document_id);
CREATE INDEX idx_deadlines_date ON deadlines(deadline_date);
CREATE INDEX idx_deadlines_status ON deadlines(status);
CREATE INDEX idx_classifications_category ON document_classifications(category);
CREATE INDEX idx_analysis_type ON strategic_analysis(analysis_type);
