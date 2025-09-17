#!/usr/bin/env python3
"""
Comprehensive test script to validate all assertion fixes.
"""

import json
from app.testrunner.executor import TestExecutor
import httpx
from unittest.mock import Mock

def test_comprehensive_assertions():
    """Test all assertion types with the actual data structure."""
    
    # Mock response
    mock_response = Mock(spec=httpx.Response)
    
    # Response body from the failing test
    response_body = [
        {
            "lineage": "HL7",
            "admit_source": None,
            "batch_id": "1c07837f-3a07-4e9c-b501-47f604034679",
            "patient_class": "OUTPATIENT",
            "type": "A08",
            "datetime": "2024-12-03 17:50:50",
            "encounter_id": "84461ddb-b822-5946-bf23-ca0da343b1d3",
            "visit_number": "10800050497",
            "hospital_service": "Not assigned.",
            "patient_id": "6efad10a-c887-319c-81ca-c6cc0b38bcf2",
            "bundle_id": "280B4CA2_ADT",
            "facility": "6a2ef1fb-2dc4-5671-b881-6bffb5820258",
            "insurance": [{"insurance_company_id": "10001", "id_type": "BLUE CROSS PPO TRUST"}],
            "providers": [{"provider_type": "attender", "provider_id": "H24809"}]
        }
    ]
    
    # Set up mock response
    mock_response.json.return_value = response_body
    mock_response.status_code = 201
    mock_response.headers = {"content-type": "application/json; charset=utf-8"}
    
    # Create executor
    executor = TestExecutor(base_url="https://example.com")
    
    # Test comprehensive assertions covering all types
    test_assertions = [
        # Status code assertion
        {
            "type": "status_code",
            "expected": 201
        },
        # Header assertion  
        {
            "type": "header",
            "path": "content-type", 
            "expected": "application/json; charset=utf-8"
        },
        # Exists assertions
        {
            "type": "exists",
            "path": "[0]"
        },
        {
            "type": "exists",
            "path": "[0].lineage"
        },
        {
            "type": "exists",
            "path": "[0].admit_source"  # This exists but is null
        },
        # Equals assertions with "value" field
        {
            "type": "equals",
            "path": "[0].lineage",
            "value": "HL7"
        },
        {
            "type": "equals",
            "path": "[0].patient_class",
            "value": "OUTPATIENT"
        },
        {
            "type": "equals", 
            "path": "[0].type",
            "value": "A08"
        },
        # Nested path assertions
        {
            "type": "exists",
            "path": "[0].insurance[0]"
        },
        {
            "type": "equals",
            "path": "[0].insurance[0].insurance_company_id", 
            "value": "10001"
        },
        {
            "type": "equals",
            "path": "[0].providers[0].provider_type",
            "value": "attender"
        }
    ]
    
    print("Testing comprehensive assertions:")
    print("=" * 80)
    print(f"{'Status':<8} | {'Type':<12} | {'Path':<30} | {'Expected':<15} | {'Result'}")
    print("-" * 80)
    
    passed_count = 0
    total_count = len(test_assertions)
    
    for assertion in test_assertions:
        try:
            result = executor._run_single_assertion(assertion, mock_response)
            status = "✓ PASS" if result['passed'] else "✗ FAIL"
            if result['passed']:
                passed_count += 1
            
            assertion_type = result.get('type', 'unknown')
            path = result.get('path', '')[:30] if result.get('path') else ''
            expected = str(result.get('expected', ''))[:15] if result.get('expected') is not None else 'None'
            
            print(f"{status:<8} | {assertion_type:<12} | {path:<30} | {expected:<15} | {result['message'][:40]}...")
            
        except Exception as e:
            print(f"✗ ERROR  | {'error':<12} | {'':<30} | {'':<15} | {str(e)}")
    
    print("-" * 80)
    print(f"Final Results: {passed_count}/{total_count} assertions passed ({passed_count/total_count*100:.1f}%)")
    
    if passed_count == total_count:
        print("🎉 ALL ASSERTIONS WORKING PERFECTLY!")
        print("✓ Status code assertions")
        print("✓ Header assertions")
        print("✓ Exists assertions (including null fields)")
        print("✓ Equals assertions with 'value' field")
        print("✓ Nested JSON path assertions")
        print("✓ Array indexing in paths")
    else:
        print("⚠️  Some assertions still failing:")
        print(f"   {total_count - passed_count} out of {total_count} failed")
        return False
        
    return True

if __name__ == "__main__":
    success = test_comprehensive_assertions()
    if success:
        print("\n" + "="*50)
        print("🚀 READY TO TEST WITH REAL API CALLS!")
        print("   Your assertion fixes should now work correctly.")
        print("="*50)
    else:
        print("\n⚠️  Please check the failing assertions above.")
