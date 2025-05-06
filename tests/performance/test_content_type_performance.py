"""Performance tests for content type handling."""

import io
import json

import pytest
from flask import Flask
from pydantic import BaseModel, Field
from werkzeug.datastructures import FileStorage

from flask_x_openapi_schema.core.content_type_utils import (
    FormUrlencodedStrategy,
    JsonContentTypeStrategy,
    MultipartFormDataStrategy,
)
from flask_x_openapi_schema.models.file_models import (
    FileField,
    ImageField,
)


@pytest.mark.no_cover
class SimpleModel(BaseModel):
    """Simple model for performance testing."""

    name: str = ""
    age: int = 0
    email: str = ""
    is_active: bool = True


@pytest.mark.no_cover
class ComplexModel(BaseModel):
    """Complex model for performance testing."""

    name: str = ""
    age: int = 0
    email: str = ""
    is_active: bool = True
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)
    nested: dict[str, dict[str, str]] = Field(default_factory=dict)
    scores: list[int] = Field(default_factory=list)


@pytest.mark.no_cover
class FileModel(BaseModel):
    """File model for performance testing."""

    file: FileField
    description: str = ""


@pytest.mark.no_cover
class ImageModel(BaseModel):
    """Image model for performance testing."""

    image: ImageField
    title: str = ""
    is_primary: bool = False


@pytest.mark.no_cover
class MultipleFilesModel(BaseModel):
    """Multiple files model for performance testing."""

    files: list[FileField]
    description: str = ""


@pytest.fixture
def app():
    """Create a Flask app for testing."""
    return Flask(__name__)


@pytest.fixture
def json_data_small():
    """Create a small JSON data sample."""
    return json.dumps({"name": "Test", "age": 30, "email": "test@example.com", "is_active": True})


@pytest.fixture
def json_data_medium():
    """Create a medium-sized JSON data sample."""
    return json.dumps(
        {
            "name": "Test",
            "age": 30,
            "email": "test@example.com",
            "is_active": True,
            "tags": ["tag1", "tag2", "tag3"],
            "metadata": {"key1": "value1", "key2": "value2"},
        }
    )


@pytest.fixture
def json_data_large():
    """Create a large JSON data sample."""
    data = {
        "name": "Test",
        "age": 30,
        "email": "test@example.com",
        "is_active": True,
        "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
        "metadata": {f"key{i}": f"value{i}" for i in range(20)},
        "nested": {f"section{i}": {f"key{j}": f"value{j}" for j in range(10)} for i in range(10)},
        "scores": list(range(100)),
    }
    return json.dumps(data)


@pytest.fixture
def form_data_small():
    """Create a small form data sample."""
    return {"name": "Test", "age": "30", "email": "test@example.com", "is_active": "true"}


@pytest.fixture
def form_data_medium():
    """Create a medium-sized form data sample."""
    return {
        "name": "Test",
        "age": "30",
        "email": "test@example.com",
        "is_active": "true",
        "tags": '["tag1", "tag2", "tag3"]',
        "metadata": '{"key1": "value1", "key2": "value2"}',
    }


@pytest.fixture
def form_data_large():
    """Create a large form data sample."""
    return {
        "name": "Test",
        "age": "30",
        "email": "test@example.com",
        "is_active": "true",
        "tags": json.dumps(["tag1", "tag2", "tag3", "tag4", "tag5"]),
        "metadata": json.dumps({f"key{i}": f"value{i}" for i in range(20)}),
        "nested": json.dumps({f"section{i}": {f"key{j}": f"value{j}" for j in range(10)} for i in range(10)}),
        "scores": json.dumps(list(range(100))),
    }


@pytest.fixture
def test_file_small():
    """Create a small test file."""
    return FileStorage(
        stream=io.BytesIO(b"Small test file content"),
        filename="small.txt",
        content_type="text/plain",
    )


@pytest.fixture
def test_file_medium():
    """Create a medium-sized test file."""
    # Create a 100KB file
    content = b"Medium test file content" * 5000
    return FileStorage(
        stream=io.BytesIO(content),
        filename="medium.txt",
        content_type="text/plain",
    )


@pytest.fixture
def test_file_large():
    """Create a large test file."""
    # Create a 1MB file
    content = b"Large test file content" * 50000
    return FileStorage(
        stream=io.BytesIO(content),
        filename="large.txt",
        content_type="text/plain",
    )


@pytest.mark.benchmark(group="json-strategy")
class TestJsonContentTypeStrategyPerformance:
    """Performance tests for JsonContentTypeStrategy."""

    def test_process_small_json(self, benchmark, app, json_data_small):
        """Test processing a small JSON request."""
        strategy = JsonContentTypeStrategy()

        def process_json():
            with app.test_request_context(
                "/",
                method="POST",
                data=json_data_small,
                content_type="application/json",
            ) as ctx:
                kwargs = {}
                return strategy.process_request(ctx.request, SimpleModel, "model", kwargs)

        result = benchmark(process_json)
        assert "model" in result
        assert isinstance(result["model"], SimpleModel)

    def test_process_medium_json(self, benchmark, app, json_data_medium):
        """Test processing a medium-sized JSON request."""
        strategy = JsonContentTypeStrategy()

        def process_json():
            with app.test_request_context(
                "/",
                method="POST",
                data=json_data_medium,
                content_type="application/json",
            ) as ctx:
                kwargs = {}
                return strategy.process_request(ctx.request, ComplexModel, "model", kwargs)

        result = benchmark(process_json)
        assert "model" in result
        assert isinstance(result["model"], ComplexModel)

    def test_process_large_json(self, benchmark, app, json_data_large):
        """Test processing a large JSON request."""
        strategy = JsonContentTypeStrategy()

        def process_json():
            with app.test_request_context(
                "/",
                method="POST",
                data=json_data_large,
                content_type="application/json",
            ) as ctx:
                kwargs = {}
                return strategy.process_request(ctx.request, ComplexModel, "model", kwargs)

        result = benchmark(process_json)
        assert "model" in result
        assert isinstance(result["model"], ComplexModel)


@pytest.mark.benchmark(group="form-strategy")
class TestFormUrlencodedStrategyPerformance:
    """Performance tests for FormUrlencodedStrategy."""

    def test_process_small_form(self, benchmark, app, form_data_small):
        """Test processing a small form request."""
        strategy = FormUrlencodedStrategy()

        def process_form():
            with app.test_request_context(
                "/",
                method="POST",
                data=form_data_small,
                content_type="application/x-www-form-urlencoded",
            ) as ctx:
                kwargs = {}
                return strategy.process_request(ctx.request, SimpleModel, "model", kwargs)

        result = benchmark(process_form)
        assert "model" in result
        assert isinstance(result["model"], SimpleModel)

    def test_process_medium_form(self, benchmark, app, form_data_medium):
        """Test processing a medium-sized form request."""
        strategy = FormUrlencodedStrategy()

        def process_form():
            with app.test_request_context(
                "/",
                method="POST",
                data=form_data_medium,
                content_type="application/x-www-form-urlencoded",
            ) as ctx:
                kwargs = {}
                return strategy.process_request(ctx.request, ComplexModel, "model", kwargs)

        result = benchmark(process_form)
        assert "model" in result
        assert isinstance(result["model"], ComplexModel)

    def test_process_large_form(self, benchmark, app, form_data_large):
        """Test processing a large form request."""
        strategy = FormUrlencodedStrategy()

        def process_form():
            with app.test_request_context(
                "/",
                method="POST",
                data=form_data_large,
                content_type="application/x-www-form-urlencoded",
            ) as ctx:
                kwargs = {}
                return strategy.process_request(ctx.request, ComplexModel, "model", kwargs)

        result = benchmark(process_form)
        assert "model" in result
        assert isinstance(result["model"], ComplexModel)


@pytest.mark.benchmark(group="multipart-strategy")
@pytest.mark.skip(reason="File upload performance tests need to be updated in the library")
class TestMultipartFormDataStrategyPerformance:
    """Performance tests for MultipartFormDataStrategy."""

    def test_process_small_file(self, benchmark, app, test_file_small):
        """Test processing a small file upload."""
        strategy = MultipartFormDataStrategy()

        def process_file():
            with app.test_request_context(
                "/",
                method="POST",
                data={"file": test_file_small, "description": "Small file"},
                content_type="multipart/form-data",
            ) as ctx:
                # Mock the files attribute
                ctx.request.files = {"file": test_file_small}
                ctx.request.form = {"description": "Small file"}

                kwargs = {}
                return strategy.process_request(ctx.request, FileModel, "model", kwargs)

        result = benchmark(process_file)
        assert "model" in result
        assert isinstance(result["model"], FileModel)

    def test_process_medium_file(self, benchmark, app, test_file_medium):
        """Test processing a medium-sized file upload."""
        strategy = MultipartFormDataStrategy()

        def process_file():
            with app.test_request_context(
                "/",
                method="POST",
                data={"file": test_file_medium, "description": "Medium file"},
                content_type="multipart/form-data",
            ) as ctx:
                # Mock the files attribute
                ctx.request.files = {"file": test_file_medium}
                ctx.request.form = {"description": "Medium file"}

                kwargs = {}
                return strategy.process_request(ctx.request, FileModel, "model", kwargs)

        result = benchmark(process_file)
        assert "model" in result
        assert isinstance(result["model"], FileModel)

    def test_process_large_file(self, benchmark, app, test_file_large):
        """Test processing a large file upload."""
        strategy = MultipartFormDataStrategy()

        def process_file():
            with app.test_request_context(
                "/",
                method="POST",
                data={"file": test_file_large, "description": "Large file"},
                content_type="multipart/form-data",
            ) as ctx:
                # Mock the files attribute
                ctx.request.files = {"file": test_file_large}
                ctx.request.form = {"description": "Large file"}

                kwargs = {}
                return strategy.process_request(ctx.request, FileModel, "model", kwargs)

        result = benchmark(process_file)
        assert "model" in result
        assert isinstance(result["model"], FileModel)
