from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import timezone


class CustomPasswordResetTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        if user.last_login_at is None:
            login_timestamp = ""
        else:
            aware_datetime = user.last_login_at.astimezone(
                timezone.get_current_timezone()
            )
            naive_datetime = aware_datetime.replace(tzinfo=None)
            login_timestamp = naive_datetime.replace(microsecond=0)

        return f"{user.pk}{user.password.password}{login_timestamp}{timestamp}"


custom_token_generator = CustomPasswordResetTokenGenerator()
