from django.conf import settings
from django.db import transaction


class DefaultRouter:
    """Database router"""

    def _get_model_database(self, model):
        """Get the database value from the model's Meta class"""

        return getattr(model._meta, "database", None)

    def db_for_read(self, model, **hints):
        """Database to use for reads"""

        # 1. Connect to the explicitly specified database
        model_database = self._get_model_database(model)
        if model_database:
            return model_database

        # 2. Use the default database inside a "default" transaction block
        if (
            not transaction.get_autocommit()
            and transaction.get_connection("default").in_atomic_block
        ):
            return "default"

        # 3. Otherwise connect to the "replica" database
        return "replica"

    def db_for_write(self, model, **hints):
        """Database to use for writes"""

        # 1. Connect to the explicitly specified database
        model_database = self._get_model_database(model)
        if model_database:
            return model_database

        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        """Check whether a relation is allowed"""

        db_obj1 = self.db_for_write(obj1.__class__, **hints)
        db_obj2 = self.db_for_write(obj2.__class__, **hints)

        # 1. When both objects use the same database
        if db_obj1 and db_obj2:
            return db_obj1 == db_obj2

        # 2. When objects use different databases
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Determine whether migration is allowed"""

        migration_mapping = settings.DATABASE_APPS_MAPPING_FOR_MIGRATIONS
        mapped_db = migration_mapping.get(app_label)

        # 1. Connect to the explicitly specified database
        if mapped_db:
            return db == mapped_db

        # 2. Use the default database inside a "default" transaction block
        return db == "default"
