# 데이터 암호화

본 문서에서는 Django Enterprise Boilerplate에서 제공하는 데이터 암호화 기능과 유틸리티에 대해 설명합니다.

## 목차

- [AES-256 암호화 필드](#aes-256-암호화-필드)
- [사용 방법](#사용-방법)
- [고급 설정](#고급-설정)
- [보안 권장사항](#보안-권장사항)
- [관련 유틸리티](#관련-유틸리티)

## AES-256 암호화 필드

`EncryptedCharField`는 데이터베이스에 저장되는 민감한 정보를 AES-256 암호화 알고리즘을 사용하여 자동으로 암호화하고 복호화하는 Django 모델 필드입니다. 이 필드는 Django의 표준 `CharField`를 확장하여 만들어졌으며, 사용 방법도 기존 `CharField`와 동일합니다.

### 주요 특징

- **강력한 암호화**: AES-256 암호화 알고리즘 사용
- **투명한 작동**: 모델 사용 시 암호화/복호화 자동 처리
- **안전한 초기화 벡터(IV)**: 매번 새로운 IV를 사용하여 동일 데이터도 다르게 암호화
- **안정적인 예외 처리**: 복호화 실패 시 원본값 반환으로 애플리케이션 안정성 확보

## 사용 방법

### 1. 필요한 패키지 설치

```bash
pip install pycryptodome
```

### 2. settings.py에 암호화 키 설정

```python
# AES-256 암호화를 위한 32바이트(256비트) 키
USER_ENCRYPTION_KEY = '32글자의_매우_안전한_비밀_키_설정하세요'
```

> **중요**: 실제 환경에서는 암호화 키를 코드에 직접 넣지 마시고, 환경 변수나 안전한 비밀 관리 시스템을 통해 관리하세요.

### 3. 모델에서 사용하기

```python
from django.db import models
from base.fields import EncryptedCharField


class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    # 민감한 정보는 암호화 필드 사용
    social_security_number = EncryptedCharField(max_length=255)
    credit_card = EncryptedCharField(max_length=255)

    def __str__(self):
        return self.name
```

암호화 필드는 데이터베이스에 저장될 때 자동으로 암호화되며, 조회 시 자동으로 복호화됩니다. 개발자는 일반 `CharField`와 동일한 방식으로 사용할 수 있습니다.

## 고급 설정

### 다양한 키 길이 사용

AES는 16, 24, 32바이트 키를 지원합니다. 키 길이에 따라 보안 강도가 달라집니다:
- 16바이트 = AES-128
- 24바이트 = AES-192
- 32바이트 = AES-256 (권장)

### 다중 키 설정

여러 종류의 데이터에 대해 서로 다른 암호화 키를 사용하고 싶다면 다음과 같이 설정할 수 있습니다:

```python
# settings.py
USER_ENCRYPTION_KEY = '...'  # 일반 사용자 데이터용 키
PAYMENT_ENCRYPTION_KEY = '...'  # 결제 정보용 키

# fields.py에서 커스텀 필드 생성
class PaymentEncryptedField(EncryptedCharField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.key = settings.PAYMENT_ENCRYPTION_KEY.encode('utf-8')
```

## 보안 권장사항

1. **안전한 키 관리**:
   - 운영 환경에서는 환경 변수를 통해 키 관리
   - AWS KMS, Google Cloud KMS, Azure Key Vault 등의 키 관리 서비스 활용 고려

2. **키 순환 정책**:
   - 정기적으로 암호화 키를 교체하는 정책 수립
   - 키 교체 시 기존 데이터 재암호화 방안 마련

3. **암호화 범위 최소화**:
   - 꼭 필요한 민감 정보만 암호화하여 성능 영향 최소화
   - PII(개인식별정보), 결제정보, 비밀번호 등 중요 데이터에 집중

4. **복호화 실패 대응**:
   - 복호화 실패 로깅 및 알림 시스템 구축
   - 주기적인 암호화 데이터 무결성 검증

## 관련 유틸리티

### AES 유틸리티 함수

데이터베이스 모델과 별개로 임의의 데이터를 암호화/복호화해야 할 경우 사용할 수 있는 유틸리티 함수들입니다.

```python
# base/utils/encryption.py
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from django.conf import settings
import base64

def encrypt_data(data, key=None):
    """데이터를 AES-256으로 암호화합니다."""
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
    """AES-256으로 암호화된 데이터를 복호화합니다."""
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

### 데이터 마스킹 유틸리티

민감한 정보를 부분적으로 마스킹하기 위한 유틸리티 함수:

```python
# base/utils/masking.py

def mask_credit_card(card_number):
    """신용카드 번호를 마스킹합니다. (예: **** **** **** 1234)"""
    if not card_number or len(card_number) < 4:
        return card_number
    return '*' * (len(card_number) - 4) + card_number[-4:]

def mask_email(email):
    """이메일 주소를 마스킹합니다. (예: a****@example.com)"""
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
    """전화번호를 마스킹합니다."""
    if not phone or len(phone) < 4:
        return phone
    return '*' * (len(phone) - 4) + phone[-4:]
```

## 구현 코드

`EncryptedCharField` 구현 코드는 다음과 같습니다:

```python
from django.db import models
from django.conf import settings
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64

class EncryptedCharField(models.CharField):
    """
    AES-256 암호화를 지원하는 Django CharField
    
    settings.USER_ENCRYPTION_KEY를 사용하여 데이터를 암호화하고 복호화합니다.
    데이터베이스에는 암호화된 값이 Base64로 인코딩되어 저장됩니다.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # settings에서 암호화 키 가져오기
        self.key = settings.USER_ENCRYPTION_KEY.encode('utf-8')
        # 키 길이 확인 (AES는 16, 24, 32바이트 키 사용)
        if len(self.key) not in [16, 24, 32]:
            raise ValueError("USER_ENCRYPTION_KEY must be 16, 24, or 32 bytes long")
    
    def from_db_value(self, value, expression, connection):
        """
        데이터베이스에서 값을 가져올 때 호출되는 메서드
        암호화된 값을 복호화하여 반환합니다.
        """
        if value is None:
            return value
        try:
            return self.to_python(value)
        except Exception:
            # 복호화 실패 시 원본 값 반환 (애플리케이션 중단 방지)
            return value
    
    def to_python(self, value):
        """
        데이터베이스에서 값을 읽어 복호화하는 메서드
        """
        if value is None:
            return value
        
        # Base64 디코딩
        encrypted_data = base64.b64decode(value)
        # 초기화 벡터(IV)와 암호문 분리
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        # AES 복호화
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size)
        return decrypted.decode('utf-8')
    
    def get_prep_value(self, value):
        """
        데이터베이스에 저장하기 전 값을 암호화하는 메서드
        """
        if value is None:
            return value
        
        # 문자열이 아닌 경우 문자열로 변환
        if not isinstance(value, str):
            value = str(value)
            
        # AES 암호화 (CBC 모드)
        cipher = AES.new(self.key, AES.MODE_CBC)
        iv = cipher.iv  # 랜덤 초기화 벡터 생성
        encrypted = cipher.encrypt(pad(value.encode('utf-8'), AES.block_size))
        
        # IV와 암호문을 결합 후 Base64 인코딩
        encrypted_data = iv + encrypted
        return base64.b64encode(encrypted_data).decode('utf-8')
```

## 참고 자료

- [AES 암호화 알고리즘](https://en.wikipedia.org/wiki/Advanced_Encryption_Standard)
- [Django Field Types](https://docs.djangoproject.com/en/stable/ref/models/fields/)
- [PyCryptodome 라이브러리](https://pycryptodome.readthedocs.io/)
- [GDPR 암호화 요구사항](https://gdpr-info.eu/)
- [HIPAA 보안 규정](https://www.hhs.gov/hipaa/for-professionals/security/index.html)