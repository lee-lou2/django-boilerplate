from django.apps import AppConfig


class DeviceConfig(AppConfig):
    name = "apps.device"

    def ready(self):
        import sys

        if "runserver" in sys.argv or "gunicorn" in sys.argv:
            from conf import firebase_config

            firebase_config.initialize_firebase()
