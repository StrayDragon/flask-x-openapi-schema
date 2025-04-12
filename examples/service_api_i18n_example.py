"""
Example of how to use the i18n functionality with service API endpoints.

This example demonstrates how to:
1. Create Pydantic models with internationalized fields
2. Use the I18nString class for API documentation
3. Generate OpenAPI schemas in multiple languages
"""

from uuid import UUID

from flask_restful import Resource  # type: ignore
from pydantic import BaseModel, Field

from flask_x_openapi_schema import (
    I18nBaseModel,
    I18nString,
    get_current_language,
    openapi_metadata,
    responses_schema,
    set_current_language,
    success_response,
)
from flask_x_openapi_schema.models.base import BaseRespModel


# Define models with internationalized fields
class ServiceI18nResponse(I18nBaseModel, BaseRespModel):
    """Response model with internationalized fields."""

    id: UUID = Field(..., description="The ID of the service")
    name: str = Field(..., description="The name of the service")
    description: I18nString = Field(
        ..., description="The description of the service (internationalized)"
    )
    status: str = Field(..., description="The status of the service")
    created_at: str = Field(..., description="The creation timestamp")
    updated_at: str = Field(..., description="The last update timestamp")


class ServiceCreateRequest(BaseModel):
    """Request model for creating a service."""

    name: str = Field(..., description="The name of the service")
    description: str = Field(..., description="The description of the service")


class ServiceListResponse(BaseRespModel):
    """Response model for a list of services."""

    data: list[ServiceI18nResponse] = Field(..., description="List of services")


# Example API resource with internationalized metadata
class ServiceApiExample(Resource):
    """Example API resource using internationalized OpenAPI metadata."""

    @openapi_metadata(
        summary=I18nString(
            {
                "en-US": "Create a service",
                "zh-Hans": "创建服务",
                "ja-JP": "サービスを作成する",
            }
        ),
        description=I18nString(
            {
                "en-US": "Create a new service with the provided information",
                "zh-Hans": "使用提供的信息创建新服务",
                "ja-JP": "提供された情報で新しいサービスを作成する",
            }
        ),
        tags=["Services"],
        operation_id="createService",
        responses=responses_schema(
            success_responses={
                "201": success_response(
                    model=ServiceI18nResponse,
                    description=I18nString(
                        {
                            "en-US": "Service created successfully",
                            "zh-Hans": "服务创建成功",
                            "ja-JP": "サービスが正常に作成されました",
                        }
                    ),
                ),
            },
            errors={
                "400": I18nString(
                    {
                        "en-US": "Invalid request",
                        "zh-Hans": "无效请求",
                        "ja-JP": "無効なリクエスト",
                    }
                ),
                "403": I18nString(
                    {
                        "en-US": "Permission denied",
                        "zh-Hans": "权限被拒绝",
                        "ja-JP": "権限が拒否されました",
                    }
                ),
            },
        ),
    )
    def post(self, tenant_id: str, x_request_body: ServiceCreateRequest):
        """
        Create a new service.

        This example demonstrates how to use internationalized fields in API responses.
        """
        # Create a response with internationalized fields
        return ServiceI18nResponse(
            id=UUID("00000000-0000-0000-0000-000000000001"),
            name=x_request_body.name,
            description=I18nString(
                {
                    "en-US": x_request_body.description,
                    "zh-Hans": f"[中文] {x_request_body.description}",
                    "ja-JP": f"[日本語] {x_request_body.description}",
                }
            ),
            status="active",
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
        ), 201

    @openapi_metadata(
        summary=I18nString(
            {
                "en-US": "Get services",
                "zh-Hans": "获取服务列表",
                "ja-JP": "サービス一覧を取得する",
            }
        ),
        description=I18nString(
            {
                "en-US": "Get a list of all services",
                "zh-Hans": "获取所有服务的列表",
                "ja-JP": "すべてのサービスのリストを取得する",
            }
        ),
        tags=["Services"],
        operation_id="getServices",
        responses=responses_schema(
            success_responses={
                "200": success_response(
                    model=ServiceListResponse,
                    description=I18nString(
                        {
                            "en-US": "List of services",
                            "zh-Hans": "服务列表",
                            "ja-JP": "サービス一覧",
                        }
                    ),
                ),
            },
            errors={
                "403": I18nString(
                    {
                        "en-US": "Permission denied",
                        "zh-Hans": "权限被拒绝",
                        "ja-JP": "権限が拒否されました",
                    }
                ),
            },
        ),
    )
    def get(self, tenant_id: str):
        """
        Get a list of services.

        This example demonstrates how to use internationalized fields in API responses.
        """
        # Create a response with internationalized fields
        return ServiceListResponse(
            data=[
                ServiceI18nResponse(
                    id=UUID("00000000-0000-0000-0000-000000000001"),
                    name="Service 1",
                    description=I18nString(
                        {
                            "en-US": "This is service 1",
                            "zh-Hans": "这是服务1",
                            "ja-JP": "これはサービス1です",
                        }
                    ),
                    status="active",
                    created_at="2023-01-01T00:00:00Z",
                    updated_at="2023-01-01T00:00:00Z",
                ),
                ServiceI18nResponse(
                    id=UUID("00000000-0000-0000-0000-000000000002"),
                    name="Service 2",
                    description=I18nString(
                        {
                            "en-US": "This is service 2",
                            "zh-Hans": "这是服务2",
                            "ja-JP": "これはサービス2です",
                        }
                    ),
                    status="inactive",
                    created_at="2023-01-02T00:00:00Z",
                    updated_at="2023-01-02T00:00:00Z",
                ),
            ]
        )


# Example of how to use the i18n functionality
def demonstrate_service_api_i18n():
    """Demonstrate how to use the i18n functionality with service API endpoints."""

    # Create an instance of the API resource
    api = ServiceApiExample()

    # Get the OpenAPI metadata in English
    set_current_language("en-US")
    print(f"Current language: {get_current_language()}")
    metadata_en = api.post._openapi_metadata
    print(f"Summary (EN): {metadata_en.get('summary')}")
    print(f"Description (EN): {metadata_en.get('description')}")

    # Get the OpenAPI metadata in Chinese
    set_current_language("zh-Hans")
    print(f"Current language: {get_current_language()}")
    metadata_zh = api.post._openapi_metadata
    print(f"Summary (ZH): {metadata_zh.get('summary')}")
    print(f"Description (ZH): {metadata_zh.get('description')}")

    # Get the OpenAPI metadata in Japanese
    set_current_language("ja-JP")
    print(f"Current language: {get_current_language()}")
    metadata_ja = api.post._openapi_metadata
    print(f"Summary (JA): {metadata_ja.get('summary')}")
    print(f"Description (JA): {metadata_ja.get('description')}")

    # Create a request and get a response in different languages
    request = ServiceCreateRequest(
        name="Test Service", description="This is a test service"
    )

    set_current_language("en-US")
    response_en, _ = api.post("tenant1", request)
    print(f"Response description (EN): {response_en.description}")

    set_current_language("zh-Hans")
    response_zh, _ = api.post("tenant1", request)
    print(f"Response description (ZH): {response_zh.description}")

    set_current_language("ja-JP")
    response_ja, _ = api.post("tenant1", request)
    print(f"Response description (JA): {response_ja.description}")


if __name__ == "__main__":
    demonstrate_service_api_i18n()
