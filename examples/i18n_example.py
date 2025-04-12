"""
Example usage of the i18n functionality in the OpenAPI module.
"""

from typing import Optional

from pydantic import Field

from flask_x_openapi_schema import (
    I18nBaseModel,
    I18nString,
    get_current_language,
    openapi_metadata,
    responses_schema,
    set_current_language,
    success_response,
)
from ..models.base import BaseRespModel


# Define a model with internationalized fields
class ItemI18nResponse(I18nBaseModel, BaseRespModel):
    """Response model for an item with internationalized fields."""

    id: str = Field(..., description="The ID of the item")
    name: str = Field(..., description="The name of the item")
    description: I18nString = Field(..., description="The description of the item (internationalized)")
    category: Optional[I18nString] = Field(None, description="The category of the item (internationalized)")


# Example API resource with internationalized metadata
class ItemsApiExample:
    """Example API resource using internationalized OpenAPI metadata."""

    @openapi_metadata(
        summary=I18nString(
            {
                "en-US": "Get an item",
                "zh-Hans": "获取一个项目",
                "ja-JP": "アイテムを取得する",
            }
        ),
        description=I18nString(
            {
                "en-US": "Get an item by ID from the database",
                "zh-Hans": "通过ID从数据库获取一个项目",
                "ja-JP": "IDからデータベースからアイテムを取得する",
            }
        ),
        tags=["Items"],
        operation_id="getItem",
        responses=responses_schema(
            success_responses={
                "200": success_response(
                    model=ItemI18nResponse,
                    description=I18nString(
                        {
                            "en-US": "Item retrieved successfully",
                            "zh-Hans": "项目检索成功",
                            "ja-JP": "アイテムが正常に取得されました",
                        }
                    ),
                ),
            },
            errors={
                "404": I18nString(
                    {
                        "en-US": "Item not found",
                        "zh-Hans": "找不到项目",
                        "ja-JP": "アイテムが見つかりません",
                    }
                ),
            },
        ),
    )
    def get(self, tenant_id: str, item_id: str):
        """
        Get an item by ID.

        This example demonstrates how to use internationalized fields in API responses.
        """
        # Create a response with internationalized fields
        return ItemI18nResponse(
            id=item_id,
            name="Example Item",
            description=I18nString(
                {
                    "en-US": "This is an example item",
                    "zh-Hans": "这是一个示例项目",
                    "ja-JP": "これはサンプルアイテムです",
                }
            ),
            category=I18nString(
                {
                    "en-US": "Examples",
                    "zh-Hans": "示例",
                    "ja-JP": "例",
                }
            ),
        )


# Example of how to use the i18n functionality
def demonstrate_i18n():
    """Demonstrate how to use the i18n functionality."""

    # Create an instance of the API resource
    api = ItemsApiExample()

    # Get the OpenAPI metadata in English
    set_current_language("en-US")
    print(f"Current language: {get_current_language()}")
    metadata_en = api.get._openapi_metadata
    print(f"Summary (EN): {metadata_en.get('summary')}")
    print(f"Description (EN): {metadata_en.get('description')}")

    # Get the OpenAPI metadata in Chinese
    set_current_language("zh-Hans")
    print(f"Current language: {get_current_language()}")
    metadata_zh = api.get._openapi_metadata
    print(f"Summary (ZH): {metadata_zh.get('summary')}")
    print(f"Description (ZH): {metadata_zh.get('description')}")

    # Get the OpenAPI metadata in Japanese
    set_current_language("ja-JP")
    print(f"Current language: {get_current_language()}")
    metadata_ja = api.get._openapi_metadata
    print(f"Summary (JA): {metadata_ja.get('summary')}")
    print(f"Description (JA): {metadata_ja.get('description')}")

    # Get a response in different languages
    response_en = api.get("tenant1", "item1")
    print(f"Response description (EN): {response_en.description}")

    set_current_language("zh-Hans")
    response_zh = api.get("tenant1", "item1")
    print(f"Response description (ZH): {response_zh.description}")

    set_current_language("ja-JP")
    response_ja = api.get("tenant1", "item1")
    print(f"Response description (JA): {response_ja.description}")


if __name__ == "__main__":
    demonstrate_i18n()
