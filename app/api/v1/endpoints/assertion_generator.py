"""Assertion generator endpoints for creating smart test assertions."""

from typing import Optional, List, Dict, Any, Union
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import json

from app.utils.assertion_generator import (
    AssertionGenerator, 
    AssertionConfig, 
    create_assertion_generator,
    generate_assertions_from_json
)

router = APIRouter()


class AssertionGenerationConfig(BaseModel):
    """Configuration for assertion generation."""
    max_depth: int = Field(default=5, ge=1, le=10, description="Maximum depth to traverse nested objects")
    max_array_size: int = Field(default=3, ge=1, le=20, description="Maximum array elements to process")
    include_nulls: bool = Field(default=False, description="Whether to include null value assertions")
    include_response_time: bool = Field(default=True, description="Include response time assertions")
    include_headers: bool = Field(default=True, description="Include header assertions")
    include_body_structure: bool = Field(default=True, description="Include body structure assertions")
    include_data_types: bool = Field(default=True, description="Include data type assertions")
    max_assertions: int = Field(default=20, ge=1, le=100, description="Maximum number of assertions to generate")


class ResponseDataInput(BaseModel):
    """Input schema for response data."""
    status_code: Optional[int] = Field(None, description="HTTP status code")
    headers: Optional[Dict[str, str]] = Field(None, description="Response headers")
    body: Optional[Union[str, Dict, List]] = Field(None, description="Response body (JSON string, object, or array)")
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")


class GenerateAssertionsRequest(BaseModel):
    """Request schema for generating assertions from response data."""
    response_data: ResponseDataInput = Field(..., description="Response data to analyze")
    config: Optional[AssertionGenerationConfig] = Field(default=None, description="Generation configuration")


class GenerateFromJSONRequest(BaseModel):
    """Request schema for generating assertions from raw JSON."""
    json_data: Union[str, Dict, List] = Field(..., description="JSON data as string, object, or array")
    status_code: Optional[int] = Field(None, description="Optional status code to include")
    config: Optional[AssertionGenerationConfig] = Field(default=None, description="Generation configuration")


class TestSpecInput(BaseModel):
    """Input schema for test specification."""
    method: str = Field(..., description="HTTP method")
    path: str = Field(..., description="URL path")
    name: Optional[str] = Field(None, description="Test name")


class GenerateFromSpecRequest(BaseModel):
    """Request schema for generating assertions from test spec."""
    test_spec: TestSpecInput = Field(..., description="Test specification")
    response_analysis: Optional[ResponseDataInput] = Field(None, description="Optional response analysis for smarter assertions")


class AssertionGenerationResponse(BaseModel):
    """Response schema for assertion generation."""
    assertions: List[Dict[str, Any]] = Field(..., description="Generated assertions")
    count: int = Field(..., description="Number of assertions generated")
    config_used: AssertionGenerationConfig = Field(..., description="Configuration used for generation")
    success: bool = Field(default=True, description="Whether generation was successful")
    message: str = Field(default="Successfully generated assertions", description="Status message")


@router.post("/from-response", response_model=AssertionGenerationResponse, status_code=status.HTTP_200_OK)
async def generate_assertions_from_response(request: GenerateAssertionsRequest):
    """
    Generate assertions from response data.
    
    This endpoint analyzes actual response data (status code, headers, body, response time)
    and generates intelligent assertions that can be used in test cases.
    """
    try:
        # Convert request to the format expected by the generator
        response_data = {}
        
        if request.response_data.status_code is not None:
            response_data['status_code'] = request.response_data.status_code
        
        if request.response_data.headers:
            response_data['headers'] = request.response_data.headers
        
        if request.response_data.body is not None:
            response_data['body'] = request.response_data.body
        
        if request.response_data.response_time_ms is not None:
            response_data['response_time_ms'] = request.response_data.response_time_ms
        
        # Use provided config or default
        config = request.config or AssertionGenerationConfig()
        
        # Convert to options dict for the generator
        options = {
            'include_response_time': config.include_response_time,
            'include_headers': config.include_headers,
            'include_body_structure': config.include_body_structure,
            'include_data_types': config.include_data_types,
            'max_assertions': config.max_assertions
        }
        
        # Create generator with config
        generator = create_assertion_generator(
            max_depth=config.max_depth,
            max_array_size=config.max_array_size,
            include_nulls=config.include_nulls
        )
        
        # Generate assertions
        assertions = generator.generate_assertions_from_response(response_data, options)
        
        return AssertionGenerationResponse(
            assertions=assertions,
            count=len(assertions),
            config_used=config,
            success=True,
            message=f"Successfully generated {len(assertions)} assertions from response data"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate assertions: {str(e)}"
        )


@router.post("/from-json", response_model=AssertionGenerationResponse, status_code=status.HTTP_200_OK)
async def generate_assertions_from_json_data(request: GenerateFromJSONRequest):
    """
    Generate assertions from raw JSON data.
    
    This endpoint analyzes JSON data structure and generates assertions
    based on the data types, nested objects, arrays, and values present.
    Similar to the Go assertion generator functionality.
    """
    try:
        # Use provided config or default
        config = request.config or AssertionGenerationConfig()
        
        # Generate assertions using the convenience function
        assertions = generate_assertions_from_json(
            json_data=request.json_data,
            status_code=request.status_code,
            max_depth=config.max_depth,
            max_array_size=config.max_array_size,
            include_nulls=config.include_nulls
        )
        
        # Limit assertions if needed
        if len(assertions) > config.max_assertions:
            assertions = assertions[:config.max_assertions]
        
        return AssertionGenerationResponse(
            assertions=assertions,
            count=len(assertions),
            config_used=config,
            success=True,
            message=f"Successfully generated {len(assertions)} assertions from JSON data"
        )
    
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON data: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate assertions: {str(e)}"
        )


@router.post("/from-spec", response_model=AssertionGenerationResponse, status_code=status.HTTP_200_OK)
async def generate_assertions_from_test_spec(request: GenerateFromSpecRequest):
    """
    Generate assertions from test specification.
    
    This endpoint generates assertions based on the test specification (method, path)
    and optionally enhances them with analysis from actual response data.
    """
    try:
        # Convert test spec to dict
        test_spec_dict = {
            'method': request.test_spec.method,
            'path': request.test_spec.path,
            'name': request.test_spec.name
        }
        
        # Convert response analysis if provided
        response_analysis = None
        if request.response_analysis:
            response_analysis = {}
            if request.response_analysis.status_code is not None:
                response_analysis['status_code'] = request.response_analysis.status_code
            if request.response_analysis.headers:
                response_analysis['headers'] = request.response_analysis.headers
            if request.response_analysis.body is not None:
                response_analysis['body'] = request.response_analysis.body
            if request.response_analysis.response_time_ms is not None:
                response_analysis['response_time_ms'] = request.response_analysis.response_time_ms
        
        # Create generator
        generator = AssertionGenerator()
        
        # Generate assertions
        assertions = generator.generate_assertions_from_spec(test_spec_dict, response_analysis)
        
        # Use default config for response
        config = AssertionGenerationConfig()
        
        return AssertionGenerationResponse(
            assertions=assertions,
            count=len(assertions),
            config_used=config,
            success=True,
            message=f"Successfully generated {len(assertions)} assertions from test specification"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate assertions: {str(e)}"
        )


@router.get("/examples", response_model=Dict[str, Any])
async def get_assertion_examples():
    """
    Get example assertion generation requests and responses.
    
    This endpoint provides examples of different types of assertion generation
    scenarios and their expected results.
    """
    examples = {
        "simple_json_object": {
            "input": {
                "json_data": {"id": 1, "name": "John", "email": "john@example.com"},
                "status_code": 200
            },
            "description": "Generate assertions for a simple JSON object",
            "expected_assertion_types": ["status_code", "exists", "equals"]
        },
        "json_array": {
            "input": {
                "json_data": [
                    {"id": 1, "name": "John"},
                    {"id": 2, "name": "Jane"}
                ]
            },
            "description": "Generate assertions for a JSON array",
            "expected_assertion_types": ["exists", "equals"]
        },
        "nested_object": {
            "input": {
                "json_data": {
                    "user": {
                        "id": 1,
                        "profile": {
                            "name": "John",
                            "preferences": {"theme": "dark"}
                        }
                    }
                }
            },
            "description": "Generate assertions for nested JSON objects",
            "expected_assertion_types": ["exists", "equals"]
        },
        "response_data": {
            "input": {
                "response_data": {
                    "status_code": 201,
                    "headers": {"Content-Type": "application/json"},
                    "body": {"message": "Created successfully", "id": 123},
                    "response_time_ms": 150
                }
            },
            "description": "Generate assertions from full response data",
            "expected_assertion_types": ["status_code", "response_time", "header", "body"]
        },
        "test_spec": {
            "input": {
                "test_spec": {
                    "method": "POST",
                    "path": "/api/users"
                }
            },
            "description": "Generate assertions from test specification",
            "expected_assertion_types": ["status_code", "header", "body"]
        }
    }
    
    config_options = {
        "max_depth": "Maximum depth to traverse nested objects (1-10)",
        "max_array_size": "Maximum array elements to process (1-20)",
        "include_nulls": "Whether to include null value assertions",
        "include_response_time": "Include response time assertions",
        "include_headers": "Include header assertions", 
        "include_body_structure": "Include body structure assertions",
        "include_data_types": "Include data type assertions",
        "max_assertions": "Maximum number of assertions to generate (1-100)"
    }
    
    assertion_types = {
        "status_code": "Verifies HTTP status code",
        "exists": "Verifies that a field exists",
        "equals": "Verifies that a field equals a specific value",
        "response_time": "Verifies response time is within threshold",
        "header": "Verifies response header values",
        "body": "Verifies response body content"
    }
    
    return {
        "examples": examples,
        "config_options": config_options,
        "assertion_types": assertion_types,
        "supported_data_types": ["string", "number", "boolean", "null", "object", "array"],
        "tips": [
            "Use max_depth to control how deeply nested objects are analyzed",
            "Set max_array_size to limit processing of large arrays",
            "Enable include_nulls to assert on null values",
            "Combine response data with test specs for comprehensive assertions"
        ]
    }


@router.get("/config/defaults", response_model=AssertionGenerationConfig)
async def get_default_config():
    """Get the default configuration for assertion generation."""
    return AssertionGenerationConfig()
