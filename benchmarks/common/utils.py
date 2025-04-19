"""
Shared utilities for benchmarking.

This module contains utility functions used in benchmarks.
"""

import random
import string
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List

from benchmarks.common.models import UserRole

# Constants for generating test data
FIRST_NAMES = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth",
              "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor",
             "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson"]
DOMAINS = ["example.com", "test.org", "benchmark.net", "demo.io", "sample.dev"]
CITIES = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"]
STATES = ["NY", "CA", "IL", "TX", "AZ", "PA", "FL", "OH", "MI", "GA"]
COUNTRIES = ["US", "CA", "UK", "AU", "DE", "FR", "JP", "CN", "BR", "IN"]
TAGS = ["test", "user", "api", "benchmark", "performance", "flask", "openapi", "python", "web", "rest",
       "http", "json", "database", "frontend", "backend", "fullstack", "mobile", "desktop", "cloud", "security"]
THEMES = ["light", "dark", "system", "blue", "green", "red", "purple", "orange", "custom"]
LANGUAGES = ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"]
TIMEZONES = ["UTC", "America/New_York", "Europe/London", "Asia/Tokyo", "Australia/Sydney", "Pacific/Auckland"]
EMAIL_FREQUENCIES = ["daily", "weekly", "monthly", "never"]


def generate_random_string(length: int = 10) -> str:
    """Generate a random string of fixed length."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_random_date(start_date: datetime = datetime(2020, 1, 1),
                        end_date: datetime = datetime.now()) -> str:
    """Generate a random date between start_date and end_date."""
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    random_date = start_date + timedelta(days=random_number_of_days)
    return random_date.isoformat()


def generate_address() -> Dict[str, Any]:
    """Generate a random address."""
    return {
        "street": f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Pine', 'Maple', 'Cedar'])} {random.choice(['St', 'Ave', 'Blvd', 'Rd', 'Ln'])}",
        "city": random.choice(CITIES),
        "state": random.choice(STATES),
        "postal_code": f"{random.randint(10000, 99999)}",
        "country": random.choice(COUNTRIES),
        "is_primary": random.choice([True, False])
    }


def generate_contact_info() -> Dict[str, Any]:
    """Generate random contact information."""
    return {
        "phone": f"+1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}",
        "alternative_email": f"{generate_random_string(8)}@{random.choice(DOMAINS)}",
        "emergency_contact": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}: +1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}"
    }


def generate_preferences() -> Dict[str, Any]:
    """Generate random user preferences."""
    return {
        "theme": random.choice(THEMES),
        "notifications_enabled": random.choice([True, False]),
        "language": random.choice(LANGUAGES),
        "timezone": random.choice(TIMEZONES),
        "email_frequency": random.choice(EMAIL_FREQUENCIES)
    }


def generate_metadata() -> Dict[str, Any]:
    """Generate random metadata."""
    return {
        "last_login_ip": f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
        "browser": random.choice(["Chrome", "Firefox", "Safari", "Edge"]),
        "os": random.choice(["Windows", "macOS", "Linux", "iOS", "Android"]),
        "registration_source": random.choice(["web", "mobile", "api", "import"]),
        "account_tier": random.choice(["free", "basic", "premium", "enterprise"]),
        "custom_field_1": generate_random_string(),
        "custom_field_2": random.randint(1000, 9999)
    }


# Generate complex test data
USER_DATA = []
for i in range(1, 101):
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    username = f"{first_name.lower()}{last_name.lower()}{random.randint(1, 999)}"
    
    user = {
        "username": username,
        "email": f"{username}@{random.choice(DOMAINS)}",
        "full_name": f"{first_name} {last_name}",
        "age": random.randint(18, 80),
        "is_active": random.choice([True, False]),
        "role": random.choice([role.value for role in UserRole]),
        "tags": random.sample(TAGS, k=random.randint(1, 8)),
        "addresses": [generate_address() for _ in range(random.randint(1, 3))],
        "contact_info": generate_contact_info() if random.random() > 0.3 else None,
        "preferences": generate_preferences() if random.random() > 0.2 else None,
        "metadata": generate_metadata() if random.random() > 0.1 else {}
    }
    USER_DATA.append(user)

# Base query parameters
BASE_QUERY_PARAMS = {
    "include_inactive": ["true", "false"],
    "sort_by": ["username", "email", "full_name", "age", "created_at"],
    "sort_order": ["asc", "desc"],
    "limit": ["10", "20", "50", "100"],
    "offset": ["0", "10", "20", "50"],
    "filter_role": [role.value for role in UserRole] + [""],
    "search": ["", "test", "user", "admin"],
    "min_age": ["", "18", "25", "30", "40"],
    "max_age": ["", "30", "40", "50", "65"],
    "tags": ["", "test", "api,web", "python,flask,api"],
    "created_after": ["", "2022-01-01T00:00:00Z"],
    "created_before": ["", "2023-01-01T00:00:00Z"]
}


def get_random_user_data() -> Dict[str, Any]:
    """Get a random user data dictionary."""
    # Add a small delay to simulate real-world processing
    if random.random() < 0.05:  # 5% chance of a small delay
        time.sleep(random.uniform(0.001, 0.01))
    return random.choice(USER_DATA)


def get_random_user_id() -> str:
    """Get a random user ID."""
    return f"user-{random.randint(1000, 9999)}"


def get_query_params() -> str:
    """Get random query parameters for benchmarking."""
    # Randomly select a subset of parameters to include
    params = {}
    for key, values in BASE_QUERY_PARAMS.items():
        # 50% chance to include each parameter
        if random.random() > 0.5:
            params[key] = random.choice(values)
    
    # Always include at least these basic parameters
    if "include_inactive" not in params:
        params["include_inactive"] = random.choice(BASE_QUERY_PARAMS["include_inactive"])
    if "sort_by" not in params:
        params["sort_by"] = random.choice(BASE_QUERY_PARAMS["sort_by"])
    if "limit" not in params:
        params["limit"] = random.choice(BASE_QUERY_PARAMS["limit"])
    
    # Convert to URL query string
    query_string = "?" + "&".join([f"{k}={v}" for k, v in params.items()])
    return query_string


def get_performance_metrics() -> Dict[str, Any]:
    """Get performance metrics for the current request."""
    return {
        "timestamp": datetime.now().isoformat(),
        "cpu_usage": random.uniform(0.1, 100.0),
        "memory_usage": random.uniform(10.0, 1024.0),
        "request_duration_ms": random.uniform(1.0, 100.0),
        "db_query_count": random.randint(1, 20),
        "db_query_duration_ms": random.uniform(0.5, 50.0),
        "cache_hits": random.randint(0, 10),
        "cache_misses": random.randint(0, 5),
        "status_code": 201,  # For create user operations
        "error_count": 0,
    }