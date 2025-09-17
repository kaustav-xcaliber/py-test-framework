#!/usr/bin/env python3
"""
Test exists assertions with real test data.
"""

from app.testrunner.executor import TestExecutor
import httpx
from unittest.mock import Mock

def test_real_exists():
    """Test exists assertions with your actual test data."""
    
    # Mock response with actual test data
    mock_response = Mock(spec=httpx.Response)
    
    response_body = [
        {
            "lineage": "HL7",
            "admit_source": None,  # null but exists
            "reason": None,        # null but exists  
            "batch_id": "1c07837f-3a07-4e9c-b501-47f604034679",
            "patient_class": "OUTPATIENT",
            "type": "A08",
            "insurance": [{"insurance_company_id": "10001"}],
            "providers": [{"provider_type": "attender"}]
        }
    ]
    
    mock_response.json.return_value = response_body
    mock_response.status_code = 201
    
    executor = TestExecutor(base_url="https://example.com")
    
    # Test the exact assertions from your original test
    assertions = [
        {"type": "exists", "path": "[0]"},
        {"type": "exists", "path": "[0].lineage"},
        {"type": "exists", "path": "[0].admit_source"},  # null but should pass
        {"type": "exists", "path": "[0].reason"},        # null but should pass
        {"type": "exists", "path": "[0].batch_id"}, 
        {"type": "exists", "path": "[0].insurance"},
        {"type": "exists", "path": "[0].insurance[0]"},
        {"type": "exists", "path": "[0].providers"}
    ]
    
    print("Testing exists assertions with real data:")
    print("=" * 50)
    
    passed = 0
    for assertion in assertions:
        result = executor._assert_exists(assertion, mock_response)
        status = "✓" if result['passed'] else "✗"
        if result['passed']:
            passed += 1
        print(f"{status} {assertion['path']}: {result['message']}")
    
    print(f"\nResult: {passed}/{len(assertions)} passed")
    
    if passed == len(assertions):
        print("🎉 All exists assertions working correctly!")
    else:
        print("⚠️ Some assertions failed")

if __name__ == "__main__":
    test_real_exists()
