#!/usr/bin/env python3
"""
Test upload endpoint response structure
Tests that the upload response includes document_id field
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_upload_response_structure():
    """Test that upload endpoint returns document_id in response"""
    print("Testing upload response structure...")
    
    try:
        api_server_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'api_server.py')
        
        with open(api_server_path, 'r') as f:
            content = f.read()
        
        # Find the upload_document function
        func_start = content.find('async def upload_document')
        if func_start == -1:
            print("✗ upload_document function not found")
            return False
        
        print("✓ upload_document function found")
        
        # Get function content (up to next function or end)
        next_func = content.find('\n@app.', func_start + 1)
        if next_func == -1:
            next_func = len(content)
        
        func_content = content[func_start:next_func]
        
        # Check for return statement with document_id
        if '"document_id"' not in func_content and "'document_id'" not in func_content:
            print("✗ document_id field not found in return statement")
            return False
        
        print("✓ document_id field found in return statement")
        
        # Check that it's in a return statement (not just a comment)
        return_start = func_content.find('return {')
        if return_start == -1:
            print("✗ Return statement not found")
            return False
        
        # Get the return dictionary
        return_end = func_content.find('}', return_start)
        return_dict = func_content[return_start:return_end + 1]
        
        # Verify document_id is in the return dictionary
        if '"document_id"' not in return_dict and "'document_id'" not in return_dict:
            print("✗ document_id not in return dictionary")
            return False
        
        print("✓ document_id is in return dictionary")
        
        # Check that other required fields are also present
        required_fields = ['success', 'filename', 'client_id', 'chunks_created', 
                          'classification', 'deadlines_extracted', 'deadlines']
        
        for field in required_fields:
            if f'"{field}"' not in return_dict and f"'{field}'" not in return_dict:
                print(f"✗ Required field {field} not found in return dictionary")
                return False
            print(f"✓ Required field {field} found")
        
        return True
    except Exception as e:
        print(f"✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("Testing Upload Response Structure")
    print("="*60)
    
    success = test_upload_response_structure()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    status = "✓ PASSED" if success else "✗ FAILED"
    print(f"Upload Response Structure: {status}")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
