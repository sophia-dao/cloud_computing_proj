from locust import HttpUser, task, between


class RecipeUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def browse_recipes(self):
        self.client.get(
            "/api/recipes/",
            name="GET /api/recipes/",
        )