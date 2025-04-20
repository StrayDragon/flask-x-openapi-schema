"""
Locust load test for Flask-RESTful with and without flask-x-openapi-schema.

This file contains a Locust load test that simulates real-world usage of the library.
It compares the performance of a standard Flask-RESTful application versus one using flask-x-openapi-schema.

To run:
    locust -f benchmarks/flask_restful/locustfile.py --headless -u 100 -r 10 -t 30s --csv=benchmarks/results/flask_restful
"""

from locust import HttpUser, task, between

from benchmarks.common.utils import (
    get_random_user_data,
    get_random_user_id,
    get_query_params,
)


class StandardFlaskRestfulUser(HttpUser):
    """User that tests the standard Flask-RESTful implementation."""

    host = "http://localhost:5000"
    wait_time = between(1, 3)

    @task
    def create_user(self):
        """Create a user using the standard Flask-RESTful endpoint."""
        user_data = get_random_user_data()
        user_id = get_random_user_id()
        query_params = get_query_params()

        with self.client.post(
            f"/standard/api/users/{user_id}{query_params}",
            json=user_data,
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Failed with status code: {response.status_code}")


class OpenAPIFlaskRestfulUser(HttpUser):
    """User that tests the flask-x-openapi-schema implementation with Flask-RESTful."""

    host = "http://localhost:5000"
    wait_time = between(1, 3)

    @task
    def create_user(self):
        """Create a user using the OpenAPI Flask-RESTful endpoint."""
        user_data = get_random_user_data()
        user_id = get_random_user_id()
        query_params = get_query_params()

        with self.client.post(
            f"/openapi/api/users/{user_id}{query_params}",
            json=user_data,
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Failed with status code: {response.status_code}")
