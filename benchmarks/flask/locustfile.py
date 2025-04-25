"""
Locust load test for Flask with and without flask-x-openapi-schema.

This file contains a Locust load test that simulates real-world usage of the library.
It compares the performance of a standard Flask application versus one using flask-x-openapi-schema.

To run:
    locust -f benchmarks/flask/locustfile.py --headless -u 10 -r 10 -t 10s --csv=benchmarks/results/flask
"""

from locust import HttpUser, task, between

from benchmarks.common.utils import (
    get_random_user_data,
    get_random_user_id,
    get_query_params,
)

class StandardFlaskUser(HttpUser):
    """User that tests the standard Flask implementation."""

    host = "http://localhost:5000"
    wait_time = between(0.1, 0.5)  # Faster requests to complete quickly

    @task
    def create_user(self):
        """Create a user using the standard Flask endpoint."""
        user_data = get_random_user_data()
        user_id = get_random_user_id()
        query_params = get_query_params()

        with self.client.post(
            f"/standard/api/users/{user_id}",
            params=query_params,
            json=user_data,
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Failed with status code: {response.status_code}")


class OpenAPIFlaskUser(HttpUser):
    """User that tests the flask-x-openapi-schema implementation."""

    host = "http://localhost:5000"
    wait_time = between(0.1, 0.5)  # Faster requests to complete quickly

    @task
    def create_user(self):
        """Create a user using the OpenAPI Flask endpoint."""
        user_data = get_random_user_data()
        user_id = get_random_user_id()
        query_params = get_query_params()

        with self.client.post(
            f"/openapi/api/users/{user_id}",
            params=query_params,
            json=user_data,
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Failed with status code: {response.status_code}")