from django.conf import settings
from django.db import models

from common.utils.aes_chipher import AESCipher


class EncryptedCharField(models.CharField):
    """
    암호화된 CharField

    이 필드는 AES 암호화를 사용하여 데이터를 암호화하고 복호화합니다.
    암호화 키는 Django 설정에서 USER_ENCRYPTION_KEY로 지정되어야 합니다.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.aes_cipher = AESCipher(settings.USER_ENCRYPTION_KEY)

    def from_db_value(self, value, expression, connection):
        """데이터 조회 시 복호화"""
        if value is None:
            return value
        return self.to_python(value)

    def to_python(self, value):
        if value is None:
            return value
        if not isinstance(value, str) or len(value) < 24:
            return value
        return self.aes_cipher.decrypt(value)

    def get_prep_value(self, value):
        """데이터 저장 시 암호화"""
        if value is None:
            return value
        value_str = str(value)
        return self.aes_cipher.encrypt(value_str)
