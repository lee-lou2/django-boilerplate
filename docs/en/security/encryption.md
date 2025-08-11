# Data Encryption

This document explains the data encryption features and utilities provided by Django Enterprise Boilerplate.

## Table of Contents

- [AES-256 Encryption Field](#aes-256-encryption-field)
- [Usage Instructions](#usage-instructions)
- [Advanced Configuration](#advanced-configuration)
- [Security Recommendations](#security-recommendations)
- [Related Utilities](#related-utilities)

## AES-256 Encryption Field

`EncryptedCharField` is a Django model field that automatically encrypts and decrypts sensitive information stored in the database using the AES-256 encryption algorithm. This field extends Django's standard `CharField` and can be used in the same way as the existing `CharField`.

### Key Features

- **Strong encryption**: Uses AES-256 encryption algorithm
- **Transparent operation**: Automatic encryption/decryption when using the model
- **Secure initialization vector (IV)**: Uses a new IV each time to encrypt identical data differently
- **Reliable exception handling**: Returns original value when decryption fails to ensure application stability

## Usage Instructions

### 1. Install Required Package

```bash
pip install pycryptodome
```

### 2. Configure Encryption Key in settings.py

```python
# 32-byte (256-bit) key for AES-256 encryption
USER_ENCRYPTION_KEY = 'set_a_very_secure_32_character_secret_key'
```

> **Important**: In production environments, do not include encryption keys directly in your code. Use environment variables or secure secret management systems.

### 3. Using in Models

```python
from django.db import models
from base.fields import EncryptedCharField


class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    # Use encryption fields for sensitive information
    social_security_number = EncryptedCharField(max_length=255)
    credit_card = EncryptedCharField(max_length=255)

    def __str__(self):
        return self.name
```

The encryption field automatically encrypts data when saving to the database and decrypts when retrieving. Developers can use it in the same way as a regular `CharField`.

## Advanced Configuration

### Using Different Key Lengths

AES supports 16, 24, and 32-byte keys. Security strength varies by key length:
- 16 bytes = AES-128
- 24 bytes = AES-192
- 32 bytes = AES-256 (recommended)

### Multiple Key Configuration

If you want to use different encryption keys for various types of data, you can configure as follows:

```python
# settings.py
USER_ENCRYPTION_KEY = '...'  # Key for general user data
PAYMENT_ENCRYPTION_KEY = '...'  # Key for payment information

# Create custom field in fields.py
class PaymentEncryptedField(EncryptedCharField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.key = settings.PAYMENT_ENCRYPTION_KEY.encode('utf-8')
```

## Security Recommendations

1. **Secure Key Management**:
   - Manage keys through environment variables in production
   - Consider using key management services like AWS KMS, Google Cloud KMS, Azure Key Vault

2. **Key Rotation Policy**:
   - Establish a policy for regular encryption key rotation
   - Develop a plan for re-encrypting existing data when keys are rotated

3. **Minimize Encryption Scope**:
   - Encrypt only necessary sensitive information to minimize performance impact
   - Focus on critical data such as PII (Personally Identifiable Information), payment details, passwords

4. **Decryption Failure Response**:
   - Implement logging and alert systems for decryption failures
   - Conduct periodic integrity validation of encrypted data

## Related Utilities

### AES Utility Functions

Utility functions for encrypting/decrypting arbitrary data outside of database models:

```python
# base/utils/encryption.py
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from django.conf import settings
import base64

def encrypt_data(data, key=None):
    """Encrypts data using AES-256."""
    if key is None:
        key = settings.USER_ENCRYPTION_KEY.encode('utf-8')
    elif isinstance(key, str):
        key = key.encode('utf-8')
        
    if isinstance(data, str):
        data = data.encode('utf-8')
        
    cipher = AES.new(key, AES.MODE_CBC)
    iv = cipher.iv
    encrypted = cipher.encrypt(pad(data, AES.block_size))
    encrypted_data = iv + encrypted
    
    return base64.b64encode(encrypted_data).decode('utf-8')

def decrypt_data(encrypted_data, key=None):
    """Decrypts data encrypted with AES-256."""
    if key is None:
        key = settings.USER_ENCRYPTION_KEY.encode('utf-8')
    elif isinstance(key, str):
        key = key.encode('utf-8')
        
    binary_data = base64.b64decode(encrypted_data)
    iv = binary_data[:16]
    ciphertext = binary_data[16:]
    
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size)
    
    return decrypted.decode('utf-8')
```

### Data Masking Utilities

Utility functions for partially masking sensitive information:

```python
# base/utils/masking.py

def mask_credit_card(card_number):
    """Masks credit card number. (e.g., **** **** **** 1234)"""
    if not card_number or len(card_number) < 4:
        return card_number
    return '*' * (len(card_number) - 4) + card_number[-4:]

def mask_email(email):
    """Masks email address. (e.g., a****@example.com)"""
    if not email or '@' not in email:
        return email
    parts = email.split('@')
    username = parts[0]
    domain = parts[1]
    
    if len(username) <= 1:
        masked_username = username
    else:
        masked_username = username[0] + '*' * (len(username) - 1)
    
    return f"{masked_username}@{domain}"

def mask_phone(phone):
    """Masks phone number."""
    if not phone or len(phone) < 4:
        return phone
    return '*' * (len(phone) - 4) + phone[-4:]
```

## Implementation Code

The implementation code for `EncryptedCharField` is as follows:

```python
from django.db import models
from django.conf import settings
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64

class EncryptedCharField(models.CharField):
    """
    Django CharField supporting AES-256 encryption
    
    Uses settings.USER_ENCRYPTION_KEY to encrypt and decrypt data.
    Encrypted values are stored in the database encoded in Base64.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get encryption key from settings
        self.key = settings.USER_ENCRYPTION_KEY.encode('utf-8')
        # Verify key length (AES uses 16, 24, or 32 byte keys)
        if len(self.key) not in [16, 24, 32]:
            raise ValueError("USER_ENCRYPTION_KEY must be 16, 24, or 32 bytes long")
    
    def from_db_value(self, value, expression, connection):
        """
        Method called when retrieving values from the database
        Returns decrypted value
        """
        if value is None:
            return value
        try:
            return self.to_python(value)
        except Exception:
            # Return original value on decryption failure (prevents application interruption)
            return value
    
    def to_python(self, value):
        """
        Method for reading and decrypting values from the database
        """
        if value is None:
            return value
        
        # Base64 decoding
        encrypted_data = base64.b64decode(value)
        # Separate initialization vector (IV) and ciphertext
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        # AES decryption
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size)
        return decrypted.decode('utf-8')
    
    def get_prep_value(self, value):
        """
        Method for encrypting values before saving to database
        """
        if value is None:
            return value
        
        # Convert to string if not already
        if not isinstance(value, str):
            value = str(value)
            
        # AES encryption (CBC mode)
        cipher = AES.new(self.key, AES.MODE_CBC)
        iv = cipher.iv  # Generate random initialization vector
        encrypted = cipher.encrypt(pad(value.encode('utf-8'), AES.block_size))
        
        # Combine IV and ciphertext, then encode in Base64
        encrypted_data = iv + encrypted
        return base64.b64encode(encrypted_data).decode('utf-8')
```

## References

- [AES Encryption Algorithm](https://en.wikipedia.org/wiki/Advanced_Encryption_Standard)
- [Django Field Types](https://docs.djangoproject.com/en/stable/ref/models/fields/)
- [PyCryptodome Library](https://pycryptodome.readthedocs.io/)
- [GDPR Encryption Requirements](https://gdpr-info.eu/)
- [HIPAA Security Regulations](https://www.hhs.gov/hipaa/for-professionals/security/index.html)
