import time
from collections import Counter

from django.db import connection


class QueryDebug:
    """쿼리 분석기"""

    help = """
    쿼리를 관찰하고 로깅하는 클래스

    [ 사용법 ]

    1. 데코레이터로 사용
    from base.tests.debug import QueryDebug

    @QueryDebug(is_print=True)
    def get(self, request, *args, **kwargs):
        ...

    2. with 문으로 사용
    from django.db import connection

    q = QueryDebug()
    with connection.execute_wrapper(q):
        ...
    # 요약을 보고 싶은 경우
    ql.summary()
    """

    def __init__(self, is_print: bool = False):
        self.is_print = is_print
        self.queries = []
        self.sql_list = []
        self.total_duration = 0

    def __call__(self, *args, **kwargs):
        """호출 위치에 따라 분류"""
        if len(args) == 1 and callable(args[0]):
            # 1. 데코레이터
            return self._decorator(args[0])
        else:
            # 2. with 문
            return self._execute(*args, **kwargs)

    def _decorator(self, func):
        """데코레이터로 호출될 경우"""

        def inner(*args, **kwargs):
            with connection.execute_wrapper(self):
                resp = func(*args, **kwargs)
            if self.is_print:
                self.summary()
            return resp

        return inner

    def _execute(self, execute, sql, params, many, context):
        """with 문으로 호출될 경우"""
        current_query = {"sql": sql, "params": params, "many": many}
        start = time.monotonic()
        try:
            result = execute(sql, params, many, context)
        except Exception as e:
            current_query["status"] = "error"
            current_query["exception"] = e
            raise
        else:
            current_query["status"] = "ok"
            return result
        finally:
            self._debug_query(current_query, start)

    def _debug_query(self, current_query, start):
        """쿼리 수행 시간 측정 및 로깅"""
        duration = time.monotonic() - start
        duration_ms = duration * 1000
        current_query["duration"] = duration_ms
        self.total_duration += duration_ms
        current_query["total_duration"] = self.total_duration

        self.sql_list.append(current_query["sql"])
        current_query["sql_count"] = len(self.sql_list)
        result = Counter(self.sql_list)
        for key, value in result.items():
            if value >= 2:
                current_query["duplicate_query"] = value
        if self.is_print:
            print(f"[{current_query['sql_count']}] => {current_query}")
        self.queries.append(current_query)

    def summary(self):
        """쿼리 요약 정보 출력"""
        queries = sorted(self.queries, key=lambda x: x["duration"], reverse=True)
        print("------------- [ QUERY SUMMARY ] -------------")
        print("▶️ 쿼리 수 : ", len(queries), "개")
        if queries:
            print("▶️ 가장 오래 걸린 쿼리 :\n", queries[0]["sql"])
            print("▶️ 중복 쿼리 수 : ", queries[0].get("duplicate_query", 0), "개")
        print("▶️ 총 소요 시간 : ", self.total_duration, "ms")
