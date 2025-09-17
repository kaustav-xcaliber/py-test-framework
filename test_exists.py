#!/usr/bin/env python3
"""
Test the new exists assertion logic.
"""

import json
from app.testrunner.executor import TestExecutor
import httpx
from unittest.mock import Mock

def test_exists_assertions():
    """Test that exists assertions only check field presence."""
    
    # Mock response
    mock_response = Mock(spec=httpx.Response)
    
    # Response body with mixed data types and null values
    response_body = [
        {
            "lineage": "HL7",
            "admit_source": None,  # Exists but null
            "patient_class": "OUTPATIENT",
            "insurance": [{"id": "10001"}],
            # Note: "nonexistent_field" is NOT in the response
        }
    ]
    
    # Set up mock response
    mock_response.json.return_value = response_body
    mock_response.status_code = 201
    
    # Create executor
    executor = TestExecutor(base_url="https://example.com")
    
    # Test exists assertions using the correct method
    test_assertions = [
        {
            "type": "exists",
            "path": "[0].lineage"  # Exists with value "HL7"
        },
        {
            "type": "exists", 
            "path": "[0].admit_source"  # Exists but is null
        },
        {
            "type": "exists",
            "path": "[0].patient_class"  # Exists with value "OUTPATIENT"
        },
        {
            "type": "exists",
            "path": "[0].insurance"  # Exists as array
        },
        {
            "type": "exists",
            "path": "[0].insurance[0]"  # Nested exists
        },
        {
            "type": "exists",
            "path": "[0].nonexistent_field"  # Does NOT exist
        }
    ]
    
    print("Testing 'exists' assertions (field presence only):")
    print("=" * 70)
    print(f"{'Status':<8} | {'Path':<30} | {'Result'}")
    print("-" * 70)
    
    passed_count = 0
    total_count = len(test_assertions)
    
    for assertion in test_assertions:
        try:
            # Use the correct exists assertion method
            result = executor._assert_exists(assertion, mock_response)
            status = "✓ PASS" if result['passed'] else "✗ FAIL"
            if result['passed']:
                passed_count += 1
            
            path = assertion.get('path', '')[:30]
            message = result['message']
            
            print(f"{status:<8} | {path:<30} | {message}")
            
        except Exception as e:
            print(f"✗ ERROR  | {assertion.get('path', ''):<30} | {str(e)}")
    
    print("-" * 70)
    print(f"Results: {passed_count}/{total_count} assertions passed ({passed_count/total_count*100:.1f}%)")
    
    expected_results = [
        ("lineage", True, "exists with value"),
        ("admit_source", True, "exists but null"), 
        ("patient_class", True, "exists with value"),
        ("insurance", True, "exists as array"),
        ("insurance[0]", True, "nested exists"),
        ("nonexistent_field", False, "doesn't exist")
    ]
    
    print("\nExpected vs Actual:")
    for i, (field, should_pass, description) in enumerate(expected_results):
        if i < len(test_assertions):
            assertion = test_assertions[i]
            result = executor._assert_exists(assertion, mock_response)
            actual_pass = result['passed']
            status = "✓" if actual_pass == should_pass else "✗"
            print(f"{status} {field}: {description} - {'PASS' if actual_pass else 'FAIL'}")
    
    if passed_count == 5:  # Should be 5 passes (all except nonexistent_field)
        print("\n🎉 EXISTS ASSERTIONS WORKING CORRECTLY!")
        print("✓ Fields with values pass")
        print("✓ Fields with null values pass") 
        print("✓ Non-existent fields fail")
        print("✓ Nested paths work correctly")
    else:
        print(f"\n⚠️  Expected 5 passes, got {passed_count}")

if __name__ == "__main__":
    test_exists_assertions()
