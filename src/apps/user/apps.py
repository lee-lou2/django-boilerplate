from django.apps import AppConfig


class UserConfig(AppConfig):
    name = "apps.user"

    def ready(self):
        import apps.user.signals
