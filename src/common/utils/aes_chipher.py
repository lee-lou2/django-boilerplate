from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import os


class AESCipher:
    """
    A class that performs AES-256 encryption and decryption.
    It uses CBC mode and prepends the IV to the ciphertext before Base64 encoding.
    """

    def __init__(self, key: str):
        """
        Initialization method.

        Args:
            key (str): 32-byte AES-256 encryption key (string).
        Raises:
            ValueError: Raised if the key length is not 32 bytes.
        """
        self.key = key.encode("utf-8")
        if len(self.key) != 32:
            raise ValueError("AES-256 key must be 32 bytes.")
        self.block_size = AES.block_size  # AES block size is 16 bytes

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypts the given plaintext using AES-256.

        Args:
            plaintext (str): String to be encrypted.

        Returns:
            str: Base64 encoded ciphertext (including IV).
        """
        plaintext_bytes = plaintext.encode("utf-8")

        # Generate random IV for CBC mode (16 bytes)
        iv = os.urandom(self.block_size)

        # Create AES cipher object (CBC mode)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)

        # Pad and encrypt plaintext
        padded_plaintext = pad(plaintext_bytes, self.block_size)
        ciphertext_bytes = cipher.encrypt(padded_plaintext)

        # Combine IV and ciphertext then Base64 encode
        encrypted_data = iv + ciphertext_bytes
        return base64.b64encode(encrypted_data).decode("utf-8")

    def decrypt(self, encrypted_text: str) -> str:
        """
        Decrypts the Base64 encoded ciphertext using AES-256.

        Args:
            encrypted_text (str): Base64 encoded ciphertext (including IV).

        Returns:
            str: Decrypted original string.
        """
        # Base64 decoding
        encrypted_data = base64.b64decode(encrypted_text)

        # Separate IV and ciphertext
        iv = encrypted_data[: self.block_size]
        ciphertext_bytes = encrypted_data[self.block_size :]

        # Create AES cipher object (CBC mode)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)

        # Decrypt and remove padding
        decrypted_padded_bytes = cipher.decrypt(ciphertext_bytes)
        decrypted_bytes = unpad(decrypted_padded_bytes, self.block_size)

        # Decode to UTF-8 string and return
        return decrypted_bytes.decode("utf-8")
