"""
Gemini Preprocessor Agent
Extracts structured data from documents as the first step in the validation pipeline
"""

import os
import json
from typing import Dict, Optional
import google.generativeai as genai


class GeminiPreprocessor:
    """
    Preprocesses documents using Gemini to extract structured data.
    This data is used to provide context hints to Claude and for validation.
    """
    
    def __init__(self, gemini_api_key: str = None):
        """
        Initialize the Gemini preprocessor.
        
        Args:
            gemini_api_key: Gemini API key (defaults to GEMINI_API_KEY environment variable)
        """
        print("Initializing Gemini Preprocessor...")
        
        # Get API key from parameter or environment
        self.api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            print("⚠️ Warning: GEMINI_API_KEY not provided. Gemini preprocessing will be disabled.")
            self.model = None
            return
        
        # Configure and initialize Gemini
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-3-flash-preview')
            print("✓ Gemini Preprocessor ready")
        except Exception as e:
            print(f"⚠️ Warning: Failed to initialize Gemini: {str(e)}")
            self.model = None
    
    async def extract_structured_data(self, text: str, filename: str = None) -> Dict:
        """
        Extract structured data from document text using Gemini.
        
        This method extracts:
        - Entities (people, organizations, locations, amounts)
        - Dates and deadlines
        - Key facts
        - Document metadata
        
        Args:
            text: The document text to analyze
            filename: Optional filename for context
            
        Returns:
            Dict with:
                - success: bool indicating if extraction succeeded
                - data: Extracted structured data (if successful)
                - error: Error message (if failed)
        """
        # If Gemini is not available, return gracefully
        if not self.model:
            return {
                'success': False,
                'error': 'Gemini API not configured',
                'data': None
            }
        
        try:
            print(f"  → Gemini preprocessing: {filename or 'document'}")
            
            # Construct the prompt for Gemini
            prompt = f"""Analyze this document and extract structured information in JSON format.

Document{f' ({filename})' if filename else ''}:
{text[:8000]}

Extract the following information and respond with ONLY valid JSON:

{{
    "entities": {{
        "people": ["list of person names mentioned"],
        "organizations": ["list of companies/organizations"],
        "locations": ["list of places/locations"],
        "amounts": ["list of monetary amounts with currency"]
    }},
    "dates_and_deadlines": [
        {{
            "date": "YYYY-MM-DD format",
            "description": "what happens on this date",
            "importance": "critical/high/medium/low"
        }}
    ],
    "key_facts": [
        "important fact 1",
        "important fact 2"
    ],
    "document_metadata": {{
        "suggested_type": "contract/invoice/email/report/memo/legal/other",
        "language": "detected language",
        "topic": "main topic or subject",
        "sentiment": "positive/neutral/negative"
    }}
}}

Respond with ONLY the JSON object, no additional text."""

            # Call Gemini API
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Try to parse JSON from response
            # Remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Parse the JSON
            extracted_data = json.loads(response_text)
            
            print(f"  ✓ Gemini extracted {len(extracted_data.get('key_facts', []))} key facts")
            
            return {
                'success': True,
                'data': extracted_data,
                'error': None
            }
            
        except json.JSONDecodeError as e:
            print(f"  ⚠️ Gemini response was not valid JSON: {str(e)}")
            return {
                'success': False,
                'error': f'JSON parsing error: {str(e)}',
                'data': None
            }
        except Exception as e:
            print(f"  ⚠️ Gemini preprocessing failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': None
            }
