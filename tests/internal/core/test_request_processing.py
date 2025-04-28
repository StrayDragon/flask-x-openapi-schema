"""Tests for request_processing module."""

from pydantic import BaseModel

from flask_x_openapi_schema.core.request_processing import preprocess_request_data


class TestPreprocessRequestData:
    """Tests for preprocess_request_data function."""

    def test_simple_data(self):
        """Test preprocessing simple data."""

        class SimpleModel(BaseModel):
            name: str
            age: int

        data = {"name": "John", "age": 30}
        result = preprocess_request_data(data, SimpleModel)

        assert result == data

    def test_list_field_with_string_json(self):
        """Test preprocessing list field with string JSON."""

        class ListModel(BaseModel):
            tags: list[str]

        # String that looks like a JSON array
        data = {"tags": '["tag1", "tag2", "tag3"]'}
        result = preprocess_request_data(data, ListModel)

        assert result["tags"] == ["tag1", "tag2", "tag3"]

    def test_list_field_with_invalid_json(self):
        """Test preprocessing list field with invalid JSON."""

        class ListModel(BaseModel):
            tags: list[str]

        # Invalid JSON string
        data = {"tags": "[tag1, tag2, tag3]"}
        result = preprocess_request_data(data, ListModel)

        # Should convert to a list with one element (the original string)
        assert result["tags"] == ["[tag1, tag2, tag3]"]

    def test_list_field_with_single_value(self):
        """Test preprocessing list field with a single value."""

        class ListModel(BaseModel):
            tags: list[str]

        # Single value for a list field
        data = {"tags": "tag1"}
        result = preprocess_request_data(data, ListModel)

        # Should convert to a list with one element
        assert result["tags"] == ["tag1"]

    def test_list_field_with_list_value(self):
        """Test preprocessing list field with a list value."""

        class ListModel(BaseModel):
            tags: list[str]

        # Already a list
        data = {"tags": ["tag1", "tag2", "tag3"]}
        result = preprocess_request_data(data, ListModel)

        # Should keep the list as is
        assert result["tags"] == ["tag1", "tag2", "tag3"]

    def test_dict_field_with_string_json(self):
        """Test preprocessing dict field with string JSON."""

        class DictModel(BaseModel):
            metadata: dict[str, str]

        # String that looks like a JSON object
        data = {"metadata": '{"key1": "value1", "key2": "value2"}'}
        result = preprocess_request_data(data, DictModel)

        assert result["metadata"] == {"key1": "value1", "key2": "value2"}

    def test_dict_field_with_invalid_json(self):
        """Test preprocessing dict field with invalid JSON."""

        class DictModel(BaseModel):
            metadata: dict[str, str]

        # Invalid JSON string
        data = {"metadata": "{key1: value1, key2: value2}"}
        result = preprocess_request_data(data, DictModel)

        # Should keep the original string
        assert result["metadata"] == "{key1: value1, key2: value2}"

    def test_dict_field_with_dict_value(self):
        """Test preprocessing dict field with a dict value."""

        class DictModel(BaseModel):
            metadata: dict[str, str]

        # Already a dict
        data = {"metadata": {"key1": "value1", "key2": "value2"}}
        result = preprocess_request_data(data, DictModel)

        # Should keep the dict as is
        assert result["metadata"] == {"key1": "value1", "key2": "value2"}

    def test_nested_model_field_with_string_json(self):
        """Test preprocessing nested model field with string JSON."""

        class NestedModel(BaseModel):
            key: str
            value: str

        class ParentModel(BaseModel):
            nested: NestedModel

        # String that looks like a JSON object
        data = {"nested": '{"key": "test_key", "value": "test_value"}'}
        result = preprocess_request_data(data, ParentModel)

        assert result["nested"] == {"key": "test_key", "value": "test_value"}

    def test_nested_model_field_with_invalid_json(self):
        """Test preprocessing nested model field with invalid JSON."""

        class NestedModel(BaseModel):
            key: str
            value: str

        class ParentModel(BaseModel):
            nested: NestedModel

        # Invalid JSON string
        data = {"nested": "{key: test_key, value: test_value}"}
        result = preprocess_request_data(data, ParentModel)

        # Should keep the original string
        assert result["nested"] == "{key: test_key, value: test_value}"

    def test_nested_model_field_with_dict_value(self):
        """Test preprocessing nested model field with a dict value."""

        class NestedModel(BaseModel):
            key: str
            value: str

        class ParentModel(BaseModel):
            nested: NestedModel

        # Already a dict
        data = {"nested": {"key": "test_key", "value": "test_value"}}
        result = preprocess_request_data(data, ParentModel)

        # Should keep the dict as is
        assert result["nested"] == {"key": "test_key", "value": "test_value"}

    def test_unknown_fields(self):
        """Test preprocessing with unknown fields."""

        class SimpleModel(BaseModel):
            name: str

        data = {"name": "John", "unknown": "value"}
        result = preprocess_request_data(data, SimpleModel)

        # Should keep unknown fields
        assert result["name"] == "John"
        assert result["unknown"] == "value"

    def test_missing_fields(self):
        """Test preprocessing with missing fields."""

        class SimpleModel(BaseModel):
            name: str
            age: int = 0

        data = {"name": "John"}
        result = preprocess_request_data(data, SimpleModel)

        # Should not add missing fields
        assert result == {"name": "John"}
        assert "age" not in result

    def test_non_model_input(self):
        """Test preprocessing with a non-model input."""

        # A class without model_fields
        class NonModel:
            def __init__(self, name):
                self.name = name

        data = {"name": "John"}
        result = preprocess_request_data(data, NonModel)

        # Should return data unchanged
        assert result == data
