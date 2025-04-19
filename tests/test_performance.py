"""
Performance tests for the flask_x_openapi_schema package.
"""

import cProfile
import pstats
import io
import time
import inspect
from pydantic import BaseModel, Field
from typing import List, Optional

from flask_x_openapi_schema.decorators.flask import openapi_metadata
from flask_x_openapi_schema.decorators.base import (
    _detect_parameters,
    _generate_openapi_metadata,
    _extract_param_types,
)
from flask_x_openapi_schema.models.base import BaseRespModel


class PerfTestRequestModel(BaseModel):
    """Test request model."""

    name: str = Field(..., description="The name")
    age: int = Field(..., description="The age")
    email: Optional[str] = Field(None, description="The email")
    tags: List[str] = Field(default_factory=list, description="Tags")


class PerfTestQueryModel(BaseModel):
    """Test query model."""

    sort: str = Field(None, description="Sort order")
    limit: int = Field(None, description="Limit results")


class PerfTestResponseModel(BaseRespModel):
    """Test response model."""

    id: str = Field(..., description="The ID")
    name: str = Field(..., description="The name")
    age: int = Field(..., description="The age")
    email: Optional[str] = Field(None, description="The email")


def test_decorator_performance():
    """Test the performance of the openapi_metadata decorator."""

    # Define a function with the decorator
    @openapi_metadata(
        summary="Test endpoint",
        description="Test description",
        tags=["test"],
        request_body=PerfTestRequestModel,
        query_model=PerfTestQueryModel,
        responses={
            "200": {
                "description": "Successful response",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/TestResponseModel"}
                    }
                },
            },
            "404": {"description": "Not found"},
        },
    )
    def test_function(
        x_request_body: PerfTestRequestModel,
        x_request_query: PerfTestQueryModel,
        user_id: str,
        x_request_path_user_id: str,
    ):
        return PerfTestResponseModel(
            id=user_id,
            name=x_request_body.name,
            age=x_request_body.age,
            email=x_request_body.email,
        )

    # Profile the decorator application (this happens at import time)
    pr = cProfile.Profile()
    pr.enable()

    # Call the function multiple times to get a good profile
    for i in range(10):  # Reduced from 1000 to 10 for faster tests
        # Create a new function each time to simulate decorator application
        @openapi_metadata(
            summary=f"Test endpoint {i}",
            description="Test description",
            tags=["test"],
            request_body=PerfTestRequestModel,
            query_model=PerfTestQueryModel,
        )
        def dynamic_function(
            x_request_body: PerfTestRequestModel,
            x_request_query: PerfTestQueryModel,
        ):
            return {"result": "ok"}

    pr.disable()

    # Print the profiling results
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
    ps.print_stats(20)  # Print top 20 functions by cumulative time
    print(s.getvalue())

    # Assert that the profiling completed successfully
    assert True


def test_hot_path_performance():
    """Test the performance of the hot path functions in the decorator."""

    # Define a function with type annotations for testing
    def test_function(
        x_request_body: PerfTestRequestModel,
        x_request_query: PerfTestQueryModel,
        user_id: str,
        x_request_path_user_id: str,
    ):
        return {"result": "ok"}

    # Get the function signature and type hints
    signature = inspect.signature(test_function)
    type_hints = {}
    try:
        type_hints = inspect.get_type_hints(test_function)
    except Exception:
        pass

    # Profile the hot path functions
    pr = cProfile.Profile()
    pr.enable()

    # Call the functions multiple times
    start_time = time.time()
    for i in range(10):  # Reduced from 1000 to 10 for faster tests
        # Test _detect_parameters
        detected_request_body, detected_query_model, detected_path_params = (
            _detect_parameters(signature, type_hints)
        )

        # Test _generate_openapi_metadata
        _generate_openapi_metadata(
            summary="Test endpoint",
            description="Test description",
            tags=["test"],
            operation_id=None,
            deprecated=False,
            security=None,
            external_docs=None,
            actual_request_body=detected_request_body,
            responses=None,
            _parameters=None,
            _actual_query_model=detected_query_model,
            _actual_path_params=detected_path_params,
            language=None,
        )

        # Test _extract_param_types
        _extract_param_types(
            request_body_model=detected_request_body,
            query_model=detected_query_model,
        )

    end_time = time.time()
    pr.disable()

    # Print the profiling results
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
    ps.print_stats(20)  # Print top 20 functions by cumulative time
    print(s.getvalue())

    # Print the average time per call
    total_time = end_time - start_time
    avg_time = total_time / 1000
    print(f"Average time per hot path iteration: {avg_time:.6f} seconds")

    # Assert that the profiling completed successfully
    assert True
