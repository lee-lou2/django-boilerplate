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
        """Store cache data"""
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
        """Smooth retrieval and setting of data"""
        # Retrieve data
        data = self.get(key)
        if data is None or type(data) != dict:
            data = {}

        # Retrieve data
        value = data.get("value")
        smoothly_datetime = (
            datetime.datetime.strptime(
                data.get("smoothly_datetime"), "%Y-%m-%d %H:%M:%S"
            )
            if data.get("smoothly_datetime")
            else None
        )

        # 1. If data is valid, return it as is
        if smoothly_datetime is not None and smoothly_datetime >= timezone.localtime():
            return value
        args = [key, value_class, value_kwargs, timeout, smoothly_timeout]
        # 2. Data exists but is not valid
        if smoothly_datetime is not None and smoothly_datetime < timezone.localtime():
            # Return existing data while asynchronous process runs
            self._set_value(
                key=key,
                value_class=lambda v: v,
                value_kwargs={"v": value},
                timeout=timeout,
                smoothly_timeout=smoothly_timeout,
            )
            # Asynchronous
            threading.Thread(target=self._set_value, args=args).start()
        # 3. If there is no data
        else:
            # Synchronous
            value = self._set_value(*args)
        return value
