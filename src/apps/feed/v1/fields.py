class CurrentFeedDefault:
    """현재 조회된 피드 설정"""

    requires_context = True

    def __call__(self, serializer_field):
        return serializer_field.context["view"].kwargs["feed_pk"]
