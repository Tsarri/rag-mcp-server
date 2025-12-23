#!/usr/bin/env python3
"""
Test validation status values to ensure they match frontend expectations.

This test verifies that:
- Gemini validator prompts request 'validated' and 'warning' status values
- Server.py uses 'validated' and 'warning' in emoji mappings
- Old values 'verified' and 'discrepancy' are not present
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_gemini_validator_classification_prompt():
    """Test that classification validation uses correct status values"""
    print("Testing gemini_validator.py classification validation prompt...")
    
    validator_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'agents', 'gemini_validator.py')
    
    with open(validator_path, 'r') as f:
        content = f.read()
    
    # Check that the new status values are present in the prompt
    if '"validation_status": "validated|warning|error"' in content:
        print("✓ Classification prompt uses 'validated|warning|error'")
    else:
        print("✗ Classification prompt does not use correct status values")
        return False
    
    # Check that instructions use 'validated'
    if "Use 'validated' status when classification is accurate" in content:
        print("✓ Classification instructions use 'validated'")
    else:
        print("✗ Classification instructions do not use 'validated'")
        return False
    
    # Check that instructions use 'warning'
    if "Use 'warning' status when there are issues" in content:
        print("✓ Classification instructions use 'warning'")
    else:
        print("✗ Classification instructions do not use 'warning'")
        return False
    
    # Check that old values are NOT present in classification prompt area
    # We need to be careful here - just check that the old pattern isn't in the prompts
    classification_section = content[content.find('async def validate_classification'):content.find('async def validate_deadlines')]
    
    if '"validation_status": "verified|discrepancy|error"' in classification_section:
        print("✗ Classification prompt still uses old 'verified|discrepancy|error' values")
        return False
    
    if "Use 'verified' status when classification is accurate" in classification_section:
        print("✗ Classification instructions still use 'verified'")
        return False
    
    if "Use 'discrepancy' status when there are issues" in classification_section:
        print("✗ Classification instructions still use 'discrepancy'")
        return False
    
    print("✓ Classification prompt does not use old status values")
    
    return True

def test_gemini_validator_deadlines_prompt():
    """Test that deadline validation uses correct status values"""
    print("\nTesting gemini_validator.py deadline validation prompt...")
    
    validator_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'agents', 'gemini_validator.py')
    
    with open(validator_path, 'r') as f:
        content = f.read()
    
    # Get the deadline validation section
    deadline_section = content[content.find('async def validate_deadlines'):]
    
    # Check that the new status values are present in the deadline prompt
    if '"validation_status": "validated|warning|error"' in deadline_section:
        print("✓ Deadline prompt uses 'validated|warning|error'")
    else:
        print("✗ Deadline prompt does not use correct status values")
        return False
    
    # Check that instructions use 'validated'
    if "Use 'validated' status when deadlines are accurate" in deadline_section:
        print("✓ Deadline instructions use 'validated'")
    else:
        print("✗ Deadline instructions do not use 'validated'")
        return False
    
    # Check that instructions use 'warning'
    if "Use 'warning' status when there are issues" in deadline_section:
        print("✓ Deadline instructions use 'warning'")
    else:
        print("✗ Deadline instructions do not use 'warning'")
        return False
    
    # Check that old values are NOT present
    if '"validation_status": "verified|discrepancy|error"' in deadline_section:
        print("✗ Deadline prompt still uses old 'verified|discrepancy|error' values")
        return False
    
    if "Use 'verified' status when deadlines are accurate" in deadline_section:
        print("✗ Deadline instructions still use 'verified'")
        return False
    
    if "Use 'discrepancy' status when there are issues" in deadline_section:
        print("✗ Deadline instructions still use 'discrepancy'")
        return False
    
    print("✓ Deadline prompt does not use old status values")
    
    return True

def test_gemini_validator_docstrings():
    """Test that docstrings are updated with correct status values"""
    print("\nTesting gemini_validator.py docstrings...")
    
    validator_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'agents', 'gemini_validator.py')
    
    with open(validator_path, 'r') as f:
        content = f.read()
    
    # Check validate_classification docstring
    classification_section = content[content.find('async def validate_classification'):content.find('async def validate_deadlines')]
    
    if "validation_status: 'validated', 'warning', or 'error'" in classification_section:
        print("✓ Classification docstring uses correct status values")
    else:
        print("✗ Classification docstring does not use correct status values")
        return False
    
    # Check validate_deadlines docstring
    deadline_section = content[content.find('async def validate_deadlines'):]
    
    if "validation_status: 'validated', 'warning', or 'error'" in deadline_section:
        print("✓ Deadline docstring uses correct status values")
    else:
        print("✗ Deadline docstring does not use correct status values")
        return False
    
    return True

def test_server_classification_emoji_mapping():
    """Test that server.py classification validation uses correct emoji mapping"""
    print("\nTesting server.py classification validation emoji mapping...")
    
    server_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'server.py')
    
    with open(server_path, 'r') as f:
        content = f.read()
    
    # Find the classification validation section
    # Look for the area around "Add validation results" and "classification_validation"
    classification_section_start = content.find("# Add validation results")
    classification_section_end = content.find("except Exception as e:", classification_section_start)
    classification_section = content[classification_section_start:classification_section_end]
    
    # Check for new emoji mappings
    if "'validated': '✅'" in classification_section:
        print("✓ Classification uses 'validated' emoji mapping")
    else:
        print("✗ Classification does not use 'validated' emoji mapping")
        return False
    
    if "'warning': '⚠️'" in classification_section:
        print("✓ Classification uses 'warning' emoji mapping")
    else:
        print("✗ Classification does not use 'warning' emoji mapping")
        return False
    
    # Check that old mappings are NOT present
    if "'verified': '✅'" in classification_section:
        print("✗ Classification still uses old 'verified' emoji mapping")
        return False
    
    if "'discrepancy': '⚠️'" in classification_section:
        print("✗ Classification still uses old 'discrepancy' emoji mapping")
        return False
    
    print("✓ Classification does not use old emoji mappings")
    
    return True

def test_server_deadline_emoji_mapping():
    """Test that server.py deadline validation uses correct emoji mapping"""
    print("\nTesting server.py deadline validation emoji mapping...")
    
    server_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'server.py')
    
    with open(server_path, 'r') as f:
        content = f.read()
    
    # Find the deadline validation section
    # Look for "Add deadline validation results"
    deadline_section_start = content.find("# Add deadline validation results")
    deadline_section_end = content.find("else:", deadline_section_start)
    deadline_section = content[deadline_section_start:deadline_section_end]
    
    # Check for new emoji mappings
    if "'validated': '✅'" in deadline_section:
        print("✓ Deadline uses 'validated' emoji mapping")
    else:
        print("✗ Deadline does not use 'validated' emoji mapping")
        return False
    
    if "'warning': '⚠️'" in deadline_section:
        print("✓ Deadline uses 'warning' emoji mapping")
    else:
        print("✗ Deadline does not use 'warning' emoji mapping")
        return False
    
    # Check that old mappings are NOT present
    if "'verified': '✅'" in deadline_section:
        print("✗ Deadline still uses old 'verified' emoji mapping")
        return False
    
    if "'discrepancy': '⚠️'" in deadline_section:
        print("✗ Deadline still uses old 'discrepancy' emoji mapping")
        return False
    
    print("✓ Deadline does not use old emoji mappings")
    
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("VALIDATION STATUS VALUES FIX TESTS")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(('Gemini Validator Classification Prompt', test_gemini_validator_classification_prompt()))
    results.append(('Gemini Validator Deadlines Prompt', test_gemini_validator_deadlines_prompt()))
    results.append(('Gemini Validator Docstrings', test_gemini_validator_docstrings()))
    results.append(('Server Classification Emoji Mapping', test_server_classification_emoji_mapping()))
    results.append(('Server Deadline Emoji Mapping', test_server_deadline_emoji_mapping()))
    
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
