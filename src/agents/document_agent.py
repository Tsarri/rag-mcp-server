"""
Document Agent Wrapper
Integrates document classification functionality into MCP server
Based on: https://github.com/dr-p1n/v2-demos-document.agent-agentta
"""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime
from anthropic import Anthropic
from supabase import create_client, Client


class DocumentAgent:
    """
    Classify and extract metadata from documents using Claude AI.
    Identifies document type, entities, matter IDs, and generates summaries.
    """
    
    def __init__(self, supabase_url: str = None, supabase_key: str = None, anthropic_key: str = None):
        """Initialize the document agent with API credentials"""
        print("Initializing Document Agent...")
        
        # Get credentials from parameters or environment
        self.supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        self.supabase_key = supabase_key or os.getenv('SUPABASE_KEY')
        self.anthropic_key = anthropic_key or os.getenv('ANTHROPIC_API_KEY')
        
        # Validate credentials
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing Supabase credentials (SUPABASE_URL, SUPABASE_KEY)")
        
        if not self.anthropic_key:
            raise ValueError("Missing Anthropic API key (ANTHROPIC_API_KEY)")
        
        # Initialize API clients
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.anthropic = Anthropic(api_key=self.anthropic_key)
        
        print("✓ Document Agent ready")
    
    async def classify_document(
        self, 
        document_id: str,
        filename: str,
        extracted_text: str,
        metadata: dict = None,
        client_id: str = None,
        gemini_context: Dict = None
    ) -> Dict:
        """
        Classify a document and extract structured metadata.
        
        This method:
        1. Sends document text to Claude for analysis
        2. Extracts document type, entities, matter ID, tags
        3. Generates a summary
        4. Stores classification in Supabase
        
        Args:
            document_id: Unique identifier for the document
            filename: Original filename
            extracted_text: Full text content of the document
            metadata: Optional additional metadata
            client_id: Optional client UUID to associate document with
            
        Returns:
            Dict with:
                - document_id: The document identifier
                - doc_type: Classification (contract, invoice, email, etc.)
                - matter_id: Extracted case/matter identifier
                - tags: List of relevant tags
                - key_entities: Dict with people, organizations, dates, amounts
                - summary: Brief description
                - confidence: Classification confidence (0-1)
        """
        try:
            print(f"  → Classifying document: {filename}")
            
            # Create text preview (first 500 chars for storage)
            text_preview = extracted_text[:500] if len(extracted_text) > 500 else extracted_text
            
            # Build Gemini context hint if available
            gemini_hint = ""
            if gemini_context:
                gemini_hint = "\n\nANOTHER AI MODEL'S ANALYSIS:\n"
                
                if gemini_context.get('document_metadata'):
                    doc_meta = gemini_context['document_metadata']
                    if doc_meta.get('suggested_type'):
                        gemini_hint += f"- Suggested type: {doc_meta['suggested_type']}\n"
                    if doc_meta.get('topic'):
                        gemini_hint += f"- Topic: {doc_meta['topic']}\n"
                
                if gemini_context.get('entities'):
                    entities = gemini_context['entities']
                    if entities.get('people'):
                        gemini_hint += f"- People identified: {', '.join(entities['people'][:5])}\n"
                    if entities.get('organizations'):
                        gemini_hint += f"- Organizations: {', '.join(entities['organizations'][:5])}\n"
                
                gemini_hint += "\nUse this as reference, but make your own classification based on the full text.\n"
            
            # Construct the prompt for Claude
            prompt = f"""You are analyzing a document to classify it and extract structured metadata.
{gemini_hint}
Document filename: {filename}
Document text:
{extracted_text[:5000]}  

Analyze this document and respond with ONLY valid JSON in this exact format:
{{
    "doc_type": "one of: contract, invoice, email, report, memo, legal, other",
    "matter_id": "case or matter identifier if found (e.g., ACME-2024-001), or null",
    "tags": ["relevant", "keywords", "here"],
    "key_entities": {{
        "people": ["list of person names"],
        "organizations": ["list of company/org names"],
        "dates": ["list of important dates in YYYY-MM-DD format"],
        "amounts": ["list of monetary amounts"]
    }},
    "summary": "one sentence summary of the document",
    "confidence": 0.95
}}

Document type definitions:
- contract: Legal agreements, contracts, terms of service
- invoice: Bills, invoices, payment requests
- email: Email correspondence, notifications
- report: Business reports, analysis documents
- memo: Internal memos, notes
- legal: Legal filings, court documents, legal notices
- other: Anything that doesn't fit above categories

Rules:
- doc_type must be one of the specified types
- matter_id should be any case/matter identifier found (format: CLIENT-YEAR-NUMBER or similar)
- tags should be 3-8 relevant keywords
- Extract ALL people, organizations, dates, and amounts mentioned
- Summary should be concise (under 150 characters)
- Confidence should reflect how certain you are about the classification (0.0 to 1.0)
- Return ONLY valid JSON, no other text
"""

            # Call Claude API
            print(f"  → Calling Claude AI for classification...")
            
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Get the response text
            response_text = response.content[0].text.strip()
            
            # Clean up response (remove markdown code blocks if present)
            if "```" in response_text:
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                else:
                    response_text = response_text.replace("```", "").strip()
            
            # Parse JSON
            try:
                classification = json.loads(response_text)
            except json.JSONDecodeError as e:
                print(f"  ⚠️ JSON parse error: {e}")
                print(f"  Response was: {response_text[:300]}")
                # Fallback classification
                classification = {
                    "doc_type": "other",
                    "matter_id": None,
                    "tags": [],
                    "key_entities": {"people": [], "organizations": [], "dates": [], "amounts": []},
                    "summary": "Document could not be classified",
                    "confidence": 0.0
                }
            
            # Prepare database record
            db_record = {
                "document_id": document_id,
                "filename": filename,
                "doc_type": classification.get("doc_type", "other"),
                "matter_id": classification.get("matter_id"),
                "tags": classification.get("tags", []),
                "key_entities": classification.get("key_entities", {}),
                "summary": classification.get("summary", ""),
                "confidence": classification.get("confidence", 0.0),
                "original_metadata": metadata or {},
                "text_preview": text_preview,
                "client_id": client_id
            }
            
            # Store in Supabase (upsert to handle duplicates)
            try:
                result = self.supabase.table('documents').upsert(
                    db_record,
                    on_conflict='document_id'
                ).execute()
                
                print(f"  ✓ Document classified as: {classification['doc_type']} (confidence: {classification['confidence']:.0%})")
                
                if classification.get('matter_id'):
                    print(f"  ✓ Matter ID identified: {classification['matter_id']}")
                
                if classification.get('key_entities'):
                    entities = classification['key_entities']
                    entity_summary = []
                    if entities.get('people'):
                        entity_summary.append(f"{len(entities['people'])} people")
                    if entities.get('organizations'):
                        entity_summary.append(f"{len(entities['organizations'])} organizations")
                    if entities.get('dates'):
                        entity_summary.append(f"{len(entities['dates'])} dates")
                    if entities.get('amounts'):
                        entity_summary.append(f"{len(entities['amounts'])} amounts")
                    
                    if entity_summary:
                        print(f"  ✓ Entities extracted: {', '.join(entity_summary)}")
                
            except Exception as db_error:
                print(f"  ⚠️ Error storing classification: {db_error}")
            
            return {
                "document_id": document_id,
                "classification": classification
            }
        
        except Exception as e:
            print(f"  ✗ Error classifying document: {e}")
            raise
    
    async def search_documents(
        self,
        query: str = None,
        doc_type: str = None,
        matter_id: str = None,
        limit: int = 50,
        client_id: str = None
    ) -> List[Dict]:
        """
        Search documents with optional filters.
        
        Args:
            query: Text to search in filename, summary, and tags
            doc_type: Filter by document type
            matter_id: Filter by matter ID
            limit: Maximum number of results
            client_id: Optional client UUID to filter by
            
        Returns:
            List of matching document records
        """
        try:
            # Start with base query
            db_query = self.supabase.table('documents').select('*')
            
            # Apply filters
            if doc_type:
                db_query = db_query.eq('doc_type', doc_type)
            
            if matter_id:
                db_query = db_query.eq('matter_id', matter_id)
            
            if client_id:
                db_query = db_query.eq('client_id', client_id)
            
            if query:
                # Search in filename, summary, or tags
                # Note: This is a simple approach; for production you'd use full-text search
                db_query = db_query.or_(
                    f'filename.ilike.%{query}%,'
                    f'summary.ilike.%{query}%'
                )
            
            # Order by most recent first
            db_query = db_query.order('created_at', desc=True)
            
            # Apply limit
            db_query = db_query.limit(limit)
            
            # Execute query
            response = db_query.execute()
            
            return response.data
        
        except Exception as e:
            print(f"Error searching documents: {e}")
            raise
    
    async def get_document_stats(self, client_id: str = None) -> Dict:
        """
        Get statistics about classified documents.
        
        Args:
            client_id: Optional client UUID to filter by
        
        Returns:
            Dict with counts by document type and total
        """
        try:
            # Get all documents
            query = self.supabase.table('documents').select('doc_type')
            
            if client_id:
                query = query.eq('client_id', client_id)
            
            all_docs = query.execute()
            
            # Count by type
            stats = {
                "total": len(all_docs.data),
                "contract": 0,
                "invoice": 0,
                "email": 0,
                "report": 0,
                "memo": 0,
                "legal": 0,
                "other": 0
            }
            
            for doc in all_docs.data:
                doc_type = doc.get('doc_type', 'other')
                if doc_type in stats:
                    stats[doc_type] += 1
            
            return stats
        
        except Exception as e:
            print(f"Error getting document stats: {e}")
            raise