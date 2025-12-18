-- Add Gemini Extractions and Validations tables for three-step validation architecture

-- Gemini Extractions table: Store Gemini preprocessing results
CREATE TABLE IF NOT EXISTS gemini_extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    document_id TEXT NOT NULL,
    extracted_data JSONB DEFAULT '{}',
    model_version TEXT DEFAULT 'gemini-1.5-pro',
    extraction_timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Validations table: Store Gemini validation results
CREATE TABLE IF NOT EXISTS validations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    validation_type TEXT NOT NULL CHECK (validation_type IN ('classification', 'deadline', 'other')),
    entity_id TEXT NOT NULL,  -- ID of the entity being validated (document_id, extraction_id, etc.)
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    extraction_id UUID REFERENCES gemini_extractions(id) ON DELETE CASCADE,
    validation_status TEXT NOT NULL CHECK (validation_status IN ('verified', 'discrepancy', 'error')),
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    feedback TEXT,
    verified_items JSONB DEFAULT '[]',
    discrepancies JSONB DEFAULT '[]',
    missing_information JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_gemini_extractions_client_id ON gemini_extractions(client_id);
CREATE INDEX IF NOT EXISTS idx_gemini_extractions_document_id ON gemini_extractions(document_id);
CREATE INDEX IF NOT EXISTS idx_gemini_extractions_created_at ON gemini_extractions(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_validations_client_id ON validations(client_id);
CREATE INDEX IF NOT EXISTS idx_validations_entity_id ON validations(entity_id);
CREATE INDEX IF NOT EXISTS idx_validations_type ON validations(validation_type);
CREATE INDEX IF NOT EXISTS idx_validations_extraction_id ON validations(extraction_id);
CREATE INDEX IF NOT EXISTS idx_validations_created_at ON validations(created_at DESC);
