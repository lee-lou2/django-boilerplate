from django.conf import settings
from django.db import transaction


class DefaultRouter:
    """데이터베이스 라우터"""

    def _get_model_database(self, model):
        """모델의 Meta 클래스에서 database 속성 값 조회"""

        return getattr(model._meta, "database", None)

    def db_for_read(self, model, **hints):
        """읽기에서 사용할 데이터베이스"""

        # 1. 실제 지정한 데이터베이스로 연결
        model_database = self._get_model_database(model)
        if model_database:
            return model_database

        # 2. "default" 트랜잭션 블록 내부는 기본 데이터베이스 연결
        if (
            not transaction.get_autocommit()
            and transaction.get_connection("default").in_atomic_block
        ):
            return "default"

        # 3. 그 외, "replica" 데이터베이스 연결
        return "replica"

    def db_for_write(self, model, **hints):
        """쓰기에서 사용할 데이터베이스"""

        # 1. 실제 지정한 데이터베이스로 연결
        model_database = self._get_model_database(model)
        if model_database:
            return model_database

        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        """연결 허용 여부 확인"""

        db_obj1 = self.db_for_write(obj1.__class__, **hints)
        db_obj2 = self.db_for_write(obj2.__class__, **hints)

        # 1. 같은 데이터베이스에 연결된 경우
        if db_obj1 and db_obj2:
            return db_obj1 == db_obj2

        # 2. 서로 다른 데이터베이스에 연결된 경우
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """마이그레이션 허용 여부 확인"""

        migration_mapping = settings.DATABASE_APPS_MAPPING_FOR_MIGRATIONS
        mapped_db = migration_mapping.get(app_label)

        # 1. 실제 지정한 데이터베이스로 연결
        if mapped_db:
            return db == mapped_db

        # 2. "default" 트랜잭션 블록 내부는 기본 데이터베이스 연결
        return db == "default"
