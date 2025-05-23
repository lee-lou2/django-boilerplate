import hashlib

from rest_framework import serializers

from apps.short_url.models import ShortUrl, ShortUrlVisit
from apps.short_url.v1.utils import generate_random_key, id_to_key
from common.enums.errors import (
    E005_HASHED_VALUE_ALREADY_EXISTS,
    E005_INVALID_OG_TAG_FORMAT,
)


class ShortUrlSerializer(serializers.ModelSerializer):
    """
    Short URL Serializer:
    Checks existence using input information.
    Generates a unique, non-duplicate value in a special way.
    Always creates and manages quickly and safely.
    """

    random_key = serializers.HiddenField(
        default=generate_random_key,
        help_text="Random key",
    )
    hashed_value = serializers.HiddenField(
        default="",
        help_text="Hash value",
    )
    short_key = serializers.CharField(
        read_only=True,
        help_text="Short URL",
    )

    def validate_og_tag(self, value):
        # OG tag must be in JSON format
        if value and not isinstance(value, dict):
            raise serializers.ValidationError(E005_INVALID_OG_TAG_FORMAT)
        return value

    def validate(self, attrs):
        # Generate hashed_value
        concatenated = "".join(
            [
                attrs.get("ios_deep_link", ""),
                attrs.get("ios_fallback_url", ""),
                attrs.get("android_deep_link", ""),
                attrs.get("android_fallback_url", ""),
                attrs.get("default_fallback_url", ""),
            ]
        )

        # Generate SHA-256 hash
        # [Why]
        # Q. Why use SHA-256 hash?
        # A. SHA-256 is highly secure and has a low probability of hash collisions.
        #    Also, since the hash value must be unique, it is used for duplicate checking when creating short URLs.
        hasher = hashlib.sha256()
        hasher.update(concatenated.encode("utf-8"))
        hashed_value = hasher.hexdigest()

        if ShortUrl.objects.filter(hashed_value=hashed_value).exists():
            raise serializers.ValidationError(E005_HASHED_VALUE_ALREADY_EXISTS)
        attrs["hashed_value"] = hashed_value
        return attrs

    def to_representation(self, instance):
        # Generate Key value for ShortURL
        short_key = id_to_key(instance.id)
        random_key = instance.random_key
        # [Why]
        # Q. Why generate a short URL using a random key and an index for the PK?
        # A. The random key ensures uniqueness, and the PK guarantees uniqueness in the database.
        #    Combining these two values always allows for the creation of a unique short URL.
        instance.short_key = f"{random_key[:2]}{short_key}{random_key[2:]}"
        return super().to_representation(instance)

    class Meta:
        model = ShortUrl
        fields = [
            "id",
            "short_key",
            "random_key",
            "ios_deep_link",
            "ios_fallback_url",
            "android_deep_link",
            "android_fallback_url",
            "default_fallback_url",
            "hashed_value",
            "og_tag",
        ]


class ShortUrlRedirectSerializer(serializers.ModelSerializer):
    """
    Short URL Redirect Serializer:
    Redirects to the original link corresponding to the short link.
    Saves visit history.
    """

    def save(self, **kwargs):
        # Extract necessary information from the request object
        request = self.context.get("request")

        # Extract IP address
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            # If X-Forwarded-For exists, use only the first IP (actual client IP)
            ip_address = x_forwarded_for.split(",")[0].strip()
        else:
            # Otherwise, use REMOTE_ADDR
            ip_address = request.META.get("REMOTE_ADDR")

        # Extract additional data
        user_agent = request.META.get("HTTP_USER_AGENT")
        referrer = request.query_params.get("referrer")

        # Create visit record
        ShortUrlVisit.objects.create(
            short_url=self.instance,
            referrer=referrer,
            user_agent=user_agent,
            ip_address=ip_address,
        )

    class Meta:
        model = ShortUrl
        fields = [
            "id",
            "ios_deep_link",
            "ios_fallback_url",
            "android_deep_link",
            "android_fallback_url",
            "default_fallback_url",
            "hashed_value",
            "og_tag",
        ]
