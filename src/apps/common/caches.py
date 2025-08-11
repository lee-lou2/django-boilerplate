import hashlib
import json
from functools import wraps

from django.core.cache import cache
from rest_framework.response import Response


def get_cache_version_key(cls):
    return f"cache_version:{cls.__module__}.{cls.__name__}"


def invalidate_cache(cls):
    version_key = get_cache_version_key(cls)
    try:
        cache.incr(version_key)
    except ValueError:
        cache.set(version_key, 1, timeout=None)  # 영구 보존


def cache_action(action_type):
    def decorator(func):
        @wraps(func)
        def wrapper(view, request, *args, **kwargs):
            version_key = get_cache_version_key(view.__class__)
            version = cache.get(version_key, 1)

            if action_type == "list":
                # 쿼리 파라미터 해시 생성
                query_params = request.query_params.items()
                sorted_params = sorted(query_params)
                params_string = json.dumps(sorted_params)
                params_hash = hashlib.md5(params_string.encode("utf-8")).hexdigest()
                unique_part = params_hash
            elif action_type == "retrieve":
                # lookup_value 추출
                lookup_value = kwargs.get(view.lookup_field, None)
                if not lookup_value:
                    return func(view, request, *args, **kwargs)
                unique_part = str(lookup_value)
            else:
                raise ValueError(f"Unsupported action_type: {action_type}")

            cache_key = f"{version}:{view.get_cache_key(unique_part=unique_part)}"
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                return Response(cached_data)

            response = func(view, request, *args, **kwargs)

            if response.status_code == 200:
                cache.set(cache_key, response.data, timeout=60 * 60)  # 1시간 캐시

            return response

        return wrapper

    return decorator
