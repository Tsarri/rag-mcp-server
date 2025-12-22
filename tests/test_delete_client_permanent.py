#!/usr/bin/env python3
"""
Test permanent delete client endpoint
Tests the structure without requiring database connection
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_endpoint_exists():
    """Test that the permanent delete client endpoint exists in api_server.py"""
    print("Testing permanent delete client endpoint existence...")
    
    try:
        api_server_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'api_server.py')
        
        with open(api_server_path, 'r') as f:
            content = f.read()
        
        # Check for endpoint definition
        assert '@app.delete("/api/clients/{client_id}/permanent")' in content
        print("✓ DELETE permanent endpoint route defined")
        
        # Check for function definition
        assert 'async def delete_client_permanent(client_id: str)' in content
        print("✓ Endpoint function signature correct")
        
        # Check for docstring with key operations
        assert 'Permanently delete a client and ALL associated data' in content
        print("✓ Endpoint docstring present")
        
        # Check for client verification
        assert 'client_manager.get_client(client_id)' in content
        print("✓ Client verification present")
        
        # Check for 404 error on client not found
        assert 'HTTPException(status_code=404, detail="Client not found")' in content
        print("✓ 404 error handling for missing client")
        
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
        
        # Find the delete_client_permanent function
        func_start = content.find('async def delete_client_permanent')
        if func_start == -1:
            print("✗ Function not found")
            return False
        
        # Get function content (up to next function or end)
        next_func = content.find('\n@app.', func_start + 1)
        if next_func == -1:
            next_func = content.find('\ndef ', func_start + 1)
        if next_func == -1:
            next_func = content.find('\n# Document Upload Endpoint', func_start + 1)
        if next_func == -1:
            next_func = len(content)
        
        func_content = content[func_start:next_func]
        
        # Check for deletion summary tracking
        assert 'deletion_summary' in func_content
        assert '"documents_deleted"' in func_content
        assert '"deadlines_deleted"' in func_content
        assert '"validations_deleted"' in func_content
        assert '"extractions_deleted"' in func_content
        assert '"files_deleted"' in func_content
        print("✓ Deletion summary tracking included")
        
        # Check for documents table query
        assert "table('documents')" in func_content
        assert ".select('document_id')" in func_content
        assert ".eq('client_id', client_id)" in func_content
        print("✓ Documents table query included")
        
        # Check for deadlines table query
        assert "table('deadlines')" in func_content
        assert ".select('id')" in func_content
        print("✓ Deadlines table query included")
        
        # Check for validations deletion (both deadline and classification)
        assert "table('validations')" in func_content
        assert "'deadline'" in func_content or '"deadline"' in func_content
        assert "'classification'" in func_content or '"classification"' in func_content
        assert ".eq('validation_type'" in func_content
        assert ".eq('entity_id'" in func_content
        print("✓ Validations deletion for both deadline and classification")
        
        # Check for gemini_extractions deletion
        assert "table('gemini_extractions')" in func_content
        print("✓ Gemini extractions deletion included")
        
        # Check for documents deletion from database
        documents_delete = func_content.find("table('documents')")
        documents_delete_second = func_content.find("table('documents')", documents_delete + 1)
        assert documents_delete_second > 0
        print("✓ Documents deletion from database included")
        
        # Check for local file deletion
        assert 'get_client_document_dir(client_id)' in func_content
        assert 'shutil.rmtree' in func_content
        print("✓ Local file and directory deletion included")
        
        # Check for client record deletion
        assert "table('clients')" in func_content
        assert ".delete()" in func_content
        print("✓ Client record deletion included")
        
        # Check for proper error handling
        assert 'HTTPException' in func_content
        assert 'status_code=404' in func_content
        assert 'status_code=500' in func_content
        print("✓ Proper error handling present")
        
        # Check return structure
        assert '"success": True' in func_content
        assert '"message"' in func_content
        assert '"client_id"' in func_content
        assert '"deletion_summary"' in func_content
        print("✓ Proper return value structure")
        
        # Check logging
        assert 'logger.info' in func_content
        assert 'logger.warning' in func_content or 'logger.error' in func_content
        print("✓ Comprehensive logging included")
        
        return True
    except AssertionError as e:
        print(f"✗ Logic check failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Logic check error: {e}")
        return False

def test_soft_delete_unchanged():
    """Test that the soft delete endpoint remains unchanged"""
    print("\nTesting soft delete endpoint remains unchanged...")
    
    try:
        api_server_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'api_server.py')
        
        with open(api_server_path, 'r') as f:
            content = f.read()
        
        # Check for soft delete endpoint
        assert '@app.delete("/api/clients/{client_id}", response_model=ClientResponse)' in content
        print("✓ Soft delete endpoint still exists")
        
        # Check for function definition
        assert 'async def delete_client(client_id: str):' in content
        print("✓ Soft delete function signature unchanged")
        
        # Find the soft delete function
        func_start = content.find('async def delete_client(client_id: str):')
        if func_start == -1:
            print("✗ Soft delete function not found")
            return False
        
        # Get function content (up to the permanent delete function)
        next_func = content.find('async def delete_client_permanent', func_start + 1)
        if next_func == -1:
            next_func = len(content)
        
        func_content = content[func_start:next_func]
        
        # Check it's still calling client_manager.delete_client
        assert 'client_manager.delete_client(client_id)' in func_content
        print("✓ Soft delete still uses client_manager.delete_client")
        
        # Make sure it's not doing hard deletion
        assert 'shutil.rmtree' not in func_content
        assert 'deletion_summary' not in func_content
        print("✓ Soft delete does not perform hard deletion")
        
        return True
    except AssertionError as e:
        print(f"✗ Soft delete check failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Soft delete check error: {e}")
        return False

def test_cascade_order():
    """Test that deletions happen in the correct order"""
    print("\nTesting cascade deletion order...")
    
    try:
        api_server_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'api_server.py')
        
        with open(api_server_path, 'r') as f:
            content = f.read()
        
        # Find the delete_client_permanent function
        func_start = content.find('async def delete_client_permanent')
        if func_start == -1:
            print("✗ Function not found")
            return False
        
        # Get function content
        next_func = content.find('\n# Document Upload Endpoint', func_start + 1)
        if next_func == -1:
            next_func = len(content)
        
        func_content = content[func_start:next_func]
        
        # Get positions of key operations
        documents_query_pos = func_content.find("# 1. Get all documents")
        deadlines_query_pos = func_content.find("# 2. Get all deadlines")
        validations_deadline_pos = func_content.find("# 3. Delete all validations for deadlines")
        validations_classification_pos = func_content.find("# 4. Delete all validations for document classifications")
        gemini_delete_pos = func_content.find("# 5. Delete all gemini extractions")
        deadlines_delete_pos = func_content.find("# 6. Delete all deadlines")
        documents_delete_pos = func_content.find("# 7. Delete all documents from database")
        files_delete_pos = func_content.find("# 8. Delete all local files")
        client_delete_pos = func_content.find("# 9. Delete client record")
        
        # Verify order
        assert documents_query_pos > 0
        assert deadlines_query_pos > documents_query_pos
        assert validations_deadline_pos > deadlines_query_pos
        assert validations_classification_pos > validations_deadline_pos
        assert gemini_delete_pos > validations_classification_pos
        assert deadlines_delete_pos > gemini_delete_pos
        assert documents_delete_pos > deadlines_delete_pos
        assert files_delete_pos > documents_delete_pos
        assert client_delete_pos > files_delete_pos
        print("✓ Cascade deletion order is correct")
        
        # Verify client is deleted last
        client_table_delete = func_content.find("table('clients')")
        assert client_table_delete > documents_delete_pos
        assert client_table_delete > deadlines_delete_pos
        print("✓ Client record is deleted last")
        
        return True
    except AssertionError as e:
        print(f"✗ Cascade order check failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Cascade order check error: {e}")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("Testing Permanent Delete Client Endpoint")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Endpoint Exists", test_endpoint_exists()))
    results.append(("Endpoint Logic", test_endpoint_logic()))
    results.append(("Soft Delete Unchanged", test_soft_delete_unchanged()))
    results.append(("Cascade Order", test_cascade_order()))
    
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
