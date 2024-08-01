import os

from django.conf import settings
from django.core.management import CommandError
from django.core.management.templates import TemplateCommand


class Command(TemplateCommand):
    help = (
        "Creates a Django app directory structure for the given app name in "
        "the current directory or optionally in the given directory."
    )
    missing_args_message = "You must provide an application name."

    def handle(self, **options):
        app_name = options.pop("name")
        options["app_name"] = app_name
        options["camel_case_app_name"] = app_name.capitalize()
        app_dir = os.path.join(settings.BASE_DIR, "app")
        target = os.path.join(app_dir, app_name)
        top_dir = os.path.abspath(os.path.expanduser(target))
        try:
            os.makedirs(top_dir)
            options["template"] = f"file://{app_dir}/common/management/app_template"
            super().handle(app_dir, app_name, target, **options)
        except FileExistsError:
            raise CommandError("'%s' already exists" % top_dir)
        except CommandError:
            self.stderr.write(f'"{app_name}" app is already exists.')
