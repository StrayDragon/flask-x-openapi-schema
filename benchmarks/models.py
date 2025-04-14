"""
Common models for benchmarks.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

from flask_x_openapi_schema.models.base import BaseRespModel


class UserRequest(BaseModel):
    """User request model."""

    username: str = Field(..., description="The username")
    email: str = Field(..., description="The email address")
    full_name: str = Field(..., description="The full name")
    age: int = Field(..., description="The age")
    is_active: bool = Field(True, description="Whether the user is active")
    tags: List[str] = Field(default_factory=list, description="User tags")


class UserQueryParams(BaseModel):
    """User query parameters."""

    include_inactive: bool = Field(False, description="Include inactive users")
    sort_by: str = Field("username", description="Field to sort by")
    limit: int = Field(10, description="Maximum number of results")
    offset: int = Field(0, description="Offset for pagination")


class UserResponse(BaseRespModel):
    """User response model."""

    id: str = Field(..., description="The user ID")
    username: str = Field(..., description="The username")
    email: str = Field(..., description="The email address")
    full_name: str = Field(..., description="The full name")
    age: int = Field(..., description="The age")
    is_active: bool = Field(..., description="Whether the user is active")
    tags: List[str] = Field(..., description="User tags")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
