#!/usr/bin/env python3
"""
Test code structure without requiring dependencies
Validates files exist and contain expected code patterns
"""

import sys
import os
import re

def test_file_exists(filepath, description):
    """Test that a file exists"""
    if os.path.exists(filepath):
        print(f"✓ {description} exists")
        return True
    else:
        print(f"✗ {description} not found")
        return False

def test_pattern_in_file(filepath, pattern, description):
    """Test that a pattern exists in a file"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            if re.search(pattern, content, re.MULTILINE):
                print(f"✓ {description}")
                return True
            else:
                print(f"✗ {description} - pattern not found")
                return False
    except Exception as e:
        print(f"✗ {description} - error: {e}")
        return False

def main():
    """Run all structural tests"""
    print("="*60)
    print("Testing Code Structure")
    print("="*60)
    
    results = []
    base_path = os.path.join(os.path.dirname(__file__), '..')
    
    # Test 1: Core files exist
    print("\n--- Testing File Existence ---")
    results.append(test_file_exists(
        os.path.join(base_path, 'src', 'api_server.py'),
        "API Server"
    ))
    results.append(test_file_exists(
        os.path.join(base_path, 'src', 'database', 'client_manager.py'),
        "Client Manager"
    ))
    results.append(test_file_exists(
        os.path.join(base_path, 'database', 'schema.sql'),
        "Database Schema"
    ))
    results.append(test_file_exists(
        os.path.join(base_path, 'data', 'documents', 'README.md'),
        "Documents Directory"
    ))
    
    # Test 2: Database schema has required tables
    print("\n--- Testing Database Schema ---")
    schema_path = os.path.join(base_path, 'database', 'schema.sql')
    results.append(test_pattern_in_file(
        schema_path,
        r'CREATE TABLE IF NOT EXISTS clients',
        "Clients table exists"
    ))
    results.append(test_pattern_in_file(
        schema_path,
        r'client_id UUID REFERENCES clients',
        "Client foreign keys exist"
    ))
    results.append(test_pattern_in_file(
        schema_path,
        r'CREATE TABLE IF NOT EXISTS deadline_extractions',
        "Deadline extractions table exists"
    ))
    results.append(test_pattern_in_file(
        schema_path,
        r'CREATE TABLE IF NOT EXISTS analyses',
        "Analyses table exists"
    ))
    results.append(test_pattern_in_file(
        schema_path,
        r'idx_documents_client_id',
        "Document client index exists"
    ))
    results.append(test_pattern_in_file(
        schema_path,
        r'idx_deadlines_client_id',
        "Deadline client index exists"
    ))
    
    # Test 3: Client Manager has required methods
    print("\n--- Testing Client Manager ---")
    client_mgr_path = os.path.join(base_path, 'src', 'database', 'client_manager.py')
    results.append(test_pattern_in_file(
        client_mgr_path,
        r'async def create_client',
        "create_client method exists"
    ))
    results.append(test_pattern_in_file(
        client_mgr_path,
        r'async def get_client',
        "get_client method exists"
    ))
    results.append(test_pattern_in_file(
        client_mgr_path,
        r'async def get_all_clients',
        "get_all_clients method exists"
    ))
    results.append(test_pattern_in_file(
        client_mgr_path,
        r'async def update_client',
        "update_client method exists"
    ))
    results.append(test_pattern_in_file(
        client_mgr_path,
        r'async def delete_client',
        "delete_client method exists"
    ))
    results.append(test_pattern_in_file(
        client_mgr_path,
        r'async def get_client_document_count',
        "get_client_document_count method exists"
    ))
    
    # Test 4: API Server has required endpoints
    print("\n--- Testing API Server Endpoints ---")
    api_path = os.path.join(base_path, 'src', 'api_server.py')
    results.append(test_pattern_in_file(
        api_path,
        r'@app\.post\("/api/clients"',
        "POST /api/clients endpoint"
    ))
    results.append(test_pattern_in_file(
        api_path,
        r'@app\.get\("/api/clients"',
        "GET /api/clients endpoint"
    ))
    results.append(test_pattern_in_file(
        api_path,
        r'@app\.get\("/api/clients/\{client_id\}"',
        "GET /api/clients/{client_id} endpoint"
    ))
    results.append(test_pattern_in_file(
        api_path,
        r'@app\.put\("/api/clients/\{client_id\}"',
        "PUT /api/clients/{client_id} endpoint"
    ))
    results.append(test_pattern_in_file(
        api_path,
        r'@app\.delete\("/api/clients/\{client_id\}"',
        "DELETE /api/clients/{client_id} endpoint"
    ))
    results.append(test_pattern_in_file(
        api_path,
        r'@app\.post\("/api/clients/\{client_id\}/documents"',
        "POST /api/clients/{client_id}/documents endpoint"
    ))
    results.append(test_pattern_in_file(
        api_path,
        r'@app\.get\("/api/clients/\{client_id\}/deadlines"',
        "GET /api/clients/{client_id}/deadlines endpoint"
    ))
    results.append(test_pattern_in_file(
        api_path,
        r'@app\.get\("/api/clients/\{client_id\}/documents/stats"',
        "GET /api/clients/{client_id}/documents/stats endpoint"
    ))
    results.append(test_pattern_in_file(
        api_path,
        r'allow_origins=\["http://localhost:8080"\]',
        "CORS configured for frontend"
    ))
    
    # Test 5: Agents updated with client_id
    print("\n--- Testing Agent Updates ---")
    deadline_path = os.path.join(base_path, 'src', 'agents', 'deadline_agent.py')
    results.append(test_pattern_in_file(
        deadline_path,
        r'async def extract_deadlines\(self, text: str, source_id: str = None, client_id: str = None\)',
        "DeadlineAgent.extract_deadlines has client_id parameter"
    ))
    results.append(test_pattern_in_file(
        deadline_path,
        r'async def get_deadlines_by_risk\(self, risk_level: str = None, client_id: str = None\)',
        "DeadlineAgent.get_deadlines_by_risk has client_id parameter"
    ))
    results.append(test_pattern_in_file(
        deadline_path,
        r'"client_id": client_id',
        "DeadlineAgent stores client_id in database"
    ))
    
    document_path = os.path.join(base_path, 'src', 'agents', 'document_agent.py')
    results.append(test_pattern_in_file(
        document_path,
        r'client_id: str = None',
        "DocumentAgent.classify_document has client_id parameter"
    ))
    results.append(test_pattern_in_file(
        document_path,
        r'async def search_documents\([^)]*client_id: str = None',
        "DocumentAgent.search_documents has client_id parameter"
    ))
    
    smartcontext_path = os.path.join(base_path, 'src', 'agents', 'smartcontext_agent.py')
    results.append(test_pattern_in_file(
        smartcontext_path,
        r'async def analyze_deadline_risk\([^)]*client_id: str = None',
        "SmartContextAgent.analyze_deadline_risk has client_id parameter"
    ))
    
    # Test 6: Requirements updated
    print("\n--- Testing Requirements ---")
    req_path = os.path.join(base_path, 'requirements.txt')
    results.append(test_pattern_in_file(
        req_path,
        r'fastapi>=',
        "FastAPI in requirements"
    ))
    results.append(test_pattern_in_file(
        req_path,
        r'uvicorn',
        "Uvicorn in requirements"
    ))
    results.append(test_pattern_in_file(
        req_path,
        r'python-multipart',
        "python-multipart in requirements"
    ))
    
    # Test 7: README updated
    print("\n--- Testing Documentation ---")
    readme_path = os.path.join(base_path, 'README.md')
    results.append(test_pattern_in_file(
        readme_path,
        r'python src/api_server\.py',
        "API server run instructions in README"
    ))
    results.append(test_pattern_in_file(
        readme_path,
        r'http://localhost:8000',
        "API server URL in README"
    ))
    results.append(test_pattern_in_file(
        readme_path,
        r'POST /api/clients',
        "API endpoints documented"
    ))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results if result)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All structure tests passed!")
        print("The implementation is complete and ready for testing with dependencies installed.")
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        print("Some expected code patterns or files are missing.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
