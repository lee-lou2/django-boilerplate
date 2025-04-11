import datetime
import threading

from django.core.cache.backends.redis import RedisCache as DjangoRedisCache
from django.utils import timezone


class RedisCache(DjangoRedisCache):
    """Redis Cache"""

    def _set_value(
        self,
        key,
        value_class,
        value_kwargs=None,
        timeout=60 * 60,
        smoothly_timeout=60 * 10,
    ):
        """캐시 데이터 저장"""
        value = value_class(**value_kwargs)
        self.set(
            key,
            {
                "value": value,
                "smoothly_datetime": (
                    timezone.localtime() + datetime.timedelta(seconds=smoothly_timeout)
                ).strftime("%Y-%m-%d %H:%M:%S"),
            },
            timeout,
        )
        return value

    def smooth(
        self,
        key,
        value_class,
        value_kwargs=None,
        timeout=60 * 60,
        smoothly_timeout=60 * 10,
    ):
        """스무스한 데이터 조회 및 설정"""
        # 데이터 조회
        data = self.get(key)
        if data is None or type(data) != dict:
            data = {}

        # 데이터 조회
        value = data.get("value")
        smoothly_datetime = (
            datetime.datetime.strptime(
                data.get("smoothly_datetime"), "%Y-%m-%d %H:%M:%S"
            )
            if data.get("smoothly_datetime")
            else None
        )

        # 1. 유효한 데이터의 경우 그대로 반환
        if smoothly_datetime is not None and smoothly_datetime >= timezone.localtime():
            return value
        args = [key, value_class, value_kwargs, timeout, smoothly_timeout]
        # 2. 데이터는 있지만 유효하지 않은 경우
        if smoothly_datetime is not None and smoothly_datetime < timezone.localtime():
            # 비동기 처리되는 동안 기존 데이터를 반환
            self._set_value(
                key=key,
                value_class=lambda v: v,
                value_kwargs={"v": value},
                timeout=timeout,
                smoothly_timeout=smoothly_timeout,
            )
            # 비동기
            threading.Thread(target=self._set_value, args=args).start()
        # 3. 데이터가 없는 경우
        else:
            # 동기
            value = self._set_value(*args)
        return value
