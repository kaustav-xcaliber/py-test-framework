#!/usr/bin/env python3
"""
Test script to validate assertions using the actual test data structure.
"""

import json
from app.testrunner.executor import TestExecutor
import httpx
from unittest.mock import Mock

def test_actual_assertions():
    """Test assertions using the exact data structure from the failing test."""
    
    # Mock response with the actual failing test data
    mock_response = Mock(spec=httpx.Response)
    
    # Response body from the failing test
    response_body = [
        {
            "lineage": "HL7",
            "admit_source": None,
            "reason": None,
            "batch_id": "1c07837f-3a07-4e9c-b501-47f604034679",
            "patient_class": "OUTPATIENT",
            "recorded_datetime": None,
            "total_payments": None,
            "rating": None,
            "admission_type": None,
            "account_status": None,
            "discharge_disposition": None,
            "type": "A08",
            "xc_visit_id": "096076481",
            "total_charges": None,
            "ambulatory_status": None,
            "datetime": "2024-12-03 17:50:50",
            "patient_type": None,
            "preadmit_number": None,
            "preadmit_test_indicator": None,
            "alternate_visit_id": "096076481",
            "admit_datetime": "2024-12-03 17:50:46",
            "encounter_id": "84461ddb-b822-5946-bf23-ca0da343b1d3",
            "visit_indicator": None,
            "bed_status": None,
            "bedside_datetime": "2024-12-03 17:50:50",
            "discharge_datetime": None,
            "servicing_facility": "LKE",
            "diet_type": None,
            "message_type": "ADT",
            "discharged_to_location": None,
            "total_adjustments": None,
            "visit_number": "10800050497",
            "hospital_service": "Not assigned.",
            "financial_class": None,
            "readmission_indicator": None,
            "patient_id": "6efad10a-c887-319c-81ca-c6cc0b38bcf2",
            "bundle_id": "280B4CA2_ADT",
            "current_patient_balance": None,
            "facility": "6a2ef1fb-2dc4-5671-b881-6bffb5820258",
            "insurance": [
                {
                    "insurance_company_id": "10001",
                    "insurance_company_name": None,
                    "id_type": "BLUE CROSS PPO TRUST",
                    "id_type_code": "10001011"
                }
            ],
            "providers": [
                {
                    "provider_type": "attender",
                    "report_grouper_twelve": None,
                    "provider_id": "1093712093",
                    "prov_cred": None
                },
                {
                    "provider_type": "referrer",
                    "report_grouper_twelve": None,
                    "provider_id": "1093712093",
                    "prov_cred": None
                },
                {
                    "provider_type": "attender",
                    "report_grouper_twelve": None,
                    "provider_id": "H24809",
                    "prov_cred": None
                },
                {
                    "provider_type": "referrer",
                    "report_grouper_twelve": None,
                    "provider_id": "H24809",
                    "prov_cred": None
                }
            ],
            "facilities": [
                {
                    "bed": None,
                    "point_of_care": "1060170018:HFM:MOP LAB:PATHOLOGY",
                    "description": None,
                    "facility_type": "Assigned Patient Location",
                    "facility_code": "LKE",
                    "room": None
                }
            ]
        }
    ]
    
    # Set up mock response
    mock_response.json.return_value = response_body
    mock_response.status_code = 201
    
    # Create executor
    executor = TestExecutor(base_url="https://example.com")
    
    # Test the actual assertions from your JSON
    test_assertions = [
        {
            "type": "exists",
            "path": "[0]"
        },
        {
            "type": "exists",
            "path": "[0].lineage"
        },
        {
            "type": "equals",
            "path": "[0].lineage",
            "value": "HL7"
        },
        {
            "type": "exists",
            "path": "[0].admit_source"
        },
        {
            "type": "exists",
            "path": "[0].reason"
        },
        {
            "type": "exists",
            "path": "[0].batch_id"
        },
        {
            "type": "equals",
            "path": "[0].batch_id",
            "value": "1c07837f-3a07-4e9c-b501-47f604034679"
        },
        {
            "type": "exists",
            "path": "[0].patient_class"
        },
        {
            "type": "equals",
            "path": "[0].patient_class",
            "value": "OUTPATIENT"
        },
        {
            "type": "exists",
            "path": "[0].type"
        },
        {
            "type": "equals",
            "path": "[0].type",
            "value": "A08"
        }
    ]
    
    print("Testing actual assertions from your JSON:")
    print("=" * 60)
    
    passed_count = 0
    total_count = len(test_assertions)
    
    for i, assertion in enumerate(test_assertions):
        try:
            result = executor._run_single_assertion(assertion, mock_response)
            status = "✓ PASS" if result['passed'] else "✗ FAIL"
            if result['passed']:
                passed_count += 1
            
            # Format the output to be more readable
            assertion_type = result.get('type', 'unknown')
            path = result.get('path', 'N/A')
            expected = result.get('expected')
            actual = result.get('actual')
            
            # Truncate long actual values for display
            actual_str = str(actual)
            if len(actual_str) > 40:
                actual_str = actual_str[:40] + "..."
            
            print(f"{status} | {assertion_type:<8} | {path:<25} | Expected: {expected} | Actual: {actual_str}")
            
        except Exception as e:
            print(f"✗ ERROR | assertion {i} | Error: {str(e)}")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed_count}/{total_count} assertions passed")
    
    if passed_count == total_count:
        print("🎉 All assertions are now working correctly!")
    else:
        print("⚠️  Some assertions still need adjustment.")
        print(f"   {total_count - passed_count} assertions failed")

if __name__ == "__main__":
    test_actual_assertions()
