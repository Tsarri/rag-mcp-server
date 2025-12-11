#!/usr/bin/env python3
"""
Test delete document endpoint
Tests the structure without requiring database connection
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_endpoint_exists():
    """Test that the delete document endpoint exists in api_server.py"""
    print("Testing delete document endpoint existence...")
    
    try:
        api_server_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'api_server.py')
        
        with open(api_server_path, 'r') as f:
            content = f.read()
        
        # Check for endpoint definition
        assert '@app.delete("/api/clients/{client_id}/documents/{document_id}")' in content
        print("✓ DELETE endpoint route defined")
        
        # Check for function definition
        assert 'async def delete_client_document(client_id: str, document_id: str)' in content
        print("✓ Endpoint function signature correct")
        
        # Check for docstring
        assert 'Delete a document completely' in content
        print("✓ Endpoint docstring present")
        
        # Check for key operations in the function
        assert 'supabase.table(\'documents\')' in content
        print("✓ Documents table query present")
        
        assert 'supabase.table(\'deadlines\')' in content
        print("✓ Deadlines table delete present")
        
        assert 'file_path.unlink()' in content or 'unlink()' in content
        print("✓ File deletion logic present")
        
        # Check for proper error handling
        assert 'HTTPException(status_code=404' in content
        print("✓ 404 error handling present")
        
        assert 'HTTPException(status_code=500' in content
        print("✓ 500 error handling present")
        
        return True
    except AssertionError as e:
        print(f"✗ Endpoint check failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Endpoint check error: {e}")
        return False

def test_endpoint_logic():
    """Test that the endpoint has proper deletion logic"""
    print("\nTesting endpoint deletion logic...")
    
    try:
        api_server_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'api_server.py')
        
        with open(api_server_path, 'r') as f:
            content = f.read()
        
        # Find the delete_client_document function
        func_start = content.find('async def delete_client_document')
        if func_start == -1:
            print("✗ Function not found")
            return False
        
        # Get function content (up to next function or end)
        next_func = content.find('\n@app.', func_start + 1)
        if next_func == -1:
            next_func = content.find('\ndef ', func_start + 1)
        if next_func == -1:
            next_func = len(content)
        
        func_content = content[func_start:next_func]
        
        # Check that deadlines table is mentioned
        assert "table('deadlines')" in func_content
        print("✓ Deadlines deletion included")
        
        # Check that documents table is mentioned
        assert "table('documents')" in func_content
        print("✓ Documents table query included")
        
        # Check for source_id pattern matching using document_id
        assert 'source_id' in func_content
        assert f'document:{{document_id}}' in func_content or 'document:{document_id}' in func_content
        print("✓ Source ID pattern matching uses document_id (not filename)")
        
        # Check for file deletion
        assert 'unlink()' in func_content
        print("✓ File deletion included")
        
        # Check for client verification
        assert 'client_manager.get_client' in func_content
        print("✓ Client verification included")
        
        # Check for document verification with both document_id and client_id
        assert '.eq(\'document_id\', document_id)' in func_content
        assert '.eq(\'client_id\', client_id)' in func_content
        print("✓ Client ownership verification included")
        
        # Check return value
        assert '"success": True' in func_content
        assert '"message"' in func_content
        assert '"document_id"' in func_content
        print("✓ Proper return value structure")
        
        # Check deletion happens in both deadlines and documents tables
        deadlines_delete = func_content.find("table('deadlines')")
        documents_delete_query = func_content.find("table('documents')", deadlines_delete + 1)
        assert deadlines_delete > 0
        assert documents_delete_query > deadlines_delete
        print("✓ Deadlines are queried/deleted before final document deletion")
        
        return True
    except AssertionError as e:
        print(f"✗ Logic check failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Logic check error: {e}")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("Testing Delete Document Endpoint")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Endpoint Exists", test_endpoint_exists()))
    results.append(("Endpoint Logic", test_endpoint_logic()))
    
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
