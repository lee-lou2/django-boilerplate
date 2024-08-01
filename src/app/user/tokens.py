from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return str(user.pk) + user.email + str(user.is_email) + str(timestamp)


email_verification_token = EmailVerificationTokenGenerator()
