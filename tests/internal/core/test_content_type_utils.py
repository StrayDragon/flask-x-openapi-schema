"""Tests for content_type_utils module."""

import json

from flask import Flask
from pydantic import BaseModel, Field

from flask_x_openapi_schema.core.content_type_utils import (
    BinaryContentTypeStrategy,
    ContentTypeProcessor,
    ContentTypeRegistry,
    DefaultStrategy,
    FormUrlencodedStrategy,
    JsonContentTypeStrategy,
)
from flask_x_openapi_schema.models.file_models import FileField


class SampleModel(BaseModel):
    """Test model for content type tests."""

    name: str = ""
    age: int = 0


class FileUploadModel(BaseModel):
    """Test model for file upload tests."""

    file: FileField
    description: str = ""


class MultipleFieldsModel(BaseModel):
    """Test model with multiple fields."""

    name: str
    age: int
    email: str
    is_active: bool = True
    tags: list[str] = Field(default_factory=list)


class TestContentTypeRegistry:
    """Tests for ContentTypeRegistry class."""

    def test_singleton_instance(self):
        """Test that ContentTypeRegistry is a singleton."""
        registry1 = ContentTypeRegistry()
        registry2 = ContentTypeRegistry()
        assert registry1 is registry2

    def test_register_strategy(self):
        """Test registering a strategy."""
        registry = ContentTypeRegistry()
        registry._strategies = {}  # Reset for test
        registry._default_strategy = None

        registry.register(JsonContentTypeStrategy)
        assert len(registry._strategies) == 1
        assert isinstance(registry._strategies[JsonContentTypeStrategy], JsonContentTypeStrategy)

    def test_register_default_strategy(self):
        """Test registering a default strategy."""
        registry = ContentTypeRegistry()
        registry._strategies = {}  # Reset for test
        registry._default_strategy = None

        registry.register(DefaultStrategy, is_default=True)
        assert registry._default_strategy is not None
        assert isinstance(registry._default_strategy, DefaultStrategy)

    def test_get_strategy_for_content_type(self):
        """Test getting a strategy for a content type."""
        registry = ContentTypeRegistry()
        registry._strategies = {}  # Reset for test
        registry._default_strategy = None

        registry.register(JsonContentTypeStrategy)
        registry.register(DefaultStrategy, is_default=True)

        strategy = registry.get_strategy_for_content_type("application/json")
        assert isinstance(strategy, JsonContentTypeStrategy)

        # Test fallback to default strategy
        strategy = registry.get_strategy_for_content_type("unknown/content-type")
        assert isinstance(strategy, DefaultStrategy)


class TestJsonContentTypeStrategy:
    """Tests for JsonContentTypeStrategy class."""

    def setup_method(self):
        """Set up test environment."""
        self.app = Flask(__name__)
        self.strategy = JsonContentTypeStrategy()

    def test_can_handle(self):
        """Test can_handle method."""
        assert self.strategy.can_handle("application/json")
        assert self.strategy.can_handle("application/json; charset=utf-8")
        assert self.strategy.can_handle("text/json")
        assert not self.strategy.can_handle("text/plain")

    def test_process_request_valid_json(self):
        """Test processing a valid JSON request."""
        with self.app.test_request_context(
            "/",
            method="POST",
            data=json.dumps({"name": "Test", "age": 30}),
            content_type="application/json",
        ) as ctx:
            kwargs = {}
            result = self.strategy.process_request(ctx.request, SampleModel, "model", kwargs)
            assert "model" in result
            assert result["model"].name == "Test"
            assert result["model"].age == 30

    def test_process_request_invalid_json(self):
        """Test processing an invalid JSON request."""
        with self.app.test_request_context(
            "/",
            method="POST",
            data="invalid json",
            content_type="application/json",
        ) as ctx:
            kwargs = {}
            result = self.strategy.process_request(ctx.request, SampleModel, "model", kwargs)
            assert "model" in result
            # Should create an empty model instance
            assert isinstance(result["model"], SampleModel)


class TestBinaryContentTypeStrategy:
    """Tests for BinaryContentTypeStrategy class."""

    def setup_method(self):
        """Set up test environment."""
        self.app = Flask(__name__)
        self.strategy = BinaryContentTypeStrategy()

    def test_can_handle(self):
        """Test can_handle method."""
        assert self.strategy.can_handle("image/jpeg")
        assert self.strategy.can_handle("audio/mp3")
        assert self.strategy.can_handle("video/mp4")
        assert self.strategy.can_handle("application/octet-stream")
        assert self.strategy.can_handle("application/pdf")
        assert not self.strategy.can_handle("text/plain")

    def test_process_small_binary_file(self):
        """Test processing a small binary file."""
        test_data = b"test binary data"
        with self.app.test_request_context(
            "/",
            method="POST",
            data=test_data,
            content_type="application/octet-stream",
        ) as ctx:
            kwargs = {}
            result = self.strategy.process_request(ctx.request, FileUploadModel, "model", kwargs)
            assert "model" in result
            assert isinstance(result["model"], FileUploadModel)


class TestFormUrlencodedStrategy:
    """Tests for FormUrlencodedStrategy class."""

    def setup_method(self):
        """Set up test environment."""
        self.app = Flask(__name__)
        self.strategy = FormUrlencodedStrategy()

    def test_can_handle(self):
        """Test can_handle method."""
        assert self.strategy.can_handle("application/x-www-form-urlencoded")
        assert not self.strategy.can_handle("text/plain")

    def test_process_request_with_form_data(self):
        """Test processing a request with form data."""
        with self.app.test_request_context(
            "/",
            method="POST",
            data={"name": "Test", "age": "30"},
            content_type="application/x-www-form-urlencoded",
        ) as ctx:
            kwargs = {}
            result = self.strategy.process_request(ctx.request, SampleModel, "model", kwargs)
            assert "model" in result
            assert result["model"].name == "Test"
            assert result["model"].age == 30

    def test_extract_form_data(self):
        """Test extracting form data from request."""
        with self.app.test_request_context(
            "/",
            method="POST",
            data={"name": "Test", "age": "30"},
            content_type="application/x-www-form-urlencoded",
        ) as ctx:
            form_data = self.strategy._extract_form_data(ctx.request)
            assert form_data == {"name": "Test", "age": "30"}


class TestContentTypeProcessor:
    """Tests for ContentTypeProcessor class."""

    def setup_method(self):
        """Set up test environment."""
        self.app = Flask(__name__)
        self.processor = ContentTypeProcessor()

    def test_process_request_body_json(self):
        """Test processing a JSON request body."""
        with self.app.test_request_context(
            "/",
            method="POST",
            data=json.dumps({"name": "Test", "age": 30}),
            content_type="application/json",
        ) as ctx:
            kwargs = {}
            result = self.processor.process_request_body(ctx.request, SampleModel, "model", kwargs)
            assert "model" in result
            assert result["model"].name == "Test"
            assert result["model"].age == 30
