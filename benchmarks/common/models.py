"""
Shared models for benchmarking.

This module contains Pydantic models used in benchmarks.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

from flask_x_openapi_schema.models.base import BaseRespModel


class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"
    GUEST = "guest"


class AddressModel(BaseModel):
    """Address model for users."""
    street: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State or province")
    postal_code: str = Field(..., description="Postal code")
    country: str = Field(..., description="Country")
    is_primary: bool = Field(True, description="Whether this is the primary address")

    model_config = {"arbitrary_types_allowed": True}


class ContactInfo(BaseModel):
    """Contact information model."""
    phone: Optional[str] = Field(None, description="Phone number")
    alternative_email: Optional[str] = Field(None, description="Alternative email")
    emergency_contact: Optional[str] = Field(None, description="Emergency contact")

    model_config = {"arbitrary_types_allowed": True}


class Preferences(BaseModel):
    """User preferences model."""
    theme: str = Field("light", description="UI theme preference")
    notifications_enabled: bool = Field(True, description="Whether notifications are enabled")
    language: str = Field("en", description="Preferred language")
    timezone: str = Field("UTC", description="Preferred timezone")
    email_frequency: str = Field("daily", description="Email notification frequency")

    model_config = {"arbitrary_types_allowed": True}


class UserRequest(BaseModel):
    """Request model for creating a user."""

    username: str = Field(..., description="The username", min_length=3, max_length=50)
    email: str = Field(..., description="The email address")
    full_name: str = Field(..., description="The full name")
    age: int = Field(..., description="The age", ge=18, le=120)
    is_active: bool = Field(True, description="Whether the user is active")
    role: UserRole = Field(UserRole.USER, description="User role")
    tags: List[str] = Field(default_factory=list, description="Tags for the user")
    addresses: List[AddressModel] = Field(default_factory=list, description="User addresses")
    contact_info: Optional[ContactInfo] = Field(None, description="Additional contact information")
    preferences: Optional[Preferences] = Field(None, description="User preferences")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator('email')
    def email_must_be_valid(cls, v):
        if not v or '@' not in v:
            raise ValueError('must be a valid email')
        return v

    model_config = {"arbitrary_types_allowed": True}


class UserQueryParams(BaseModel):
    """Query parameters for user endpoints."""

    include_inactive: bool = Field(False, description="Include inactive users")
    sort_by: str = Field("username", description="Field to sort by")
    sort_order: str = Field("asc", description="Sort order (asc or desc)")
    limit: int = Field(10, description="Maximum number of results", ge=1, le=100)
    offset: int = Field(0, description="Offset for pagination", ge=0)
    filter_role: Optional[UserRole] = Field(None, description="Filter by role")
    search: Optional[str] = Field(None, description="Search term for username or full name")
    min_age: Optional[int] = Field(None, description="Minimum age", ge=18, le=120)
    max_age: Optional[int] = Field(None, description="Maximum age", ge=18, le=120)
    tags: Optional[List[str]] = Field(None, description="Filter by tags (comma-separated)")
    created_after: Optional[str] = Field(None, description="Filter by creation date (ISO format)")
    created_before: Optional[str] = Field(None, description="Filter by creation date (ISO format)")

    model_config = {"arbitrary_types_allowed": True}


class UserStats(BaseModel):
    """User statistics model."""
    login_count: int = Field(0, description="Number of logins")
    last_login: Optional[str] = Field(None, description="Last login timestamp")
    post_count: int = Field(0, description="Number of posts")
    comment_count: int = Field(0, description="Number of comments")
    reputation: int = Field(0, description="User reputation score")

    model_config = {"arbitrary_types_allowed": True}


class UserResponse(BaseRespModel):
    """Response model for a user."""

    id: str = Field(..., description="The user ID")
    username: str = Field(..., description="The username")
    email: str = Field(..., description="The email address")
    full_name: str = Field(..., description="The full name")
    age: int = Field(..., description="The age")
    is_active: bool = Field(True, description="Whether the user is active")
    role: UserRole = Field(UserRole.USER, description="User role")
    tags: List[str] = Field(default_factory=list, description="Tags for the user")
    addresses: List[AddressModel] = Field(default_factory=list, description="User addresses")
    contact_info: Optional[ContactInfo] = Field(None, description="Additional contact information")
    preferences: Optional[Preferences] = Field(None, description="User preferences")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    stats: UserStats = Field(default_factory=UserStats, description="User statistics")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")

    model_config = {"arbitrary_types_allowed": True}