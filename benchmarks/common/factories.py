"""
Factory classes for generating valid test data.

This module contains factory classes for generating valid test data using polyfactory.
"""

import random
from polyfactory.factories.pydantic_factory import ModelFactory
from benchmarks.common.models import (
    UserRequest,
    UserQueryParams,
    UserRole,
    AddressModel,
    ContactInfo,
    Preferences,
)


class AddressFactory(ModelFactory[AddressModel]):
    """Factory for generating valid address data."""

    __model__ = AddressModel


class ContactInfoFactory(ModelFactory[ContactInfo]):
    """Factory for generating valid contact information."""

    __model__ = ContactInfo


class PreferencesFactory(ModelFactory[Preferences]):
    """Factory for generating valid user preferences."""

    __model__ = Preferences


class UserRequestFactory(ModelFactory[UserRequest]):
    """Factory for generating valid user request data."""

    __model__ = UserRequest


class UserQueryParamsFactory(ModelFactory[UserQueryParams]):
    """Factory for generating valid query parameters."""

    __model__ = UserQueryParams

    # 使用自定义提供者来确保生成有效的数据
    __custom_providers__ = {
        "filter_role": lambda: UserRole.USER.value,
    }
