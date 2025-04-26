"""Factory classes for generating valid test data.

This module contains factory classes for generating valid test data using polyfactory.
"""

from polyfactory.factories.pydantic_factory import ModelFactory

from benchmarks.common.models import (
    AddressModel,
    ContactInfo,
    Preferences,
    UserQueryParams,
    UserRequest,
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
