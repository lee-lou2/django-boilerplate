import base64
import os

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class AESCipher:
    """
    AES-256 암호화 및 복호화를 수행하는 클래스.
    CBC 모드를 사용하며, IV를 암호문 앞에 붙여 Base64로 인코딩합니다.
    """

    def __init__(self, key: str):
        """
        초기화 메서드.

        Args:
            key (str): 32바이트 길이의 AES-256 암호화 키 (문자열).
        Raises:
            ValueError: 키 길이가 32바이트가 아닐 경우 발생합니다.
        """
        self.key = key.encode("utf-8")
        if len(self.key) != 32:
            raise ValueError("AES-256 키는 반드시 32바이트여야 합니다.")
        self.block_size = AES.block_size  # AES 블록 크기는 16바이트

    def encrypt(self, plaintext: str) -> str:
        """
        주어진 평문을 AES-256으로 암호화합니다.

        Args:
            plaintext (str): 암호화할 문자열.

        Returns:
            str: Base64로 인코딩된 암호문 (IV 포함).
        """
        plaintext_bytes = plaintext.encode("utf-8")

        # CBC 모드를 위한 랜덤 IV 생성 (16바이트)
        iv = os.urandom(self.block_size)

        # AES 암호화 객체 생성 (CBC 모드)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)

        # 평문 패딩 및 암호화
        padded_plaintext = pad(plaintext_bytes, self.block_size)
        ciphertext_bytes = cipher.encrypt(padded_plaintext)

        # IV와 암호문 결합 후 Base64 인코딩
        encrypted_data = iv + ciphertext_bytes
        return base64.b64encode(encrypted_data).decode("utf-8")

    def decrypt(self, encrypted_text: str) -> str:
        """
        Base64 인코딩된 암호문을 AES-256으로 복호화합니다.

        Args:
            encrypted_text (str): Base64로 인코딩된 암호문 (IV 포함).

        Returns:
            str: 복호화된 원본 문자열.
        """
        # Base64 디코딩
        encrypted_data = base64.b64decode(encrypted_text)

        # IV와 암호문 분리
        iv = encrypted_data[: self.block_size]
        ciphertext_bytes = encrypted_data[self.block_size :]

        # AES 복호화 객체 생성 (CBC 모드)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)

        # 복호화 및 패딩 제거
        decrypted_padded_bytes = cipher.decrypt(ciphertext_bytes)
        decrypted_bytes = unpad(decrypted_padded_bytes, self.block_size)

        # UTF-8 문자열로 디코딩하여 반환
        return decrypted_bytes.decode("utf-8")
