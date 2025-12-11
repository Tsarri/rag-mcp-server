#!/usr/bin/env python3
"""
Test urgent deadlines endpoint
Tests the structure and response format without requiring database connection
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_endpoint_exists():
    """Test that the urgent deadlines endpoint exists in api_server.py"""
    print("Testing urgent deadlines endpoint existence...")
    
    try:
        api_server_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'api_server.py')
        
        with open(api_server_path, 'r') as f:
            content = f.read()
        
        # Check for endpoint definition
        assert '@app.get("/api/urgent-deadlines"' in content
        print("✓ Endpoint route defined")
        
        # Check for response model
        assert 'response_model=UrgentDeadlinesResponse' in content
        print("✓ Response model specified")
        
        # Check for limit parameter
        assert 'limit: int = 10' in content
        print("✓ Limit parameter with default value")
        
        # Check for docstring
        assert 'Get the most urgent deadlines across all clients' in content
        print("✓ Endpoint docstring present")
        
        return True
    except Exception as e:
        print(f"✗ Endpoint check error: {e}")
        return False

def test_pydantic_models():
    """Test that the required Pydantic models exist"""
    print("\nTesting Pydantic models...")
    
    try:
        api_server_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'api_server.py')
        
        with open(api_server_path, 'r') as f:
            content = f.read()
        
        # Check for UrgentDeadline model
        assert 'class UrgentDeadline(BaseModel):' in content
        print("✓ UrgentDeadline model defined")
        
        # Check for UrgentDeadlinesResponse model
        assert 'class UrgentDeadlinesResponse(BaseModel):' in content
        print("✓ UrgentDeadlinesResponse model defined")
        
        # Check for required fields in UrgentDeadline
        required_fields = [
            'id: str',
            'date: str',
            'description: str',
            'working_days_remaining: int',
            'risk_level: str',
            'client_id: Optional[str]',
            'client_name: Optional[str]',
            'client_email: Optional[str]'
        ]
        
        for field in required_fields:
            assert field in content
            print(f"✓ Field '{field}' defined")
        
        # Check for fields in UrgentDeadlinesResponse
        assert 'count: int' in content
        assert 'deadlines: List[UrgentDeadline]' in content
        print("✓ UrgentDeadlinesResponse fields defined")
        
        return True
    except Exception as e:
        print(f"✗ Model check error: {e}")
        return False

def test_implementation_logic():
    """Test that the implementation has the required logic"""
    print("\nTesting implementation logic...")
    
    try:
        api_server_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'api_server.py')
        
        with open(api_server_path, 'r') as f:
            content = f.read()
        
        # Check for risk priority mapping
        assert "risk_priority = {" in content
        assert "'overdue': 1," in content
        assert "'critical': 2," in content
        assert "'high': 3," in content
        assert "'medium': 4," in content
        assert "'low': 5" in content
        print("✓ Risk priority mapping present")
        
        # Check for sorting logic
        assert "sorted_deadlines = sorted(" in content
        print("✓ Sorting logic present")
        
        # Check for client info extraction
        assert "clients(name, email)" in content
        print("✓ Client info query present")
        
        # Check for proper error handling
        assert "except Exception as e:" in content
        assert "logger.error(" in content
        assert "HTTPException" in content
        print("✓ Error handling present")
        
        # Check for logging
        assert 'logger.info(f"Fetching top {limit} urgent deadlines across all clients")' in content
        print("✓ Logging present")
        
        return True
    except Exception as e:
        print(f"✗ Implementation logic check error: {e}")
        return False

def test_supabase_import():
    """Test that Supabase is imported and initialized"""
    print("\nTesting Supabase import and initialization...")
    
    try:
        api_server_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'api_server.py')
        
        with open(api_server_path, 'r') as f:
            content = f.read()
        
        # Check for Supabase import
        assert 'from supabase import create_client, Client' in content
        print("✓ Supabase import present")
        
        # Check for Supabase client initialization
        assert "supabase: Client = create_client(supabase_url, supabase_key)" in content
        print("✓ Supabase client initialization present")
        
        return True
    except Exception as e:
        print(f"✗ Supabase import check error: {e}")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("Testing Urgent Deadlines Endpoint")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Endpoint Exists", test_endpoint_exists()))
    results.append(("Pydantic Models", test_pydantic_models()))
    results.append(("Implementation Logic", test_implementation_logic()))
    results.append(("Supabase Import", test_supabase_import()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return all(result for _, result in results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
