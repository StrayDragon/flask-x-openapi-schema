"""
Generator for MDX documentation from OpenAPI schemas.
"""

import json
import os
from typing import Any

from .i18n.i18n_string import set_current_language


def generate_mdx_from_openapi(schema: dict[str, Any], output_file: str, language: str = "en-US") -> None:
    """
    Generate MDX documentation from an OpenAPI schema.

    Args:
        schema: The OpenAPI schema
        output_file: The output file path
        language: The language for the documentation (default: "en-US")
    """
    # Set the current language for the thread
    set_current_language(language)

    # Create the MDX content
    mdx_content = _create_mdx_content(schema, language)

    # Write to file
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    with open(output_file, "w") as f:
        f.write(mdx_content)


def _create_mdx_content(schema: dict[str, Any], language: str) -> str:
    """
    Create MDX content from an OpenAPI schema.

    Args:
        schema: The OpenAPI schema
        language: The language for the documentation

    Returns:
        The MDX content
    """
    # Get info from schema
    info = schema.get("info", {})
    title = info.get("title", "API Documentation")
    description = info.get("description", "")
    version = info.get("version", "1.0.0")

    # Handle I18nString objects
    if isinstance(title, dict) and "type" in title and title.get("type") == "i18n_string":
        title = title.get("value", {}).get(language, title.get("value", {}).get("en-US", "API Documentation"))

    if isinstance(description, dict) and "type" in description and description.get("type") == "i18n_string":
        description = description.get("value", {}).get(language, description.get("value", {}).get("en-US", ""))

    # Create header
    mdx = f"""---
title: {title}
description: {description}
---

# {title}

Version: {version}

{description}

"""

    # Add paths
    paths = schema.get("paths", {})
    for path, path_item in sorted(paths.items()):
        mdx += f"## Endpoint: `{path}`\n\n"

        for method, operation in sorted(path_item.items()):
            method_upper = method.upper()
            summary = operation.get("summary", "")
            description = operation.get("description", "")
            operation_id = operation.get("operationId", "")

            # Handle I18nString objects for summary and description
            if isinstance(summary, dict) and "type" in summary and summary.get("type") == "i18n_string":
                summary = summary.get("value", {}).get(language, summary.get("value", {}).get("en-US", ""))

            if isinstance(description, dict) and "type" in description and description.get("type") == "i18n_string":
                description = description.get("value", {}).get(language, description.get("value", {}).get("en-US", ""))

            mdx += f"### {method_upper} {summary}\n\n"

            if description:
                mdx += f"{description}\n\n"

            if operation_id:
                mdx += f"**Operation ID:** `{operation_id}`\n\n"

            # Add request information
            mdx += "#### Request\n\n"

            # Path parameters
            parameters = operation.get("parameters", [])
            path_params = [p for p in parameters if p.get("in") == "path"]
            if path_params:
                mdx += "**Path Parameters:**\n\n"
                mdx += "| Name | Type | Required | Description |\n"
                mdx += "|------|------|----------|-------------|\n"
                for param in path_params:
                    name = param.get("name", "")
                    required = "Yes" if param.get("required", False) else "No"
                    description = param.get("description", "")

                    # Handle I18nString objects for parameter descriptions
                    if (
                        isinstance(description, dict)
                        and "type" in description
                        and description.get("type") == "i18n_string"
                    ):
                        description = description.get("value", {}).get(
                            language, description.get("value", {}).get("en-US", "")
                        )

                    schema = param.get("schema", {})
                    param_type = schema.get("type", "")
                    mdx += f"| {name} | {param_type} | {required} | {description} |\n"
                mdx += "\n"

            # Query parameters
            query_params = [p for p in parameters if p.get("in") == "query"]
            if query_params:
                mdx += "**Query Parameters:**\n\n"
                mdx += "| Name | Type | Required | Description |\n"
                mdx += "|------|------|----------|-------------|\n"
                for param in query_params:
                    name = param.get("name", "")
                    required = "Yes" if param.get("required", False) else "No"
                    description = param.get("description", "")

                    # Handle I18nString objects for parameter descriptions
                    if (
                        isinstance(description, dict)
                        and "type" in description
                        and description.get("type") == "i18n_string"
                    ):
                        description = description.get("value", {}).get(
                            language, description.get("value", {}).get("en-US", "")
                        )

                    schema = param.get("schema", {})
                    param_type = schema.get("type", "")
                    mdx += f"| {name} | {param_type} | {required} | {description} |\n"
                mdx += "\n"

            # Request body
            request_body = operation.get("requestBody", {})
            if request_body:
                mdx += "**Request Body:**\n\n"
                content = request_body.get("content", {})
                for content_type, content_schema in content.items():
                    mdx += f"Content Type: `{content_type}`\n\n"
                    schema = content_schema.get("schema", {})
                    if "$ref" in schema:
                        ref = schema["$ref"].split("/")[-1]
                        mdx += f"Schema: `{ref}`\n\n"
                        # Add schema details from components
                        components = schema.get("components", {})
                        schemas = components.get("schemas", {})
                        if ref in schemas:
                            mdx += "```json\n"
                            mdx += json.dumps(schemas[ref], indent=2)
                            mdx += "\n```\n\n"
                    else:
                        mdx += "```json\n"
                        mdx += json.dumps(schema, indent=2)
                        mdx += "\n```\n\n"

            # Add response information
            mdx += "#### Responses\n\n"
            responses = operation.get("responses", {})
            for status_code, response in sorted(responses.items()):
                description = response.get("description", "")

                # Handle I18nString objects for response descriptions
                if isinstance(description, dict) and "type" in description and description.get("type") == "i18n_string":
                    description = description.get("value", {}).get(
                        language, description.get("value", {}).get("en-US", "")
                    )

                mdx += f"**{status_code}**: {description}\n\n"

                content = response.get("content", {})
                for content_type, content_schema in content.items():
                    mdx += f"Content Type: `{content_type}`\n\n"
                    schema = content_schema.get("schema", {})
                    if "$ref" in schema:
                        ref = schema["$ref"].split("/")[-1]
                        mdx += f"Schema: `{ref}`\n\n"
                        # Add schema details from components
                        components = schema.get("components", {})
                        schemas = components.get("schemas", {})
                        if ref in schemas:
                            mdx += "```json\n"
                            mdx += json.dumps(schemas[ref], indent=2)
                            mdx += "\n```\n\n"
                    else:
                        mdx += "```json\n"
                        mdx += json.dumps(schema, indent=2)
                        mdx += "\n```\n\n"

            # Add example
            mdx += "#### Example\n\n"
            mdx += "```bash\n"
            example_url = path.replace("{", "${")
            mdx += f"curl -X {method_upper} \\\n"
            mdx += f"  'https://api.example.com{example_url}' \\\n"
            mdx += "  -H 'Authorization: Bearer YOUR_API_KEY' \\\n"
            if request_body and "application/json" in request_body.get("content", {}):
                mdx += "  -H 'Content-Type: application/json' \\\n"
                mdx += "  -d '{}'\n"
            else:
                mdx += "\n"
            mdx += "```\n\n"

            mdx += "---\n\n"

    return mdx
