import os

from django.conf import settings
from django.core.management import CommandError
from django.core.management.templates import TemplateCommand


class Command(TemplateCommand):
    help = (
        "Creates a Django app directory structure for the given app name in the "
        "current directory or optionally in a new directory given by the first "
        "argument. The app name is the name of the app directory. The app name "
        "may contain only letters, numbers and underscores."
    )
    missing_args_message = "Please provide an app name."

    def handle(self, **options):
        app_name = options.pop("name")

        self._create_app(
            app_name=app_name,
            template_name="app_template",
            **options,
        )

    def _create_app(self, app_name, template_name, **options):
        target = f"apps/{app_name}"
        top_dir = os.path.abspath(os.path.expanduser(target))
        try:
            self._make_dirs(top_dir)
            options["template"] = "file://" + str(
                settings.BASE_DIR / "apps" / "common" / "management" / template_name
            )
            super().handle("app", app_name, target, **options)
        except CommandError:
            self.stderr.write(f'"{app_name}" app is already exists.')

    @staticmethod
    def _make_dirs(top_dir):
        try:
            os.makedirs(top_dir)
        except FileExistsError:
            raise CommandError("'%s' already exists" % top_dir)
        except OSError as e:
            raise CommandError(e)
