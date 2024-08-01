import contextvars

from django.conf import settings
from django.db import transaction

# API 별 상태 관리
db_for_read = contextvars.ContextVar("db_for_read", default="replica")


class DefaultRouter:
    """데이터베이스 라우터"""

    app_labels = list(set(settings.DATABASES.keys()) - {"default", "replica"})

    def db_for_read(self, model, **hints):
        """읽기에서 사용할 데이터베이스"""

        # 1. 기본 라우팅
        if model._meta.app_label in self.app_labels:
            return model._meta.app_label

        # 2. "default" 트랜잭션 블록 내부는 기본 데이터베이스 연결
        if (
            not transaction.get_autocommit()
            and transaction.get_connection("default").in_atomic_block
        ):
            return "default"

        # 3. "replica" 기본 적용, write 가 한 번이라도 있었던 경우 "default" 적용
        return db_for_read.get()

    def db_for_write(self, model, **hints):
        """쓰기에서 사용할 데이터베이스"""

        # 1. 기본 라우팅
        if model._meta.app_label in self.app_labels:
            return model._meta.app_label

        # 2. write 가 발생한 경우 db_for_read 값을 "default"로 설정
        db_for_read.set("default")

        # 3. 그 외, "default" 로 적용
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        """연결 허용 여부 확인"""

        # 1. 동일한 기본 데이터베이스 엔드포인트는 연결 허용
        default_host = settings.DATABASES.get("default", {}).get("HOST")
        replica_host = settings.DATABASES.get("replica", {}).get("HOST")
        db_list = [
            key
            for key, value in settings.DATABASES.items()
            if value.get("HOST") in [default_host, replica_host]
        ]
        if obj1._state.db in db_list and obj2._state.db in db_list:
            return True

        # 2. Host 가 동일한 경우 연결 허용
        obj1_host = settings.DATABASES.get(str(obj1._state.db), {}).get("HOST")
        obj2_host = settings.DATABASES.get(str(obj2._state.db), {}).get("HOST")
        if obj1_host is not None and obj1_host == obj2_host:
            return True

        # 3. 그 외, 다음 라우터 또는 "default" 로 적용
        return None


class DBRouterMiddleware:
    """기본 라우터 지정 미들웨어"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 시작 종료시 기본 값 설정
        db_for_read.set("replica")
        response = self.get_response(request)
        return response
