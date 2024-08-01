import binascii
import random
import string

from django import forms
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from app.common.utils.crypt import AESCipher


def get_encryption_key():
    return getattr(settings, "ENCRYPT_KEY")


def get_encryption_iv():
    return getattr(settings, "ENCRYPT_IV")


def get_nested_encryption_key():
    return getattr(settings, "NESTED_ENCRYPT_KEY")


def get_nested_encryption_iv():
    return getattr(settings, "NESTED_ENCRYPT_IV")


class AesField(models.Field):
    def __init__(self, nested=None, *args, **kwargs):
        self.cipher = (
            AESCipher(get_nested_encryption_key(), get_nested_encryption_iv())
            if nested
            else AESCipher(get_encryption_key(), get_encryption_iv())
        )
        super().__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection, context=None):
        return self.to_python(value)

    def to_python(self, value):
        if not value:
            return value

        try:
            return self.cipher.decrypt(value)
        except (binascii.Error, ValueError):
            return None

    def get_prep_value(self, value):
        if not value:
            return value
        if not isinstance(value, str):
            value = str(value)
        return self.cipher.encrypt(value)

    def get_encrypted_value(self, value):
        if value:
            return self.get_prep_value(value)
        return value


class EncryptedCharField(AesField):
    description = _("String")

    def formfield(self, **kwargs):
        defaults = {"widget": forms.TextInput}
        defaults.update(kwargs)
        return super().formfield(**defaults)

    def db_type(self, connection):
        return "varchar(%s)" % self.max_length


class NestedEncryptedCharField(AesField):
    description = _("String")

    def __init__(self, *args, **kwargs):
        super().__init__(nested=True, *args, **kwargs)

    def formfield(self, **kwargs):
        defaults = {"widget": forms.TextInput}
        defaults.update(kwargs)
        return super().formfield(**defaults)

    def db_type(self, connection):
        return "varchar(%s)" % self.max_length


class EncryptedEmailField(EncryptedCharField):
    description = _("Email address")

    def formfield(self, **kwargs):
        defaults = {"widget": forms.EmailField}
        defaults.update(kwargs)
        return super().formfield(**defaults)


def encrypted_phone_no_generator():
    cipher = AESCipher(get_encryption_key(), get_encryption_iv())
    random_phone_no = "010" + "".join(random.choice(string.digits) for _ in range(8))
    encrypted_phone_no = cipher.encrypt(random_phone_no)
    return encrypted_phone_no


def encrypted_email_generator():
    cipher = AESCipher(get_encryption_key(), get_encryption_iv())
    user_name = "".join(random.choices(string.ascii_letters + string.digits, k=10))
    random_email = f"{user_name}@gmail.com"
    encrypted_email = cipher.encrypt(random_email)
    return encrypted_email


def encrypted_account_no_generator():
    cipher = AESCipher(get_encryption_key(), get_encryption_iv())
    account_no = "".join(random.choices(string.digits, k=11))
    encrypted_account_no = cipher.encrypt(account_no)
    return encrypted_account_no


def encrypted_account_owner_generator():
    cipher = AESCipher(get_encryption_key(), get_encryption_iv())
    account_owner = "".join(random.choices(string.ascii_letters + string.digits, k=3))
    encrypted_account_owner = cipher.encrypt(account_owner)
    return encrypted_account_owner
