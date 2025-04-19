"""
共享的 Pydantic 模型，用于示例应用程序。
"""

from typing import List, Optional
from pydantic import BaseModel, Field

from flask_x_openapi_schema import BaseRespModel
from flask_x_openapi_schema.models import ImageUploadModel, DocumentUploadModel


class ItemRequest(BaseModel):
    """创建项目的请求模型。"""
    name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    price: float = Field(..., description="项目价格")
    tags: List[str] = Field(default_factory=list, description="项目标签")


class ItemResponse(BaseRespModel):
    """项目的响应模型。"""
    id: str = Field(..., description="项目ID")
    name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    price: float = Field(..., description="项目价格")
    tags: List[str] = Field(default_factory=list, description="项目标签")


class QueryParams(BaseModel):
    """查询参数模型。"""
    limit: Optional[int] = Field(10, description="返回结果的最大数量")
    offset: Optional[int] = Field(0, description="结果的偏移量")
    sort_by: Optional[str] = Field("name", description="排序字段")
    order: Optional[str] = Field("asc", description="排序顺序 (asc 或 desc)")


class CustomImageUploadModel(ImageUploadModel):
    """自定义图片上传模型。"""
    allowed_extensions: List[str] = Field(
        default=["jpg", "jpeg", "png"],
        description="允许的文件扩展名"
    )
    max_size: int = Field(
        default=5 * 1024 * 1024,  # 5MB
        description="最大文件大小（字节）"
    )


class CustomDocumentUploadModel(DocumentUploadModel):
    """自定义文档上传模型。"""
    allowed_extensions: List[str] = Field(
        default=["pdf", "doc", "docx"],
        description="允许的文件扩展名"
    )
    max_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="最大文件大小（字节）"
    )