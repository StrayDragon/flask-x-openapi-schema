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

    # 使用自定义提供者来确保生成有效的数据
    __custom_providers__ = {
        "street": lambda: f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Pine', 'Maple', 'Cedar'])} {random.choice(['St', 'Ave', 'Blvd', 'Rd', 'Ln'])}",
        "city": lambda: random.choice(
            [
                "New York",
                "Los Angeles",
                "Chicago",
                "Houston",
                "Phoenix",
                "Philadelphia",
                "San Antonio",
                "San Diego",
                "Dallas",
                "San Jose",
            ]
        ),
        "state": lambda: random.choice(
            ["NY", "CA", "IL", "TX", "AZ", "PA", "FL", "OH", "MI", "GA"]
        ),
        "postal_code": lambda: f"{random.randint(10000, 99999)}",
        "country": lambda: random.choice(
            ["US", "CA", "UK", "AU", "DE", "FR", "JP", "CN", "BR", "IN"]
        ),
        "is_primary": lambda: random.choice([True, False]),
    }


class ContactInfoFactory(ModelFactory[ContactInfo]):
    """Factory for generating valid contact information."""

    __model__ = ContactInfo

    # 使用自定义提供者来确保生成有效的数据
    __custom_providers__ = {
        "phone": lambda: f"+1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}",
        "emergency_contact": lambda: f"{random.choice(['John', 'Mary', 'Robert', 'Linda', 'William'])} {random.choice(['Smith', 'Johnson', 'Williams', 'Jones', 'Brown'])}: +1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}",
    }


class PreferencesFactory(ModelFactory[Preferences]):
    """Factory for generating valid user preferences."""

    __model__ = Preferences

    # 使用自定义提供者来确保生成有效的数据
    __custom_providers__ = {
        "theme": lambda: random.choice(
            [
                "light",
                "dark",
                "system",
                "blue",
                "green",
                "red",
                "purple",
                "orange",
                "custom",
            ]
        ),
        "notifications_enabled": lambda: random.choice([True, False]),
        "language": lambda: random.choice(
            ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"]
        ),
        "timezone": lambda: random.choice(
            [
                "UTC",
                "America/New_York",
                "Europe/London",
                "Asia/Tokyo",
                "Australia/Sydney",
                "Pacific/Auckland",
            ]
        ),
        "email_frequency": lambda: random.choice(
            ["daily", "weekly", "monthly", "never"]
        ),
    }


class UserRequestFactory(ModelFactory[UserRequest]):
    """Factory for generating valid user request data."""

    __model__ = UserRequest

    # 使用自定义提供者来确保生成有效的数据
    __custom_providers__ = {
        "username": lambda: f"{random.choice(['user', 'test', 'admin', 'support'])}{random.randint(1, 999)}",
        "full_name": lambda: f"{random.choice(['John', 'Mary', 'Robert', 'Linda', 'William', 'David', 'Richard', 'Susan', 'Joseph', 'Jessica'])} {random.choice(['Smith', 'Johnson', 'Williams', 'Jones', 'Brown', 'Davis', 'Miller', 'Wilson', 'Moore', 'Taylor'])}",
        "age": lambda: random.randint(18, 80),
    }

    @classmethod
    def get_provider_map(cls):
        provider_map = super().get_provider_map()
        provider_map.update(
            {
                AddressModel: lambda: AddressFactory.build(),
                ContactInfo: lambda: ContactInfoFactory.build(),
                Preferences: lambda: PreferencesFactory.build(),
                UserRole: lambda: UserRole.USER,  # Default to USER role for consistency
            }
        )
        return provider_map


class UserQueryParamsFactory(ModelFactory[UserQueryParams]):
    """Factory for generating valid query parameters."""

    __model__ = UserQueryParams

    # 使用自定义提供者来确保生成有效的数据
    __custom_providers__ = {
        "tags": lambda: ",".join(
            random.sample(
                ["test", "api", "user", "admin", "web", "mobile", "python", "flask"],
                k=random.randint(1, 3),
            )
        ),
        "min_age": lambda: random.randint(18, 60),
        "max_age": lambda: random.randint(61, 120),
        "filter_role": lambda: UserRole.USER,  # Default to USER role for consistency
    }
