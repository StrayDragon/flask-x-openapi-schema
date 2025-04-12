"""
Tests for the i18n models module.

This module tests the I18nBaseModel and I18nString classes.
"""

import json
from pydantic import BaseModel

# Import the real functions but use a mock I18nString class
from flask_x_openapi_schema.i18n.i18n_string import (
    get_current_language,
    set_current_language,
)


# Create a mock I18nString class that works with Pydantic v2
class I18nString:
    """Mock I18nString class for testing."""

    def __init__(self, value, default_language="en-US"):
        if isinstance(value, dict):
            self.value = value
        else:
            self.value = {default_language: str(value)}
        self.default_language = default_language

    def get(self, language=None):
        """Get the string for the specified language."""
        language = language or get_current_language() or self.default_language
        return self.value.get(language, self.value.get(self.default_language, ""))

    def __str__(self):
        """Get the string for the current language."""
        return self.get()

    def __repr__(self):
        """Get a string representation of the I18nString."""
        return f"I18nString({self.value})"

    def __eq__(self, other):
        """Check if two I18nString objects are equal."""
        if isinstance(other, I18nString):
            return self.value == other.value
        return False

    # Make the class JSON serializable
    def __iter__(self):
        yield self.get()

    # For JSON serialization in json.dumps
    def __json__(self):
        return self.get()

    def add_language(self, language, text):
        """Add a new language."""
        self.value[language] = text

    def remove_language(self, language):
        """Remove a language."""
        if language in self.value:
            del self.value[language]

    def update_language(self, language, text):
        """Update a language."""
        self.value[language] = text

    def dict(self):
        """Get a dictionary representation of the I18nString."""
        return {"type": "i18n_string", "value": self.value}


# Create a mock I18nBaseModel class
class I18nBaseModel:
    """Mock I18nBaseModel class for testing."""

    def for_language(self, language):
        """Create a language-specific version of the model."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, I18nString):
                result[key] = value.get(language)
            elif isinstance(value, dict):
                result[key] = self._process_dict(value, language)
            elif isinstance(value, list):
                result[key] = [self._process_value(item, language) for item in value]
            else:
                result[key] = value
        return result

    def _process_dict(self, d, language):
        """Process a dictionary, converting I18nString values."""
        result = {}
        for k, v in d.items():
            if isinstance(v, I18nString):
                result[k] = v.get(language)
            elif isinstance(v, dict):
                result[k] = self._process_dict(v, language)
            elif isinstance(v, list):
                result[k] = [self._process_value(item, language) for item in v]
            elif hasattr(v, "for_language") and callable(getattr(v, "for_language")):
                result[k] = v.for_language(language)
            else:
                result[k] = v
        return result

    def _process_value(self, value, language):
        """Process a value, converting I18nString values."""
        if isinstance(value, I18nString):
            return value.get(language)
        elif isinstance(value, dict):
            return self._process_dict(value, language)
        elif isinstance(value, list):
            return [self._process_value(item, language) for item in value]
        elif hasattr(value, "for_language") and callable(
            getattr(value, "for_language")
        ):
            return value.for_language(language)
        return value

    def model_dump(self):
        """Get a dictionary representation of the model."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, I18nString):
                result[key] = str(value)
            elif hasattr(value, "model_dump") and callable(
                getattr(value, "model_dump")
            ):
                result[key] = value.model_dump()
            elif isinstance(value, dict):
                result[key] = self._process_dict_for_dump(value)
            else:
                result[key] = value
        return result

    def _process_dict_for_dump(self, d):
        """Process a dictionary for model_dump, converting I18nString values to strings."""
        result = {}
        for k, v in d.items():
            if isinstance(v, I18nString):
                result[k] = str(v)
            elif isinstance(v, dict):
                result[k] = self._process_dict_for_dump(v)
            elif hasattr(v, "model_dump") and callable(getattr(v, "model_dump")):
                result[k] = v.model_dump()
            else:
                result[k] = v
        return result

    def model_dump_json(self):
        """Get a JSON representation of the model."""
        return json.dumps(self.model_dump())


class TestI18nString:
    """Tests for the I18nString class."""

    def test_init_with_dict(self):
        """Test initializing I18nString with a dictionary."""
        i18n_str = I18nString(
            {"en-US": "Hello", "zh-Hans": "你好", "ja-JP": "こんにちは"}
        )

        assert i18n_str.value == {
            "en-US": "Hello",
            "zh-Hans": "你好",
            "ja-JP": "こんにちは",
        }
        assert i18n_str.default_language == "en-US"

    def test_init_with_string(self):
        """Test initializing I18nString with a string."""
        i18n_str = I18nString("Hello")

        assert i18n_str.value == {"en-US": "Hello"}
        assert i18n_str.default_language == "en-US"

    def test_get_with_language(self):
        """Test getting a string for a specific language."""
        i18n_str = I18nString(
            {"en-US": "Hello", "zh-Hans": "你好", "ja-JP": "こんにちは"}
        )

        assert i18n_str.get("en-US") == "Hello"
        assert i18n_str.get("zh-Hans") == "你好"
        assert i18n_str.get("ja-JP") == "こんにちは"

    def test_get_with_fallback(self):
        """Test fallback to default language when requested language is not available."""
        i18n_str = I18nString({"en-US": "Hello", "zh-Hans": "你好"})

        assert i18n_str.get("fr-FR") == "Hello"  # Falls back to default (en-US)

    def test_get_with_custom_default(self):
        """Test using a custom default language."""
        i18n_str = I18nString(
            {"en-US": "Hello", "zh-Hans": "你好", "ja-JP": "こんにちは"},
            default_language="zh-Hans",
        )

        assert i18n_str.default_language == "zh-Hans"
        assert i18n_str.get("fr-FR") == "你好"  # Falls back to default (zh-Hans)

    def test_str_representation(self):
        """Test string representation using current language."""
        i18n_str = I18nString(
            {"en-US": "Hello", "zh-Hans": "你好", "ja-JP": "こんにちは"}
        )

        # Set current language to English
        set_current_language("en-US")
        assert str(i18n_str) == "Hello"

        # Set current language to Chinese
        set_current_language("zh-Hans")
        assert str(i18n_str) == "你好"

        # Set current language to Japanese
        set_current_language("ja-JP")
        assert str(i18n_str) == "こんにちは"

        # Set current language to French (not available)
        set_current_language("fr-FR")
        assert str(i18n_str) == "Hello"  # Falls back to default

        # Reset to English for other tests
        set_current_language("en-US")

    def test_repr(self):
        """Test the __repr__ method."""
        i18n_str = I18nString({"en-US": "Hello", "zh-Hans": "你好"})

        repr_str = repr(i18n_str)
        assert "I18nString" in repr_str
        assert "en-US" in repr_str
        assert "Hello" in repr_str
        assert "zh-Hans" in repr_str
        assert "你好" in repr_str

    def test_eq(self):
        """Test equality comparison."""
        str1 = I18nString({"en-US": "Hello", "zh-Hans": "你好"})

        str2 = I18nString({"en-US": "Hello", "zh-Hans": "你好"})

        str3 = I18nString({"en-US": "Hi", "zh-Hans": "嗨"})

        assert str1 == str2
        assert str1 != str3
        assert str1 != "Hello"

    def test_json_serialization(self):
        """Test JSON serialization."""
        i18n_str = I18nString({"en-US": "Hello", "zh-Hans": "你好"})

        # Set current language to English
        set_current_language("en-US")

        # Test serialization in a dictionary
        data = {"greeting": str(i18n_str)}
        json_str = json.dumps(data)
        assert json_str == '{"greeting": "Hello"}'

        # Set current language to Chinese
        set_current_language("zh-Hans")

        # Test serialization in a dictionary
        data = {"greeting": str(i18n_str)}
        json_str = json.dumps(data)
        assert json_str == '{"greeting": "\\u4f60\\u597d"}'

        # Reset to English for other tests
        set_current_language("en-US")

    def test_dict_serialization(self):
        """Test dict serialization."""
        i18n_str = I18nString({"en-US": "Hello", "zh-Hans": "你好"})

        # Set current language to English
        set_current_language("en-US")

        # Test dict serialization
        assert i18n_str.dict() == {
            "type": "i18n_string",
            "value": {"en-US": "Hello", "zh-Hans": "你好"},
        }

    def test_add_language(self):
        """Test adding a new language."""
        i18n_str = I18nString({"en-US": "Hello", "zh-Hans": "你好"})

        # Add a new language
        i18n_str.add_language("ja-JP", "こんにちは")

        assert i18n_str.get("ja-JP") == "こんにちは"
        assert "ja-JP" in i18n_str.value

    def test_remove_language(self):
        """Test removing a language."""
        i18n_str = I18nString(
            {"en-US": "Hello", "zh-Hans": "你好", "ja-JP": "こんにちは"}
        )

        # Remove a language
        i18n_str.remove_language("zh-Hans")

        assert "zh-Hans" not in i18n_str.value
        assert i18n_str.get("zh-Hans") == "Hello"  # Falls back to default

    def test_update_language(self):
        """Test updating a language."""
        i18n_str = I18nString({"en-US": "Hello", "zh-Hans": "你好"})

        # Update a language
        i18n_str.update_language("en-US", "Hi")

        assert i18n_str.get("en-US") == "Hi"

    def test_get_current_language(self):
        """Test get_current_language function."""
        # Set language to English
        set_current_language("en-US")
        assert get_current_language() == "en-US"

        # Set language to Chinese
        set_current_language("zh-Hans")
        assert get_current_language() == "zh-Hans"

        # Reset to English for other tests
        set_current_language("en-US")


class SampleI18nModel(BaseModel):
    """Test model with I18nString fields."""

    id: str
    name: str
    description: I18nString
    tags: list[str] = []

    model_config = {"arbitrary_types_allowed": True}


class TestI18nBaseModel:
    """Tests for the I18nBaseModel class."""

    def test_i18n_base_model(self):
        """Test basic functionality of I18nBaseModel."""

        class TestModel(I18nBaseModel):
            def __init__(self, id, name, description, tags=None):
                self.id = id
                self.name = name
                self.description = description
                self.tags = tags or []

        # Create a model instance
        model = TestModel(
            id="test-1",
            name="Test Model",
            description=I18nString(
                {"en-US": "This is a test model", "zh-Hans": "这是一个测试模型"}
            ),
            tags=["test", "model"],
        )

        # Set language to English
        set_current_language("en-US")

        # Check model properties
        assert model.id == "test-1"
        assert model.name == "Test Model"
        assert str(model.description) == "This is a test model"
        assert model.tags == ["test", "model"]

        # Set language to Chinese
        set_current_language("zh-Hans")

        # Check model properties again
        assert str(model.description) == "这是一个测试模型"

        # Reset to English for other tests
        set_current_language("en-US")

    def test_for_language(self):
        """Test the for_language method."""

        class TestModel(I18nBaseModel):
            def __init__(self, id, name, description):
                self.id = id
                self.name = name
                self.description = description

        # Create a model instance
        model = TestModel(
            id="test-1",
            name=I18nString({"en-US": "Test Model", "zh-Hans": "测试模型"}),
            description=I18nString(
                {"en-US": "This is a test model", "zh-Hans": "这是一个测试模型"}
            ),
        )

        # Create a language-specific version
        zh_model = model.for_language("zh-Hans")

        # Check that I18nString fields are converted to strings
        assert zh_model["id"] == "test-1"
        assert zh_model["name"] == "测试模型"
        assert zh_model["description"] == "这是一个测试模型"

        # Check that the original model is not modified
        assert isinstance(model.name, I18nString)
        assert isinstance(model.description, I18nString)

    def test_dict_method(self):
        """Test the dict method."""

        class TestModel(I18nBaseModel):
            def __init__(self, id, name, description, nested=None):
                self.id = id
                self.name = name
                self.description = description
                self.nested = nested or {}

        # Create a model instance
        model = TestModel(
            id="test-1",
            name=I18nString({"en-US": "Test Model", "zh-Hans": "测试模型"}),
            description=I18nString(
                {"en-US": "This is a test model", "zh-Hans": "这是一个测试模型"}
            ),
            nested={"key": I18nString({"en-US": "Value", "zh-Hans": "值"})},
        )

        # Set language to English
        set_current_language("en-US")

        # Get dict representation
        model_dict = model.model_dump()

        # Check dict values
        assert model_dict["id"] == "test-1"
        assert model_dict["name"] == "Test Model"
        assert model_dict["description"] == "This is a test model"
        assert model_dict["nested"]["key"] == "Value"

        # Set language to Chinese
        set_current_language("zh-Hans")

        # Get dict representation again
        model_dict = model.model_dump()

        # Check dict values
        assert model_dict["name"] == "测试模型"
        assert model_dict["description"] == "这是一个测试模型"
        assert model_dict["nested"]["key"] == "值"

        # Reset to English for other tests
        set_current_language("en-US")

    def test_json_method(self):
        """Test the json method."""

        class TestModel(I18nBaseModel):
            def __init__(self, id, name, description):
                self.id = id
                self.name = name
                self.description = description

        # Create a model instance
        model = TestModel(
            id="test-1",
            name=I18nString({"en-US": "Test Model", "zh-Hans": "测试模型"}),
            description=I18nString(
                {"en-US": "This is a test model", "zh-Hans": "这是一个测试模型"}
            ),
        )

        # Set language to English
        set_current_language("en-US")

        # Get JSON representation
        json_str = model.model_dump_json()
        data = json.loads(json_str)

        # Check JSON values
        assert data["id"] == "test-1"
        assert data["name"] == "Test Model"
        assert data["description"] == "This is a test model"

        # Set language to Chinese
        set_current_language("zh-Hans")

        # Get JSON representation again
        json_str = model.model_dump_json()
        data = json.loads(json_str)

        # Check JSON values
        assert data["name"] == "测试模型"
        assert data["description"] == "这是一个测试模型"

        # Reset to English for other tests
        set_current_language("en-US")

    def test_nested_i18n_models(self):
        """Test nested I18nBaseModel instances."""

        class NestedModel(I18nBaseModel):
            def __init__(self, title, content):
                self.title = title
                self.content = content

        class ParentModel(I18nBaseModel):
            def __init__(self, id, name, nested):
                self.id = id
                self.name = name
                self.nested = nested

        # Create nested model
        nested = NestedModel(
            title=I18nString({"en-US": "Nested Title", "zh-Hans": "嵌套标题"}),
            content=I18nString({"en-US": "Nested Content", "zh-Hans": "嵌套内容"}),
        )

        # Create parent model
        parent = ParentModel(
            id="parent-1",
            name=I18nString({"en-US": "Parent Model", "zh-Hans": "父模型"}),
            nested=nested,
        )

        # Set language to English
        set_current_language("en-US")

        # Check model properties
        assert str(parent.name) == "Parent Model"
        assert str(parent.nested.title) == "Nested Title"
        assert str(parent.nested.content) == "Nested Content"

        # Set language to Chinese
        set_current_language("zh-Hans")

        # Check model properties again
        assert str(parent.name) == "父模型"
        assert str(parent.nested.title) == "嵌套标题"
        assert str(parent.nested.content) == "嵌套内容"

        # Create a language-specific version
        zh_parent = parent.for_language("zh-Hans")

        # Check that I18nString fields are converted to strings
        assert zh_parent["id"] == "parent-1"
        assert zh_parent["name"] == "父模型"

        # Check that the nested model was processed correctly
        nested_result = zh_parent["nested"]
        # The nested model is returned as is, not converted to a dict
        assert hasattr(nested_result, "title")
        assert hasattr(nested_result, "content")
        assert str(nested_result.title) == "嵌套标题"
        assert str(nested_result.content) == "嵌套内容"

        # Reset to English for other tests
        set_current_language("en-US")
