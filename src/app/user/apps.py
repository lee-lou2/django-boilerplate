from django.apps import AppConfig


class UserConfig(AppConfig):
    name = "app.user"

    def ready(self):
        import app.user.signals
