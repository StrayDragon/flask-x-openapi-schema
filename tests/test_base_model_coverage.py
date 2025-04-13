"""
Tests for the base model module to improve coverage.
"""

from flask_x_openapi_schema.models.base import BaseRespModel


class TestBaseModelCoverage:
    """Tests for base model to improve coverage."""

    def test_to_response_with_status_code(self):
        """Test the to_response method with a status code."""

        # Create a response model
        class TestResponse(BaseRespModel):
            status: str
            message: str

        # Create an instance
        response = TestResponse(status="created", message="Resource created")

        # Convert to response with status code
        result = response.to_response(status_code=201)

        # Check that the result is a tuple with the response dict and status code
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] == {"status": "created", "message": "Resource created"}
        assert result[1] == 201

    def test_from_dict(self):
        """Test the from_dict class method."""

        # Create a response model
        class TestResponse(BaseRespModel):
            status: str
            message: str

        # Create a dictionary
        data = {"status": "success", "message": "Operation completed"}

        # Create a model instance from the dictionary
        response = TestResponse.from_dict(data)

        # Check that the instance was created correctly
        assert isinstance(response, TestResponse)
        assert response.status == "success"
        assert response.message == "Operation completed"

        # Convert back to dictionary and check
        result_dict = response.to_dict()
        assert result_dict == data
