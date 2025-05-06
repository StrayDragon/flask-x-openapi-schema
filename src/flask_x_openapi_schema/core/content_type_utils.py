"""Content type processing utilities.

This module provides utilities for processing content types in HTTP requests and responses.
It includes classes and functions for detecting content types, handling file uploads,
and processing request data based on content types.
"""

import io
import json
import tempfile
import urllib
from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path
from typing import Any, Self

from flask import make_response
from pydantic import BaseModel, ValidationError
from werkzeug.datastructures import FileStorage

from flask_x_openapi_schema.core.error_handlers import (
    create_error_response,
    create_status_error_response,
    handle_request_validation_error,
    handle_validation_error,
)
from flask_x_openapi_schema.core.logger import get_logger
from flask_x_openapi_schema.core.request_extractors import ModelFactory, safe_operation
from flask_x_openapi_schema.core.request_processing import preprocess_request_data
from flask_x_openapi_schema.models.base import BaseErrorResponse
from flask_x_openapi_schema.models.content_types import (
    RequestContentTypes,
)
from flask_x_openapi_schema.models.file_models import FileField


class ContentTypeStrategy(ABC):
    """Abstract base class for content type processing strategies.

    This class defines the interface for content type processing strategies.
    Each strategy handles a specific content type or category of content types.
    """

    @abstractmethod
    def can_handle(self, content_type: str) -> bool:
        """Check if this strategy can handle the given content type.

        Args:
            content_type: The content type to check.

        Returns:
            bool: True if this strategy can handle the content type, False otherwise.

        """

    @abstractmethod
    def process_request(
        self, request: Any, model: type[BaseModel], param_name: str, kwargs: dict[str, Any]
    ) -> dict[str, Any]:
        """Process a request with this content type.

        Args:
            request: The request object.
            model: The model to validate the request data against.
            param_name: The parameter name to bind the model instance to.
            kwargs: The keyword arguments to update.

        Returns:
            Dict[str, Any]: Updated kwargs dictionary with the model instance.

        """


class JsonContentTypeStrategy(ContentTypeStrategy):
    """Strategy for processing JSON content types."""

    def can_handle(self, content_type: str) -> bool:
        """Check if this strategy can handle the given content type.

        Args:
            content_type: The content type to check.

        Returns:
            bool: True if this is a JSON content type, False otherwise.

        """
        return "application/json" in content_type or "json" in content_type

    def process_request(
        self, request: Any, model: type[BaseModel], param_name: str, kwargs: dict[str, Any]
    ) -> dict[str, Any]:
        """Process a JSON request.

        Args:
            request: The request object.
            model: The model to validate the request data against.
            param_name: The parameter name to bind the model instance to.
            kwargs: The keyword arguments to update.

        Returns:
            Dict[str, Any]: Updated kwargs dictionary with the model instance.

        """
        logger = get_logger(__name__)
        logger.debug(f"Processing JSON request for {param_name} with model {model.__name__}")

        json_data = request.get_json(silent=True)
        if json_data:
            try:
                model_instance = model.model_validate(json_data)
                kwargs[param_name] = model_instance
            except ValidationError as e:
                logger.warning(f"Validation error for {model.__name__}: {e}")

                error_response = handle_validation_error(e)

                return make_response(*error_response)
            except Exception as e:
                logger.exception(f"Failed to validate JSON data against model {model.__name__}", exc_info=e)

                error_response = handle_request_validation_error(model.__name__, e)

                return make_response(*error_response)
            else:
                return kwargs

        try:
            model_instance = model()
            kwargs[param_name] = model_instance
        except Exception as e:
            logger.exception(f"Failed to create empty model instance for {model.__name__}")

            error_response = create_status_error_response(
                status_code=500,
                message=f"Failed to create instance of {model.__name__}",
                details={"error": str(e)},
            )

            return make_response(*error_response)

        return kwargs


class MultipartFormDataStrategy(ContentTypeStrategy):
    """Strategy for processing multipart/form-data content types."""

    def can_handle(self, content_type: str) -> bool:
        """Check if this strategy can handle the given content type.

        Args:
            content_type: The content type to check.

        Returns:
            bool: True if this is a multipart/form-data content type, False otherwise.

        """
        return "multipart/form-data" in content_type

    def process_request(
        self, request: Any, model: type[BaseModel], param_name: str, kwargs: dict[str, Any]
    ) -> dict[str, Any]:
        """Process a multipart/form-data request.

        Args:
            request: The request object.
            model: The model to validate the request data against.
            param_name: The parameter name to bind the model instance to.
            kwargs: The keyword arguments to update.

        Returns:
            Dict[str, Any]: Updated kwargs dictionary with the model instance.

        """
        logger = get_logger(__name__)
        logger.debug(f"Processing multipart/form-data request for {param_name} with model {model.__name__}")

        has_file_fields = check_for_file_fields(model)

        if has_file_fields and (request.files or request.form):
            result = process_file_upload_model(request, model)
            if result:
                kwargs[param_name] = result
                return kwargs

            error_response = create_status_error_response(
                status_code=400,
                message=f"Failed to process file upload for {model.__name__}",
                details={
                    "model": model.__name__,
                    "fields": [
                        f
                        for f in model.model_fields
                        if hasattr(model.model_fields[f].annotation, "__origin__")
                        and model.model_fields[f].annotation.__origin__ is FileField
                    ],
                },
            )
            return make_response(*error_response)

        if request.form:
            form_data = dict(request.form.items())
            try:
                processed_data = preprocess_request_data(form_data, model)
                model_instance = safe_operation(
                    lambda: ModelFactory.create_from_data(model, processed_data), fallback=None
                )
                if model_instance:
                    kwargs[param_name] = model_instance
                    return kwargs
            except ValidationError as e:
                logger.warning(f"Validation error for {model.__name__}: {e}")

                error_response = handle_validation_error(e)
                return make_response(*error_response)
            except Exception as e:
                logger.exception(f"Failed to process form data for {model.__name__}")

                error_response = handle_request_validation_error(model.__name__, e)
                return make_response(*error_response)

        elif hasattr(request, "files") and request.files:
            model_data = {}
            for field_name in model.model_fields:
                if field_name in request.files:
                    model_data[field_name] = request.files[field_name]

            if model_data:
                try:
                    model_instance = model(**model_data)
                    kwargs[param_name] = model_instance
                except ValidationError as e:
                    logger.warning(f"Validation error for {model.__name__} with mock files: {e}")

                    error_response = handle_validation_error(e)
                    return make_response(*error_response)
                except Exception as e:
                    logger.exception(f"Failed to create model instance with mock files for {model.__name__}")

                    error_response = handle_request_validation_error(model.__name__, e)
                    return make_response(*error_response)
                else:
                    return kwargs

        try:
            model_instance = model()
            kwargs[param_name] = model_instance
        except Exception as e:
            logger.exception(f"Failed to create empty model instance for {model.__name__}")

            error_response = create_error_response(
                error_code="MODEL_CREATION_ERROR",
                message=f"Failed to create instance of {model.__name__}",
                status_code=500,
                details={"error": str(e)},
            )
            return make_response(*error_response)
        else:
            return kwargs


class BinaryContentTypeStrategy(ContentTypeStrategy):
    """Strategy for processing binary content types.

    This strategy handles binary content types such as images, audio, video, and
    application/octet-stream. It supports streaming large files to avoid memory issues.

    Attributes:
        max_memory_size: Maximum memory size for file uploads in bytes.
        chunk_size: Size of chunks to use when streaming large files.

    """

    def __init__(self) -> None:
        """Initialize the binary content type strategy."""
        self.max_memory_size = 10 * 1024 * 1024
        self.chunk_size = 1024 * 1024
        self.binary_types = [
            "image/",
            "audio/",
            "video/",
            "application/octet-stream",
            "application/pdf",
            "application/zip",
            "application/x-tar",
            "application/x-gzip",
        ]

    def set_max_memory_size(self, max_size: int) -> None:
        """Set the maximum memory size for file uploads.

        Args:
            max_size: Maximum memory size in bytes.

        """
        self.max_memory_size = max_size

    def can_handle(self, content_type: str) -> bool:
        """Check if this strategy can handle the given content type.

        Args:
            content_type: The content type to check.

        Returns:
            bool: True if this is a binary content type, False otherwise.

        """
        return any(binary_type in content_type for binary_type in self.binary_types)

    def process_request(
        self, request: Any, model: type[BaseModel], param_name: str, kwargs: dict[str, Any]
    ) -> dict[str, Any]:
        """Process a binary request.

        Args:
            request: The request object.
            model: The model to validate the request data against.
            param_name: The parameter name to bind the model instance to.
            kwargs: The keyword arguments to update.

        Returns:
            Dict[str, Any]: Updated kwargs dictionary with the model instance.

        """
        logger = get_logger(__name__)
        logger.debug(f"Processing binary request for {param_name} with model {model.__name__}")

        try:
            content_length = request.content_length or 0
            logger.debug(f"Binary content length: {content_length} bytes")

            if content_length > self.max_memory_size:
                return self._process_large_binary_file(request, model, param_name, kwargs)
            return self._process_small_binary_file(request, model, param_name, kwargs)

        except Exception as e:
            logger.exception(f"Failed to process binary content for {model.__name__}")

            error_response = create_error_response(
                error_code="BINARY_PROCESSING_ERROR",
                message=f"Failed to process binary content for {model.__name__}",
                status_code=400,
                details={"error": str(e), "content_type": request.content_type},
            )
            return make_response(*error_response)

    def _process_small_binary_file(
        self, request: Any, model: type[BaseModel], param_name: str, kwargs: dict[str, Any]
    ) -> dict[str, Any]:
        """Process a small binary file that fits in memory.

        Args:
            request: The request object.
            model: The model to validate the request data against.
            param_name: The parameter name to bind the model instance to.
            kwargs: The keyword arguments to update.

        Returns:
            Dict[str, Any]: Updated kwargs dictionary with the model instance.

        """
        logger = get_logger(__name__)

        file_name = self._extract_filename(request)
        content_type = request.content_type or "application/octet-stream"

        raw_data = request.get_data()

        file_obj = FileStorage(
            stream=io.BytesIO(raw_data),
            filename=file_name,
            content_type=content_type,
        )

        if hasattr(model, "model_fields") and "file" in model.model_fields:
            model_data = {"file": file_obj}
            processed_data = preprocess_request_data(model_data, model)
            try:
                model_instance = ModelFactory.create_from_data(model, processed_data)
                kwargs[param_name] = model_instance
            except ValidationError as e:
                logger.warning(f"Validation error for binary data against {model.__name__}: {e}")
                error_response = handle_validation_error(e)
                return make_response(*error_response)
            except Exception as e:
                logger.exception(f"Failed to create model instance from binary data for {model.__name__}")
                error_response = handle_request_validation_error(model.__name__, e)
                return make_response(*error_response)
            else:
                return kwargs
        else:
            try:
                model_instance = model()
                model_instance._raw_data = raw_data
                model_instance._file_obj = file_obj
                kwargs[param_name] = model_instance
            except Exception as e:
                logger.exception("Failed to create model instance for binary data")
                error_response = create_error_response(
                    error_code="MODEL_CREATION_ERROR",
                    message=f"Failed to create instance of {model.__name__} for binary data",
                    status_code=500,
                    details={"error": str(e), "content_type": content_type},
                )
                return make_response(*error_response)
            else:
                return kwargs

    def _process_large_binary_file(
        self, request: Any, model: type[BaseModel], param_name: str, kwargs: dict[str, Any]
    ) -> dict[str, Any]:
        """Process a large binary file using streaming to avoid memory issues.

        Args:
            request: The request object.
            model: The model to validate the request data against.
            param_name: The parameter name to bind the model instance to.
            kwargs: The keyword arguments to update.

        Returns:
            Dict[str, Any]: Updated kwargs dictionary with the model instance.

        """
        logger = get_logger(__name__)
        logger.debug("Processing large binary file using streaming")

        file_name = self._extract_filename(request)
        content_type = request.content_type or "application/octet-stream"

        try:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_path = temp_file.name

                if hasattr(request, "stream"):
                    chunk = request.stream.read(self.chunk_size)
                    while chunk:
                        temp_file.write(chunk)
                        chunk = request.stream.read(self.chunk_size)
                else:
                    temp_file.write(request.get_data())

                temp_file.flush()

            with Path(temp_path).open("rb") as f:
                file_obj = FileStorage(
                    stream=f,
                    filename=file_name,
                    content_type=content_type,
                )

                if hasattr(model, "model_fields") and "file" in model.model_fields:
                    model_data = {"file": file_obj}
                    processed_data = preprocess_request_data(model_data, model)
                    try:
                        model_instance = ModelFactory.create_from_data(model, processed_data)

                        model_instance._temp_file_path = temp_path
                        kwargs[param_name] = model_instance
                    except ValidationError as e:
                        logger.warning(f"Validation error for binary data against {model.__name__}: {e}")
                        self._cleanup_temp_file(temp_path)
                        error_response = handle_validation_error(e)
                        return make_response(*error_response)
                    except Exception as e:
                        logger.exception(f"Failed to create model instance from binary data for {model.__name__}")
                        self._cleanup_temp_file(temp_path)
                        error_response = handle_request_validation_error(model.__name__, e)
                        return make_response(*error_response)
                    else:
                        return kwargs
                else:
                    try:
                        model_instance = model()
                        model_instance._file_obj = file_obj
                        model_instance._temp_file_path = temp_path
                        kwargs[param_name] = model_instance
                    except Exception as e:
                        logger.exception("Failed to create model instance for binary data")
                        self._cleanup_temp_file(temp_path)
                        error_response = create_error_response(
                            error_code="MODEL_CREATION_ERROR",
                            message=f"Failed to create instance of {model.__name__} for binary data",
                            status_code=500,
                            details={"error": str(e), "content_type": content_type},
                        )
                        return make_response(*error_response)
                    else:
                        return kwargs
        except Exception as e:
            logger.exception("Error processing large binary file")
            error_response = create_error_response(
                error_code="LARGE_FILE_PROCESSING_ERROR",
                message=f"Failed to process large binary file for {model.__name__}",
                status_code=400,
                details={"error": str(e), "content_type": content_type},
            )
            return make_response(*error_response)

    def _extract_filename(self, request: Any) -> str:
        """Extract filename from request headers.

        Args:
            request: The request object.

        Returns:
            str: The extracted filename or a default name.

        """
        content_disposition = request.headers.get("Content-Disposition", "")
        if "filename=" in content_disposition:
            return content_disposition.split("filename=")[-1].strip('"')

        if hasattr(request, "path"):
            path = request.path
            if "/" in path:
                path_parts = path.split("/")
                if path_parts[-1]:
                    return path_parts[-1]

        content_type = request.content_type or "application/octet-stream"
        if "image/" in content_type:
            extension = content_type.split("/")[-1] or "jpg"
            return f"image.{extension}"
        if "audio/" in content_type:
            extension = content_type.split("/")[-1] or "mp3"
            return f"audio.{extension}"
        if "video/" in content_type:
            extension = content_type.split("/")[-1] or "mp4"
            return f"video.{extension}"
        if "pdf" in content_type:
            return "document.pdf"
        return "file.bin"

    def _cleanup_temp_file(self, file_path: str) -> None:
        """Clean up temporary file.

        Args:
            file_path: Path to the temporary file.

        """
        try:
            file_path_obj = Path(file_path)
            if file_path_obj.exists():
                file_path_obj.unlink()
        except Exception:
            logger = get_logger(__name__)
            logger.exception(f"Failed to clean up temporary file: {file_path}")


class MultipartMixedStrategy(ContentTypeStrategy):
    """Strategy for processing multipart/mixed content types.

    This strategy handles multipart/mixed content types, which contain multiple parts
    with different content types. It supports parsing the different parts and binding
    them to the appropriate model fields.

    Attributes:
        max_memory_size: Maximum memory size for file uploads in bytes.
        chunk_size: Size of chunks to use when streaming large files.

    """

    def __init__(self) -> None:
        """Initialize the multipart/mixed content type strategy."""
        self.max_memory_size = 10 * 1024 * 1024
        self.chunk_size = 1024 * 1024

    def set_max_memory_size(self, max_size: int) -> None:
        """Set the maximum memory size for file uploads.

        Args:
            max_size: Maximum memory size in bytes.

        """
        self.max_memory_size = max_size

    def can_handle(self, content_type: str) -> bool:
        """Check if this strategy can handle the given content type.

        Args:
            content_type: The content type to check.

        Returns:
            bool: True if this is a multipart/mixed content type, False otherwise.

        """
        return "multipart/mixed" in content_type or "multipart/related" in content_type

    def process_request(
        self, request: Any, model: type[BaseModel], param_name: str, kwargs: dict[str, Any]
    ) -> dict[str, Any]:
        """Process a multipart/mixed request.

        Args:
            request: The request object.
            model: The model to validate the request data against.
            param_name: The parameter name to bind the model instance to.
            kwargs: The keyword arguments to update.

        Returns:
            Dict[str, Any]: Updated kwargs dictionary with the model instance.

        """
        logger = get_logger(__name__)
        logger.debug(f"Processing multipart/mixed request for {param_name} with model {model.__name__}")

        try:
            content_length = request.content_length or 0
            logger.debug(f"Multipart content length: {content_length} bytes")

            if "boundary=" not in request.content_type:
                logger.warning("No boundary found in multipart/mixed content type")
                error_response = create_error_response(
                    error_code="INVALID_MULTIPART_REQUEST",
                    message="No boundary found in multipart/mixed content type",
                    status_code=400,
                    details={"content_type": request.content_type},
                )
                return make_response(*error_response)

            boundary = request.content_type.split("boundary=")[-1].strip()

            if content_length > self.max_memory_size:
                return self._process_large_multipart_request(request, model, param_name, kwargs, boundary)
            return self._process_small_multipart_request(request, model, param_name, kwargs, boundary)

        except Exception as e:
            logger.exception(f"Failed to process multipart/mixed content for {model.__name__}")
            error_response = create_error_response(
                error_code="MULTIPART_PROCESSING_ERROR",
                message=f"Failed to process multipart/mixed content for {model.__name__}",
                status_code=400,
                details={"error": str(e), "content_type": request.content_type},
            )
            return make_response(*error_response)

    def _process_small_multipart_request(
        self, request: Any, model: type[BaseModel], param_name: str, kwargs: dict[str, Any], boundary: str
    ) -> dict[str, Any]:
        """Process a small multipart/mixed request that fits in memory.

        Args:
            request: The request object.
            model: The model to validate the request data against.
            param_name: The parameter name to bind the model instance to.
            kwargs: The keyword arguments to update.
            boundary: The boundary string for the multipart request.

        Returns:
            Dict[str, Any]: Updated kwargs dictionary with the model instance.

        """
        logger = get_logger(__name__)

        try:
            raw_data = request.get_data()
            parts = raw_data.decode("latin1").split(f"--{boundary}")

            parsed_parts = self._parse_multipart_parts(parts, model)

            if parsed_parts:
                return self._create_model_from_parts(parsed_parts, model, param_name, kwargs)
            logger.warning(f"No valid parts found in multipart/mixed request for {model.__name__}")
            error_response = create_error_response(
                error_code="EMPTY_MULTIPART_REQUEST",
                message="No valid parts found in multipart/mixed request",
                status_code=400,
                details={"model": model.__name__},
            )
            return make_response(*error_response)

        except Exception as e:
            logger.exception(f"Failed to process small multipart/mixed content for {model.__name__}")
            error_response = create_error_response(
                error_code="MULTIPART_PROCESSING_ERROR",
                message=f"Failed to process multipart/mixed content for {model.__name__}",
                status_code=400,
                details={"error": str(e), "content_type": request.content_type},
            )
            return make_response(*error_response)

    def _process_large_multipart_request(
        self, request: Any, model: type[BaseModel], param_name: str, kwargs: dict[str, Any], boundary: str
    ) -> dict[str, Any]:
        """Process a large multipart/mixed request using streaming to avoid memory issues.

        Args:
            request: The request object.
            model: The model to validate the request data against.
            param_name: The parameter name to bind the model instance to.
            kwargs: The keyword arguments to update.
            boundary: The boundary string for the multipart request.

        Returns:
            Dict[str, Any]: Updated kwargs dictionary with the model instance.

        """
        logger = get_logger(__name__)
        logger.debug("Processing large multipart/mixed file using streaming")

        try:
            temp_dir = tempfile.mkdtemp()
            temp_files = []

            if hasattr(request, "stream"):
                buffer = b""
                current_part = None

                chunk = request.stream.read(self.chunk_size)
                while chunk:
                    buffer += chunk

                    boundary_bytes = f"--{boundary}".encode("latin1")
                    parts = buffer.split(boundary_bytes)

                    for i, part in enumerate(parts[:-1]):
                        if i == 0 and not part.strip():
                            continue

                        if part.endswith(b"--\r\n") or part == b"--":
                            if current_part:
                                current_part.close()
                            break

                        if b"\r\n\r\n" in part:
                            headers_bytes, content = part.split(b"\r\n\r\n", 1)
                            headers_str = headers_bytes.decode("latin1")
                            headers = {}

                            for header_line in headers_str.split("\r\n"):
                                if ":" in header_line:
                                    key, value = header_line.split(":", 1)
                                    headers[key.strip().lower()] = value.strip()

                            content_type = headers.get("content-type", "")
                            with tempfile.NamedTemporaryFile(delete=False, dir=temp_dir) as part_file:
                                temp_files.append((part_file.name, content_type, headers))
                                part_file.write(content)

                    buffer = parts[-1]
                    chunk = request.stream.read(self.chunk_size)

                if buffer:
                    if b"\r\n\r\n" in buffer:
                        headers_bytes, content = buffer.split(b"\r\n\r\n", 1)
                        headers_str = headers_bytes.decode("latin1")
                        headers = {}

                        for header_line in headers_str.split("\r\n"):
                            if ":" in header_line:
                                key, value = header_line.split(":", 1)
                                headers[key.strip().lower()] = value.strip()

                        content_type = headers.get("content-type", "")
                        with tempfile.NamedTemporaryFile(delete=False, dir=temp_dir) as part_file:
                            temp_files.append((part_file.name, content_type, headers))
                            part_file.write(content)
            else:
                parts = request.get_data().decode("latin1").split(f"--{boundary}")

                for part in parts:
                    if not part.strip() or part.strip() == "--":
                        continue

                    if "\r\n\r\n" in part:
                        headers_str, content = part.split("\r\n\r\n", 1)
                        headers = {}

                        for header_line in headers_str.split("\r\n"):
                            if ":" in header_line:
                                key, value = header_line.split(":", 1)
                                headers[key.strip().lower()] = value.strip()

                        content_type = headers.get("content-type", "")
                        with tempfile.NamedTemporaryFile(delete=False, dir=temp_dir) as part_file:
                            temp_files.append((part_file.name, content_type, headers))
                            part_file.write(content.encode("latin1"))

            parsed_parts = {}

            for file_path, content_type, headers in temp_files:
                content = Path(file_path).read_bytes()
                if "application/json" in content_type:
                    try:
                        parsed_parts["json"] = json.loads(content.decode("utf-8"))
                    except json.JSONDecodeError:
                        parsed_parts["json"] = content.decode("utf-8")
                elif any(
                    binary_type in content_type
                    for binary_type in ["image/", "audio/", "video/", "application/octet-stream"]
                ):
                    filename = headers.get("content-disposition", "").split("filename=")[-1].strip('"') or "file"
                    file_obj = FileStorage(
                        stream=io.BytesIO(content),
                        filename=filename,
                        content_type=content_type,
                    )
                    parsed_parts["file"] = file_obj
                else:
                    parsed_parts["text"] = content.decode("utf-8")

            for file_path, _, _ in temp_files:
                try:
                    Path.unlink(file_path)
                except Exception:
                    logger.exception(f"Failed to clean up temporary file: {file_path}")

            try:
                Path.rmdir(temp_dir)
            except Exception:
                logger.exception(f"Failed to clean up temporary directory: {temp_dir}")

            if parsed_parts:
                return self._create_model_from_parts(parsed_parts, model, param_name, kwargs)
            logger.warning(f"No valid parts found in multipart/mixed request for {model.__name__}")
            error_response = create_error_response(
                error_code="EMPTY_MULTIPART_REQUEST",
                message="No valid parts found in multipart/mixed request",
                status_code=400,
                details={"model": model.__name__},
            )
            return make_response(*error_response)

        except Exception as e:
            logger.exception(f"Failed to process large multipart/mixed content for {model.__name__}")
            error_response = create_error_response(
                error_code="MULTIPART_PROCESSING_ERROR",
                message=f"Failed to process multipart/mixed content for {model.__name__}",
                status_code=400,
                details={"error": str(e), "content_type": request.content_type},
            )
            return make_response(*error_response)

    def _parse_multipart_parts(self, parts: list[str], model: type[BaseModel]) -> dict[str, Any]:  # noqa: ARG002
        """Parse multipart parts into a dictionary of values.

        Args:
            parts: List of multipart parts.
            model: The model to validate against.

        Returns:
            dict[str, Any]: Dictionary of parsed parts.

        """
        logger = get_logger(__name__)
        parsed_parts = {}

        for part in parts:
            if not part.strip() or part.strip() == "--":
                continue

            if "\r\n\r\n" in part:
                headers_str, content = part.split("\r\n\r\n", 1)
                headers = {}

                for header_line in headers_str.split("\r\n"):
                    if ":" in header_line:
                        key, value = header_line.split(":", 1)
                        headers[key.strip().lower()] = value.strip()

                content_type = headers.get("content-type", "")
                content_disposition = headers.get("content-disposition", "")

                field_name = None
                if "name=" in content_disposition:
                    field_name = content_disposition.split("name=")[-1].split(";")[0].strip('"')

                if "application/json" in content_type:
                    try:
                        value = json.loads(content)
                        if field_name:
                            parsed_parts[field_name] = value
                        else:
                            parsed_parts["json"] = value
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSON content in multipart/mixed: {e}")
                        if field_name:
                            parsed_parts[field_name] = content
                        else:
                            parsed_parts["json"] = content
                elif any(
                    binary_type in content_type
                    for binary_type in ["image/", "audio/", "video/", "application/octet-stream"]
                ):
                    filename = "file"
                    if "filename=" in content_disposition:
                        filename = content_disposition.split("filename=")[-1].strip('"')

                    file_obj = FileStorage(
                        stream=io.BytesIO(content.encode("latin1")),
                        filename=filename,
                        content_type=content_type,
                    )

                    if field_name:
                        parsed_parts[field_name] = file_obj
                    else:
                        parsed_parts["file"] = file_obj
                elif field_name:
                    parsed_parts[field_name] = content
                else:
                    parsed_parts["text"] = content

        return parsed_parts

    def _create_model_from_parts(
        self, parsed_parts: dict[str, Any], model: type[BaseModel], param_name: str, kwargs: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a model instance from parsed parts.

        Args:
            parsed_parts: Dictionary of parsed parts.
            model: The model to create an instance of.
            param_name: The parameter name to bind the model instance to.
            kwargs: The keyword arguments to update.

        Returns:
            Dict[str, Any]: Updated kwargs dictionary with the model instance.

        """
        logger = get_logger(__name__)

        try:
            if hasattr(model, "model_fields"):
                model_data = {}

                for field_name in model.model_fields:
                    if field_name in parsed_parts:
                        model_data[field_name] = parsed_parts[field_name]

                processed_data = preprocess_request_data(model_data, model)
                try:
                    model_instance = ModelFactory.create_from_data(model, processed_data)
                    kwargs[param_name] = model_instance
                except ValidationError as e:
                    logger.warning(f"Validation error for multipart/mixed data against {model.__name__}: {e}")
                    error_response = handle_validation_error(e)
                    return make_response(*error_response)
                else:
                    return kwargs

            model_instance = model()
            for key, value in parsed_parts.items():
                if hasattr(model_instance, key):
                    setattr(model_instance, key, value)

            kwargs[param_name] = model_instance
        except Exception as e:
            logger.exception(f"Failed to create model instance from multipart/mixed data for {model.__name__}")
            error_response = handle_request_validation_error(model.__name__, e)
            return make_response(*error_response)
        else:
            return kwargs


class FormUrlencodedStrategy(ContentTypeStrategy):
    """Strategy for processing application/x-www-form-urlencoded content types.

    This strategy handles form-urlencoded content types, which are commonly used
    for HTML form submissions. It supports parsing form data and binding it to
    model fields.
    """

    def can_handle(self, content_type: str) -> bool:
        """Check if this strategy can handle the given content type.

        Args:
            content_type: The content type to check.

        Returns:
            bool: True if this is a form-urlencoded content type, False otherwise.

        """
        return "application/x-www-form-urlencoded" in content_type

    def process_request(
        self, request: Any, model: type[BaseModel], param_name: str, kwargs: dict[str, Any]
    ) -> dict[str, Any]:
        """Process a form-urlencoded request.

        Args:
            request: The request object.
            model: The model to validate the request data against.
            param_name: The parameter name to bind the model instance to.
            kwargs: The keyword arguments to update.

        Returns:
            Dict[str, Any]: Updated kwargs dictionary with the model instance.

        """
        logger = get_logger(__name__)
        logger.debug(f"Processing form-urlencoded request for {param_name} with model {model.__name__}")

        form_data = self._extract_form_data(request)

        if form_data:
            return self._process_form_data(form_data, model, param_name, kwargs)
        try:
            model_instance = model()
            kwargs[param_name] = model_instance
        except Exception as e:
            logger.exception(f"Failed to create empty model instance for {model.__name__}")

            error_response = create_status_error_response(
                status_code=400,
                message="No form data found in request",
                details={"model": model.__name__, "error": str(e)},
            )
            return make_response(*error_response)
        else:
            return kwargs

    def _extract_form_data(self, request: Any) -> dict[str, Any]:
        """Extract form data from request.

        Args:
            request: The request object.

        Returns:
            dict[str, Any]: Dictionary of form data.

        """
        logger = get_logger(__name__)

        if hasattr(request, "form") and request.form:
            return dict(request.form.items())

        if hasattr(request, "get_data"):
            try:
                raw_data = request.get_data(as_text=True)
                if raw_data:
                    parsed_data = urllib.parse.parse_qs(raw_data)

                    form_data = {}
                    for key, value in parsed_data.items():
                        if isinstance(value, list) and len(value) == 1:
                            form_data[key] = value[0]
                        else:
                            form_data[key] = value

                    return form_data
            except Exception:
                logger.exception("Failed to parse form data from request body")

        if hasattr(request, "values") and request.values:
            return dict(request.values.items())

        return {}

    def _process_form_data(
        self, form_data: dict[str, Any], model: type[BaseModel], param_name: str, kwargs: dict[str, Any]
    ) -> dict[str, Any]:
        """Process form data and create model instance.

        Args:
            form_data: Dictionary of form data.
            model: The model to validate the data against.
            param_name: The parameter name to bind the model instance to.
            kwargs: The keyword arguments to update.

        Returns:
            Dict[str, Any]: Updated kwargs dictionary with the model instance.

        """
        logger = get_logger(__name__)

        try:
            processed_form_data = {}
            for key, value in form_data.items():
                if "." in key:
                    parts = key.split(".")
                    current = processed_form_data
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    current[parts[-1]] = value
                else:
                    processed_form_data[key] = value

            processed_data = preprocess_request_data(processed_form_data, model)

            try:
                model_instance = ModelFactory.create_from_data(model, processed_data)
                kwargs[param_name] = model_instance
            except ValidationError as e:
                logger.warning(f"Validation error for form data against {model.__name__}: {e}")
                error_response = handle_validation_error(e)
                return make_response(*error_response)
            else:
                return kwargs

        except Exception as e:
            logger.exception(f"Failed to process form data for {model.__name__}")
            error_response = handle_request_validation_error(model.__name__, e)
            return make_response(*error_response)


class DefaultStrategy(ContentTypeStrategy):
    """Default strategy for processing requests with unknown content types."""

    def can_handle(self, content_type: str) -> bool:  # noqa: ARG002
        """Always returns True as this is the default strategy.

        Args:
            content_type: The content type to check.

        Returns:
            bool: Always True.

        """
        return True

    def process_request(
        self,
        request: Any,  # noqa: ARG002
        model: type[BaseModel],
        param_name: str,
        kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        """Process a request with an unknown content type.

        Args:
            request: The request object.
            model: The model to validate the request data against.
            param_name: The parameter name to bind the model instance to.
            kwargs: The keyword arguments to update.

        Returns:
            Dict[str, Any]: Updated kwargs dictionary with the model instance.

        """
        logger = get_logger(__name__)
        logger.debug(f"Using default strategy for {param_name} with model {model.__name__}")

        try:
            model_instance = model()
            kwargs[param_name] = model_instance
        except ValidationError as e:
            logger.warning(f"Validation error creating default instance of {model.__name__}: {e}")

            error_response = handle_validation_error(e)
            return make_response(*error_response)
        except Exception as e:
            logger.exception(f"Failed to create empty model instance for {model.__name__}")

            error_response = create_status_error_response(
                status_code=500,
                message=f"Failed to create instance of {model.__name__}",
                details={"error": str(e)},
            )
            return make_response(*error_response)
        else:
            return kwargs


class ContentTypeRegistry:
    """Registry for content type processing strategies.

    This class implements the registry pattern for content type processing strategies.
    It allows for dynamic registration of strategies and provides a way to find
    the appropriate strategy for a given content type.

    Attributes:
        _strategies: Dictionary mapping strategy classes to their instances.
        _default_strategy: Default strategy to use when no matching strategy is found.

    """

    _instance = None

    def __new__(cls) -> Self:
        """Create a singleton instance of the registry."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._strategies = {}
            cls._instance._default_strategy = None
        return cls._instance

    def register(self, strategy_class: type[ContentTypeStrategy], is_default: bool = False) -> None:
        """Register a strategy class with the registry.

        Args:
            strategy_class: The strategy class to register.
            is_default: Whether this strategy should be used as the default.

        """
        strategy_instance = strategy_class()
        self._strategies[strategy_class] = strategy_instance
        if is_default:
            self._default_strategy = strategy_instance

    def get_strategy_for_content_type(self, content_type: str) -> ContentTypeStrategy:
        """Get the appropriate strategy for a given content type.

        Args:
            content_type: The content type to find a strategy for.

        Returns:
            ContentTypeStrategy: The appropriate strategy for the content type.

        """
        for strategy in self._strategies.values():
            if strategy.can_handle(content_type):
                return strategy

        if self._default_strategy:
            return self._default_strategy

        msg = f"No strategy found for content type: {content_type}"
        raise ValueError(msg)

    def get_all_strategies(self) -> list[ContentTypeStrategy]:
        """Get all registered strategies.

        Returns:
            list[ContentTypeStrategy]: List of all registered strategies.

        """
        return list(self._strategies.values())


_registry = ContentTypeRegistry()
_registry.register(JsonContentTypeStrategy)
_registry.register(MultipartFormDataStrategy)
_registry.register(BinaryContentTypeStrategy)
_registry.register(MultipartMixedStrategy)
_registry.register(FormUrlencodedStrategy)
_registry.register(DefaultStrategy, is_default=True)


class ContentTypeProcessor:
    """Processor for handling different content types in requests.

    This class provides a unified interface for processing different content types
    in HTTP requests. It uses a strategy pattern to delegate processing to the
    appropriate strategy based on the content type.

    Attributes:
        registry: Registry of content type processing strategies.
        request_content_types: Configuration for request content types.
        content_type: Custom content type for request body.
        content_type_resolver: Function to determine content type based on request.
        default_error_response: Default error response class.
        max_memory_size: Maximum memory size for file uploads in bytes.

    """

    def __init__(
        self,
        content_type: str | None = None,
        request_content_types: RequestContentTypes | None = None,
        content_type_resolver: Callable | None = None,
        default_error_response: type[BaseErrorResponse] = BaseErrorResponse,
        max_memory_size: int = 10 * 1024 * 1024,
    ) -> None:
        """Initialize the content type processor.

        Args:
            content_type: Custom content type for request body. If None, will be auto-detected.
            request_content_types: Multiple content types for request body.
            content_type_resolver: Function to determine content type based on request.
            default_error_response: Default error response class.
            max_memory_size: Maximum memory size for file uploads in bytes.

        """
        self.content_type = content_type
        self.request_content_types = request_content_types
        self.content_type_resolver = content_type_resolver
        self.default_error_response = default_error_response
        self.max_memory_size = max_memory_size
        self.registry = _registry

    def process_request_body(
        self, request: Any, model: type[BaseModel], param_name: str, kwargs: dict[str, Any]
    ) -> dict[str, Any]:
        """Process request body based on content type.

        Args:
            request: The request object.
            model: The model to validate the request data against.
            param_name: The parameter name to bind the model instance to.
            kwargs: The keyword arguments to update.

        Returns:
            Dict[str, Any]: Updated kwargs dictionary with the model instance.

        """
        logger = get_logger(__name__)
        logger.debug(f"Processing request body for {param_name} with model {model.__name__}")

        actual_content_type = request.content_type or ""
        logger.debug(f"Actual request content type: {actual_content_type}")

        effective_content_type = self._resolve_content_type(request, actual_content_type)

        mapped_model = self._resolve_model_for_content_type(request, actual_content_type, effective_content_type)

        if mapped_model:
            model = mapped_model
            logger.debug(f"Using mapped model: {model.__name__}")

        try:
            strategy = self.registry.get_strategy_for_content_type(effective_content_type)
            logger.debug(f"Using strategy {strategy.__class__.__name__} for content type {effective_content_type}")

            if hasattr(strategy, "set_max_memory_size"):
                strategy.set_max_memory_size(self.max_memory_size)

            return strategy.process_request(request, model, param_name, kwargs)
        except Exception as e:
            logger.exception(f"Error processing request with content type {effective_content_type}")

            try:
                model_instance = model()
                kwargs[param_name] = model_instance
            except Exception:
                logger.exception(f"Failed to create empty model instance for {model.__name__}")

                error_response = create_status_error_response(
                    status_code=400,
                    message=f"Failed to process request with content type {effective_content_type}",
                    details={"error": str(e), "model": model.__name__},
                )
                return make_response(*error_response)

        return kwargs

    def _resolve_content_type(self, request: Any, actual_content_type: str) -> str:
        """Resolve the effective content type using available resolvers.

        Args:
            request: The request object.
            actual_content_type: The actual content type from the request.

        Returns:
            str: The resolved content type.

        """
        logger = get_logger(__name__)
        effective_content_type = self.content_type or actual_content_type

        if self.content_type_resolver and hasattr(request, "args"):
            try:
                resolved_content_type = self.content_type_resolver(request)
                if resolved_content_type:
                    logger.debug(f"Resolved content type using custom resolver: {resolved_content_type}")
                    effective_content_type = resolved_content_type
            except Exception:
                logger.exception("Error resolving content type with custom resolver")

        if self.request_content_types and isinstance(self.request_content_types, RequestContentTypes):
            if self.request_content_types.default_content_type:
                default_type = self.request_content_types.default_content_type
                logger.debug(f"Using default content type from RequestContentTypes: {default_type}")
                effective_content_type = default_type

            if self.request_content_types.content_type_resolver and hasattr(request, "args"):
                try:
                    resolved_content_type = self.request_content_types.content_type_resolver(request)
                    if resolved_content_type:
                        logger.debug(
                            f"Resolved content type using RequestContentTypes resolver: {resolved_content_type}"
                        )
                        effective_content_type = resolved_content_type
                except Exception:
                    logger.exception("Error resolving content type from RequestContentTypes")

        if hasattr(request, "args") and "content_type" in request.args:
            url_content_type = request.args.get("content_type")
            logger.debug(f"Found content type in URL parameters: {url_content_type}")
            effective_content_type = url_content_type

        logger.debug(f"Resolved effective content type: {effective_content_type}")
        return effective_content_type

    def _resolve_model_for_content_type(
        self, _: Any, actual_content_type: str, effective_content_type: str
    ) -> type[BaseModel] | None:
        """Resolve the model to use based on content type.

        Args:
            request: The request object.
            actual_content_type: The actual content type from the request.
            effective_content_type: The resolved effective content type.

        Returns:
            Optional[type[BaseModel]]: The model to use, or None if no mapping is found.

        """
        logger = get_logger(__name__)
        mapped_model = None

        if not self.request_content_types:
            return None

        if not isinstance(self.request_content_types, RequestContentTypes):
            return None

        for content_type, content_model in self.request_content_types.content_types.items():
            if content_type in actual_content_type:
                if isinstance(content_model, type) and issubclass(content_model, BaseModel):
                    logger.debug(f"Found matching model for content type {content_type}: {content_model.__name__}")
                    mapped_model = content_model
                    break

        if (
            not mapped_model
            and effective_content_type
            and effective_content_type in self.request_content_types.content_types
        ):
            content_model = self.request_content_types.content_types[effective_content_type]
            if isinstance(content_model, type) and issubclass(content_model, BaseModel):
                logger.debug(f"Using mapped model for content type {effective_content_type}: {content_model.__name__}")
                mapped_model = content_model

        return mapped_model


def check_for_file_fields(model: type[BaseModel]) -> bool:
    """Check if a model contains file upload fields.

    Args:
        model: The model to check.

    Returns:
        bool: True if the model has file fields, False otherwise.

    """
    if not hasattr(model, "model_fields"):
        return False

    for field_info in model.model_fields.values():
        field_type = field_info.annotation

        if isinstance(field_type, type) and issubclass(field_type, FileField):
            return True

        origin = getattr(field_type, "__origin__", None)
        if origin is list or origin is list:
            args = getattr(field_type, "__args__", [])
            if args and isinstance(args[0], type) and issubclass(args[0], FileField):
                return True

    return False


def process_file_upload_model(request: Any, model: type[BaseModel]) -> BaseModel | None:
    """Process a file upload model with form data and files.

    Args:
        request: The request object.
        model: The model class to instantiate.

    Returns:
        Optional[BaseModel]: An instance of the model with file data, or None if processing failed.

    """
    logger = get_logger(__name__)
    logger.debug(f"Processing file upload model for {model.__name__}")

    model_data = dict(request.form.items())
    logger.debug(f"Form data: {model_data}")

    has_file_fields = False
    file_field_names = []

    for field_name, field_info in model.model_fields.items():
        field_type = field_info.annotation

        if isinstance(field_type, type) and issubclass(field_type, FileField):
            has_file_fields = True
            file_field_names.append(field_name)
            continue

        origin = getattr(field_type, "__origin__", None)
        if origin is list or origin is list:
            args = getattr(field_type, "__args__", [])
            if args and isinstance(args[0], type) and issubclass(args[0], FileField):
                has_file_fields = True
                file_field_names.append(field_name)

    files_found = False

    for field_name, field_info in model.model_fields.items():
        field_type = field_info.annotation

        if isinstance(field_type, type) and issubclass(field_type, FileField):
            if field_name in request.files:
                model_data[field_name] = request.files[field_name]
                files_found = True
                logger.debug(f"Found file for field {field_name}: {request.files[field_name].filename}")
            elif "file" in request.files and field_name == "file":
                model_data[field_name] = request.files["file"]
                files_found = True
                logger.debug(f"Using default file for field {field_name}: {request.files['file'].filename}")
            elif "avatar" in request.files and field_name == "avatar":
                model_data[field_name] = request.files["avatar"]
                files_found = True
                logger.debug(f"Using avatar file for field {field_name}: {request.files['avatar'].filename}")
            elif len(request.files) == 1:
                file_key = next(iter(request.files))
                model_data[field_name] = request.files[file_key]
                files_found = True
                logger.debug(f"Using single file for field {field_name}: {request.files[file_key].filename}")

        else:
            origin = getattr(field_type, "__origin__", None)
            if origin is list or origin is list:
                args = getattr(field_type, "__args__", [])
                if args and isinstance(args[0], type) and issubclass(args[0], FileField):
                    if field_name in request.files:
                        if hasattr(request.files, "getlist"):
                            files_list = request.files.getlist(field_name)
                            if files_list:
                                model_data[field_name] = files_list
                                files_found = True
                                logger.debug(f"Found multiple files for field {field_name}: {len(files_list)} files")
                    else:
                        all_files = []
                        for file_key in request.files:
                            if hasattr(request.files, "getlist"):
                                all_files.extend(request.files.getlist(file_key))
                            else:
                                all_files.append(request.files[file_key])

                        if all_files:
                            model_data[field_name] = all_files
                            files_found = True
                            logger.debug(f"Collected all files for field {field_name}: {len(all_files)} files")

    if has_file_fields and not files_found:
        logger.warning(f"No files found for file fields: {file_field_names}")
        return None

    processed_data = preprocess_request_data(model_data, model)
    logger.debug(f"Processed data: {processed_data}")

    try:
        return ModelFactory.create_from_data(model, processed_data)
    except ValidationError:
        logger.warning(f"Validation error for file upload model {model.__name__}")
        return None
    except Exception:
        logger.exception("Error creating model instance")
        try:
            return model(**model_data)
        except Exception:
            logger.exception("Error creating model instance with raw data")
            return None


def detect_content_type(request: Any) -> str:
    """Detect content type from request.

    Args:
        request: The request object.

    Returns:
        str: The detected content type.

    """
    content_type = request.content_type or ""

    if "application/json" in content_type:
        return "application/json"
    if "multipart/form-data" in content_type:
        return "multipart/form-data"
    if "application/x-www-form-urlencoded" in content_type:
        return "application/x-www-form-urlencoded"
    if "multipart/mixed" in content_type:
        return "multipart/mixed"
    if any(binary_type in content_type for binary_type in ["image/", "audio/", "video/", "application/octet-stream"]):
        return content_type

    if hasattr(request, "is_json") and request.is_json:
        return "application/json"
    if hasattr(request, "files") and request.files:
        return "multipart/form-data"
    if hasattr(request, "form") and request.form:
        return "application/x-www-form-urlencoded"

    return "application/json"
