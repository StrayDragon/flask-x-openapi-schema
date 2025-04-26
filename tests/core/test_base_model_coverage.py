"""Tests for the base model to improve coverage."""

from __future__ import annotations

from pydantic import Field

from flask_x_openapi_schema.models.base import BaseRespModel


class TestBaseModelCoverage:
    """Tests for BaseRespModel to improve coverage."""

    def test_from_dict(self):
        """Test the from_dict class method."""

        # Create a test model
        class TestModel(BaseRespModel):
            id: str = Field(..., description="The ID")
            name: str = Field(..., description="The name")
            age: int | None = Field(None, description="The age")

        # Create a dictionary
        data = {"id": "123", "name": "Test", "age": 30}

        # Create a model from the dictionary
        model = TestModel.from_dict(data)

        # Check that the model was created correctly
        assert model.id == "123"
        assert model.name == "Test"
        assert model.age == 30

    def test_to_dict(self):
        """Test the to_dict method."""

        # Create a test model
        class TestModel(BaseRespModel):
            id: str = Field(..., description="The ID")
            name: str = Field(..., description="The name")
            age: int | None = Field(None, description="The age")

        # Create a model instance
        model = TestModel(id="123", name="Test", age=30)

        # Convert to dictionary
        data = model.to_dict()

        # Check that the dictionary was created correctly
        assert data["id"] == "123"
        assert data["name"] == "Test"
        assert data["age"] == 30

        # Test with None values
        model = TestModel(id="123", name="Test")
        data = model.to_dict()
        assert "age" not in data

    def test_to_response(self):
        """Test the to_response method."""

        # Create a test model
        class TestModel(BaseRespModel):
            id: str = Field(..., description="The ID")
            name: str = Field(..., description="The name")
            age: int | None = Field(None, description="The age")

        # Create a model instance
        model = TestModel(id="123", name="Test", age=30)

        # Convert to response without status code
        response = model.to_response()
        assert isinstance(response, dict)
        assert response["id"] == "123"
        assert response["name"] == "Test"
        assert response["age"] == 30

        # Convert to response with status code
        response = model.to_response(status_code=201)
        assert isinstance(response, tuple)
        assert len(response) == 2
        assert response[0]["id"] == "123"
        assert response[0]["name"] == "Test"
        assert response[0]["age"] == 30
        assert response[1] == 201
