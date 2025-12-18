# Gemini Validation - Usage Examples

## Example 1: Upload and Validate a Document

### Request
```bash
curl -X POST "http://localhost:8000/api/clients/{client_id}/documents" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@contract.pdf"
```

### Response (with Gemini enabled)
```json
{
  "success": true,
  "filename": "contract.pdf",
  "client_id": "550e8400-e29b-41d4-a716-446655440000",
  "chunks_created": 15,
  "classification": {
    "doc_type": "contract",
    "matter_id": "CASE-2024-001",
    "tags": ["employment", "legal", "agreement"],
    "key_entities": {
      "people": ["John Smith", "Jane Doe"],
      "organizations": ["Acme Corporation", "TechStart Inc"],
      "dates": ["2025-01-15", "2025-06-30"],
      "amounts": ["$50,000", "$5,000"]
    },
    "summary": "Employment contract between Acme Corporation and John Smith",
    "confidence": 0.95
  },
  "deadlines_extracted": 2,
  "deadlines": [
    {
      "id": "deadline-uuid-1",
      "date": "2025-01-15",
      "description": "Contract signing deadline",
      "working_days_remaining": 5,
      "risk_level": "critical"
    },
    {
      "id": "deadline-uuid-2", 
      "date": "2025-06-30",
      "description": "First performance review",
      "working_days_remaining": 90,
      "risk_level": "low"
    }
  ],
  "gemini_extraction_id": "extraction-uuid",
  "classification_validation": {
    "validation_status": "verified",
    "confidence_score": 0.96,
    "feedback": "Classification verified. All key entities and document type confirmed.",
    "verified_items": [
      "Document type: contract",
      "Organizations: Acme Corporation, TechStart Inc",
      "People: John Smith, Jane Doe"
    ],
    "discrepancies": [],
    "missing_information": []
  },
  "deadline_validation": {
    "validation_status": "verified",
    "confidence_score": 0.94,
    "feedback": "All critical deadlines correctly identified and verified.",
    "verified_items": [
      "2025-01-15: Contract signing deadline",
      "2025-06-30: Performance review deadline"
    ],
    "discrepancies": [],
    "missing_information": []
  }
}
```

## Example 2: Response with Discrepancy

When Gemini and Claude disagree:

```json
{
  "success": true,
  "classification_validation": {
    "validation_status": "discrepancy",
    "confidence_score": 0.72,
    "feedback": "Some discrepancies found between analyses. Manual review recommended.",
    "verified_items": [
      "Document type: legal",
      "Main parties identified"
    ],
    "discrepancies": [
      "Claude identified document as 'legal', Gemini suggested 'contract'",
      "Date 2025-02-01 mentioned but not extracted by Claude"
    ],
    "missing_information": [
      "Potential deadline on 2025-02-01 may have been missed"
    ]
  }
}
```

## Example 3: Retrieve Validation Results

### Get Classification Validation
```bash
curl -X GET "http://localhost:8000/api/validations/classification/contract.pdf"
```

Response:
```json
{
  "success": true,
  "validation": {
    "id": "validation-uuid",
    "validation_type": "classification",
    "entity_id": "contract.pdf",
    "client_id": "550e8400-e29b-41d4-a716-446655440000",
    "extraction_id": "extraction-uuid",
    "validation_status": "verified",
    "confidence_score": 0.96,
    "feedback": "Classification verified successfully",
    "verified_items": ["doc_type", "entities", "summary"],
    "discrepancies": [],
    "missing_information": [],
    "created_at": "2025-01-15T10:30:00Z"
  }
}
```

### Get Deadline Validation
```bash
curl -X GET "http://localhost:8000/api/validations/deadline/extraction-uuid"
```

Response:
```json
{
  "success": true,
  "validation": {
    "id": "validation-uuid-2",
    "validation_type": "deadline",
    "entity_id": "extraction-uuid",
    "validation_status": "verified",
    "confidence_score": 0.94,
    "feedback": "All deadlines verified",
    "verified_items": [
      "2025-01-15: Critical deadline verified",
      "2025-06-30: Review date verified"
    ],
    "discrepancies": [],
    "missing_information": [],
    "created_at": "2025-01-15T10:30:15Z"
  }
}
```

## Example 4: Without Gemini API Key

When GEMINI_API_KEY is not configured, the system gracefully degrades:

```json
{
  "success": true,
  "filename": "contract.pdf",
  "classification": {
    "doc_type": "contract",
    "confidence": 0.93,
    "summary": "Employment agreement"
  },
  "deadlines_extracted": 2,
  "deadlines": [...],
  "gemini_extraction_id": null,
  "classification_validation": {
    "validation_status": "error",
    "confidence_score": 0.0,
    "feedback": "Gemini API not configured",
    "verified_items": [],
    "discrepancies": [],
    "missing_information": []
  },
  "deadline_validation": {
    "validation_status": "error",
    "confidence_score": 0.0,
    "feedback": "Gemini API not configured",
    "verified_items": [],
    "discrepancies": [],
    "missing_information": []
  }
}
```

## Example 5: MCP Server Usage

### Index Document with Validation

Using the MCP server through Claude Desktop or other MCP clients:

```
User: "Index the contract.pdf document"

Response:
✅ Successfully indexed: contract.pdf

**Vector Database:**
- Total characters: 12,450
- Chunks created: 15
- Average chunk size: 830 characters
- Document type: pdf

---

**📄 Document Classification:**

- **Type:** contract
- **Confidence:** 95%
- **Matter ID:** CASE-2024-001
- **Summary:** Employment contract between Acme Corporation and John Smith
- **Tags:** employment, legal, agreement

**Entities Extracted:**
- People: John Smith, Jane Doe
- Organizations: Acme Corporation, TechStart Inc
- Dates: 2025-01-15, 2025-06-30
- Amounts: $50,000, $5,000

✅ **Gemini Validation: VERIFIED (96% confidence)**
└─ Classification verified. All key entities and document type confirmed.

---

**📅 Deadlines Extracted: 2**

1. 🔴 **2025-01-15** - Contract signing deadline
   └─ 5 working days · CRITICAL

2. 🟢 **2025-06-30** - First performance review
   └─ 90 working days · LOW

✅ **Gemini Validation: VERIFIED (94% confidence)**
└─ All critical deadlines correctly identified and verified.
```

## Example 6: Python Code Usage

### Using the Agents Directly

```python
import asyncio
from agents.gemini_preprocessor import GeminiPreprocessor
from agents.gemini_validator import GeminiValidator
from agents.document_agent import DocumentAgent

async def process_document():
    # Step 1: Preprocess with Gemini
    preprocessor = GeminiPreprocessor()
    extraction = await preprocessor.extract_structured_data(
        text=document_text,
        filename="contract.pdf"
    )
    
    gemini_context = extraction['data'] if extraction['success'] else None
    
    # Step 2: Classify with Claude (enhanced with Gemini context)
    document_agent = DocumentAgent()
    classification = await document_agent.classify_document(
        document_id="contract.pdf",
        filename="contract.pdf",
        extracted_text=document_text,
        gemini_context=gemini_context
    )
    
    # Step 3: Validate with Gemini
    validator = GeminiValidator()
    validation = await validator.validate_classification(
        claude_output=classification['classification'],
        original_text=document_text,
        gemini_extraction=gemini_context
    )
    
    print(f"Validation Status: {validation['validation_status']}")
    print(f"Confidence: {validation['confidence_score']:.0%}")
    print(f"Feedback: {validation['feedback']}")
    
    if validation['discrepancies']:
        print("\nDiscrepancies found:")
        for disc in validation['discrepancies']:
            print(f"  - {disc}")

asyncio.run(process_document())
```

## Example 7: Handling Validation Results

### Check Confidence Threshold

```python
def should_require_review(validation):
    """Determine if manual review is needed"""
    if validation['validation_status'] == 'error':
        # Gemini not available, proceed with Claude only
        return False
    
    if validation['validation_status'] == 'discrepancy':
        # Always review discrepancies
        return True
    
    if validation['confidence_score'] < 0.85:
        # Low confidence, recommend review
        return True
    
    return False

# Usage
if should_require_review(classification_validation):
    print("⚠️ Manual review recommended")
    print(f"Reason: {classification_validation['feedback']}")
    for disc in classification_validation['discrepancies']:
        print(f"  - {disc}")
```

### Alert on Missing Information

```python
def check_missing_information(validation):
    """Alert if important information might be missing"""
    missing = validation.get('missing_information', [])
    
    if missing:
        print("⚠️ Potentially missing information:")
        for item in missing:
            print(f"  - {item}")
        return True
    
    return False
```

## Example 8: Database Queries

### Get All Validations for a Client

```sql
SELECT 
    v.*,
    ge.document_id,
    ge.model_version
FROM validations v
LEFT JOIN gemini_extractions ge ON v.extraction_id = ge.id
WHERE v.client_id = 'client-uuid'
ORDER BY v.created_at DESC;
```

### Get Low Confidence Validations

```sql
SELECT 
    validation_type,
    entity_id,
    confidence_score,
    feedback,
    discrepancies
FROM validations
WHERE confidence_score < 0.85
  AND validation_status != 'error'
ORDER BY confidence_score ASC;
```

### Get Validation Statistics

```sql
SELECT 
    validation_type,
    validation_status,
    COUNT(*) as count,
    AVG(confidence_score) as avg_confidence,
    MIN(confidence_score) as min_confidence,
    MAX(confidence_score) as max_confidence
FROM validations
WHERE validation_status != 'error'
GROUP BY validation_type, validation_status;
```

## Key Takeaways

1. **Three-step process**: Preprocess → Process → Validate
2. **Graceful degradation**: Works without Gemini API key
3. **Non-blocking**: Validation errors don't stop the workflow
4. **Rich feedback**: Confidence scores, verified items, discrepancies
5. **Audit trail**: All validations stored for analysis
6. **API flexibility**: Access validations through dedicated endpoints
