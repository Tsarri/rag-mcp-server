#!/usr/bin/env python3
"""
Test health check endpoints
Tests the basic /health and detailed /health/detailed endpoints
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_health_endpoint_structure():
    """
    Test that health check endpoints are properly structured.
    This test validates the code structure without requiring a running server.
    """
    print("Testing health check endpoint structure...")
    
    try:
        # Import the module to check structure
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'api_server', 
            os.path.join(os.path.dirname(__file__), '..', 'src', 'api_server.py')
        )
        if spec is not None:
            print("✓ api_server.py can be loaded")
        else:
            print("✗ api_server.py cannot be loaded")
            return False
        
        # Read the file to check for endpoint definitions
        with open(os.path.join(os.path.dirname(__file__), '..', 'src', 'api_server.py'), 'r') as f:
            content = f.read()
            
        # Check for basic health endpoint
        if '@app.get("/health")' in content:
            print("✓ Basic /health endpoint exists")
        else:
            print("✗ Basic /health endpoint not found")
            return False
            
        # Check for detailed health endpoint
        if '@app.get("/health/detailed")' in content:
            print("✓ Detailed /health/detailed endpoint exists")
        else:
            print("✗ Detailed /health/detailed endpoint not found")
            return False
            
        # Check for Gemini status checks in detailed endpoint
        if 'gemini_preprocessor.model' in content and 'gemini_validator.model' in content:
            print("✓ Gemini service status checks present")
        else:
            print("✗ Gemini service status checks not found")
            return False
            
        # Check for warnings in health status
        if '"warnings": []' in content or "'warnings': []" in content:
            print("✓ Warnings field in health status")
        else:
            print("✗ Warnings field not found in health status")
            return False
            
        # Check for degraded status logic
        if '"degraded"' in content and 'health_status["status"]' in content:
            print("✓ Degraded status logic present")
        else:
            print("✗ Degraded status logic not found")
            return False
            
        print("\n✅ All health check endpoint structure tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Error testing health endpoints: {e}")
        return False


def test_gemini_initialization_logging():
    """
    Test that Gemini initialization logging is present in the code.
    """
    print("\nTesting Gemini initialization logging...")
    
    try:
        # Read the file to check for initialization logging
        with open(os.path.join(os.path.dirname(__file__), '..', 'src', 'api_server.py'), 'r') as f:
            content = f.read()
            
        # Check for initialization status logging
        if 'Service Initialization Status:' in content:
            print("✓ Service initialization status logging present")
        else:
            print("✗ Service initialization status logging not found")
            return False
            
        # Check for Gemini Preprocessor status check
        if 'Gemini Preprocessor: READY' in content or 'Gemini Preprocessor: NOT AVAILABLE' in content:
            print("✓ Gemini Preprocessor status logging present")
        else:
            print("✗ Gemini Preprocessor status logging not found")
            return False
            
        # Check for Gemini Validator status check
        if 'Gemini Validator: READY' in content or 'Gemini Validator: NOT AVAILABLE' in content:
            print("✓ Gemini Validator status logging present")
        else:
            print("✗ Gemini Validator status logging not found")
            return False
            
        # Check for API key warning
        if 'Set GEMINI_API_KEY in environment' in content:
            print("✓ GEMINI_API_KEY warning present")
        else:
            print("✗ GEMINI_API_KEY warning not found")
            return False
            
        # Check for confidence warning
        if 'All validations will return 0% confidence' in content:
            print("✓ Validation confidence warning present")
        else:
            print("✗ Validation confidence warning not found")
            return False
            
        print("\n✅ All Gemini initialization logging tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Error testing initialization logging: {e}")
        return False


def test_document_upload_warnings():
    """
    Test that document upload warnings are present in the code.
    """
    print("\nTesting document upload warnings...")
    
    try:
        # Read the file to check for upload warnings
        with open(os.path.join(os.path.dirname(__file__), '..', 'src', 'api_server.py'), 'r') as f:
            content = f.read()
            
        # Check for Gemini status check before upload
        if 'gemini_status = {' in content and '"preprocessor":' in content and '"validator":' in content:
            print("✓ Gemini status check in upload function")
        else:
            print("✗ Gemini status check in upload function not found")
            return False
            
        # Check for degraded services warning
        if 'Processing document' in content and 'with degraded Gemini services' in content:
            print("✓ Degraded services warning present")
        else:
            print("✗ Degraded services warning not found")
            return False
            
        # Check for validation confidence warning in upload
        if 'Classification validation will return 0% confidence' in content:
            print("✓ Classification validation warning present")
        else:
            print("✗ Classification validation warning not found")
            return False
            
        # Check for preprocessing warning
        if 'No preprocessing hints will be provided to Claude' in content:
            print("✓ Preprocessing warning present")
        else:
            print("✗ Preprocessing warning not found")
            return False
            
        print("\n✅ All document upload warning tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Error testing upload warnings: {e}")
        return False


def test_validation_error_logging():
    """
    Test that enhanced validation error logging is present.
    """
    print("\nTesting validation error logging...")
    
    try:
        # Read the file to check for validation error logging
        with open(os.path.join(os.path.dirname(__file__), '..', 'src', 'api_server.py'), 'r') as f:
            content = f.read()
            
        # Check for 0% confidence warning
        if 'Validation returned 0% confidence with error status' in content:
            print("✓ 0% confidence warning present")
        else:
            print("✗ 0% confidence warning not found")
            return False
            
        # Check for Gemini API configuration hint
        if 'This usually indicates Gemini API is not configured or failed' in content:
            print("✓ Gemini API configuration hint present")
        else:
            print("✗ Gemini API configuration hint not found")
            return False
            
        # Check for validation feedback logging
        if 'Validation feedback:' in content:
            print("✓ Validation feedback logging present")
        else:
            print("✗ Validation feedback logging not found")
            return False
            
        print("\n✅ All validation error logging tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Error testing validation error logging: {e}")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("HEALTH CHECK AND LOGGING TESTS")
    print("=" * 70)
    
    all_passed = True
    
    all_passed = test_health_endpoint_structure() and all_passed
    all_passed = test_gemini_initialization_logging() and all_passed
    all_passed = test_document_upload_warnings() and all_passed
    all_passed = test_validation_error_logging() and all_passed
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 70)
        sys.exit(1)
