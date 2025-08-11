# --- Django Setup Start ---
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_project.settings.test")
import django

django.setup()
# --- Django Setup End ---


from locust import HttpUser, task, events, exception, constant


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """테스트 시작 전"""
    print("--- Test Start: Creating Test DB and ... ---")
    pass


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """테스트 종료 후"""
    print("--- Test Stop: Cleaning up... ---")
    pass


class HealthCheckAPIUser(HttpUser):
    # wait_time = between(1, 3)
    wait_time = constant(0)

    @task(1)
    def health_check(self):
        self.client.get("/_health")
