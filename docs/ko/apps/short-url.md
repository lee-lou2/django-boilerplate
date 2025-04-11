# Short URL API Documentation

## Overview

이 문서는 단축 URL 생성 및 리다이렉션 API 기능에 대한 가이드입니다. 이 서비스는 긴 URL을 짧은 URL로 변환하여 사용자에게 제공하며, 사용자의 디바이스 유형에 따라 적절한 URL로 리다이렉션합니다. 혁신적인 URL 생성 방식과 다양한 기술적 특징을 갖추고 있습니다.

## API 엔드포인트

| 경로 | 메서드 | 설명 |
|------|--------|------|
| `/v1/short-url/` | POST | 단축 URL 생성 |
| `url.{호스트}/{short_key}/` | GET | 단축 URL 리다이렉트 |

## 기술적 특징

### 1. 혁신적인 단축 키 생성 방식

일반적인 단축 URL 서비스들은 랜덤 키를 생성한 후 데이터베이스에 중복 여부를 확인하고 추가하는 방식을 사용합니다. 이 방식은 매번 데이터베이스 조회가 필요하며 성능 저하를 일으킬 수 있습니다.

본 서비스는 **데이터베이스 조회 없이** 고유한 단축 키를 보장하는 혁신적인 방식을 사용합니다:

1. 4자리 랜덤 문자열(`random_key`) 생성
2. 테이블의 자동 증가 PK(Primary Key)를 문자열로 변환하는 커스텀 인코딩(`id_to_key` 함수)
   - 소문자, 대문자, 숫자(총 62개 문자)를 사용하여 PK 값을 고유한 문자열로 변환
3. 랜덤 키의 일부를 앞에, 나머지를 뒤에 배치하여 PK 기반 키를 감싸는 형태로 최종 단축 키 생성

```
최종 단축 키 = random_key[:2] + id_to_key(id) + random_key[2:]
```

이 방식을 통해 중복 검사 없이도 항상 고유한 단축 키가 보장됩니다.

### 2. URL 해싱을 통한 중복 방지

동일한 URL 조합에 대해 중복으로 단축 URL이 생성되는 것을 방지하기 위해 URL 해싱 방식을 적용합니다:

1. 모든 입력 URL(iOS/Android 딥링크, 폴백 URL 등)을 연결
2. SHA-256 해시 알고리즘을 사용하여 해시값 생성
3. 데이터베이스에 동일한 해시값이 존재하는지 확인하여 중복 생성 방지

이를 통해 효율적으로 리소스를 관리하고 동일한 URL 조합에 대해 항상 동일한 단축 URL을 제공합니다.

### 3. 디바이스 감지 및 적응형 리다이렉션

사용자의 디바이스 유형(iOS, Android, 기타)을 자동으로 감지하여 최적화된 경험을 제공합니다:

1. User-Agent 분석을 통한 디바이스 식별
2. iOS 사용자 → iOS 딥링크 또는 iOS 폴백 URL로 리다이렉트
3. Android 사용자 → Android 딥링크 또는 Android 폴백 URL로 리다이렉트
4. 기타 디바이스 → 기본 폴백 URL로 리다이렉트

### 4. 딥링크 지원 및 폴백 메커니즘

앱 설치 여부에 따른 지능적인 리다이렉션을 제공합니다:

1. 딥링크를 통해 앱 실행 시도
2. 앱이 설치되어 있지 않은 경우, 2초 후 자동으로 폴백 URL로 리다이렉트
3. 디바이스 유형별 맞춤형 폴백 URL 지원

### 5. OG 태그 지원

소셜 미디어 공유 시 풍부한 미리보기를 제공하기 위한 Open Graph 태그를 지원합니다:

```json
{
  "og:title": "웹사이트 제목",
  "og:description": "웹사이트 설명",
  "og:image": "이미지 URL"
}
```

### 6. 사용자 방문 추적 및 분석

모든 방문 기록을 자세히 추적하여 분석에 활용할 수 있습니다:

1. IP 주소 추적 (X-Forwarded-For 헤더 지원)
2. 사용자 에이전트 정보 기록
3. 레퍼러(referrer) 추적
4. 타임스탬프 기록

### 7. 아키텍처 분리

Django Hosts를 활용한 도메인 기반 서비스 분리:

1. 메인 도메인 → 단축 URL 생성 API 서비스
2. `url.{host}` 서브도메인 → 리다이렉션 서비스

이 구조를 통해 각 서비스를 독립적으로 확장하고 관리할 수 있습니다.

## 흐름도

```mermaid
flowchart TD
    classDef userAction fill:#f9d6d6,stroke:#e88e8e,stroke-width:2px,color:#333
    classDef systemAction fill:#d6e5f9,stroke:#8eb5e8,stroke-width:2px,color:#333
    classDef success fill:#d6f9d6,stroke:#8ee88e,stroke-width:2px,color:#333
    
    Start([시작]) --> CreateRequest[단축 URL 생성 요청]
    CreateRequest --> GenerateHash[URL 조합 해시 생성]
    GenerateHash --> CheckHash{해시 중복 확인}
    
    CheckHash -->|중복 있음| ReturnExisting[기존 단축 URL 반환]
    ReturnExisting --> End([종료])
    
    CheckHash -->|중복 없음| GenerateRandom[4자리 랜덤 키 생성]
    GenerateRandom --> SaveURL[데이터베이스에 저장]
    SaveURL --> EncodePK[PK를 문자열로 변환]
    EncodePK --> CombineKeys[랜덤 키와 변환된 PK 조합]
    CombineKeys --> ReturnShortURL[단축 URL 반환]
    ReturnShortURL --> End
    
    Start2([시작]) --> AccessShortURL[단축 URL 접속]
    AccessShortURL --> ExtractKey[단축 키 추출]
    ExtractKey --> ExtractPK[변환된 PK 추출]
    ExtractPK --> DecodePK[PK를 숫자로 복원]
    DecodePK --> FetchURL[데이터베이스에서 URL 정보 조회]
    FetchURL --> DetectDevice[사용자 디바이스 감지]
    
    DetectDevice -->|iOS| iOSPath[iOS 경로 선택]
    DetectDevice -->|Android| AndroidPath[Android 경로 선택]
    DetectDevice -->|기타| DefaultPath[기본 경로 선택]
    
    iOSPath --> CheckiOSDeeplink{딥링크 존재?}
    CheckiOSDeeplink -->|Yes| TryiOSApp[iOS 앱 실행 시도]
    CheckiOSDeeplink -->|No| iOSFallback[iOS 폴백 URL로 리다이렉트]
    
    TryiOSApp --> iOSAppCheck{앱 실행 성공?}
    iOSAppCheck -->|Yes| iOSSuccess[앱에서 컨텐츠 표시]
    iOSAppCheck -->|No| iOSFallback
    
    AndroidPath --> CheckAndroidDeeplink{딥링크 존재?}
    CheckAndroidDeeplink -->|Yes| TryAndroidApp[Android 앱 실행 시도]
    CheckAndroidDeeplink -->|No| AndroidFallback[Android 폴백 URL로 리다이렉트]
    
    TryAndroidApp --> AndroidAppCheck{앱 실행 성공?}
    AndroidAppCheck -->|Yes| AndroidSuccess[앱에서 컨텐츠 표시]
    AndroidAppCheck -->|No| AndroidFallback
    
    DefaultPath --> DefaultRedirect[기본 폴백 URL로 리다이렉트]
    
    iOSFallback --> RecordVisit[방문 기록 저장]
    AndroidFallback --> RecordVisit
    DefaultRedirect --> RecordVisit
    iOSSuccess --> RecordVisit
    AndroidSuccess --> RecordVisit
    
    RecordVisit --> End2([종료])
    
    class CreateRequest,AccessShortURL userAction
    class GenerateHash,CheckHash,GenerateRandom,SaveURL,EncodePK,CombineKeys,ExtractKey,ExtractPK,DecodePK,FetchURL,DetectDevice,RecordVisit systemAction
    class ReturnShortURL,iOSSuccess,AndroidSuccess,iOSFallback,AndroidFallback,DefaultRedirect success
```

## API 세부 설명

### 1. 단축 URL 생성 API

인증된 사용자가 URL 정보를 제공하여 단축 URL을 생성합니다.

**URL**: `/v1/short-url/`

**메서드**: `POST`

**인증**: 액세스 토큰 필요 (Authorization 헤더)

**요청 본문**:
```json
{
  "ios_deep_link": "앱스킴://경로",
  "ios_fallback_url": "https://example.com/ios",
  "android_deep_link": "앱스킴://경로",
  "android_fallback_url": "https://example.com/android",
  "default_fallback_url": "https://example.com",
  "og_tag": {
    "og:title": "제목",
    "og:description": "설명",
    "og:image": "https://example.com/image.jpg"
  }
}
```

**응답 (201 Created)**:
```json
{
  "id": 123,
  "short_key": "ab1Xcd",
  "ios_deep_link": "앱스킴://경로",
  "ios_fallback_url": "https://example.com/ios",
  "android_deep_link": "앱스킴://경로",
  "android_fallback_url": "https://example.com/android",
  "default_fallback_url": "https://example.com",
  "og_tag": {
    "og:title": "제목",
    "og:description": "설명",
    "og:image": "https://example.com/image.jpg"
  }
}
```

**필수 필드**:
- `default_fallback_url`: 기본 폴백 URL (유효한 URL 형식)

**선택적 필드**:
- `ios_deep_link`: iOS 앱 딥링크
- `ios_fallback_url`: iOS 폴백 URL (유효한 URL 형식)
- `android_deep_link`: Android 앱 딥링크
- `android_fallback_url`: Android 폴백 URL (유효한 URL 형식)
- `og_tag`: Open Graph 태그 (JSON 객체)

### 2. 단축 URL 리다이렉트 API

단축 URL에 접근하여 적절한 URL로 리다이렉션합니다.

**URL**: `url.{호스트}/{short_key}/`

**메서드**: `GET`

**인증**: 불필요

**파라미터**:
- `short_key`: 단축 URL 키
- `referrer`: (선택적) 레퍼러 정보

**동작**:
1. 단축 키에서 PK를 추출하여 URL 정보를 조회
2. 사용자 에이전트를 분석하여 디바이스 유형 감지
3. 적절한 딥링크 또는 폴백 URL로 리다이렉트
4. 방문 정보 기록 (IP, 에이전트, 레퍼러, 타임스탬프)

## 단축 키 생성 알고리즘

단축 키 생성은 다음과 같은 단계로 이루어집니다:

1. **랜덤 키 생성**:
   ```python
   def generate_random_key():
       return "".join(random.choices(string.ascii_letters + string.digits, k=4))
   ```

2. **ID를 문자열 키로 변환**:
   ```python
   def id_to_key(idx: int):
       if idx < 1:
           return None
       key = []
       while idx > 0:
           idx -= 1
           digit = idx % BASE
           key.append(CHARS[digit])
           idx //= BASE
       key.reverse()
       return "".join(key)
   ```

3. **키를 ID로 변환** (리다이렉트 시):
   ```python
   def key_to_id(key: str):
       result = 0
       for c in key:
           digit = CHARS.find(c)
           if digit == -1:
               return None
           result = result * BASE + (digit + 1)
       return result
   ```

4. **최종 단축 키 조합**:
   ```python
   def to_representation(self, instance):
       short_key = id_to_key(instance.id)
       random_key = instance.random_key
       instance.short_key = f"{random_key[:2]}{short_key}{random_key[2:]}"
       return super().to_representation(instance)
   ```

## URL 해싱 알고리즘

URL 중복 방지를 위한 해싱은 다음과 같이 구현됩니다:

```python
def validate(self, attrs):
    # hashed_value 값 생성
    concatenated = "".join(
        [
            attrs.get("ios_deep_link", ""),
            attrs.get("ios_fallback_url", ""),
            attrs.get("android_deep_link", ""),
            attrs.get("android_fallback_url", ""),
            attrs.get("default_fallback_url", ""),
        ]
    )

    # SHA-256 해시 생성
    hasher = hashlib.sha256()
    hasher.update(concatenated.encode("utf-8"))
    hashed_value = hasher.hexdigest()

    if ShortUrl.objects.filter(hashed_value=hashed_value).exists():
        raise serializers.ValidationError(E005_HASHED_VALUE_ALREADY_EXISTS)
    attrs["hashed_value"] = hashed_value
    return attrs
```

## 사용 예시

### 단축 URL 생성

```
POST /v1/short-url/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

{
  "ios_deep_link": "myapp://product/123",
  "ios_fallback_url": "https://example.com/ios/product/123",
  "android_deep_link": "myapp://product/123",
  "android_fallback_url": "https://example.com/android/product/123",
  "default_fallback_url": "https://example.com/product/123",
  "og_tag": {
    "og:title": "멋진 제품",
    "og:description": "이 제품은 정말 멋집니다",
    "og:image": "https://example.com/images/product123.jpg"
  }
}
```

**응답**:
```json
{
  "id": 42,
  "short_key": "xy1Zab",
  "ios_deep_link": "myapp://product/123",
  "ios_fallback_url": "https://example.com/ios/product/123",
  "android_deep_link": "myapp://product/123",
  "android_fallback_url": "https://example.com/android/product/123",
  "default_fallback_url": "https://example.com/product/123",
  "og_tag": {
    "og:title": "멋진 제품",
    "og:description": "이 제품은 정말 멋집니다",
    "og:image": "https://example.com/images/product123.jpg"
  }
}
```

### 단축 URL 접근

사용자가 `https://url.example.com/xy1Zab/` 에 접근하면:

1. 서버는 `1Zab` 부분을 추출하여 데이터베이스 ID `42`로 변환
2. ID `42`에 해당하는 URL 정보를 조회
3. 사용자의 디바이스를 감지하여 적절한 URL로 리다이렉트:
   - iOS 사용자: `myapp://product/123` (앱 설치 시) 또는 `https://example.com/ios/product/123` (미설치 시)
   - Android 사용자: `myapp://product/123` (앱 설치 시) 또는 `https://example.com/android/product/123` (미설치 시)
   - 기타 디바이스: `https://example.com/product/123`

## 오류 응답 형식

**유효성 검사 실패 (400 Bad Request)**:
```json
{
  "필드명": [
    {
      "message": "오류 메시지",
      "error_code": "오류 코드"
    }
  ]
}
```

필드와 관련 없는 오류의 경우 `non_field` 키를 사용합니다:
```json
{
  "non_field": [
    {
      "message": "오류 메시지",
      "error_code": "오류 코드"
    }
  ]
}
```

### 예시 오류 응답

**해시값 중복**:
```json
{
  "non_field": [
    {
      "message": "동일한 URL 조합을 가진 단축 URL이 이미 존재합니다",
      "error_code": "E005"
    }
  ]
}
```

**유효하지 않은 URL 형식**:
```json
{
  "default_fallback_url": [
    {
      "message": "유효한 URL을 입력하십시오",
      "error_code": "E001"
    }
  ]
}
```

**유효하지 않은 OG 태그 형식**:
```json
{
  "og_tag": [
    {
      "message": "유효한 JSON 형식이 아닙니다",
      "error_code": "E005"
    }
  ]
}
```

## 오류 코드

| 오류 코드 | 설명 | 필드 |
|-----------|------|------|
| E005 | 동일한 URL 조합을 가진 단축 URL이 이미 존재함 | non_field |
| E005 | 유효하지 않은 OG 태그 형식 | og_tag |
| E001 | 유효하지 않은 URL 형식 | ios_fallback_url, android_fallback_url, default_fallback_url |

## 관리자 기능

단축 URL 시스템은 관리자 인터페이스를 통해 다음 작업을 지원합니다:

1. 단축 URL 조회 및 필터링
2. URL 정보 수정 (해시값 자동 업데이트)
3. 중복 URL 생성 방지
4. 방문 기록 조회 및 분석

단, 관리자 인터페이스에서는 새 단축 URL 생성 및 방문 기록 수정/삭제는 불가능하며, 조회만 가능합니다.

## 보안 고려사항

- 단축 URL 생성은 인증된 사용자만 가능
- URL 리다이렉트는 인증 없이 접근 가능
- 방문 기록에 IP 주소 저장 시 개인정보보호법 준수 필요
- 모든 API 요청은 HTTPS를 통해 이루어져야 함

이 API를 통해 빠르고 안정적인 단축 URL 서비스를 제공하면서, 사용자 경험을 최적화할 수 있습니다.