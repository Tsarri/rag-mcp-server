# Gemini Three-Step Validation Architecture

## System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      Document Upload                            │
│                    (PDF, DOCX, TXT)                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Vector Store Indexing                        │
│  • Split into chunks                                            │
│  • Generate embeddings                                          │
│  • Store in Supabase                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
╔═════════════════════════════════════════════════════════════════╗
║              STEP 1: GEMINI PREPROCESSING                       ║
╠═════════════════════════════════════════════════════════════════╣
║  Agent: GeminiPreprocessor                                      ║
║  Model: gemini-3-flash                                          ║
║                                                                 ║
║  Extracts:                                                      ║
║  ┌─────────────────────────────────────────────────┐           ║
║  │ • Entities                                      │           ║
║  │   - People: ["John Smith", "Jane Doe"]          │           ║
║  │   - Organizations: ["Acme Corp"]                │           ║
║  │   - Locations: ["New York"]                     │           ║
║  │   - Amounts: ["$50,000"]                        │           ║
║  │                                                 │           ║
║  │ • Dates & Deadlines                             │           ║
║  │   - 2025-01-15: Signing deadline (critical)     │           ║
║  │   - 2025-06-30: Review date (low)               │           ║
║  │                                                 │           ║
║  │ • Key Facts                                     │           ║
║  │   - Employment agreement                        │           ║
║  │   - 6-month probation period                    │           ║
║  │                                                 │           ║
║  │ • Document Metadata                             │           ║
║  │   - Type: contract                              │           ║
║  │   - Language: en                                │           ║
║  │   - Topic: employment                           │           ║
║  └─────────────────────────────────────────────────┘           ║
║                                                                 ║
║  Storage: gemini_extractions table                              ║
╚═════════════════════════════════════════════════════════════════╝
                              │
                              ▼
╔═════════════════════════════════════════════════════════════════╗
║          STEP 2: CLAUDE PROCESSING (Enhanced)                   ║
╠═════════════════════════════════════════════════════════════════╣
║  Agents: DocumentAgent + DeadlineAgent                          ║
║  Model: claude-3-opus                                           ║
║                                                                 ║
║  A) Document Classification                                     ║
║  ┌─────────────────────────────────────────────────┐           ║
║  │ Prompt includes Gemini hints:                   │           ║
║  │                                                 │           ║
║  │ "ANOTHER AI MODEL'S ANALYSIS:                   │           ║
║  │  - Suggested type: contract                     │           ║
║  │  - People identified: John Smith, Jane Doe      │           ║
║  │  - Organizations: Acme Corp                     │           ║
║  │                                                 │           ║
║  │  Use this as reference, but make your own       │           ║
║  │  classification based on the full text."        │           ║
║  └─────────────────────────────────────────────────┘           ║
║                                                                 ║
║  Output:                                                        ║
║  ┌─────────────────────────────────────────────────┐           ║
║  │ • doc_type: "contract"                          │           ║
║  │ • confidence: 0.95                              │           ║
║  │ • matter_id: "CASE-2024-001"                    │           ║
║  │ • tags: ["employment", "legal"]                 │           ║
║  │ • key_entities: {...}                           │           ║
║  │ • summary: "Employment agreement..."            │           ║
║  └─────────────────────────────────────────────────┘           ║
║                                                                 ║
║  Storage: documents table                                       ║
║                                                                 ║
║  B) Deadline Extraction                                         ║
║  ┌─────────────────────────────────────────────────┐           ║
║  │ Prompt includes Gemini hints:                   │           ║
║  │                                                 │           ║
║  │ "NOTE: Another AI model identified these        │           ║
║  │  dates in the document:                         │           ║
║  │  - 2025-01-15: Filing deadline (critical)       │           ║
║  │  - 2025-06-30: Review date (low)                │           ║
║  │                                                 │           ║
║  │  Use these as hints, but verify against         │           ║
║  │  the full text."                                │           ║
║  └─────────────────────────────────────────────────┘           ║
║                                                                 ║
║  Output:                                                        ║
║  ┌─────────────────────────────────────────────────┐           ║
║  │ • date: "2025-01-15"                            │           ║
║  │ • description: "Contract signing"               │           ║
║  │ • working_days_remaining: 5                     │           ║
║  │ • risk_level: "critical"                        │           ║
║  └─────────────────────────────────────────────────┘           ║
║                                                                 ║
║  Storage: deadlines & deadline_extractions tables               ║
╚═════════════════════════════════════════════════════════════════╝
                              │
                              ▼
╔═════════════════════════════════════════════════════════════════╗
║              STEP 3: GEMINI VALIDATION                          ║
╠═════════════════════════════════════════════════════════════════╣
║  Agent: GeminiValidator                                         ║
║  Model: gemini-3-flash                                          ║
║                                                                 ║
║  A) Classification Validation                                   ║
║  ┌─────────────────────────────────────────────────┐           ║
║  │ Compare:                                        │           ║
║  │  • Claude's classification                      │           ║
║  │  • Original text                                │           ║
║  │  • Gemini's extraction (optional)               │           ║
║  │                                                 │           ║
║  │ Validate:                                       │           ║
║  │  • Document type correct?                       │           ║
║  │  • Entities identified?                         │           ║
║  │  • Summary accurate?                            │           ║
║  │  • Any discrepancies?                           │           ║
║  │  • Missing information?                         │           ║
║  └─────────────────────────────────────────────────┘           ║
║                                                                 ║
║  Output:                                                        ║
║  ┌─────────────────────────────────────────────────┐           ║
║  │ • validation_status: "verified"                 │           ║
║  │ • confidence_score: 0.96                        │           ║
║  │ • feedback: "All verified"                      │           ║
║  │ • verified_items: [...]                         │           ║
║  │ • discrepancies: []                             │           ║
║  │ • missing_information: []                       │           ║
║  └─────────────────────────────────────────────────┘           ║
║                                                                 ║
║  B) Deadline Validation                                         ║
║  ┌─────────────────────────────────────────────────┐           ║
║  │ Compare:                                        │           ║
║  │  • Claude's deadlines                           │           ║
║  │  • Original text                                │           ║
║  │  • Gemini's dates (optional)                    │           ║
║  │                                                 │           ║
║  │ Validate:                                       │           ║
║  │  • All deadlines found?                         │           ║
║  │  • Dates correct?                               │           ║
║  │  • Descriptions accurate?                       │           ║
║  │  • Any discrepancies?                           │           ║
║  │  • Missing deadlines?                           │           ║
║  └─────────────────────────────────────────────────┘           ║
║                                                                 ║
║  Output:                                                        ║
║  ┌─────────────────────────────────────────────────┐           ║
║  │ • validation_status: "verified"                 │           ║
║  │ • confidence_score: 0.94                        │           ║
║  │ • feedback: "All deadlines verified"            │           ║
║  │ • verified_items: [...]                         │           ║
║  │ • discrepancies: []                             │           ║
║  │ • missing_information: []                       │           ║
║  └─────────────────────────────────────────────────┘           ║
║                                                                 ║
║  Storage: validations table                                     ║
╚═════════════════════════════════════════════════════════════════╝
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Response                               │
│  • Upload success confirmation                                  │
│  • Classification results                                       │
│  • Extracted deadlines                                          │
│  • Gemini extraction ID                                         │
│  • Classification validation                                    │
│  • Deadline validation                                          │
└─────────────────────────────────────────────────────────────────┘
```

## Database Schema

```
┌─────────────────────────┐
│       clients           │
├─────────────────────────┤
│ id (PK)                 │
│ name                    │
│ email                   │
│ phone                   │
│ company                 │
│ active                  │
│ created_at              │
└─────────────────────────┘
           │
           │ 1:N
           ▼
┌─────────────────────────┐       ┌─────────────────────────┐
│   gemini_extractions    │       │      documents          │
├─────────────────────────┤       ├─────────────────────────┤
│ id (PK)                 │       │ id (PK)                 │
│ client_id (FK)          │       │ document_id             │
│ document_id             │       │ filename                │
│ extracted_data (JSONB)  │◄──┐   │ doc_type                │
│ model_version           │   │   │ matter_id               │
│ extraction_timestamp    │   │   │ tags                    │
│ created_at              │   │   │ key_entities (JSONB)    │
└─────────────────────────┘   │   │ summary                 │
           │                  │   │ confidence              │
           │ 1:N              │   │ client_id (FK)          │
           ▼                  │   │ created_at              │
┌─────────────────────────┐   │   └─────────────────────────┘
│      validations        │   │              │
├─────────────────────────┤   │              │ 1:N
│ id (PK)                 │   │              ▼
│ validation_type         │   │   ┌─────────────────────────┐
│ entity_id               │   │   │ deadline_extractions    │
│ client_id (FK)          │   │   ├─────────────────────────┤
│ extraction_id (FK)      │───┘   │ id (PK)                 │
│ validation_status       │       │ source_id               │
│ confidence_score        │       │ text                    │
│ feedback                │       │ extracted_count         │
│ verified_items (JSONB)  │       │ client_id (FK)          │
│ discrepancies (JSONB)   │       │ created_at              │
│ missing_info (JSONB)    │       └─────────────────────────┘
│ created_at              │                  │
└─────────────────────────┘                  │ 1:N
                                            ▼
                                 ┌─────────────────────────┐
                                 │      deadlines          │
                                 ├─────────────────────────┤
                                 │ id (PK)                 │
                                 │ extraction_id (FK)      │
                                 │ date                    │
                                 │ description             │
                                 │ working_days_remaining  │
                                 │ risk_level              │
                                 │ client_id (FK)          │
                                 │ completed               │
                                 │ created_at              │
                                 └─────────────────────────┘
```

## Error Handling Flow

```
┌──────────────────────┐
│ GEMINI_API_KEY set?  │
└──────────────────────┘
           │
     ┌─────┴─────┐
     │           │
    YES         NO
     │           │
     ▼           ▼
┌─────────┐  ┌─────────────────────┐
│ Gemini  │  │ Return error status │
│ Active  │  │ Continue workflow   │
└─────────┘  └─────────────────────┘
     │                  │
     ▼                  │
┌──────────────┐        │
│ API call OK? │        │
└──────────────┘        │
     │                  │
 ┌───┴───┐              │
YES     NO              │
 │       │              │
 │       ▼              │
 │  ┌─────────────┐    │
 │  │ Catch error │    │
 │  │ Log it      │    │
 │  │ Return err  │    │
 │  └─────────────┘    │
 │       │              │
 └───────┴──────────────┘
         │
         ▼
  ┌──────────────────┐
  │ Workflow         │
  │ Continues        │
  │ Successfully     │
  └──────────────────┘
```

## Benefits of Three-Step Architecture

1. **Cross-Validation**: Two AI models verify each other
2. **Enhanced Context**: Claude gets helpful hints from Gemini
3. **Confidence Scores**: Quantifiable accuracy metrics
4. **Discrepancy Detection**: Identifies differences for review
5. **Graceful Degradation**: Works without Gemini
6. **Audit Trail**: All validations stored
7. **Non-Breaking**: Existing features unchanged

## Performance Characteristics

- **Preprocessing Time**: ~2-3 seconds (Gemini)
- **Classification Time**: ~3-5 seconds (Claude)
- **Validation Time**: ~2-3 seconds (Gemini)
- **Total Overhead**: ~7-11 seconds per document
- **Without Gemini**: Original ~3-5 seconds

## API Endpoints

### Upload Document (Modified)
```
POST /api/clients/{client_id}/documents
```
Returns: classification + deadlines + validations

### Get Validation (New)
```
GET /api/validations/{validation_type}/{entity_id}
```
Returns: latest validation for entity

### All Other Endpoints
Unchanged - backward compatible
