"""Locust load test for Flask-RESTful with and without flask-x-openapi-schema.

This file contains a Locust load test that simulates real-world usage of the library.
It compares the performance of a standard Flask-RESTful application versus one using flask-x-openapi-schema.

To run:
    locust -f benchmarks/flask_restful/locustfile.py --headless -u 10 -r 10 -t 10s --csv=benchmarks/results/flask_restful
"""

from locust import HttpUser, between, task

from benchmarks.common.utils import (
    get_query_params,
    get_random_user_data,
    get_random_user_id,
)


class StandardFlaskRestfulUser(HttpUser):
    """User that tests the standard Flask-RESTful implementation."""

    host = "http://localhost:5001"
    wait_time = between(0.1, 0.5)  # Faster requests to complete quickly

    @task
    def create_user(self):
        """Create a user using the standard Flask-RESTful endpoint."""
        user_data = get_random_user_data()
        user_id = get_random_user_id()
        query_params = get_query_params()

        with self.client.post(
            f"/standard/api/users/{user_id}",
            params=query_params,
            json=user_data,
            catch_response=True,
        ) as response:
            if response.status_code in {200, 201}:
                response.success()
            else:
                response.failure(f"Failed with status code: {response.status_code}")


class OpenAPIFlaskRestfulUser(HttpUser):
    """User that tests the flask-x-openapi-schema implementation with Flask-RESTful."""

    host = "http://localhost:5001"
    wait_time = between(0.1, 0.5)  # Faster requests to complete quickly

    @task
    def create_user(self):
        """Create a user using the OpenAPI Flask-RESTful endpoint."""
        user_data = get_random_user_data()
        user_id = get_random_user_id()
        query_params = get_query_params()

        with self.client.post(
            f"/openapi/api/users/{user_id}",
            params=query_params,
            json=user_data,
            catch_response=True,
        ) as response:
            if response.status_code in {200, 201}:
                response.success()
            else:
                response.failure(f"Failed with status code: {response.status_code}")
