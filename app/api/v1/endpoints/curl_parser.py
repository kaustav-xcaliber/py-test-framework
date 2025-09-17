"""Curl parser endpoints for converting curl commands to test specifications."""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.utils.curl_parser import CurlParser
from app.schemas.schemas import CurlRequest, TestSpecBase

router = APIRouter()


class CurlParseRequest(BaseModel):
    """Request schema for parsing curl commands."""
    curl_command: str = Field(..., description="Curl command to parse", min_length=1)
    custom_assertions: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optional custom assertions to add to the generated test spec"
    )


class CurlParseResponse(BaseModel):
    """Response schema for curl parsing."""
    parsed_request: CurlRequest = Field(..., description="Parsed curl request details")
    success: bool = Field(True, description="Whether parsing was successful")
    message: str = Field(default="Successfully parsed curl command", description="Status message")


class CurlToTestSpecRequest(BaseModel):
    """Request schema for converting curl to test specification."""
    curl_command: str = Field(..., description="Curl command to convert", min_length=1)
    test_name: Optional[str] = Field(None, description="Custom name for the test")
    custom_assertions: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optional custom assertions to add to the test spec"
    )


class CurlToTestSpecResponse(BaseModel):
    """Response schema for curl to test spec conversion."""
    test_spec: TestSpecBase = Field(..., description="Generated test specification")
    success: bool = Field(True, description="Whether conversion was successful")
    message: str = Field(default="Successfully converted curl to test specification", description="Status message")


@router.post("/parse", response_model=CurlParseResponse, status_code=status.HTTP_200_OK)
async def parse_curl_command(request: CurlParseRequest):
    """
    Parse a curl command and return the parsed request details.
    
    This endpoint takes a curl command string and parses it into its components
    including HTTP method, URL, headers, body, query parameters, etc.
    """
    try:
        parsed_request = CurlParser.parse_curl_command(request.curl_command)
        
        return CurlParseResponse(
            parsed_request=parsed_request,
            success=True,
            message="Successfully parsed curl command"
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid curl command: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse curl command: {str(e)}"
        )


@router.post("/to-test-spec", response_model=CurlToTestSpecResponse, status_code=status.HTTP_200_OK)
async def curl_to_test_specification(request: CurlToTestSpecRequest):
    """
    Convert a curl command to a test specification.
    
    This endpoint takes a curl command and converts it into a complete test specification
    with generated assertions that can be used to create a test case.
    """
    try:
        test_spec = CurlParser.curl_to_test_spec(
            request.curl_command,
            request.custom_assertions
        )
        
        # Update test name if provided
        if request.test_name:
            test_spec.name = request.test_name
        
        return CurlToTestSpecResponse(
            test_spec=test_spec,
            success=True,
            message="Successfully converted curl command to test specification"
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid curl command: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to convert curl command: {str(e)}"
        )


@router.get("/examples", response_model=Dict[str, Any])
async def get_curl_examples():
    """
    Get example curl commands and their expected parsing results.
    
    This endpoint provides examples of different types of curl commands
    that can be parsed by the system, useful for documentation and testing.
    """
    examples = {
        "basic_get": {
            "curl_command": "curl https://api.example.com/users",
            "description": "Basic GET request",
            "expected_method": "GET",
            "expected_url": "https://api.example.com/users"
        },
        "post_with_json": {
            "curl_command": 'curl -X POST https://api.example.com/users -H "Content-Type: application/json" -d \'{"name": "John", "email": "john@example.com"}\'',
            "description": "POST request with JSON body",
            "expected_method": "POST",
            "expected_content_type": "application/json"
        },
        "get_with_headers": {
            "curl_command": 'curl https://api.example.com/users -H "Authorization: Bearer token123" -H "Accept: application/json"',
            "description": "GET request with custom headers",
            "expected_headers": ["Authorization", "Accept"]
        },
        "put_with_form_data": {
            "curl_command": 'curl -X PUT https://api.example.com/users/123 --data "name=John&email=john@example.com"',
            "description": "PUT request with form data",
            "expected_method": "PUT",
            "expected_content_type": "form"
        },
        "complex_with_query_params": {
            "curl_command": 'curl "https://api.example.com/users?page=1&limit=10" -H "Authorization: Bearer token123"',
            "description": "GET request with query parameters and headers",
            "expected_query_params": {"page": "1", "limit": "10"}
        }
    }
    
    return {
        "examples": examples,
        "supported_methods": ["GET", "POST", "PUT", "PATCH", "DELETE"],
        "supported_content_types": ["application/json", "application/x-www-form-urlencoded", "multipart/form-data"],
        "supported_options": [
            "-X, --request",
            "-H, --header", 
            "-d, --data",
            "--data-raw",
            "--data-binary",
            "-F, --form",
            "--location"
        ]
    }
