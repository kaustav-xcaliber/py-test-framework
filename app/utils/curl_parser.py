"""Curl command parser utility for converting curl commands to test specifications."""

import re
import json
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse, parse_qs, unquote

from app.schemas.schemas import CurlRequest, TestSpecBase

logger = logging.getLogger(__name__)


class CurlParser:
    """Parser for converting curl commands to test specifications."""
    
    @staticmethod
    def parse_curl_command(curl_cmd: str) -> CurlRequest:
        """
        Parse a curl command and return a CurlRequest object.
        
        Args:
            curl_cmd: The curl command string
            
        Returns:
            CurlRequest object with parsed information
            
        Raises:
            ValueError: If the curl command is invalid
        """
        if not curl_cmd or not curl_cmd.strip():
            raise ValueError("Curl command cannot be empty")
        
        try:
            return CurlParser._manual_parse_curl(curl_cmd)
        except Exception as e:
            logger.error(f"Failed to parse curl command: {e}")
            raise ValueError(f"Invalid curl command: {e}") from e
    
    @staticmethod
    def _extract_path_variables(path: str) -> Dict[str, str]:
        """
        Extract potential path variables from URL path.
        This is a basic implementation that can be extended.
        """
        path_variables = {}
        
        # Look for common path variable patterns
        # This can be enhanced with more sophisticated pattern matching
        path_parts = path.split('/')
        for i, part in enumerate(path_parts):
            if part.startswith('{') and part.endswith('}'):
                var_name = part[1:-1]
                path_variables[var_name] = f"{{path_var_{i}}}"
            elif part.isdigit():
                path_variables[f"id_{i}"] = part
        
        return path_variables
    
    @staticmethod
    def _determine_request_type(parsed: Dict[str, Any]) -> str:
        """Determine the request content type based on parsed data."""
        headers = parsed.get('headers', {})
        content_type = headers.get('content-type', '').lower()
        
        if 'application/json' in content_type:
            return 'json'
        elif 'application/x-www-form-urlencoded' in content_type:
            return 'form'
        elif 'multipart/form-data' in content_type:
            return 'multipart'
        elif parsed.get('data'):
            # Try to detect JSON
            try:
                json.loads(parsed['data'])
                return 'json'
            except (json.JSONDecodeError, TypeError):
                return 'form'
        else:
            return 'none'
    
    @staticmethod
    def _manual_parse_curl(curl_cmd: str) -> CurlRequest:
        """
        Manual parsing for curl commands.
        This provides robust parsing for complex curl commands.
        """
        # Normalize the command - handle escaped quotes and newlines
        command = curl_cmd.replace('\\\n', ' ').replace('\\', '')
        command = ' '.join(command.split())
        
        # More robust tokenization that handles nested quotes
        tokens = []
        current_token = ""
        in_quotes = False
        quote_char = None
        
        for char in command:
            if char in ['"', "'"] and not in_quotes:
                in_quotes = True
                quote_char = char
                current_token += char
            elif char == quote_char and in_quotes:
                in_quotes = False
                current_token += char
                tokens.append(current_token)
                current_token = ""
                quote_char = None
            elif in_quotes:
                current_token += char
            elif char.isspace():
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
            else:
                current_token += char
        
        if current_token:
            tokens.append(current_token)
        
        if not tokens or tokens[0].lower() != 'curl':
            raise ValueError("Invalid curl command: must start with 'curl'")
        
        # Initialize default values
        method = 'GET'
        url = ''
        headers = {}
        body = ''
        query_params = {}
        path_variables = {}
        
        i = 1
        while i < len(tokens):
            token = tokens[i].strip("'\"")
            
            if token in ['-X', '--request']:
                if i + 1 < len(tokens):
                    i += 1
                    method = tokens[i].strip("'\"")
            elif token in ['-H', '--header']:
                if i + 1 < len(tokens):
                    i += 1
                    header = tokens[i].strip("'\"")
                    if ':' in header:
                        key, value = header.split(':', 1)
                        headers[key.strip()] = value.strip()
                    else:
                        # Handle malformed header gracefully
                        logger.warning(f"Malformed header: {header}")
            elif token in ['--data', '--data-raw', '--data-binary', '-d']:
                if i + 1 < len(tokens):
                    i += 1
                    body_data = tokens[i].strip("'\"")
                    # If we already have body data, append it
                    if body:
                        body += body_data
                    else:
                        body = body_data
                    if method == 'GET':
                        method = 'POST'
            elif token in ['--form', '-F']:
                if i + 1 < len(tokens):
                    i += 1
                    form_data = tokens[i].strip("'\"")
                    if '=' in form_data:
                        key, value = form_data.split('=', 1)
                        if not body:
                            body = f"{key}={value}"
                        if method == 'GET':
                            method = 'POST'
            elif token in ['--location']:
                # Ignore --location flag, it's just for following redirects
                pass
            elif not url and not token.startswith('-'):
                # Found the URL, but continue processing other tokens
                url = token
            
            i += 1
        
        if not url:
            raise ValueError("No URL found in curl command")
        
        # Parse URL components
        parsed_url = urlparse(url)
        if parsed_url.query:
            query_params = parse_qs(parsed_url.query)
            query_params = {k: v[0] if v else '' for k, v in query_params.items()}
        
        path_variables = CurlParser._extract_path_variables(parsed_url.path)
        request_type = CurlParser._determine_request_type({
            'headers': headers,
            'data': body
        })
        
        return CurlRequest(
            method=method.upper(),
            url=url,
            headers=headers,
            body=body,
            query_params=query_params,
            path_variables=path_variables,
            request_type=request_type,
            raw_command=curl_cmd
        )
    
    @staticmethod
    def curl_to_test_spec(curl_cmd: str, custom_assertions: Optional[List[Dict[str, Any]]] = None) -> TestSpecBase:
        """
        Convert a curl command to a test specification.
        
        Args:
            curl_cmd: The curl command string
            custom_assertions: Optional list of custom assertions to include
            
        Returns:
            TestSpecBase object ready for test case creation
        """
        curl_request = CurlParser.parse_curl_command(curl_cmd)
        
        # Create basic assertions based on the request
        assertions = [
            {
                "type": "status_code",
                "expected": 200,
                "description": "Check if response status is successful"
            }
        ]
        
        # Add content type assertion if specified in request headers
        content_type = curl_request.headers.get('content-type') or curl_request.headers.get('Content-Type')
        if content_type:
            assertions.append({
                "type": "header",
                "path": "content-type",
                "expected": content_type,
                "matcher": "contains",
                "description": "Check content type header matches request"
            })
        
        # Add response time assertion for performance testing
        assertions.append({
            "type": "response_time",
            "expected": 5000,  # 5 seconds max
            "matcher": "less_than",
            "description": "Check response time is acceptable"
        })
        
        # Add custom assertions if provided
        if custom_assertions:
            assertions.extend(custom_assertions)
        
        # Create test specification
        return TestSpecBase(
            name=f"Test from curl: {curl_request.method} {curl_request.url}",
            method=curl_request.method,
            path=urlparse(curl_request.url).path,
            headers=curl_request.headers,
            query_params=curl_request.query_params,
            path_variables=curl_request.path_variables,
            body=curl_request.body,
            assertions=assertions
        )


# Convenience function for direct usage
def parse_curl_command(curl_cmd: str) -> CurlRequest:
    """Parse a curl command and return a CurlRequest object."""
    return CurlParser.parse_curl_command(curl_cmd)


def curl_to_test_spec(curl_cmd: str, custom_assertions: Optional[List[Dict[str, Any]]] = None) -> TestSpecBase:
    """Convert a curl command to a test specification."""
    return CurlParser.curl_to_test_spec(curl_cmd, custom_assertions)
