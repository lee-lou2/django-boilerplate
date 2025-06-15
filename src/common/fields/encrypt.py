from django.conf import settings
from django.db import models

from common.utils.aes_chipher import AESCipher


class EncryptedCharField(models.CharField):
    """
    Encrypted CharField

    This field uses AES encryption to encrypt and decrypt data.
    The encryption key must be specified as USER_ENCRYPTION_KEY in Django settings.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.aes_cipher = AESCipher(settings.USER_ENCRYPTION_KEY)

    def from_db_value(self, value, expression, connection):
        """Decrypt when retrieving data"""
        if value is None:
            return value
        return self.to_python(value)

    def to_python(self, value):
        if value is None:
            return value
        # Assuming that encrypted values will be strings and typically longer than a raw IV (e.g., 24 chars for base64 encoded IV + some data)
        # This check is to avoid attempting to decrypt already decrypted or non-encrypted short values.
        if not isinstance(value, str) or len(value) < 24: # Heuristic to guess if data might be encrypted
            return value
        try:
            return self.aes_cipher.decrypt(value)
        except Exception: # If decryption fails, return the original value
            # Log the error or handle it as per application's error handling policy
            # For now, returning the value as is, to prevent crashes if non-encrypted data is encountered.
            return value

    def get_prep_value(self, value):
        """Encrypt when saving data"""
        if value is None:
            return value
        value_str = str(value)
        return self.aes_cipher.encrypt(value_str)
