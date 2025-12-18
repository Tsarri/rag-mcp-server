"""
Gemini Validator Agent
Validates Claude's outputs as the third step in the validation pipeline
"""

import os
import json
from typing import Dict, List, Optional
import google.generativeai as genai


class GeminiValidator:
    """
    Validates Claude's classification and deadline extraction using Gemini.
    Provides confidence scores and identifies discrepancies.
    """
    
    def __init__(self, gemini_api_key: str = None):
        """
        Initialize the Gemini validator.
        
        Args:
            gemini_api_key: Gemini API key (defaults to GEMINI_API_KEY environment variable)
        """
        print("Initializing Gemini Validator...")
        
        # Get API key from parameter or environment
        self.api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            print("⚠️ Warning: GEMINI_API_KEY not provided. Gemini validation will be disabled.")
            self.model = None
            return
        
        # Configure and initialize Gemini
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-pro')
            print("✓ Gemini Validator ready")
        except Exception as e:
            print(f"⚠️ Warning: Failed to initialize Gemini: {str(e)}")
            self.model = None
    
    async def validate_classification(
        self,
        claude_output: Dict,
        original_text: str,
        gemini_extraction: Dict = None
    ) -> Dict:
        """
        Validate Claude's document classification.
        
        Args:
            claude_output: Claude's classification result
            original_text: Original document text
            gemini_extraction: Optional Gemini preprocessing data
            
        Returns:
            Dict with:
                - validation_status: 'verified', 'discrepancy', or 'error'
                - confidence_score: 0.0 to 1.0
                - feedback: Human-readable feedback
                - verified_items: List of verified items
                - discrepancies: List of discrepancies found
                - missing_information: List of potentially missing items
        """
        # If Gemini is not available, return error status
        if not self.model:
            return {
                'validation_status': 'error',
                'confidence_score': 0.0,
                'feedback': 'Gemini API not configured',
                'verified_items': [],
                'discrepancies': [],
                'missing_information': []
            }
        
        try:
            print(f"  → Gemini validating classification...")
            
            # Build context from Gemini extraction if available
            gemini_context = ""
            if gemini_extraction:
                gemini_context = f"\n\nGemini's preliminary analysis:\n{json.dumps(gemini_extraction, indent=2)}"
            
            # Construct validation prompt
            prompt = f"""You are validating another AI's document classification. Compare it against the original text.

ORIGINAL TEXT:
{original_text[:5000]}

CLAUDE'S CLASSIFICATION:
{json.dumps(claude_output, indent=2)}
{gemini_context}

Validate the classification and respond with ONLY valid JSON:

{{
    "validation_status": "verified|discrepancy|error",
    "confidence_score": 0.95,
    "feedback": "Brief explanation of validation result",
    "verified_items": ["list of correct classifications"],
    "discrepancies": ["list of issues or differences found"],
    "missing_information": ["list of potentially missed important items"]
}}

Respond with ONLY the JSON object."""

            # Call Gemini API
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Parse JSON from response
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            validation_result = json.loads(response_text)
            
            print(f"  ✓ Validation: {validation_result['validation_status']} ({validation_result['confidence_score']:.0%})")
            
            return validation_result
            
        except Exception as e:
            print(f"  ⚠️ Gemini validation failed: {str(e)}")
            return {
                'validation_status': 'error',
                'confidence_score': 0.0,
                'feedback': f'Validation error: {str(e)}',
                'verified_items': [],
                'discrepancies': [],
                'missing_information': []
            }
    
    async def validate_deadlines(
        self,
        claude_deadlines: List[Dict],
        original_text: str,
        gemini_extraction: Dict = None
    ) -> Dict:
        """
        Validate Claude's deadline extraction.
        
        Args:
            claude_deadlines: List of deadlines extracted by Claude
            original_text: Original document text
            gemini_extraction: Optional Gemini preprocessing data
            
        Returns:
            Dict with:
                - validation_status: 'verified', 'discrepancy', or 'error'
                - confidence_score: 0.0 to 1.0
                - feedback: Human-readable feedback
                - verified_items: List of verified deadlines
                - discrepancies: List of discrepancies found
                - missing_information: List of potentially missed deadlines
        """
        # If Gemini is not available, return error status
        if not self.model:
            return {
                'validation_status': 'error',
                'confidence_score': 0.0,
                'feedback': 'Gemini API not configured',
                'verified_items': [],
                'discrepancies': [],
                'missing_information': []
            }
        
        try:
            print(f"  → Gemini validating {len(claude_deadlines)} deadlines...")
            
            # Build context from Gemini extraction if available
            gemini_context = ""
            if gemini_extraction and 'dates_and_deadlines' in gemini_extraction:
                gemini_context = f"\n\nGemini's preliminary deadline analysis:\n{json.dumps(gemini_extraction['dates_and_deadlines'], indent=2)}"
            
            # Construct validation prompt
            prompt = f"""You are validating another AI's deadline extraction. Compare it against the original text.

ORIGINAL TEXT:
{original_text[:5000]}

CLAUDE'S EXTRACTED DEADLINES:
{json.dumps(claude_deadlines, indent=2)}
{gemini_context}

Validate the deadline extraction and respond with ONLY valid JSON:

{{
    "validation_status": "verified|discrepancy|error",
    "confidence_score": 0.95,
    "feedback": "Brief explanation of validation result",
    "verified_items": ["list of correctly identified deadlines"],
    "discrepancies": ["list of issues or incorrect dates found"],
    "missing_information": ["list of potentially missed deadlines"]
}}

Respond with ONLY the JSON object."""

            # Call Gemini API
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Parse JSON from response
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            validation_result = json.loads(response_text)
            
            print(f"  ✓ Validation: {validation_result['validation_status']} ({validation_result['confidence_score']:.0%})")
            
            return validation_result
            
        except Exception as e:
            print(f"  ⚠️ Gemini validation failed: {str(e)}")
            return {
                'validation_status': 'error',
                'confidence_score': 0.0,
                'feedback': f'Validation error: {str(e)}',
                'verified_items': [],
                'discrepancies': [],
                'missing_information': []
            }
