"""Test execution engine for running API tests."""

import json
import time
import base64
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urljoin, urlencode

import httpx
from jsonschema import validate, ValidationError

from app.schemas.schemas import TestSpecBase, TestResultBase
from app.config.settings import settings


class TestExecutor:
    """Executes API tests using httpx."""
    
    def __init__(self, base_url: str, auth_config: Optional[Dict[str, Any]] = None, timeout: int = None):
        """
        Initialize the test executor.
        
        Args:
            base_url: Base URL for the service being tested
            auth_config: Authentication configuration dictionary
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.auth_config = auth_config
        self.timeout = timeout or settings.default_request_timeout
        
        # Create HTTP client with default settings
        self.client = httpx.Client(
            timeout=self.timeout,
            follow_redirects=True,
            verify=True
        )
    
    def execute_test(self, test_spec: TestSpecBase) -> TestResultBase:
        """
        Execute a single test case.
        
        Args:
            test_spec: Test specification to execute
            
        Returns:
            TestResultBase with execution results
        """
        start_time = datetime.utcnow()
        start_timestamp = time.time()
        
        try:
            # Prepare request
            url = self._build_url(test_spec)
            headers = test_spec.headers or {}
            params = test_spec.query_params or {}
            
            # Apply authentication
            headers, params = self._apply_authentication(headers, params)
            
            # Prepare request body
            body = self._prepare_body(test_spec)
            
            # Execute request
            response = self._make_request(
                method=test_spec.method,
                url=url,
                headers=headers,
                params=params,
                body=body
            )
            
            # Calculate timing
            end_timestamp = time.time()
            response_time_ms = int((end_timestamp - start_timestamp) * 1000)
            
            # Run assertions
            assertion_results = self._run_assertions(test_spec.assertions, response)
            
            # Determine test status
            status = "passed" if all(ar.get("passed", False) for ar in assertion_results) else "failed"
            
            # Prepare response data
            response_data = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": self._extract_response_body(response),
                "url": str(response.url),
                "method": test_spec.method
            }
            
            return TestResultBase(
                test_name=test_spec.name,
                status=status,
                error_message=None,
                response_data=response_data,
                assertion_results=assertion_results
            )
            
        except Exception as e:
            # Test failed due to execution error
            end_timestamp = time.time()
            response_time_ms = int((end_timestamp - start_timestamp) * 1000)
            
            return TestResultBase(
                test_name=test_spec.name,
                status="failed",
                error_message=str(e),
                response_data=None,
                assertion_results=[]
            )
    
    def _build_url(self, test_spec: TestSpecBase) -> str:
        """Build the full URL for the test request."""
        # Start with base URL
        url = self.base_url
        
        # Add path
        if test_spec.path:
            # Handle path variables
            path = test_spec.path
            if test_spec.path_variables:
                for var_name, var_value in test_spec.path_variables.items():
                    path = path.replace(f"{{{var_name}}}", str(var_value))
            url = urljoin(url, path)
        
        return url
    
    def _prepare_body(self, test_spec: TestSpecBase) -> Optional[Any]:
        """Prepare the request body based on test specification."""
        if not test_spec.body:
            return None
        
        # If body is already a string, return as-is
        if isinstance(test_spec.body, str):
            return test_spec.body
        
        # If body is a dict, convert to JSON
        if isinstance(test_spec.body, dict):
            return json.dumps(test_spec.body)
        
        # Otherwise, return as string
        return str(test_spec.body)
    
    def _make_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        params: Dict[str, str],
        body: Optional[Any]
    ) -> httpx.Response:
        """Make the HTTP request."""
        # Set default content type for JSON if not specified
        if body and isinstance(body, str) and not headers.get('content-type'):
            try:
                json.loads(body)
                headers['content-type'] = 'application/json'
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Make the request
        response = self.client.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            content=body
        )
        
        return response
    
    def _extract_response_body(self, response: httpx.Response) -> Any:
        """Extract and parse response body."""
        try:
            # Try to parse as JSON
            return response.json()
        except (json.JSONDecodeError, ValueError):
            # Return as text if not JSON
            return response.text
    
    def _run_assertions(
        self,
        assertions: List[Dict[str, Any]],
        response: httpx.Response
    ) -> List[Dict[str, Any]]:
        """Run all assertions against the response."""
        results = []
        
        for assertion in assertions:
            try:
                result = self._run_single_assertion(assertion, response)
                results.append(result)
            except Exception as e:
                # Assertion execution failed
                results.append({
                    "type": assertion.get("type", "unknown"),
                    "path": assertion.get("path"),
                    "matcher": assertion.get("matcher"),
                    "expected": assertion.get("expected"),
                    "actual": None,
                    "passed": False,
                    "message": f"Assertion execution failed: {str(e)}"
                })
        
        return results
    
    def _run_single_assertion(
        self,
        assertion: Dict[str, Any],
        response: httpx.Response
    ) -> Dict[str, Any]:
        """Run a single assertion."""
        assertion_type = assertion.get("type", "unknown")
        
        if assertion_type == "status_code":
            return self._assert_status_code(assertion, response)
        elif assertion_type == "header":
            return self._assert_header(assertion, response)
        elif assertion_type == "body":
            return self._assert_body(assertion, response)
        elif assertion_type == "schema":
            return self._assert_schema(assertion, response)
        elif assertion_type == "contains":
            return self._assert_contains(assertion, response)
        elif assertion_type == "equals":
            return self._assert_equals(assertion, response)
        elif assertion_type == "regex":
            return self._assert_regex(assertion, response)
        else:
            return {
                "type": assertion_type,
                "path": assertion.get("path"),
                "matcher": assertion.get("matcher"),
                "expected": assertion.get("expected"),
                "actual": None,
                "passed": False,
                "message": f"Unknown assertion type: {assertion_type}"
            }
    
    def _assert_status_code(
        self,
        assertion: Dict[str, Any],
        response: httpx.Response
    ) -> Dict[str, Any]:
        """Assert response status code."""
        expected = assertion.get("expected")
        actual = response.status_code
        
        passed = actual == expected
        
        return {
            "type": "status_code",
            "path": "status_code",
            "matcher": "equals",
            "expected": expected,
            "actual": actual,
            "passed": passed,
            "message": f"Expected status code {expected}, got {actual}"
        }
    
    def _assert_header(
        self,
        assertion: Dict[str, Any],
        response: httpx.Response
    ) -> Dict[str, Any]:
        """Assert response header value."""
        path = assertion.get("path")
        expected = assertion.get("expected")
        matcher = assertion.get("matcher", "equals")
        
        if not path:
            return {
                "type": "header",
                "path": path,
                "matcher": matcher,
                "expected": expected,
                "actual": None,
                "passed": False,
                "message": "Header path not specified"
            }
        
        actual = response.headers.get(path)
        
        if matcher == "equals":
            passed = actual == expected
        elif matcher == "contains":
            passed = expected in actual if actual else False
        elif matcher == "regex":
            import re
            passed = bool(re.search(expected, actual)) if actual else False
        else:
            passed = actual == expected
        
        return {
            "type": "header",
            "path": path,
            "matcher": matcher,
            "expected": expected,
            "actual": actual,
            "passed": passed,
            "message": f"Header {path}: expected {expected}, got {actual}"
        }
    
    def _assert_body(
        self,
        assertion: Dict[str, Any],
        response: httpx.Response
    ) -> Dict[str, Any]:
        """Assert response body content."""
        path = assertion.get("path")
        expected = assertion.get("expected")
        matcher = assertion.get("matcher", "equals")
        
        try:
            body = self._extract_response_body(response)
            
            if path:
                # Extract value from JSON path
                actual = self._extract_json_path(body, path)
            else:
                actual = body
            
            if matcher == "equals":
                passed = actual == expected
            elif matcher == "contains":
                passed = expected in str(actual)
            elif matcher == "regex":
                import re
                passed = bool(re.search(expected, str(actual)))
            else:
                passed = actual == expected
            
            return {
                "type": "body",
                "path": path,
                "matcher": matcher,
                "expected": expected,
                "actual": actual,
                "passed": passed,
                "message": f"Body assertion: expected {expected}, got {actual}"
            }
            
        except Exception as e:
            return {
                "type": "body",
                "path": path,
                "matcher": matcher,
                "expected": expected,
                "actual": None,
                "passed": False,
                "message": f"Body assertion failed: {str(e)}"
            }
    
    def _assert_schema(
        self,
        assertion: Dict[str, Any],
        response: httpx.Response
    ) -> Dict[str, Any]:
        """Assert response body matches JSON schema."""
        schema = assertion.get("expected")
        
        try:
            body = self._extract_response_body(response)
            validate(instance=body, schema=schema)
            
            return {
                "type": "schema",
                "path": None,
                "matcher": "schema",
                "expected": "Valid JSON schema",
                "actual": "Valid",
                "passed": True,
                "message": "Response body matches JSON schema"
            }
            
        except ValidationError as e:
            return {
                "type": "schema",
                "path": None,
                "matcher": "schema",
                "expected": "Valid JSON schema",
                "actual": f"Invalid: {str(e)}",
                "passed": False,
                "message": f"Response body does not match JSON schema: {str(e)}"
            }
        except Exception as e:
            return {
                "type": "schema",
                "path": None,
                "matcher": "schema",
                "expected": "Valid JSON schema",
                "actual": None,
                "passed": False,
                "message": f"Schema validation failed: {str(e)}"
            }
    
    def _assert_contains(
        self,
        assertion: Dict[str, Any],
        response: httpx.Response
    ) -> Dict[str, Any]:
        """Assert response contains expected content."""
        expected = assertion.get("expected")
        path = assertion.get("path")
        
        try:
            body = self._extract_response_body(response)
            
            if path:
                actual = self._extract_json_path(body, path)
            else:
                actual = body
            
            passed = expected in str(actual)
            
            return {
                "type": "contains",
                "path": path,
                "matcher": "contains",
                "expected": expected,
                "actual": str(actual)[:100] + "..." if len(str(actual)) > 100 else str(actual),
                "passed": passed,
                "message": f"Expected to find '{expected}' in response"
            }
            
        except Exception as e:
            return {
                "type": "contains",
                "path": path,
                "matcher": "contains",
                "expected": expected,
                "actual": None,
                "passed": False,
                "message": f"Contains assertion failed: {str(e)}"
            }
    
    def _assert_equals(
        self,
        assertion: Dict[str, Any],
        response: httpx.Response
    ) -> Dict[str, Any]:
        """Assert response equals expected content."""
        expected = assertion.get("expected")
        path = assertion.get("path")
        
        try:
            body = self._extract_response_body(response)
            
            if path:
                actual = self._extract_json_path(body, path)
            else:
                actual = body
            
            passed = actual == expected
            
            return {
                "type": "equals",
                "path": path,
                "matcher": "equals",
                "expected": expected,
                "actual": actual,
                "passed": passed,
                "message": f"Expected {expected}, got {actual}"
            }
            
        except Exception as e:
            return {
                "type": "equals",
                "path": path,
                "matcher": "equals",
                "expected": expected,
                "actual": None,
                "passed": False,
                "message": f"Equals assertion failed: {str(e)}"
            }
    
    def _assert_regex(
        self,
        assertion: Dict[str, Any],
        response: httpx.Response
    ) -> Dict[str, Any]:
        """Assert response matches regex pattern."""
        pattern = assertion.get("expected")
        path = assertion.get("path")
        
        try:
            body = self._extract_response_body(response)
            
            if path:
                actual = self._extract_json_path(body, path)
            else:
                actual = body
            
            import re
            passed = bool(re.search(pattern, str(actual)))
            
            return {
                "type": "regex",
                "path": path,
                "matcher": "regex",
                "expected": pattern,
                "actual": str(actual)[:100] + "..." if len(str(actual)) > 100 else str(actual),
                "passed": passed,
                "message": f"Expected response to match regex pattern: {pattern}"
            }
            
        except Exception as e:
            return {
                "type": "regex",
                "path": path,
                "matcher": "regex",
                "expected": pattern,
                "actual": None,
                "passed": False,
                "message": f"Regex assertion failed: {str(e)}"
            }
    
    def _extract_json_path(self, data: Any, path: str) -> Any:
        """Extract value from JSON data using dot notation path."""
        if not path:
            return data
        
        try:
            # Handle simple dot notation for now
            # This can be enhanced with more sophisticated JSON path support
            keys = path.split('.')
            current = data
            
            for key in keys:
                if isinstance(current, dict):
                    current = current.get(key)
                elif isinstance(current, list) and key.isdigit():
                    current = current[int(key)]
                else:
                    raise ValueError(f"Cannot extract path {path}")
                
                if current is None:
                    break
            
            return current
            
        except Exception as e:
            raise ValueError(f"Failed to extract path {path}: {str(e)}")
    
    def _apply_authentication(self, headers: Dict[str, str], params: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        Apply authentication to the request based on auth_config.
        
        Args:
            headers: Request headers
            params: Query parameters
            
        Returns:
            Tuple of (headers, params) with authentication applied
        """
        if not self.auth_config:
            return headers, params
        
        auth_type = self.auth_config.get("type", "").lower()
        
        if auth_type == "bearer":
            return self._apply_bearer_auth(headers, params)
        elif auth_type == "api_key":
            return self._apply_api_key_auth(headers, params)
        elif auth_type == "basic":
            return self._apply_basic_auth(headers, params)
        elif auth_type == "oauth2":
            return self._apply_oauth2_auth(headers, params)
        else:
            # Unknown auth type, return unchanged
            return headers, params
    
    def _apply_bearer_auth(self, headers: Dict[str, str], params: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Apply Bearer token authentication."""
        token = self.auth_config.get("token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers, params
    
    def _apply_api_key_auth(self, headers: Dict[str, str], params: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Apply API key authentication."""
        key_name = self.auth_config.get("key_name")
        key_value = self.auth_config.get("key_value")
        
        if key_name and key_value:
            # Try to determine if it should be in header or query param
            # Common header names for API keys
            header_key_names = ["x-api-key", "api-key", "authorization", "x-auth-token"]
            
            if key_name.lower() in [name.lower() for name in header_key_names]:
                headers[key_name] = key_value
            else:
                # Default to query parameter
                params[key_name] = key_value
        
        return headers, params
    
    def _apply_basic_auth(self, headers: Dict[str, str], params: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Apply Basic authentication."""
        username = self.auth_config.get("username")
        password = self.auth_config.get("password")
        
        if username and password:
            credentials = f"{username}:{password}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            headers["Authorization"] = f"Basic {encoded_credentials}"
        
        return headers, params
    
    def _apply_oauth2_auth(self, headers: Dict[str, str], params: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Apply OAuth2 authentication."""
        # For OAuth2, we need to handle token acquisition first
        # This is a simplified implementation - in production you'd want more robust token management
        
        # Check if we have a token already
        token = self.auth_config.get("token")
        
        if not token:
            # Try to get a new token
            token = self._get_oauth2_token()
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        return headers, params
    
    def _get_oauth2_token(self) -> Optional[str]:
        """Get OAuth2 token using client credentials flow."""
        try:
            client_id = self.auth_config.get("client_id")
            client_secret = self.auth_config.get("client_secret")
            token_url = self.auth_config.get("token_url")
            
            if not all([client_id, client_secret, token_url]):
                return None
            
            # Prepare token request
            token_data = {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret
            }
            
            # Add any extra parameters from auth_config
            extra = self.auth_config.get("extra", {})
            if extra:
                token_data.update(extra)
            
            # Make token request
            response = self.client.post(
                token_url,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                token_response = response.json()
                return token_response.get("access_token")
            
        except Exception as e:
            # Log error but don't fail the test
            print(f"OAuth2 token acquisition failed: {str(e)}")
        
        return None
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
