#!/usr/bin/env python3
"""
Test Gemini integration structure and graceful degradation
Tests that the system works with and without Gemini API key
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_gemini_imports():
    """Test that Gemini agent modules can be imported"""
    print("Testing Gemini agent imports...")
    
    try:
        from agents.gemini_preprocessor import GeminiPreprocessor
        print("✓ GeminiPreprocessor can be imported")
    except ImportError as e:
        print(f"✗ GeminiPreprocessor import failed: {e}")
        return False
    
    try:
        from agents.gemini_validator import GeminiValidator
        print("✓ GeminiValidator can be imported")
    except ImportError as e:
        print(f"✗ GeminiValidator import failed: {e}")
        return False
    
    return True

def test_gemini_preprocessor_structure():
    """Test GeminiPreprocessor class structure"""
    print("\nTesting GeminiPreprocessor structure...")
    
    try:
        from agents.gemini_preprocessor import GeminiPreprocessor
        
        # Test instantiation without API key
        preprocessor = GeminiPreprocessor(gemini_api_key=None)
        print("✓ GeminiPreprocessor can be instantiated without API key")
        
        # Check that model is None when no key provided
        if preprocessor.model is None:
            print("✓ GeminiPreprocessor gracefully handles missing API key")
        else:
            print("⚠️ GeminiPreprocessor should set model to None when no API key")
        
        # Check for expected method
        if hasattr(preprocessor, 'extract_structured_data'):
            print("✓ GeminiPreprocessor has extract_structured_data method")
        else:
            print("✗ GeminiPreprocessor missing extract_structured_data method")
            return False
        
        return True
    except Exception as e:
        print(f"✗ GeminiPreprocessor structure test failed: {e}")
        return False

def test_gemini_validator_structure():
    """Test GeminiValidator class structure"""
    print("\nTesting GeminiValidator structure...")
    
    try:
        from agents.gemini_validator import GeminiValidator
        
        # Test instantiation without API key
        validator = GeminiValidator(gemini_api_key=None)
        print("✓ GeminiValidator can be instantiated without API key")
        
        # Check that model is None when no key provided
        if validator.model is None:
            print("✓ GeminiValidator gracefully handles missing API key")
        else:
            print("⚠️ GeminiValidator should set model to None when no API key")
        
        # Check for expected methods
        if hasattr(validator, 'validate_classification'):
            print("✓ GeminiValidator has validate_classification method")
        else:
            print("✗ GeminiValidator missing validate_classification method")
            return False
        
        if hasattr(validator, 'validate_deadlines'):
            print("✓ GeminiValidator has validate_deadlines method")
        else:
            print("✗ GeminiValidator missing validate_deadlines method")
            return False
        
        return True
    except Exception as e:
        print(f"✗ GeminiValidator structure test failed: {e}")
        return False

def test_agent_gemini_context_parameters():
    """Test that existing agents accept gemini_context parameter"""
    print("\nTesting agent gemini_context parameters...")
    
    # Instead of importing agents (which may fail without dependencies),
    # check the source code directly
    document_agent_file = os.path.join(
        os.path.dirname(__file__), '..', 
        'src', 'agents', 'document_agent.py'
    )
    
    deadline_agent_file = os.path.join(
        os.path.dirname(__file__), '..', 
        'src', 'agents', 'deadline_agent.py'
    )
    
    try:
        # Check DocumentAgent
        with open(document_agent_file, 'r') as f:
            content = f.read()
            if 'gemini_context: Dict = None' in content or 'gemini_context=None' in content:
                print("✓ DocumentAgent.classify_document accepts gemini_context parameter")
            else:
                print("✗ DocumentAgent.classify_document missing gemini_context parameter")
                return False
        
        # Check DeadlineAgent
        with open(deadline_agent_file, 'r') as f:
            content = f.read()
            if 'gemini_context: Dict = None' in content or 'gemini_context=None' in content:
                print("✓ DeadlineAgent.extract_deadlines accepts gemini_context parameter")
            else:
                print("✗ DeadlineAgent.extract_deadlines missing gemini_context parameter")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Agent parameter test failed: {e}")
        return False

def test_database_schema():
    """Test that database migration file exists"""
    print("\nTesting database schema updates...")
    
    migration_file = os.path.join(
        os.path.dirname(__file__), '..', 
        'database', 'migrations', 'add_gemini_validation_tables.sql'
    )
    
    if os.path.exists(migration_file):
        print("✓ Gemini validation tables migration file exists")
        
        # Check for expected table definitions
        with open(migration_file, 'r') as f:
            content = f.read()
            
            if 'gemini_extractions' in content:
                print("✓ Migration includes gemini_extractions table")
            else:
                print("✗ Migration missing gemini_extractions table")
                return False
            
            if 'validations' in content:
                print("✓ Migration includes validations table")
            else:
                print("✗ Migration missing validations table")
                return False
        
        return True
    else:
        print("✗ Migration file not found")
        return False

def test_api_server_integration():
    """Test that API server imports Gemini agents"""
    print("\nTesting API server Gemini integration...")
    
    api_server_file = os.path.join(
        os.path.dirname(__file__), '..', 
        'src', 'api_server.py'
    )
    
    with open(api_server_file, 'r') as f:
        content = f.read()
        
        if 'from agents.gemini_preprocessor import GeminiPreprocessor' in content:
            print("✓ API server imports GeminiPreprocessor")
        else:
            print("✗ API server missing GeminiPreprocessor import")
            return False
        
        if 'from agents.gemini_validator import GeminiValidator' in content:
            print("✓ API server imports GeminiValidator")
        else:
            print("✗ API server missing GeminiValidator import")
            return False
        
        if 'gemini_preprocessor = GeminiPreprocessor()' in content:
            print("✓ API server initializes GeminiPreprocessor")
        else:
            print("✗ API server missing GeminiPreprocessor initialization")
            return False
        
        if 'gemini_validator = GeminiValidator()' in content:
            print("✓ API server initializes GeminiValidator")
        else:
            print("✗ API server missing GeminiValidator initialization")
            return False
        
        if '@app.get("/api/validations/{validation_type}/{entity_id}")' in content:
            print("✓ API server includes validation endpoint")
        else:
            print("✗ API server missing validation endpoint")
            return False
    
    return True

def test_requirements():
    """Test that google-generativeai is in requirements.txt"""
    print("\nTesting requirements.txt...")
    
    requirements_file = os.path.join(
        os.path.dirname(__file__), '..', 
        'requirements.txt'
    )
    
    with open(requirements_file, 'r') as f:
        content = f.read()
        
        if 'google-generativeai' in content:
            print("✓ google-generativeai added to requirements.txt")
            return True
        else:
            print("✗ google-generativeai missing from requirements.txt")
            return False

def main():
    """Run all tests"""
    print("="*60)
    print("Testing Gemini Integration Structure")
    print("="*60)
    
    results = []
    
    results.append(test_gemini_imports())
    results.append(test_gemini_preprocessor_structure())
    results.append(test_gemini_validator_structure())
    results.append(test_agent_gemini_context_parameters())
    results.append(test_database_schema())
    results.append(test_api_server_integration())
    results.append(test_requirements())
    
    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✓ All {total} test suites passed!")
        return 0
    else:
        print(f"✗ {total - passed} test suite(s) failed out of {total}")
        return 1

if __name__ == "__main__":
    exit(main())
