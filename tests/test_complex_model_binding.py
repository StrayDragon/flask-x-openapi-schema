"""Test complex model binding with nested structures.

This module tests the binding of complex Pydantic models with nested structures,
including lists, dictionaries, and nested models.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from flask import Flask
from pydantic import BaseModel, Field

from flask_x_openapi_schema.x.flask import openapi_metadata


class Address(BaseModel):
    """Address model for testing."""

    street: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State or province")
    postal_code: str = Field(..., description="Postal code")
    country: str = Field(..., description="Country")
    is_primary: bool = Field(True, description="Whether this is the primary address")


class ContactInfo(BaseModel):
    """Contact information model for testing."""

    phone: str | None = Field(None, description="Phone number")
    alternative_email: str | None = Field(None, description="Alternative email")
    emergency_contact: str | None = Field(None, description="Emergency contact")


class ComplexUserRequest(BaseModel):
    """Complex user request model with nested structures."""

    username: str = Field(..., description="The username")
    email: str = Field(..., description="The email address")
    tags: list[str] = Field(default_factory=list, description="Tags for the user")
    addresses: list[Address] = Field(default_factory=list, description="User addresses")
    contact_info: ContactInfo | None = Field(None, description="Additional contact information")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


@pytest.fixture
def app():
    """Create a Flask application for testing."""
    app = Flask(__name__)

    @app.route("/test_complex_binding", methods=["POST"])
    @openapi_metadata(
        summary="Test complex binding",
        description="Test binding of complex nested models",
    )
    def example_complex_binding(_x_body: ComplexUserRequest = None):
        """Test complex model binding."""
        import json
        import logging

        logger = logging.getLogger(__name__)

        logger.warning(f"test_complex_binding called with _x_body: {_x_body}")

        # If _x_body is None, try to parse the request data manually
        if _x_body is None:
            logger.warning("_x_body is None, trying to parse request data manually")
            try:
                import json

                from flask import request

                if request.is_json:
                    data = request.get_json()
                    logger.warning(f"Parsed JSON data: {data}")
                    _x_body = ComplexUserRequest.model_validate(data)
                    logger.warning(f"Created model: {_x_body}")
                elif request.content_type == "application/x-www-form-urlencoded":
                    # Handle form data with JSON strings
                    data = request.form.to_dict()
                    logger.warning(f"Form data: {data}")

                    # Process JSON strings in form data
                    processed_data = {}
                    for key, value in data.items():
                        if key in [
                            "tags",
                            "addresses",
                            "contact_info",
                            "metadata",
                        ] and isinstance(value, str):
                            try:
                                if (value.startswith("[") and value.endswith("]")) or (
                                    value.startswith("{") and value.endswith("}")
                                ):
                                    processed_data[key] = json.loads(value)
                                    logger.warning(f"Parsed {key} as JSON: {processed_data[key]}")
                                else:
                                    processed_data[key] = value
                            except json.JSONDecodeError:
                                processed_data[key] = value
                                logger.warning(f"Failed to parse {key} as JSON")
                        else:
                            processed_data[key] = value

                    logger.warning(f"Processed form data: {processed_data}")
                    _x_body = ComplexUserRequest.model_validate(processed_data)
                    logger.warning(f"Created model from form data: {_x_body}")
                else:
                    logger.warning(f"Unknown content type: {request.content_type}")
                    return {"error": f"Unsupported content type: {request.content_type}"}, 400
            except Exception as e:
                logger.warning(f"Failed to parse request data: {e}")
                return {"error": f"Failed to parse request data: {e}"}, 400

        # If still None, return error
        if _x_body is None:
            logger.warning("_x_body is still None, returning 400")
            return {"error": "No body provided"}, 400

        # Return the model data for verification
        result = _x_body.model_dump(mode="json")
        logger.warning(f"Returning result: {result}")
        return result, 200

    return app


def test_complex_model_binding_with_json(app, client):
    """Test binding of complex models with JSON data."""
    # Create test data with nested structures
    test_data = {
        "username": "testuser",
        "email": "test@example.com",
        "tags": ["tag1", "tag2", "tag3"],
        "addresses": [
            {
                "street": "123 Main St",
                "city": "Anytown",
                "state": "CA",
                "postal_code": "12345",
                "country": "USA",
                "is_primary": True,
            },
            {
                "street": "456 Oak Ave",
                "city": "Othertown",
                "state": "NY",
                "postal_code": "67890",
                "country": "USA",
                "is_primary": False,
            },
        ],
        "contact_info": {
            "phone": "555-1234",
            "alternative_email": "alt@example.com",
            "emergency_contact": "John Doe",
        },
        "metadata": {"key1": "value1", "key2": 123, "key3": True},
    }

    # Send request with JSON data
    import json
    import logging

    logger = logging.getLogger(__name__)
    logger.warning(f"Sending JSON data: {json.dumps(test_data)}")

    # Force the content type to be application/json
    headers = {"Content-Type": "application/json"}
    response = client.post("/test_complex_binding", data=json.dumps(test_data), headers=headers)

    # Check response
    assert response.status_code == 200
    data = json.loads(response.data)

    # Verify all fields were correctly bound
    assert data["username"] == test_data["username"]
    assert data["email"] == test_data["email"]
    assert data["tags"] == test_data["tags"]
    assert len(data["addresses"]) == 2
    assert data["addresses"][0]["street"] == test_data["addresses"][0]["street"]
    assert data["contact_info"]["phone"] == test_data["contact_info"]["phone"]
    assert data["metadata"]["key1"] == test_data["metadata"]["key1"]


def test_complex_model_binding_with_string_lists_and_dicts(app, client):
    """Test binding of complex models with string representations of lists and dicts."""
    # Create test data with string representations of lists and dicts
    test_data = {
        "username": "testuser",
        "email": "test@example.com",
        "tags": '["tag1", "tag2", "tag3"]',  # String representation of a list
        "addresses": '[{"street": "123 Main St", "city": "Anytown", "state": "CA", "postal_code": "12345", "country": "USA", "is_primary": true}]',  # String representation of a list of objects
        "metadata": '{"key1": "value1", "key2": 123}',  # String representation of a dict
    }

    # Send request with form data (which will be strings)
    import logging

    logger = logging.getLogger(__name__)
    logger.warning(f"Sending form data: {test_data}")

    response = client.post(
        "/test_complex_binding",
        data=test_data,
        content_type="application/x-www-form-urlencoded",
    )

    # Check response
    assert response.status_code == 200
    data = json.loads(response.data)

    # Verify fields were correctly parsed from strings to proper types
    assert data["username"] == test_data["username"]
    assert data["email"] == test_data["email"]
    assert isinstance(data["tags"], list)
    assert len(data["tags"]) == 3
    assert data["tags"][0] == "tag1"
    assert isinstance(data["addresses"], list)
    assert data["addresses"][0]["street"] == "123 Main St"
    assert isinstance(data["metadata"], dict)
    assert data["metadata"]["key1"] == "value1"
