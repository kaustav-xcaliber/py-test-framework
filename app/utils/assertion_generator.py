"""Assertion generator utility for creating smart test assertions based on response analysis."""

import json
import re
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AssertionConfig:
    """Configuration options for assertion generation."""
    max_depth: int = 5
    max_array_size: int = 3
    include_nulls: bool = False
    include_response_time: bool = True
    include_headers: bool = True
    include_body_structure: bool = True
    include_data_types: bool = True
    max_assertions: int = 20


class Assertion:
    """Represents a single assertion."""
    
    def __init__(self, assertion_type: str, path: str = "", value: Any = None, matcher: str = "equals"):
        self.type = assertion_type
        self.path = path
        self.value = value
        self.matcher = matcher
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert assertion to dictionary format."""
        result = {
            "type": self.type,
            "path": self.path
        }
        
        if self.value is not None:
            result["value"] = self.value
        
        if self.matcher != "equals":
            result["matcher"] = self.matcher
            
        return result
    
    def format_for_display(self) -> str:
        """Format assertion for display/logging."""
        if self.type == "status_code":
            return f'{{"type": "status_code", "value": {self.value}}}'
        elif self.type == "exists":
            return f'{{"type": "exists", "path": "{self.path}"}}'
        elif self.type == "equals":
            if self.value is None:
                return f'{{"type": "equals", "path": "{self.path}", "value": null}}'
            elif isinstance(self.value, str):
                return f'{{"type": "equals", "path": "{self.path}", "value": "{self.value}"}}'
            else:
                return f'{{"type": "equals", "path": "{self.path}", "value": {self.value}}}'
        else:
            return f'{{"type": "{self.type}", "path": "{self.path}"}}'


class AssertionGenerator:
    """Generates intelligent assertions based on response data analysis, similar to the Go implementation."""
    
    def __init__(self, config: Optional[AssertionConfig] = None):
        self.config = config or AssertionConfig()
    
    def generate_assertions(self, data: Any, path: str = "") -> List[Assertion]:
        """
        Generate assertions from JSON data, similar to Go implementation.
        
        Args:
            data: The data to generate assertions for
            path: Current JSON path (for nested objects)
        
        Returns:
            List of Assertion objects
        """
        assertions = []
        
        if isinstance(data, dict):
            # Add existence assertion for the object itself
            if path:
                assertions.append(Assertion("exists", path))
            
            # Process each field
            for key, value in data.items():
                current_path = key if not path else f"{path}.{key}"
                
                # Add existence assertion for each field
                assertions.append(Assertion("exists", current_path))
                
                # Recursively process nested values if within depth limit
                if self.config.max_depth > 0:
                    self.config.max_depth -= 1
                    nested_assertions = self.generate_assertions(value, current_path)
                    assertions.extend(nested_assertions)
                    self.config.max_depth += 1
        
        elif isinstance(data, list):
            # Add existence assertion for the array itself
            if path:
                assertions.append(Assertion("exists", path))
            
            # Process array elements (limited by max_array_size)
            for i, value in enumerate(data):
                if i >= self.config.max_array_size:
                    break
                
                current_path = f"[{i}]" if not path else f"{path}[{i}]"
                
                # Add existence assertion for each array element
                assertions.append(Assertion("exists", current_path))
                
                # Recursively process nested values if within depth limit
                if self.config.max_depth > 0:
                    self.config.max_depth -= 1
                    nested_assertions = self.generate_assertions(value, current_path)
                    assertions.extend(nested_assertions)
                    self.config.max_depth += 1
        
        elif isinstance(data, str):
            # Add value assertion for strings
            if path:
                assertions.append(Assertion("equals", path, data))
        
        elif isinstance(data, (int, float)):
            # Add value assertion for numbers
            if path:
                assertions.append(Assertion("equals", path, data))
        
        elif isinstance(data, bool):
            # Add value assertion for booleans
            if path:
                assertions.append(Assertion("equals", path, data))
        
        elif data is None:
            # Add null assertion if include_nulls is True
            if self.config.include_nulls and path:
                assertions.append(Assertion("equals", path, None))
        
        return assertions
    
    def generate_status_assertion(self, status_code: int) -> Assertion:
        """Generate a status code assertion."""
        return Assertion("status_code", "", status_code)
    
    def generate_header_assertions(self) -> List[Assertion]:
        """Generate basic header assertions."""
        return [
            Assertion("exists", "headers.Content-Type"),
            Assertion("equals", "headers.Content-Type", "application/json")
        ]
    
    def generate_common_assertions(self) -> List[Assertion]:
        """Generate common assertions for API responses."""
        return [
            Assertion("exists", "data"),
            Assertion("exists", "message"),
            Assertion("exists", "status")
        ]
    
    def generate_assertions_from_response(
        self, 
        response_data: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate assertions based on actual response data.
        Maintained for backward compatibility.
        """
        if options:
            # Update config from options
            self.config.include_response_time = options.get('include_response_time', True)
            self.config.include_headers = options.get('include_headers', True)
            self.config.include_body_structure = options.get('include_body_structure', True)
            self.config.include_data_types = options.get('include_data_types', True)
            self.config.max_assertions = options.get('max_assertions', 20)
        
        assertions = []
        
        try:
            # Status code assertion
            if 'status_code' in response_data:
                status_assertion = self.generate_status_assertion(response_data['status_code'])
                assertions.append(status_assertion.to_dict())
            
            # Response time assertion
            if self.config.include_response_time and 'response_time_ms' in response_data:
                response_time = response_data['response_time_ms']
                threshold = max(response_time * 2, 1000)  # At least 1 second or 2x actual time
                assertions.append({
                    "type": "response_time",
                    "expected": threshold,
                    "matcher": "less_than",
                    "description": f"Verify response time is under {threshold}ms"
                })
            
            # Body structure assertions using the new generate_assertions method
            if self.config.include_body_structure and 'body' in response_data:
                body = response_data['body']
                if isinstance(body, str):
                    try:
                        body = json.loads(body)
                    except json.JSONDecodeError:
                        pass  # Keep as string
                
                if body:
                    body_assertions = self.generate_assertions(body)
                    for assertion in body_assertions:
                        assertions.append(assertion.to_dict())
            
            # Header assertions
            if self.config.include_headers and 'headers' in response_data:
                header_assertions = self._generate_header_assertions_legacy(response_data['headers'])
                assertions.extend(header_assertions)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_assertions = []
            for assertion in assertions:
                key = f"{assertion.get('type')}:{assertion.get('path')}"
                if key not in seen:
                    seen.add(key)
                    unique_assertions.append(assertion)
            
            # Limit total assertions
            if len(unique_assertions) > self.config.max_assertions:
                logger.warning(f"Generated {len(unique_assertions)} assertions, limiting to {self.config.max_assertions}")
                unique_assertions = unique_assertions[:self.config.max_assertions]
            
        except Exception as e:
            logger.error(f"Error generating assertions: {e}")
            # Return basic assertions as fallback
            unique_assertions = [{
                "type": "status_code", 
                "expected": 200,
                "matcher": "equals",
                "description": "Verify successful response"
            }]
        
        return unique_assertions
    
    def _generate_header_assertions_legacy(self, headers: Dict[str, str]) -> List[Dict[str, Any]]:
        """Generate assertions for important response headers (legacy format for backward compatibility)."""
        assertions = []
        
        # Important headers to assert on
        important_headers = {
            'content-type': 'Content type matches expected format',
            'content-length': 'Response has content length header',
            'cache-control': 'Cache control header is set',
            'server': 'Server header indicates expected server',
            'x-api-version': 'API version header is present',
            'x-rate-limit-remaining': 'Rate limit header indicates remaining requests',
            'etag': 'ETag header is present for caching'
        }
        
        for header_name, description in important_headers.items():
            header_value = None
            # Case-insensitive header lookup
            for h_name, h_value in headers.items():
                if h_name.lower() == header_name.lower():
                    header_value = h_value
                    break
            
            if header_value:
                matcher = "exists" if header_name in ['content-length', 'etag'] else "equals"
                assertions.append({
                    "type": "header",
                    "path": header_name.lower(),
                    "expected": header_value,
                    "matcher": matcher,
                    "description": description
                })
        
    def generate_assertions_from_spec(
        self,
        test_spec: Dict[str, Any],
        response_analysis: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate assertions based on test specification and optional response analysis.
        
        Args:
            test_spec: Test specification containing method, path, expected behavior
            response_analysis: Optional analysis of actual responses for smarter assertions
        
        Returns:
            List of generated assertions
        """
        assertions = []
        
        method = test_spec.get('method', 'GET').upper()
        path = test_spec.get('path', '')
        
        # Method-specific assertions
        if method == 'POST':
            assertions.append({
                "type": "status_code",
                "expected": 201,
                "matcher": "equals", 
                "description": "Verify resource was created successfully"
            })
        elif method == 'PUT':
            assertions.append({
                "type": "status_code", 
                "expected": 200,
                "matcher": "equals",
                "description": "Verify resource was updated successfully"
            })
        elif method == 'DELETE':
            assertions.append({
                "type": "status_code",
                "expected": 204,
                "matcher": "equals",
                "description": "Verify resource was deleted successfully"
            })
        else:  # GET, PATCH, etc.
            assertions.append({
                "type": "status_code",
                "expected": 200,
                "matcher": "equals", 
                "description": "Verify request was successful"
            })
        
        # Path-specific assertions
        if '/users' in path:
            assertions.extend([
                {
                    "type": "header",
                    "path": "content-type",
                    "expected": "application/json",
                    "matcher": "contains",
                    "description": "Verify response is JSON format"
                },
                {
                    "type": "body",
                    "path": "id" if method != 'GET' or path.count('/') > 2 else "$[0].id",
                    "matcher": "exists",
                    "description": "Verify user ID is present"
                }
            ])
        
        # Use response analysis if provided
        if response_analysis:
            analysis_assertions = self.generate_assertions_from_response(response_analysis)
            # Merge with spec-based assertions, avoiding duplicates
            for assertion in analysis_assertions:
                if not any(a.get('type') == assertion.get('type') and 
                          a.get('path') == assertion.get('path') for a in assertions):
                    assertions.append(assertion)
        
        return assertions

    @staticmethod
    def _generate_body_assertions(body: Union[str, Dict, List], options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate assertions for response body content and structure (legacy method)."""
        assertions = []
        
        if not body:
            return assertions
        
        try:
            # Handle JSON response
            if isinstance(body, str):
                try:
                    parsed_body = json.loads(body)
                except json.JSONDecodeError:
                    # Handle non-JSON string responses
                    return AssertionGenerator._generate_text_assertions(body)
            else:
                parsed_body = body
            
            if isinstance(parsed_body, dict):
                assertions.extend(AssertionGenerator._generate_object_assertions(parsed_body, options))
            elif isinstance(parsed_body, list):
                assertions.extend(AssertionGenerator._generate_array_assertions(parsed_body, options))
            
        except Exception as e:
            logger.error(f"Error analyzing response body: {e}")
        
        return assertions
    
    @staticmethod
    def _generate_object_assertions(data: Dict[str, Any], options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate assertions for JSON object responses (legacy method)."""
        assertions = []
        include_data_types = options.get('include_data_types', True)
        
        # Check for common API response patterns
        if 'error' in data:
            assertions.append({
                "type": "body",
                "path": "error",
                "expected": data['error'],
                "matcher": "equals",
                "description": "Verify error field matches expected value"
            })
        
        if 'message' in data:
            assertions.append({
                "type": "body", 
                "path": "message",
                "expected": data['message'],
                "matcher": "contains" if len(str(data['message'])) > 50 else "equals",
                "description": "Verify message field contains expected content"
            })
        
        if 'data' in data:
            assertions.append({
                "type": "body",
                "path": "data",
                "matcher": "exists",
                "description": "Verify data field exists in response"
            })
            
            # Analyze data structure if it's an object or array
            if isinstance(data['data'], (dict, list)) and len(str(data['data'])) < 1000:
                assertions.append({
                    "type": "body",
                    "path": "data",
                    "expected": len(data['data']) if isinstance(data['data'], list) else len(data['data'].keys()),
                    "matcher": "count_equals" if isinstance(data['data'], list) else "key_count_equals",
                    "description": f"Verify data contains expected number of {'items' if isinstance(data['data'], list) else 'fields'}"
                })
        
        return assertions
    
    @staticmethod
    def _generate_array_assertions(data: List[Any], options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate assertions for JSON array responses (legacy method)."""
        assertions = []
        
        # Array length assertion
        assertions.append({
            "type": "body",
            "path": "$",
            "expected": len(data),
            "matcher": "count_equals",
            "description": f"Verify response contains exactly {len(data)} items"
        })
        
        return assertions
    
    @staticmethod 
    def _generate_text_assertions(text: str) -> List[Dict[str, Any]]:
        """Generate assertions for plain text responses (legacy method)."""
        assertions = []
        
        # Check for common text patterns
        if re.match(r'^[A-Z][a-z\s]+$', text.strip()):
            assertions.append({
                "type": "body",
                "matcher": "regex",
                "expected": r'^[A-Z][a-z\s]+$',
                "description": "Verify response is properly formatted text"
            })
        
        return assertions


# Factory function for creating assertion generators
def create_assertion_generator(
    max_depth: int = 5,
    max_array_size: int = 3,
    include_nulls: bool = False,
    **kwargs
) -> AssertionGenerator:
    """
    Create an assertion generator with custom configuration.
    Similar to NewAssertionGenerator() in the Go implementation.
    """
    config = AssertionConfig(
        max_depth=max_depth,
        max_array_size=max_array_size,
        include_nulls=include_nulls,
        **kwargs
    )
    return AssertionGenerator(config)


# Convenience functions for backward compatibility
def generate_smart_assertions(
    response_data: Dict[str, Any], 
    options: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Generate smart assertions from response data."""
    generator = AssertionGenerator()
    return generator.generate_assertions_from_response(response_data, options)


def generate_spec_assertions(
    test_spec: Dict[str, Any],
    response_analysis: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Generate assertions from test specification."""
    generator = AssertionGenerator()
    return generator.generate_assertions_from_spec(test_spec, response_analysis)


def generate_assertions_from_json(
    json_data: Union[str, Dict, List],
    status_code: Optional[int] = None,
    max_depth: int = 5,
    max_array_size: int = 3,
    include_nulls: bool = False
) -> List[Dict[str, Any]]:
    """
    Generate assertions from JSON data, similar to the Go main function.
    
    Args:
        json_data: JSON data as string, dict, or list
        status_code: Optional status code to include
        max_depth: Maximum depth to traverse
        max_array_size: Maximum array elements to process
        include_nulls: Whether to include null value assertions
    
    Returns:
        List of assertion dictionaries
    """
    # Parse JSON if it's a string
    if isinstance(json_data, str):
        try:
            parsed_data = json.loads(json_data)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON: {e}")
            return []
    else:
        parsed_data = json_data
    
    # Create generator with custom config
    generator = create_assertion_generator(
        max_depth=max_depth,
        max_array_size=max_array_size,
        include_nulls=include_nulls
    )
    
    # Generate assertions
    assertions = generator.generate_assertions(parsed_data)
    
    # Convert to dict format
    result = []
    
    # Add status code assertion if provided
    if status_code:
        status_assertion = generator.generate_status_assertion(status_code)
        result.append(status_assertion.to_dict())
    
    # Add generated assertions
    for assertion in assertions:
        result.append(assertion.to_dict())
    
    # Add common API response assertions
    common_assertions = generator.generate_common_assertions()
    for assertion in common_assertions:
        result.append(assertion.to_dict())
    
    # Remove duplicates while preserving order
    seen = set()
    unique_result = []
    for assertion in result:
        key = f"{assertion.get('type')}:{assertion.get('path')}"
        if key not in seen:
            seen.add(key)
            unique_result.append(assertion)
    
    return unique_result
