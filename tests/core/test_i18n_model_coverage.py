"""
Tests for the i18n_model module to improve coverage.
"""

import json
from pydantic import Field
from typing import Optional, List, Dict, Any

from flask_x_openapi_schema.i18n.i18n_model import I18nBaseModel
from flask_x_openapi_schema.i18n.i18n_string import I18nStr, set_current_language


class TestI18nModelCoverage:
    """Tests for I18nBaseModel to improve coverage."""

    def test_i18n_base_model_basic(self):
        """Test basic functionality of I18nBaseModel."""

        # Create a model class that inherits from I18nBaseModel
        class TestModel(I18nBaseModel):
            name: I18nStr = Field(..., description="The name")
            description: Optional[I18nStr] = Field(None, description="The description")
            tags: List[str] = Field(default_factory=list, description="Tags")
            metadata: Dict[str, Any] = Field(
                default_factory=dict, description="Metadata"
            )

        # Create a model instance with I18nStr objects
        model = TestModel(
            name=I18nStr("Test"),
            description=I18nStr("This is a test"),
            tags=["test", "example"],
            metadata={"key": "value"},
        )

        # Check that the model was created correctly
        assert str(model.name) == "Test"
        assert str(model.description) == "This is a test"
        assert model.tags == ["test", "example"]
        assert model.metadata == {"key": "value"}

        # Create a model instance with I18nStr objects
        model = TestModel(
            name=I18nStr({"en-US": "Test", "zh-Hans": "测试"}),
            description=I18nStr({"en-US": "This is a test", "zh-Hans": "这是一个测试"}),
            tags=["test", "example"],
            metadata={"key": "value"},
        )

        # Check that the model was created correctly
        assert str(model.name) == "Test"
        assert str(model.description) == "This is a test"

        # Change the language and check again
        set_current_language("zh-Hans")
        assert str(model.name) == "测试"
        assert str(model.description) == "这是一个测试"

        # Reset the language to English for other tests
        set_current_language("en-US")

    def test_i18n_base_model_serialization(self):
        """Test serialization of I18nBaseModel."""

        # Create a model class that inherits from I18nBaseModel
        class TestModel(I18nBaseModel):
            name: I18nStr = Field(..., description="The name")
            description: Optional[I18nStr] = Field(None, description="The description")

        # Create a model instance with I18nStr objects
        model = TestModel(
            name=I18nStr({"en-US": "Test", "zh-Hans": "测试"}),
            description=I18nStr({"en-US": "This is a test", "zh-Hans": "这是一个测试"}),
        )

        # Serialize the model to a dictionary
        data = model.model_dump()

        # Check that the dictionary contains the correct values
        assert data["name"] == "Test"
        assert data["description"] == "This is a test"

        # Change the language and serialize again
        set_current_language("zh-Hans")
        data = model.model_dump()

        # Check that the dictionary contains the correct values
        assert data["name"] == "测试"
        assert data["description"] == "这是一个测试"

        # Reset the language to English for other tests
        set_current_language("en-US")

    def test_i18n_base_model_json(self):
        """Test JSON serialization of I18nBaseModel."""

        # Create a model class that inherits from I18nBaseModel
        class TestModel(I18nBaseModel):
            name: I18nStr = Field(..., description="The name")
            description: Optional[I18nStr] = Field(None, description="The description")

        # Create a model instance with I18nStr objects
        model = TestModel(
            name=I18nStr({"en-US": "Test", "zh-Hans": "测试"}),
            description=I18nStr({"en-US": "This is a test", "zh-Hans": "这是一个测试"}),
        )

        # Serialize the model to JSON
        json_str = model.model_dump_json()
        data = json.loads(json_str)

        # Check that the JSON string contains the correct values
        assert data["name"] == "Test"
        assert data["description"] == "This is a test"

        # Change the language and serialize again
        set_current_language("zh-Hans")
        json_str = model.model_dump_json()
        data = json.loads(json_str)

        # Check that the JSON string contains the correct values
        assert data["name"] == "测试"
        assert data["description"] == "这是一个测试"

        # Reset the language to English for other tests
        set_current_language("en-US")
