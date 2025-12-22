#!/usr/bin/env python3
"""
Test that deadline IDs are properly attached after database insertion
This verifies the fix for deadline validation storage issue
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_deadline_id_in_processed_deadlines():
    """Test that processed_deadlines include the database ID"""
    print("Testing deadline ID attachment in deadline_agent.py...")
    
    try:
        agent_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'agents', 'deadline_agent.py')
        
        with open(agent_path, 'r') as f:
            content = f.read()
        
        # Find the extract_deadlines function
        func_start = content.find('async def extract_deadlines')
        if func_start == -1:
            print("✗ extract_deadlines function not found")
            return False
        
        print("✓ extract_deadlines function found")
        
        # Get function content
        next_func = content.find('\n    async def ', func_start + 1)
        if next_func == -1:
            next_func = len(content)
        
        func_content = content[func_start:next_func]
        
        # Check that response is captured from database insert
        if 'response = self.supabase.table(\'deadlines\').insert' not in func_content:
            print("✗ Database insert response not captured")
            return False
        
        print("✓ Database insert response is captured")
        
        # Check that ID is extracted from response
        if 'response.data[0][\'id\']' not in func_content and 'response.data[0]["id"]' not in func_content:
            print("✗ ID not extracted from response.data")
            return False
        
        print("✓ ID is extracted from response.data")
        
        # Check that ID is added to processed_deadlines
        if '"id":' not in func_content and "'id':" not in func_content:
            print("✗ ID not added to processed_deadlines")
            return False
        
        print("✓ ID is added to processed_deadlines")
        
        # Verify the ID is in the append statement
        # Find the processed_deadlines.append section
        if 'processed_deadlines.append({' not in func_content:
            print("✗ processed_deadlines.append not found")
            return False
        
        # Simplified check: just verify "id" appears near the append statement
        # (within 500 chars before it, which should cover the dict being appended)
        append_pos = func_content.find('processed_deadlines.append({')
        context_before = func_content[max(0, append_pos - 500):append_pos + 500]
        
        if '"id":' not in context_before and "'id':" not in context_before:
            print("✗ ID not in the appended deadline dict")
            return False
        
        print("✓ ID is properly included in appended deadline dict")
        
        return True
        
    except Exception as e:
        print(f"✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_validation_storage_uses_deadline_id():
    """Test that validation storage code looks for deadline ID"""
    print("\nTesting validation storage uses deadline.get('id')...")
    
    try:
        api_server_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'api_server.py')
        
        with open(api_server_path, 'r') as f:
            content = f.read()
        
        # Find the upload_document function
        func_start = content.find('async def upload_document')
        if func_start == -1:
            print("✗ upload_document function not found")
            return False
        
        # Get function content (find next function or class definition)
        # Look for next async def or def at the same indentation level
        next_func = content.find('\n@app.', func_start + 1)
        if next_func == -1:
            # Try finding next function definition
            next_func = content.find('\nasync def ', func_start + 1)
        if next_func == -1:
            next_func = len(content)
        
        func_content = content[func_start:next_func]
        
        # Check that validation storage iterates through deadlines
        if 'for deadline in deadline_result[\'deadlines\']' not in func_content and \
           'for deadline in deadline_result["deadlines"]' not in func_content:
            print("✗ Validation storage doesn't iterate through deadline_result['deadlines']")
            return False
        
        print("✓ Validation storage iterates through deadline_result['deadlines']")
        
        # Check that it tries to get the deadline ID
        if 'deadline.get(\'id\')' not in func_content and 'deadline.get("id")' not in func_content:
            print("✗ Validation storage doesn't get deadline ID")
            return False
        
        print("✓ Validation storage gets deadline ID with deadline.get('id')")
        
        # Check that ID is used in validation insert
        if 'entity_id\': deadline_id' not in func_content and 'entity_id": deadline_id' not in func_content:
            print("✗ deadline_id not used as entity_id in validation insert")
            return False
        
        print("✓ deadline_id is used as entity_id in validation insert")
        
        # Check for warning when ID is missing
        if 'Deadline missing ID' not in func_content:
            print("✗ No warning for missing deadline ID")
            return False
        
        print("✓ Warning exists for missing deadline ID")
        
        return True
        
    except Exception as e:
        print(f"✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("Testing Deadline ID Attachment Fix")
    print("="*60)
    
    test1_success = test_deadline_id_in_processed_deadlines()
    test2_success = test_validation_storage_uses_deadline_id()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    status1 = "✓ PASSED" if test1_success else "✗ FAILED"
    status2 = "✓ PASSED" if test2_success else "✗ FAILED"
    
    print(f"Deadline ID Attachment: {status1}")
    print(f"Validation Storage Logic: {status2}")
    
    all_passed = test1_success and test2_success
    
    if all_passed:
        print("\n✓ All tests passed! The fix is properly implemented.")
    else:
        print("\n✗ Some tests failed. Review the implementation.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
