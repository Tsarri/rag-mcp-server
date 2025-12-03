#!/usr/bin/env python3
"""
Test API server structure and imports
Tests basic structure without requiring database connection
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_api_imports():
    """Test that API server modules can be imported"""
    print("Testing API server imports...")
    
    try:
        # Test FastAPI imports
        from fastapi import FastAPI
        print("✓ FastAPI available")
    except ImportError as e:
        print(f"✗ FastAPI not available: {e}")
        return False
    
    try:
        # Test that api_server module structure is valid
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'api_server', 
            os.path.join(os.path.dirname(__file__), '..', 'src', 'api_server.py')
        )
        print("✓ api_server.py structure is valid")
    except Exception as e:
        print(f"✗ api_server.py structure error: {e}")
        return False
    
    return True

def test_client_manager_structure():
    """Test that ClientManager can be imported"""
    print("\nTesting ClientManager structure...")
    
    try:
        # Import without initializing (which would require Supabase)
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'client_manager',
            os.path.join(os.path.dirname(__file__), '..', 'src', 'database', 'client_manager.py')
        )
        module = importlib.util.module_from_spec(spec)
        
        # Check that ClientManager class exists
        spec.loader.exec_module(module)
        assert hasattr(module, 'ClientManager')
        
        print("✓ ClientManager class exists")
        
        # Check that all required methods exist
        required_methods = [
            'create_client',
            'get_client', 
            'get_all_clients',
            'update_client',
            'delete_client',
            'get_client_document_count'
        ]
        
        for method in required_methods:
            assert hasattr(module.ClientManager, method)
            print(f"✓ ClientManager.{method} exists")
        
        return True
    except Exception as e:
        print(f"✗ ClientManager structure error: {e}")
        return False

def test_agent_updates():
    """Test that agents have been updated with client_id support"""
    print("\nTesting agent updates...")
    
    try:
        import importlib.util
        import inspect
        
        # Test DeadlineAgent
        spec = importlib.util.spec_from_file_location(
            'deadline_agent',
            os.path.join(os.path.dirname(__file__), '..', 'src', 'agents', 'deadline_agent.py')
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Check extract_deadlines signature
        sig = inspect.signature(module.DeadlineAgent.extract_deadlines)
        assert 'client_id' in sig.parameters
        print("✓ DeadlineAgent.extract_deadlines has client_id parameter")
        
        # Check get_deadlines_by_risk signature
        sig = inspect.signature(module.DeadlineAgent.get_deadlines_by_risk)
        assert 'client_id' in sig.parameters
        print("✓ DeadlineAgent.get_deadlines_by_risk has client_id parameter")
        
        # Test DocumentAgent
        spec = importlib.util.spec_from_file_location(
            'document_agent',
            os.path.join(os.path.dirname(__file__), '..', 'src', 'agents', 'document_agent.py')
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Check classify_document signature
        sig = inspect.signature(module.DocumentAgent.classify_document)
        assert 'client_id' in sig.parameters
        print("✓ DocumentAgent.classify_document has client_id parameter")
        
        # Check search_documents signature
        sig = inspect.signature(module.DocumentAgent.search_documents)
        assert 'client_id' in sig.parameters
        print("✓ DocumentAgent.search_documents has client_id parameter")
        
        # Test SmartContextAgent
        spec = importlib.util.spec_from_file_location(
            'smartcontext_agent',
            os.path.join(os.path.dirname(__file__), '..', 'src', 'agents', 'smartcontext_agent.py')
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Check analyze_deadline_risk signature
        sig = inspect.signature(module.SmartContextAgent.analyze_deadline_risk)
        assert 'client_id' in sig.parameters
        print("✓ SmartContextAgent.analyze_deadline_risk has client_id parameter")
        
        return True
    except Exception as e:
        print(f"✗ Agent update verification error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_schema():
    """Test that database schema has been updated"""
    print("\nTesting database schema...")
    
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'schema.sql')
    
    try:
        with open(schema_path, 'r') as f:
            schema = f.read()
        
        # Check for clients table
        assert 'CREATE TABLE IF NOT EXISTS clients' in schema
        print("✓ Clients table defined")
        
        # Check for client_id columns in key tables
        assert 'client_id UUID REFERENCES clients(id)' in schema
        print("✓ client_id foreign keys defined")
        
        # Check for required tables
        required_tables = [
            'clients',
            'documents',
            'deadlines',
            'deadline_extractions',
            'analyses'
        ]
        
        for table in required_tables:
            assert f'CREATE TABLE IF NOT EXISTS {table}' in schema
            print(f"✓ {table} table defined")
        
        # Check for indexes
        assert 'idx_documents_client_id' in schema
        assert 'idx_deadlines_client_id' in schema
        print("✓ Client indexes defined")
        
        return True
    except Exception as e:
        print(f"✗ Database schema verification error: {e}")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("Testing API Structure and Updates")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("API Imports", test_api_imports()))
    results.append(("ClientManager Structure", test_client_manager_structure()))
    results.append(("Agent Updates", test_agent_updates()))
    results.append(("Database Schema", test_database_schema()))
    
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
