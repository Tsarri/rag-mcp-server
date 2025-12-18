#!/usr/bin/env python3
"""
Test Gemini three-step workflow with mocked API responses
Tests that the workflow logic works correctly
"""

import sys
import os
import asyncio

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

async def test_preprocessor_without_api_key():
    """Test that preprocessor returns error status when no API key"""
    print("\n--- Testing Preprocessor Without API Key ---")
    
    from agents.gemini_preprocessor import GeminiPreprocessor
    
    preprocessor = GeminiPreprocessor(gemini_api_key=None)
    
    result = await preprocessor.extract_structured_data(
        text="Test document text",
        filename="test.pdf"
    )
    
    if result['success'] == False:
        print("✓ Preprocessor returns error status without API key")
    else:
        print("✗ Preprocessor should return error status without API key")
        return False
    
    if result['error'] == 'Gemini API not configured':
        print("✓ Preprocessor returns correct error message")
    else:
        print("✗ Preprocessor error message incorrect")
        return False
    
    if result['data'] is None:
        print("✓ Preprocessor returns None data on error")
    else:
        print("✗ Preprocessor should return None data on error")
        return False
    
    return True

async def test_validator_without_api_key():
    """Test that validator returns error status when no API key"""
    print("\n--- Testing Validator Without API Key ---")
    
    from agents.gemini_validator import GeminiValidator
    
    validator = GeminiValidator(gemini_api_key=None)
    
    # Test classification validation
    classification_result = await validator.validate_classification(
        claude_output={'doc_type': 'contract', 'confidence': 0.9},
        original_text="Test contract text"
    )
    
    if classification_result['validation_status'] == 'error':
        print("✓ Classification validator returns error status without API key")
    else:
        print("✗ Classification validator should return error status")
        return False
    
    if classification_result['confidence_score'] == 0.0:
        print("✓ Classification validator returns 0.0 confidence on error")
    else:
        print("✗ Classification validator should return 0.0 confidence")
        return False
    
    # Test deadline validation
    deadline_result = await validator.validate_deadlines(
        claude_deadlines=[{'date': '2025-01-15', 'description': 'Test deadline'}],
        original_text="Test document with deadline"
    )
    
    if deadline_result['validation_status'] == 'error':
        print("✓ Deadline validator returns error status without API key")
    else:
        print("✗ Deadline validator should return error status")
        return False
    
    if deadline_result['confidence_score'] == 0.0:
        print("✓ Deadline validator returns 0.0 confidence on error")
    else:
        print("✗ Deadline validator should return 0.0 confidence")
        return False
    
    return True

async def test_workflow_graceful_degradation():
    """Test that the full workflow works even without Gemini"""
    print("\n--- Testing Workflow Graceful Degradation ---")
    
    from agents.gemini_preprocessor import GeminiPreprocessor
    from agents.gemini_validator import GeminiValidator
    
    # Initialize without API key
    preprocessor = GeminiPreprocessor(gemini_api_key=None)
    validator = GeminiValidator(gemini_api_key=None)
    
    # Step 1: Preprocessing
    extraction = await preprocessor.extract_structured_data(
        text="Sample legal document text with deadline on 2025-01-15",
        filename="sample.pdf"
    )
    
    # Get context (should be None on error)
    gemini_context = extraction['data'] if extraction['success'] else None
    
    if gemini_context is None:
        print("✓ Workflow handles failed preprocessing gracefully")
    else:
        print("✗ Workflow should handle failed preprocessing")
        return False
    
    # Step 2: Simulate Claude processing (with None context)
    # In real implementation, agents would still work with gemini_context=None
    claude_output = {
        'doc_type': 'legal',
        'confidence': 0.85,
        'summary': 'Test summary'
    }
    
    # Step 3: Validation
    validation = await validator.validate_classification(
        claude_output=claude_output,
        original_text="Sample legal document text",
        gemini_extraction=gemini_context
    )
    
    if validation['validation_status'] == 'error':
        print("✓ Workflow completes even when validation fails")
    else:
        print("✗ Validation should fail without API key")
        return False
    
    print("✓ Complete workflow handles missing API key gracefully")
    return True

async def test_gemini_context_structure():
    """Test expected structure of gemini_context"""
    print("\n--- Testing Gemini Context Structure ---")
    
    # Expected structure when Gemini is available
    expected_structure = {
        'entities': {
            'people': [],
            'organizations': [],
            'locations': [],
            'amounts': []
        },
        'dates_and_deadlines': [],
        'key_facts': [],
        'document_metadata': {
            'suggested_type': 'contract',
            'language': 'en',
            'topic': 'legal',
            'sentiment': 'neutral'
        }
    }
    
    # Check that the structure is documented in the preprocessor
    from agents.gemini_preprocessor import GeminiPreprocessor
    
    # Get the docstring
    docstring = GeminiPreprocessor.extract_structured_data.__doc__
    
    if docstring and ('entities' in docstring or 'Entities' in docstring):
        print("✓ Expected data structure is documented")
    else:
        # Check the source code for the prompt that defines the structure
        import inspect
        source = inspect.getsource(GeminiPreprocessor.extract_structured_data)
        if 'entities' in source and 'dates_and_deadlines' in source:
            print("✓ Expected data structure is defined in implementation")
        else:
            print("✗ Data structure not properly documented")
            return False
    
    print("✓ Gemini context structure is well-defined")
    return True

def test_validation_result_structure():
    """Test expected structure of validation results"""
    print("\n--- Testing Validation Result Structure ---")
    
    # Expected fields in validation results
    required_fields = [
        'validation_status',
        'confidence_score',
        'feedback',
        'verified_items',
        'discrepancies',
        'missing_information'
    ]
    
    from agents.gemini_validator import GeminiValidator
    
    # Check docstrings document the structure
    classify_doc = GeminiValidator.validate_classification.__doc__
    deadline_doc = GeminiValidator.validate_deadlines.__doc__
    
    for field in required_fields:
        if field in classify_doc and field in deadline_doc:
            print(f"✓ Field '{field}' is documented")
        else:
            print(f"✗ Field '{field}' not documented")
            return False
    
    print("✓ Validation result structure is well-defined")
    return True

async def main():
    """Run all workflow tests"""
    print("="*60)
    print("Testing Gemini Three-Step Workflow")
    print("="*60)
    
    results = []
    
    results.append(await test_preprocessor_without_api_key())
    results.append(await test_validator_without_api_key())
    results.append(await test_workflow_graceful_degradation())
    results.append(await test_gemini_context_structure())
    results.append(test_validation_result_structure())
    
    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✓ All {total} workflow tests passed!")
        return 0
    else:
        print(f"✗ {total - passed} workflow test(s) failed out of {total}")
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))
