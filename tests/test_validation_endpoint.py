#!/usr/bin/env python3
"""
Test validation endpoint to ensure it returns default pending validation instead of 404

Note: These tests use string-based checks on the source code to verify structural changes.
While this approach is simpler than setting up a full test environment with database mocks,
it validates that the required code patterns are present in the implementation.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_validation_endpoint_structure():
    """Test that validation endpoint returns correct structure for missing validations"""
    print("Testing validation endpoint structure...")
    
    # Read the api_server.py file to verify the changes
    api_server_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'api_server.py')
    
    with open(api_server_path, 'r') as f:
        content = f.read()
    
    # Check that the endpoint no longer raises 404 for missing validations
    if 'raise HTTPException(status_code=404, detail="Validation not found")' in content:
        print("✗ Endpoint still raises 404 for missing validations")
        return False
    
    print("✓ Endpoint does not raise 404 for missing validations")
    
    # Check that it returns default pending validation
    if '"validation_status": "pending"' in content:
        print("✓ Endpoint returns pending status for missing validations")
    else:
        print("✗ Endpoint does not return pending status")
        return False
    
    # Check that confidence_score is set to 0.0
    if '"confidence_score": 0.0' in content:
        print("✓ Endpoint returns confidence_score 0.0 for missing validations")
    else:
        print("✗ Endpoint does not return confidence_score 0.0")
        return False
    
    # Check that validation type check was removed or relaxed
    if 'if validation_type not in [\'classification\', \'deadline\', \'other\']:' in content:
        print("✗ Endpoint still has strict validation type check")
        return False
    
    print("✓ Endpoint has flexible validation type handling")
    
    return True

def test_deadline_validation_storage():
    """Test that deadline validations are stored with actual deadline IDs"""
    print("\nTesting deadline validation storage...")
    
    # Read the api_server.py file to verify the changes
    api_server_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'api_server.py')
    
    with open(api_server_path, 'r') as f:
        content = f.read()
    
    # Check that deadline validation uses for loop to iterate deadlines
    if 'for deadline in deadline_result[\'deadlines\']:' in content:
        print("✓ Code iterates through individual deadlines")
    else:
        print("✗ Code does not iterate through individual deadlines")
        return False
    
    # Check that entity_id is set to deadline_id (not extraction_id)
    if '\'entity_id\': deadline_id,' in content or '"entity_id": deadline_id,' in content:
        print("✓ Uses actual deadline ID as entity_id")
    else:
        print("✗ Does not use actual deadline ID as entity_id")
        return False
    
    # Check that the old pattern is removed
    if 'deadline_result.get(\'extraction_id\', doc[\'filename\'])' in content:
        print("✗ Still uses old extraction_id pattern")
        return False
    
    print("✓ Old extraction_id pattern removed")
    
    # Check for proper logging
    if 'logger.info(f"Stored deadline validation for: {deadline_id}")' in content:
        print("✓ Proper logging added for deadline validation storage")
    else:
        print("✗ Missing proper logging for deadline validation storage")
        return False
    
    return True

def test_validation_logging():
    """Test that proper logging is in place"""
    print("\nTesting validation endpoint logging...")
    
    # Read the api_server.py file to verify the changes
    api_server_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'api_server.py')
    
    with open(api_server_path, 'r') as f:
        content = f.read()
    
    # Check for query result logging
    if 'logger.info(f"Validation query returned {len(response.data)} results")' in content:
        print("✓ Logging added for query results")
    else:
        print("✗ Missing logging for query results")
        return False
    
    # Check for pending status logging
    if 'logger.info(f"No {validation_type} validation found for entity: {entity_id}, returning pending status")' in content:
        print("✓ Logging added for pending status return")
    else:
        print("✗ Missing logging for pending status return")
        return False
    
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("VALIDATION ENDPOINT FIX TESTS")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(('Validation Endpoint Structure', test_validation_endpoint_structure()))
    results.append(('Deadline Validation Storage', test_deadline_validation_storage()))
    results.append(('Validation Logging', test_validation_logging()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Total: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
