# Gemini Three-Step Validation Architecture

## Overview

This system implements a three-step validation architecture that enhances document processing accuracy by using Gemini for preprocessing and validation, while Claude handles the main processing.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Document Upload                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: Gemini Preprocessing                               │
│  ─────────────────────────────────────                      │
│  • Extract entities (people, orgs, locations, amounts)      │
│  • Identify dates and deadlines                             │
│  • Extract key facts                                        │
│  • Suggest document type                                    │
│  • Store in gemini_extractions table                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: Claude Processing (Enhanced)                       │
│  ─────────────────────────────────────                      │
│  • Classify document (with Gemini hints)                    │
│  • Extract deadlines (with Gemini hints)                    │
│  • Store in documents & deadlines tables                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: Gemini Validation                                  │
│  ─────────────────────────────────                          │
│  • Validate classification against original text            │
│  • Validate deadlines against original text                 │
│  • Provide confidence scores and feedback                   │
│  • Identify discrepancies                                   │
│  • Store in validations table                               │
└─────────────────────────────────────────────────────────────┘
```

## Setup

### 1. Install Dependencies

```bash
pip install google-generativeai>=0.3.0
```

### 2. Configure API Key

Add your Gemini API key to the `.env` file:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Run Database Migration

Execute the migration to create new tables:

```bash
psql -U your_user -d your_database -f database/migrations/add_gemini_validation_tables.sql
```

## Usage

### API Server

#### Upload Document with Validation

```bash
POST /api/clients/{client_id}/documents
Content-Type: multipart/form-data

file: [document file]
```

Response includes:
```json
{
  "success": true,
  "filename": "contract.pdf",
  "client_id": "uuid",
  "chunks_created": 10,
  "classification": {
    "doc_type": "contract",
    "confidence": 0.95,
    "summary": "...",
    "key_entities": {...}
  },
  "deadlines_extracted": 3,
  "deadlines": [...],
  "gemini_extraction_id": "uuid",
  "classification_validation": {
    "validation_status": "verified",
    "confidence_score": 0.96,
    "feedback": "All entities and classification verified",
    "verified_items": [...],
    "discrepancies": [],
    "missing_information": []
  },
  "deadline_validation": {
    "validation_status": "verified",
    "confidence_score": 0.94,
    "feedback": "All deadlines correctly identified",
    "verified_items": [...],
    "discrepancies": [],
    "missing_information": []
  }
}
```

#### Retrieve Validation Results

```bash
GET /api/validations/{validation_type}/{entity_id}
```

Example:
```bash
GET /api/validations/classification/contract.pdf
GET /api/validations/deadline/extraction-uuid
```

Response:
```json
{
  "success": true,
  "validation": {
    "id": "uuid",
    "validation_type": "classification",
    "entity_id": "contract.pdf",
    "validation_status": "verified",
    "confidence_score": 0.96,
    "feedback": "Classification validated successfully",
    "verified_items": ["doc_type", "entities", "summary"],
    "discrepancies": [],
    "missing_information": [],
    "created_at": "2025-01-15T10:30:00Z"
  }
}
```

### MCP Server

The MCP server automatically includes validation results in document indexing:

```
✅ Successfully indexed: contract.pdf

📄 Document Classification:
- Type: contract
- Confidence: 95%
- Summary: Legal agreement between parties

✅ Gemini Validation: VERIFIED (96% confidence)
└─ All entities and classification verified against source

📅 Deadlines Extracted: 2

1. 🔴 2025-01-15 - Contract signing deadline
   └─ 5 working days · CRITICAL

✅ Gemini Validation: VERIFIED (94% confidence)
└─ All deadlines correctly identified and verified
```

## Graceful Degradation

The system is designed to work seamlessly even without Gemini:

- **Without GEMINI_API_KEY**: 
  - Preprocessing returns error status
  - Claude processing continues normally (without hints)
  - Validation returns error status with 0.0 confidence
  - Overall workflow completes successfully

- **With GEMINI_API_KEY**:
  - Full three-step validation
  - Enhanced accuracy with context hints
  - Validation confidence scores
  - Discrepancy detection

## Database Schema

### gemini_extractions
Stores Gemini preprocessing results.

```sql
CREATE TABLE gemini_extractions (
    id UUID PRIMARY KEY,
    client_id UUID REFERENCES clients(id),
    document_id TEXT NOT NULL,
    extracted_data JSONB,  -- Contains entities, dates, facts, metadata
    model_version TEXT DEFAULT 'gemini-3-flash',
    extraction_timestamp TIMESTAMPTZ,
    created_at TIMESTAMPTZ
);
```

### validations
Stores validation results for both classification and deadlines.

```sql
CREATE TABLE validations (
    id UUID PRIMARY KEY,
    validation_type TEXT,  -- 'classification' or 'deadline'
    entity_id TEXT,  -- Document ID or extraction ID being validated
    client_id UUID REFERENCES clients(id),
    extraction_id UUID REFERENCES gemini_extractions(id),
    validation_status TEXT,  -- 'verified', 'discrepancy', or 'error'
    confidence_score FLOAT,  -- 0.0 to 1.0
    feedback TEXT,
    verified_items JSONB,
    discrepancies JSONB,
    missing_information JSONB,
    created_at TIMESTAMPTZ
);
```

## Validation Status Types

- **verified**: Claude's output matches Gemini's analysis
- **discrepancy**: Differences found between analyses
- **error**: Validation could not be completed (e.g., no API key)

## Configuration

### Environment Variables

```bash
# Required for Claude processing
ANTHROPIC_API_KEY=your_anthropic_key

# Optional - enables Gemini features
GEMINI_API_KEY=your_gemini_key

# Database
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

## Testing

Run the test suite to verify the implementation:

```bash
# Test Gemini integration structure
python3 tests/test_gemini_integration.py

# Test workflow with graceful degradation
python3 tests/test_gemini_workflow.py

# Test overall code structure
python3 tests/test_code_structure.py
```

## Benefits

1. **Enhanced Accuracy**: Cross-validation between two AI models reduces errors
2. **Context Hints**: Gemini preprocessing provides helpful hints to Claude
3. **Confidence Scores**: Quantifiable validation confidence
4. **Discrepancy Detection**: Identifies differences between models
5. **Graceful Degradation**: Works perfectly without Gemini API key
6. **Audit Trail**: All validations stored in database
7. **Non-Breaking**: Existing API contracts unchanged

## Best Practices

1. **API Key Management**: Keep GEMINI_API_KEY in environment variables
2. **Error Handling**: Always check validation_status in responses
3. **Confidence Thresholds**: Consider implementing minimum confidence scores for critical operations
4. **Monitoring**: Track validation success rates and confidence scores
5. **Feedback Loop**: Use discrepancies to improve prompts

## Troubleshooting

### Gemini API Errors
If preprocessing fails:
- Check GEMINI_API_KEY is set correctly
- Verify API key has proper permissions
- Check API quota limits
- System continues working without Gemini

### Validation Errors
If validation returns 'error' status:
- Check logs for specific error messages
- Verify Gemini API is accessible
- Ensure document text is not empty
- Claude processing still completes successfully

### Low Confidence Scores
If confidence scores are consistently low:
- Review discrepancies field for patterns
- Consider adjusting Claude prompts
- Check document quality (OCR errors, etc.)
- May indicate model disagreement requiring human review

## Future Enhancements

Potential improvements to consider:

1. **Configurable Confidence Thresholds**: Flag low-confidence results for review
2. **Model Agreement Metrics**: Track overall agreement rates
3. **Human-in-the-Loop**: Require manual review for discrepancies
4. **Custom Validation Rules**: Domain-specific validation logic
5. **Validation History**: Track improvements over time
6. **A/B Testing**: Compare results with/without Gemini context
