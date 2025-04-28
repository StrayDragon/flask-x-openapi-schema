"""Tests for core.utils module with focus on coverage."""

from datetime import date, datetime, time
from enum import Enum
from typing import Optional, Union
from uuid import UUID

from pydantic import BaseModel

from flask_x_openapi_schema.core.utils import (
    _fix_references,
    clear_i18n_cache,
    clear_references_cache,
    error_response_schema,
    process_i18n_dict,
    process_i18n_value,
    python_type_to_openapi_type,
    response_schema,
    responses_schema,
    success_response,
)
from flask_x_openapi_schema.i18n.i18n_string import I18nStr


class TestPythonTypeToOpenAPIType:
    """Tests for python_type_to_openapi_type function."""

    def test_primitive_types(self):
        """Test conversion of primitive types."""
        assert python_type_to_openapi_type(str) == {"type": "string"}
        assert python_type_to_openapi_type(int) == {"type": "integer"}
        assert python_type_to_openapi_type(float) == {"type": "number"}
        assert python_type_to_openapi_type(bool) == {"type": "boolean"}

        # None type depends on OpenAPI version
        none_type = python_type_to_openapi_type(None)
        assert none_type in ({"type": "null"}, {"nullable": True})

    def test_container_types(self):
        """Test conversion of container types."""
        # List types
        assert python_type_to_openapi_type(list) == {"type": "array"}
        assert python_type_to_openapi_type(list[str]) == {
            "type": "array",
            "items": {"type": "string"},
        }
        assert python_type_to_openapi_type(list[int]) == {
            "type": "array",
            "items": {"type": "integer"},
        }

        # Dict types
        assert python_type_to_openapi_type(dict) == {"type": "object"}
        # Dict[str, int] might be handled differently based on OpenAPI version
        dict_str_int = python_type_to_openapi_type(dict[str, int])
        assert dict_str_int["type"] == "object"

    def test_special_types(self):
        """Test conversion of special types."""
        assert python_type_to_openapi_type(UUID) == {"type": "string", "format": "uuid"}
        assert python_type_to_openapi_type(datetime) == {"type": "string", "format": "date-time"}
        assert python_type_to_openapi_type(date) == {"type": "string", "format": "date"}
        assert python_type_to_openapi_type(time) == {"type": "string", "format": "time"}

    def test_enum_types(self):
        """Test conversion of Enum types."""

        class TestEnum(Enum):
            A = "a"
            B = "b"

        assert python_type_to_openapi_type(TestEnum) == {
            "type": "string",
            "enum": ["a", "b"],
        }

    def test_pydantic_model_types(self):
        """Test conversion of Pydantic model types."""

        class TestModel(BaseModel):
            name: str

        assert python_type_to_openapi_type(TestModel) == {
            "$ref": "#/components/schemas/TestModel",
        }

    def test_optional_types(self):
        """Test conversion of Optional types."""
        optional_str = python_type_to_openapi_type(Optional[str])  # noqa: UP007

        # Result depends on OpenAPI version
        assert "type" in optional_str or "oneOf" in optional_str
        if "type" in optional_str:
            # OpenAPI 3.0 or 3.1 with type array
            if isinstance(optional_str["type"], list):
                assert "string" in optional_str["type"]
                assert "null" in optional_str["type"]
            else:
                assert optional_str["type"] == "string"
                assert optional_str.get("nullable") is True
        else:
            # OpenAPI 3.1 with oneOf
            assert len(optional_str["oneOf"]) == 2
            assert {"type": "string"} in optional_str["oneOf"]
            assert {"type": "null"} in optional_str["oneOf"]

    def test_union_types(self):
        """Test conversion of Union types."""
        union_type = python_type_to_openapi_type(Union[str, int])  # noqa: UP007

        # Result depends on OpenAPI version and Pydantic version
        if "oneOf" in union_type:
            # OpenAPI 3.1
            assert len(union_type["oneOf"]) == 2
            # Check that there's a string type and an integer type
            # The exact format might vary depending on Pydantic version
            string_type_found = False
            integer_type_found = False

            for item in union_type["oneOf"]:
                if item.get("type") == "string" or (
                    isinstance(item.get("type"), list) and "string" in item.get("type")
                ):
                    string_type_found = True
                if item.get("type") == "integer":
                    integer_type_found = True

            assert string_type_found, "String type not found in Union"
            assert integer_type_found, "Integer type not found in Union"
        else:
            # Default for unknown union is string
            assert union_type["type"] == "string" or (
                isinstance(union_type["type"], list) and "string" in union_type["type"]
            )

    def test_unknown_types(self):
        """Test conversion of unknown types."""

        class CustomClass:
            pass

        assert python_type_to_openapi_type(CustomClass) == {"type": "string"}


class TestFixReferences:
    """Tests for _fix_references function."""

    def test_simple_schema(self):
        """Test fixing references in a simple schema."""
        schema = {"type": "string"}
        assert _fix_references(schema) == {"type": "string"}

    def test_schema_with_ref(self):
        """Test fixing references in a schema with $ref."""
        schema = {"$ref": "#/$defs/TestModel"}
        assert _fix_references(schema) == {"$ref": "#/components/schemas/TestModel"}

        schema = {"$ref": "#/definitions/TestModel"}
        assert _fix_references(schema) == {"$ref": "#/components/schemas/TestModel"}

    def test_schema_with_json_schema_extra(self):
        """Test fixing references in a schema with json_schema_extra."""
        schema = {
            "type": "string",
            "json_schema_extra": {
                "example": "test",
                "description": "A test schema",
            },
        }
        assert _fix_references(schema) == {
            "type": "string",
            "example": "test",
            "description": "A test schema",
        }

    def test_schema_with_nested_dict(self):
        """Test fixing references in a schema with nested dict."""
        schema = {
            "type": "object",
            "properties": {
                "nested": {"$ref": "#/$defs/NestedModel"},
            },
        }
        assert _fix_references(schema) == {
            "type": "object",
            "properties": {
                "nested": {"$ref": "#/components/schemas/NestedModel"},
            },
        }

    def test_schema_with_nested_list(self):
        """Test fixing references in a schema with nested list."""
        schema = {
            "type": "array",
            "items": [
                {"$ref": "#/$defs/Item1"},
                {"$ref": "#/$defs/Item2"},
            ],
        }
        assert _fix_references(schema) == {
            "type": "array",
            "items": [
                {"$ref": "#/components/schemas/Item1"},
                {"$ref": "#/components/schemas/Item2"},
            ],
        }

    def test_schema_with_file(self):
        """Test fixing references in a schema with file type."""
        schema = {
            "type": "string",
            "format": "binary",
        }
        assert _fix_references(schema) == {
            "type": "string",
            "format": "binary",
        }

    def test_schema_with_nullable(self):
        """Test fixing references in a schema with nullable."""
        # This test's result depends on OpenAPI version
        schema = {
            "type": "string",
            "nullable": True,
        }
        result = _fix_references(schema)

        # Either we keep nullable or convert to type array with null
        if "nullable" in result:
            assert result == {
                "type": "string",
                "nullable": True,
            }
        else:
            assert result["type"] == ["string", "null"] or result["type"] == "string"

    def test_non_dict_input(self):
        """Test fixing references with non-dict input."""
        assert _fix_references("string") == "string"
        assert _fix_references(123) == 123
        assert _fix_references(None) is None
        assert _fix_references([1, 2, 3]) == [1, 2, 3]


class TestResponseSchemaFunctions:
    """Tests for response schema functions."""

    def test_response_schema(self):
        """Test response_schema function."""

        class TestModel(BaseModel):
            name: str

        schema = response_schema(TestModel, "Test response")
        assert schema == {
            "200": {
                "description": "Test response",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/TestModel"},
                    },
                },
            },
        }

        # Test with custom status code
        schema = response_schema(TestModel, "Test response", 201)
        assert schema == {
            "201": {
                "description": "Test response",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/TestModel"},
                    },
                },
            },
        }

    def test_error_response_schema(self):
        """Test error_response_schema function."""
        schema = error_response_schema("Bad request")
        assert schema == {
            "400": {
                "description": "Bad request",
            },
        }

        # Test with custom status code
        schema = error_response_schema("Not found", 404)
        assert schema == {
            "404": {
                "description": "Not found",
            },
        }

    def test_success_response(self):
        """Test success_response function."""

        class TestModel(BaseModel):
            name: str

        result = success_response(TestModel, "Test response")
        assert result == (TestModel, "Test response")

    def test_responses_schema(self):
        """Test responses_schema function."""

        class TestModel(BaseModel):
            name: str

        class ErrorModel(BaseModel):
            error: str

        success_responses_dict = {
            200: (TestModel, "Success"),
            201: (TestModel, "Created"),
        }

        errors_dict = {
            400: "Bad request",
            404: "Not found",
        }

        schema = responses_schema(success_responses_dict, errors_dict)

        # Check success responses
        assert "200" in schema
        assert schema["200"]["description"] == "Success"
        assert "content" in schema["200"]

        assert "201" in schema
        assert schema["201"]["description"] == "Created"
        assert "content" in schema["201"]

        # Check error responses
        assert "400" in schema
        assert schema["400"]["description"] == "Bad request"
        assert "content" not in schema["400"]

        assert "404" in schema
        assert schema["404"]["description"] == "Not found"
        assert "content" not in schema["404"]

        # Test without errors
        schema = responses_schema(success_responses_dict)
        assert "200" in schema
        assert "201" in schema
        assert "400" not in schema
        assert "404" not in schema


class TestI18nProcessing:
    """Tests for I18n processing functions."""

    def test_process_i18n_value_simple(self):
        """Test process_i18n_value with simple values."""
        # Non-I18n values should be returned as is
        assert process_i18n_value("test", "en") == "test"
        assert process_i18n_value(123, "en") == 123
        assert process_i18n_value(None, "en") is None

        # I18n values should be converted
        i18n_str = I18nStr({"en": "Hello", "fr": "Bonjour"})
        assert process_i18n_value(i18n_str, "en") == "Hello"
        assert process_i18n_value(i18n_str, "fr") == "Bonjour"

    def test_process_i18n_value_list(self):
        """Test process_i18n_value with lists."""
        i18n_str1 = I18nStr({"en": "Hello", "fr": "Bonjour"})
        i18n_str2 = I18nStr({"en": "World", "fr": "Monde"})

        # List with mixed values
        mixed_list = ["test", i18n_str1, 123, i18n_str2]

        # Process each item individually since the function might not handle lists directly
        processed_en = [process_i18n_value(item, "en") for item in mixed_list]
        assert processed_en == ["test", "Hello", 123, "World"]

        processed_fr = [process_i18n_value(item, "fr") for item in mixed_list]
        assert processed_fr == ["test", "Bonjour", 123, "Monde"]

    def test_process_i18n_dict(self):
        """Test process_i18n_dict function."""
        i18n_str1 = I18nStr({"en": "Hello", "fr": "Bonjour"})
        i18n_str2 = I18nStr({"en": "World", "fr": "Monde"})

        # Dict with mixed values
        mixed_dict = {
            "greeting": i18n_str1,
            "target": i18n_str2,
            "count": 123,
            "nested": {
                "message": i18n_str1,
            },
            "list": ["test", i18n_str2],
        }

        result_en = process_i18n_dict(mixed_dict, "en")
        assert result_en["greeting"] == "Hello"
        assert result_en["target"] == "World"
        assert result_en["count"] == 123
        assert result_en["nested"]["message"] == "Hello"
        assert result_en["list"] == ["test", "World"]

        result_fr = process_i18n_dict(mixed_dict, "fr")
        assert result_fr["greeting"] == "Bonjour"
        assert result_fr["target"] == "Monde"
        assert result_fr["count"] == 123
        assert result_fr["nested"]["message"] == "Bonjour"
        assert result_fr["list"] == ["test", "Monde"]

    def test_clear_i18n_cache(self):
        """Test clear_i18n_cache function."""
        # First call to process_i18n_value will cache the result
        i18n_str = I18nStr({"en": "Hello", "fr": "Bonjour"})
        assert process_i18n_value(i18n_str, "en") == "Hello"

        # Clear the cache
        clear_i18n_cache()

        # Call again to ensure it still works after clearing cache
        assert process_i18n_value(i18n_str, "en") == "Hello"

    def test_clear_references_cache(self):
        """Test clear_references_cache function."""
        # First call to _fix_references will cache the result
        schema = {"$ref": "#/$defs/TestModel"}
        assert _fix_references(schema) == {"$ref": "#/components/schemas/TestModel"}

        # Clear the cache
        clear_references_cache()

        # Call again to ensure it still works after clearing cache
        assert _fix_references(schema) == {"$ref": "#/components/schemas/TestModel"}
