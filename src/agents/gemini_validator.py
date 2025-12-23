"""
Gemini Validator Agent
Validates Claude's outputs as the third step in the validation pipeline
"""

import os
import json
import logging
from typing import Dict, List, Optional
import google.generativeai as genai

# Setup logging
logger = logging.getLogger(__name__)


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
        logger.info("Initializing Gemini Validator...")
        
        # Get API key from parameter or environment
        self.api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not provided. Gemini validation will be disabled.")
            self.model = None
            return
        
        # Configure and initialize Gemini
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-3-flash-preview')
            logger.info("✓ Gemini Validator ready with model: gemini-3-flash-preview")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {str(e)}", exc_info=True)
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
                - validation_status: 'validated', 'warning', or 'error'
                - confidence_score: 0.0 to 1.0
                - feedback: Human-readable feedback
                - verified_items: List of verified items
                - discrepancies: List of discrepancies found
                - missing_information: List of potentially missing items
        """
        # If Gemini is not available, return error status
        if not self.model:
            logger.warning("Gemini model not available, returning error validation")
            return {
                'validation_status': 'error',
                'confidence_score': 0.0,
                'feedback': 'Gemini API not configured',
                'verified_items': [],
                'discrepancies': [],
                'missing_information': []
            }
        
        try:
            logger.info(f"Starting classification validation for doc_type: {claude_output.get('doc_type')}")
            
            # Initialize response_text for error handling
            response_text = ""
            
            # Build context from Gemini extraction if available
            gemini_context = ""
            if gemini_extraction:
                gemini_context = f"\n\nGemini's preliminary analysis:\n{json.dumps(gemini_extraction, indent=2)}"
                logger.debug(f"Using Gemini context for validation (length: {len(gemini_context)})")
            
            # Construct validation prompt
            prompt = f"""You are validating another AI's document classification. Compare it against the original text.

ORIGINAL TEXT:
{original_text[:5000]}

CLAUDE'S CLASSIFICATION:
{json.dumps(claude_output, indent=2)}
{gemini_context}

Validate the classification and respond with ONLY valid JSON:

{{
    "validation_status": "validated|warning|error",
    "confidence_score": 0.95,
    "feedback": "Brief explanation of validation result",
    "verified_items": ["list of correct classifications"],
    "discrepancies": ["list of issues or differences found"],
    "missing_information": ["list of potentially missed important items"]
}}

Important: 
- confidence_score must be a number between 0.0 and 1.0
- Provide specific feedback about the classification accuracy
- Use 'validated' status when classification is accurate
- Use 'warning' status when there are issues

Respond with ONLY the JSON object."""

            logger.debug(f"Validation prompt constructed (length: {len(prompt)})")

            # Call Gemini API
            logger.info(f"Calling Gemini API for validation...")
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Log response at DEBUG level to avoid exposing sensitive content in production
            logger.debug(f"Raw Gemini validation response: {response_text}")
            
            # Parse JSON from response
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            logger.debug(f"Cleaned response text: {response_text}")
            
            validation_result = json.loads(response_text)
            logger.debug(f"Parsed validation result: {validation_result}")
            
            # Validate the structure and fix any issues
            if 'confidence_score' not in validation_result:
                logger.error("Gemini response missing 'confidence_score' field!")
                validation_result['confidence_score'] = 0.0
            
            if not isinstance(validation_result.get('confidence_score'), (int, float)):
                logger.error(f"Invalid confidence_score type: {type(validation_result.get('confidence_score'))}")
                validation_result['confidence_score'] = 0.0
            
            # Ensure confidence is in valid range
            confidence = float(validation_result.get('confidence_score', 0.0))
            if confidence < 0.0 or confidence > 1.0:
                logger.warning(f"Confidence {confidence} out of range [0.0, 1.0], clamping")
                confidence = max(0.0, min(1.0, confidence))
                validation_result['confidence_score'] = confidence
            
            logger.info(f"✓ Validation complete: {validation_result['validation_status']} (confidence: {validation_result['confidence_score']:.2f})")
            
            return validation_result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini validation response as JSON: {e}")
            logger.error(f"Raw response text: {response_text if response_text else 'No response captured'}")
            return {
                'validation_status': 'error',
                'confidence_score': 0.0,
                'feedback': f'JSON parsing failed: {str(e)}',
                'verified_items': [],
                'discrepancies': [],
                'missing_information': []
            }
        except Exception as e:
            logger.error(f"Gemini validation failed: {str(e)}", exc_info=True)
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
                - validation_status: 'validated', 'warning', or 'error'
                - confidence_score: 0.0 to 1.0
                - feedback: Human-readable feedback
                - verified_items: List of verified deadlines
                - discrepancies: List of discrepancies found
                - missing_information: List of potentially missed deadlines
        """
        # If Gemini is not available, return error status
        if not self.model:
            logger.warning("Gemini model not available, returning error validation for deadlines")
            return {
                'validation_status': 'error',
                'confidence_score': 0.0,
                'feedback': 'Gemini API not configured',
                'verified_items': [],
                'discrepancies': [],
                'missing_information': []
            }
        
        try:
            logger.info(f"Starting deadline validation for {len(claude_deadlines)} deadlines")
            
            # Initialize response_text for error handling
            response_text = ""
            
            # Build context from Gemini extraction if available
            gemini_context = ""
            if gemini_extraction and 'dates_and_deadlines' in gemini_extraction:
                gemini_context = f"\n\nGemini's preliminary deadline analysis:\n{json.dumps(gemini_extraction['dates_and_deadlines'], indent=2)}"
                logger.debug(f"Using Gemini deadline context (length: {len(gemini_context)})")
            
            # Construct validation prompt
            prompt = f"""You are validating another AI's deadline extraction. Compare it against the original text.

ORIGINAL TEXT:
{original_text[:5000]}

CLAUDE'S EXTRACTED DEADLINES:
{json.dumps(claude_deadlines, indent=2)}
{gemini_context}

Validate the deadline extraction and respond with ONLY valid JSON:

{{
    "validation_status": "validated|warning|error",
    "confidence_score": 0.95,
    "feedback": "Brief explanation of validation result",
    "verified_items": ["list of correctly identified deadlines"],
    "discrepancies": ["list of issues or incorrect dates found"],
    "missing_information": ["list of potentially missed deadlines"]
}}

Important:
- confidence_score must be a number between 0.0 and 1.0
- Provide specific feedback about the deadline accuracy
- Use 'validated' status when deadlines are accurate
- Use 'warning' status when there are issues

Respond with ONLY the JSON object."""

            logger.debug(f"Deadline validation prompt constructed (length: {len(prompt)})")

            # Call Gemini API
            logger.info("Calling Gemini API for deadline validation...")
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Log response at DEBUG level to avoid exposing sensitive content in production
            logger.debug(f"Raw Gemini deadline validation response: {response_text}")
            
            # Parse JSON from response
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            logger.debug(f"Cleaned deadline response text: {response_text}")
            
            validation_result = json.loads(response_text)
            logger.debug(f"Parsed deadline validation result: {validation_result}")
            
            # Validate the structure and fix any issues
            if 'confidence_score' not in validation_result:
                logger.error("Gemini deadline response missing 'confidence_score' field!")
                validation_result['confidence_score'] = 0.0
            
            if not isinstance(validation_result.get('confidence_score'), (int, float)):
                logger.error(f"Invalid deadline confidence_score type: {type(validation_result.get('confidence_score'))}")
                validation_result['confidence_score'] = 0.0
            
            # Ensure confidence is in valid range
            confidence = float(validation_result.get('confidence_score', 0.0))
            if confidence < 0.0 or confidence > 1.0:
                logger.warning(f"Deadline confidence {confidence} out of range [0.0, 1.0], clamping")
                confidence = max(0.0, min(1.0, confidence))
                validation_result['confidence_score'] = confidence
            
            logger.info(f"✓ Deadline validation complete: {validation_result['validation_status']} (confidence: {validation_result['confidence_score']:.2f})")
            
            return validation_result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini deadline validation response as JSON: {e}")
            logger.error(f"Raw response text: {response_text if response_text else 'No response captured'}")
            return {
                'validation_status': 'error',
                'confidence_score': 0.0,
                'feedback': f'JSON parsing failed: {str(e)}',
                'verified_items': [],
                'discrepancies': [],
                'missing_information': []
            }
        except Exception as e:
            logger.error(f"Gemini deadline validation failed: {str(e)}", exc_info=True)
            return {
                'validation_status': 'error',
                'confidence_score': 0.0,
                'feedback': f'Validation error: {str(e)}',
                'verified_items': [],
                'discrepancies': [],
                'missing_information': []
            }
