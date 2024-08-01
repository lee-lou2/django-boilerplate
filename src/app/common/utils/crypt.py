import base64
import hashlib
import os

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class AESCipher:
    def __init__(self, key, iv):
        self.key = key.encode()
        self.iv = iv.encode()
        self.block_size = 16

    def _create_cipher(self):
        return AES.new(self.key, AES.MODE_CBC, self.iv)

    def encrypt(self, message):
        cipher = self._create_cipher()
        cipher_text_bytes = cipher.encrypt(
            pad(pad(message.encode(), self.block_size), self.block_size)
        )
        encrypted_message_base64 = base64.b64encode(cipher_text_bytes).decode("utf-8")
        return encrypted_message_base64

    def decrypt(self, encrypted_message_base64):
        cipher = self._create_cipher()
        cipher_text_bytes = base64.b64decode(encrypted_message_base64)
        plain_text_bytes = cipher.decrypt(cipher_text_bytes)
        decrypted_message = (
            unpad(unpad(plain_text_bytes, self.block_size), self.block_size).decode(
                "utf-8"
            )
            if plain_text_bytes
            else None
        )
        return decrypted_message


class AESRandIVCipher:
    def __init__(self, key: str):
        self.BS = 16
        self.pad = lambda s: s + (self.BS - len(s) % self.BS) * chr(
            self.BS - len(s) % self.BS
        )
        self.unpad = lambda s: s[0 : -s[-1]]
        self.key = hashlib.sha256(key.encode("utf-8")).digest()

    def encrypt(self, raw):
        raw = self.pad(raw).encode("utf-8")
        iv = os.urandom(16)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw)).decode("utf-8")

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:16]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self.unpad(cipher.decrypt(enc[16:])).decode("utf-8")
