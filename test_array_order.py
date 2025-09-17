#!/usr/bin/env python3
"""
Test script to validate array order mismatch handling in assertions.
"""

import httpx
from app.testrunner.executor import TestExecutor

def test_array_order_handling():
    """Test array order mismatch scenarios."""
    print("Testing array order mismatch handling...")
    
    # Create a test executor
    executor = TestExecutor(base_url="http://test.com")
    
    # Mock response with providers array (simulating your actual API response)
    mock_response_data = {
        "providers": [
            {"provider_id": "PROVIDER_B", "name": "Second Provider", "status": "active"},
            {"provider_id": "PROVIDER_A", "name": "First Provider", "status": "active"},
            {"provider_id": "PROVIDER_C", "name": "Third Provider", "status": "inactive"}
        ],
        "items": ["item2", "item1", "item3", "item4"],
        "metadata": {
            "nested_array": [
                {"id": 100, "type": "secondary"},
                {"id": 50, "type": "primary"},
                {"id": 200, "type": "tertiary"}
            ]
        }
    }
    
    # Create a mock response
    class MockResponse:
        def __init__(self, data):
            self._json = data
            
        def json(self):
            return self._json
    
    mock_response = MockResponse(mock_response_data)
    
    # Test cases
    test_cases = [
        {
            "name": "Provider ID at wrong index (should pass with warning)",
            "assertion": {
                "type": "equals",
                "path": "providers[0].provider_id",
                "expected": "PROVIDER_A"  # Actually at index 1
            },
            "should_pass": True,
            "should_warn": True
        },
        {
            "name": "Provider ID at correct index (should pass normally)",
            "assertion": {
                "type": "equals", 
                "path": "providers[1].provider_id",
                "expected": "PROVIDER_A"
            },
            "should_pass": True,
            "should_warn": False
        },
        {
            "name": "Non-existent provider ID (should fail)",
            "assertion": {
                "type": "equals",
                "path": "providers[0].provider_id", 
                "expected": "PROVIDER_X"
            },
            "should_pass": False,
            "should_warn": False
        },
        {
            "name": "Simple array item order mismatch (should pass with warning)",
            "assertion": {
                "type": "equals",
                "path": "items[0]",
                "expected": "item1"  # Actually at index 1
            },
            "should_pass": True,
            "should_warn": True
        },
        {
            "name": "Nested array order mismatch (should pass with warning)", 
            "assertion": {
                "type": "equals",
                "path": "metadata.nested_array[0].id",
                "expected": 50  # Actually at index 1
            },
            "should_pass": True,
            "should_warn": True
        }
    ]
    
    print(f"\nRunning {len(test_cases)} test cases...\n")
    
    passed = 0
    total = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        
        # Run the assertion
        result = executor._assert_equals(test_case["assertion"], mock_response)
        
        # Check results
        test_passed = result["passed"]
        has_warning = "WARNING" in result.get("message", "")
        
        print(f"  Expected to pass: {test_case['should_pass']}")
        print(f"  Actually passed: {test_passed}")
        print(f"  Expected warning: {test_case['should_warn']}")
        print(f"  Has warning: {has_warning}")
        print(f"  Message: {result['message']}")
        
        # Validate expectations
        if (test_passed == test_case["should_pass"] and 
            has_warning == test_case["should_warn"]):
            print("  ✅ Test case PASSED")
            passed += 1
        else:
            print("  ❌ Test case FAILED")
        
        print()
    
    print(f"Results: {passed}/{total} test cases passed")
    
    if passed == total:
        print("🎉 All array order handling tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False

if __name__ == "__main__":
    test_array_order_handling()
