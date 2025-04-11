# CMS API Documentation

## Overview

이 문서는 CMS(Content Management System) 관련 API 기능에 대한 가이드입니다. 시스템은 공지사항(Notice), 이벤트(Event), FAQ를 관리하고 조회하기 위한 기능을 제공합니다. 사용자는 인증 후 활성화된 콘텐츠를 조회할 수 있습니다.

## API 엔드포인트

| 경로                       | 메서드 | 설명                 |
|---------------------------|--------|---------------------|
| `/v1/cms/notice/`         | GET    | 공지사항 리스트 조회   |
| `/v1/cms/notice/{uuid}/`  | GET    | 공지사항 상세 조회     |
| `/v1/cms/event/`          | GET    | 이벤트 리스트 조회     |
| `/v1/cms/event/{uuid}/`   | GET    | 이벤트 상세 조회       |
| `/v1/cms/faq/`            | GET    | FAQ 리스트 조회       |

## CMS 흐름도

### 1. 공지사항 조회 흐름

```mermaid
flowchart TD
    classDef userAction fill:#f9d6d6,stroke:#e88e8e,stroke-width:2px,color:#333
    classDef systemAction fill:#d6e5f9,stroke:#8eb5e8,stroke-width:2px,color:#333
    classDef success fill:#d6f9d6,stroke:#8ee88e,stroke-width:2px,color:#333
    classDef error fill:#f9f9d6,stroke:#e8e88e,stroke-width:2px,color:#333
    classDef decision fill:#d6f9f9,stroke:#8ee8e8,stroke-width:2px,color:#333
    
    Start([공지사항 조회 시작]) --> AuthCheck{인증 여부 확인}:::systemAction
    
    AuthCheck -->|인증 실패| Unauthorized[인증 오류 응답]:::error
    Unauthorized --> End1([조회 실패])
    
    AuthCheck -->|인증 성공| ListOrDetail{리스트/상세<br>요청 구분}:::decision
    
    ListOrDetail -->|리스트 조회| GetActiveNotices[현재 활성화된<br>공지사항 필터링]:::systemAction
    ListOrDetail -->|상세 조회| GetNoticeDetail[UUID로<br>공지사항 조회]:::systemAction
    
    GetActiveNotices --> ApplyFilters[필터 적용<br>(제목, 발행일)]:::systemAction
    GetActiveNotices --> ListNotice[공지사항 목록 응답]:::success
    ListNotice --> End2([목록 조회 완료])
    
    GetNoticeDetail --> NoticeExists{공지사항<br>존재 여부}:::decision
    NoticeExists -->|없음| NotFound[404 Not Found 응답]:::error
    NotFound --> End3([조회 실패])
    
    NoticeExists -->|존재| DetailNotice[공지사항 상세 응답]:::success
    DetailNotice --> End4([상세 조회 완료])
    
    class AuthCheck,GetActiveNotices,ApplyFilters,GetNoticeDetail systemAction
    class ListOrDetail,NoticeExists decision
    class Unauthorized,NotFound error
    class ListNotice,DetailNotice success
```

### 2. 이벤트 조회 흐름

```mermaid
flowchart TD
    classDef userAction fill:#f9d6d6,stroke:#e88e8e,stroke-width:2px,color:#333
    classDef systemAction fill:#d6e5f9,stroke:#8eb5e8,stroke-width:2px,color:#333
    classDef success fill:#d6f9d6,stroke:#8ee88e,stroke-width:2px,color:#333
    classDef error fill:#f9f9d6,stroke:#e8e88e,stroke-width:2px,color:#333
    classDef decision fill:#d6f9f9,stroke:#8ee8e8,stroke-width:2px,color:#333
    
    Start([이벤트 조회 시작]) --> AuthCheck{인증 여부 확인}:::systemAction
    
    AuthCheck -->|인증 실패| Unauthorized[인증 오류 응답]:::error
    Unauthorized --> End1([조회 실패])
    
    AuthCheck -->|인증 성공| ListOrDetail{리스트/상세<br>요청 구분}:::decision
    
    ListOrDetail -->|리스트 조회| GetActiveEvents[현재 활성화된<br>이벤트 필터링]:::systemAction
    ListOrDetail -->|상세 조회| GetEventDetail[UUID로<br>이벤트 조회]:::systemAction
    
    GetActiveEvents --> ApplyFilters[필터 적용<br>(제목, 발행일)]:::systemAction
    GetActiveEvents --> CheckEventStatus[이벤트 종료 상태<br>확인(is_event_ended)]:::systemAction
    
    CheckEventStatus --> ListEvent[이벤트 목록 응답]:::success
    ListEvent --> End2([목록 조회 완료])
    
    GetEventDetail --> EventExists{이벤트<br>존재 여부}:::decision
    EventExists -->|없음| NotFound[404 Not Found 응답]:::error
    NotFound --> End3([조회 실패])
    
    EventExists -->|존재| CheckEndStatus[이벤트 종료 상태<br>확인(is_event_ended)]:::systemAction
    CheckEndStatus --> DetailEvent[이벤트 상세 응답]:::success
    DetailEvent --> End4([상세 조회 완료])
    
    class AuthCheck,GetActiveEvents,ApplyFilters,CheckEventStatus,GetEventDetail,CheckEndStatus systemAction
    class ListOrDetail,EventExists decision
    class Unauthorized,NotFound error
    class ListEvent,DetailEvent success
```

### 3. FAQ 조회 흐름

```mermaid
flowchart TD
    classDef userAction fill:#f9d6d6,stroke:#e88e8e,stroke-width:2px,color:#333
    classDef systemAction fill:#d6e5f9,stroke:#8eb5e8,stroke-width:2px,color:#333
    classDef success fill:#d6f9d6,stroke:#8ee88e,stroke-width:2px,color:#333
    classDef error fill:#f9f9d6,stroke:#e8e88e,stroke-width:2px,color:#333
    classDef decision fill:#d6f9f9,stroke:#8ee8e8,stroke-width:2px,color:#333
    
    Start([FAQ 조회 시작]) --> AuthCheck{인증 여부 확인}:::systemAction
    
    AuthCheck -->|인증 실패| Unauthorized[인증 오류 응답]:::error
    Unauthorized --> End1([조회 실패])
    
    AuthCheck -->|인증 성공| GetPublishedFAQs[발행된 FAQ<br>필터링]:::systemAction
    
    GetPublishedFAQs --> CategoryFilter{카테고리<br>필터 지정}:::decision
    
    CategoryFilter -->|미지정| AllFAQs[모든 FAQ 조회]:::systemAction
    CategoryFilter -->|지정| FilterByCategory[카테고리별<br>FAQ 필터링]:::systemAction
    
    AllFAQs --> ApplyPagination[페이지네이션 적용]:::systemAction
    FilterByCategory --> ApplyPagination
    
    ApplyPagination --> ListFAQ[FAQ 목록 응답<br>(카테고리 정보 포함)]:::success
    ListFAQ --> End2([조회 완료])
    
    class AuthCheck,GetPublishedFAQs,AllFAQs,FilterByCategory,ApplyPagination systemAction
    class CategoryFilter decision
    class Unauthorized error
    class ListFAQ success
```

## API 상세 설명

### 1. 공지사항 리스트 조회 API

공지사항 목록을 조회합니다.

**URL**: `/v1/cms/notice/`

**메서드**: `GET`

**인증**: 필수 (JWT 액세스 토큰)

**쿼리 파라미터**:
- `title__icontains`: 제목 검색 (대소문자 구분 없이)
- `title__exact`: 정확한 제목 일치 검색
- `published_at__gte`: 특정 날짜 이후 발행된 공지사항 (ISO 8601 형식, 예: 2023-01-01T00:00:00Z)
- `published_at__lte`: 특정 날짜 이전 발행된 공지사항 (ISO 8601 형식, 예: 2023-01-31T23:59:59Z)
- `limit`: 페이지당 항목 수 (기본값: 10)
- `offset`: 페이지 오프셋

**응답 (200 OK)**:
```json
{
  "count": 1,
  "next": "http://example.com/v1/cms/notice/?limit=10&offset=10",
  "previous": null,
  "results": [
    {
      "uuid": "123e4567-e89b-12d3-a456-426614174000",
      "title": "공지사항 제목",
      "content": "공지사항 내용",
      "published_at": "2023-01-01T00:00:00.000000Z",
      "start_at": "2023-01-01T00:00:00.000000Z",
      "end_at": "2023-01-08T00:00:00.000000Z",
      "created_at": "2023-01-01T00:00:00.000000Z",
      "updated_at": "2023-01-01T00:00:00.000000Z"
    }
  ]
}
```

**필터링 조건**:
- 현재 시간 기준으로 시작 시간(start_at)이 지났고 종료 시간(end_at)이 지나지 않은 공지사항만 조회됨
- 종료 시간(end_at)이 null인 경우 만료되지 않은 공지사항으로 간주됨
- 발행 여부(is_published)가 true인 공지사항만 조회됨

**응답 코드**:
- `200 OK`: 성공
- `401 Unauthorized`: 인증 실패

### 2. 공지사항 상세 조회 API

특정 공지사항의 상세 정보를 조회합니다.

**URL**: `/v1/cms/notice/{uuid}/`

**메서드**: `GET`

**인증**: 필수 (JWT 액세스 토큰)

**URL 파라미터**:
- `uuid`: 조회할 공지사항의 UUID

**응답 (200 OK)**:
```json
{
  "uuid": "123e4567-e89b-12d3-a456-426614174000",
  "title": "공지사항 제목",
  "content": "공지사항 내용",
  "published_at": "2023-01-01T00:00:00.000000Z",
  "start_at": "2023-01-01T00:00:00.000000Z",
  "end_at": "2023-01-08T00:00:00.000000Z",
  "created_at": "2023-01-01T00:00:00.000000Z",
  "updated_at": "2023-01-01T00:00:00.000000Z"
}
```

**응답 코드**:
- `200 OK`: 성공
- `401 Unauthorized`: 인증 실패
- `404 Not Found`: 존재하지 않는 공지사항

### 3. 이벤트 리스트 조회 API

이벤트 목록을 조회합니다.

**URL**: `/v1/cms/event/`

**메서드**: `GET`

**인증**: 필수 (JWT 액세스 토큰)

**쿼리 파라미터**:
- `title__icontains`: 제목 검색 (대소문자 구분 없이)
- `title__exact`: 정확한 제목 일치 검색
- `published_at__gte`: 특정 날짜 이후 발행된 이벤트 (ISO 8601 형식)
- `published_at__lte`: 특정 날짜 이전 발행된 이벤트 (ISO 8601 형식)
- `limit`: 페이지당 항목 수 (기본값: 10)
- `offset`: 페이지 오프셋

**응답 (200 OK)**:
```json
{
  "count": 1,
  "next": "http://example.com/v1/cms/event/?limit=10&offset=10",
  "previous": null,
  "results": [
    {
      "uuid": "123e4567-e89b-12d3-a456-426614174001",
      "title": "이벤트 제목",
      "content": "이벤트 내용",
      "published_at": "2023-01-01T00:00:00.000000Z",
      "start_at": "2023-01-01T00:00:00.000000Z",
      "end_at": "2023-01-15T00:00:00.000000Z",
      "event_start_at": "2023-01-02T00:00:00.000000Z",
      "event_end_at": "2023-01-12T00:00:00.000000Z",
      "is_event_ended": false,
      "created_at": "2023-01-01T00:00:00.000000Z",
      "updated_at": "2023-01-01T00:00:00.000000Z"
    }
  ]
}
```

**필터링 조건**:
- 현재 시간 기준으로 시작 시간(start_at)이 지났고 종료 시간(end_at)이 지나지 않은 이벤트만 조회됨
- 종료 시간(end_at)이 null인 경우 만료되지 않은 이벤트로 간주됨
- 발행 여부(is_published)가 true인 이벤트만 조회됨

**응답 코드**:
- `200 OK`: 성공
- `401 Unauthorized`: 인증 실패

### 4. 이벤트 상세 조회 API

특정 이벤트의 상세 정보를 조회합니다.

**URL**: `/v1/cms/event/{uuid}/`

**메서드**: `GET`

**인증**: 필수 (JWT 액세스 토큰)

**URL 파라미터**:
- `uuid`: 조회할 이벤트의 UUID

**응답 (200 OK)**:
```json
{
  "uuid": "123e4567-e89b-12d3-a456-426614174001",
  "title": "이벤트 제목",
  "content": "이벤트 내용",
  "published_at": "2023-01-01T00:00:00.000000Z",
  "start_at": "2023-01-01T00:00:00.000000Z",
  "end_at": "2023-01-15T00:00:00.000000Z",
  "event_start_at": "2023-01-02T00:00:00.000000Z",
  "event_end_at": "2023-01-12T00:00:00.000000Z",
  "is_event_ended": false,
  "created_at": "2023-01-01T00:00:00.000000Z",
  "updated_at": "2023-01-01T00:00:00.000000Z"
}
```

**응답 필드**:
- `is_event_ended`: 현재 시간 기준으로 이벤트 종료 여부(event_end_at과 비교)

**응답 코드**:
- `200 OK`: 성공
- `401 Unauthorized`: 인증 실패
- `404 Not Found`: 존재하지 않는 이벤트

### 5. FAQ 리스트 조회 API

FAQ 목록을 조회합니다.

**URL**: `/v1/cms/faq/`

**메서드**: `GET`

**인증**: 필수 (JWT 액세스 토큰)

**쿼리 파라미터**:
- `category_name`: 카테고리 이름 필터 (대소문자 구분 없이)
- `published_at__gte`: 특정 날짜 이후 발행된 FAQ (ISO 8601 형식)
- `published_at__lte`: 특정 날짜 이전 발행된 FAQ (ISO 8601 형식)
- `limit`: 페이지당 항목 수 (기본값: 10)
- `offset`: 페이지 오프셋

**응답 (200 OK)**:
```json
{
  "count": 1,
  "next": "http://example.com/v1/cms/faq/?limit=10&offset=10",
  "previous": null,
  "results": [
    {
      "uuid": "123e4567-e89b-12d3-a456-426614174002",
      "category": {
        "uuid": "123e4567-e89b-12d3-a456-426614174003",
        "name": "일반",
        "created_at": "2023-01-01T00:00:00.000000Z",
        "updated_at": "2023-01-01T00:00:00.000000Z"
      },
      "title": "FAQ 제목",
      "content": "FAQ 내용",
      "published_at": "2023-01-01T00:00:00.000000Z",
      "created_at": "2023-01-01T00:00:00.000000Z",
      "updated_at": "2023-01-01T00:00:00.000000Z"
    }
  ]
}
```

**필터링 조건**:
- 발행 여부(is_published)가 true인 FAQ만 조회됨
- 카테고리 이름(category_name)으로 필터링 가능

**참고사항**:
- FAQ API는 리스트 조회만 지원하며 상세 조회는 제공하지 않음
- 카테고리 정보가 중첩된 형태로 응답에 포함됨

**응답 코드**:
- `200 OK`: 성공
- `401 Unauthorized`: 인증 실패

## 오류 응답 형식

CMS API의 오류 응답은 다음과 같은 형식을 따릅니다:

```json
{
  "detail": "오류 메시지"
}
```

### 예시 오류 응답

**인증되지 않은 사용자 접근**:
```json
{
  "detail": "자격 인증데이터(authentication credentials)가 제공되지 않았습니다."
}
```

**존재하지 않는 리소스 요청**:
```json
{
  "detail": "찾을 수 없습니다."
}
```

## 페이지네이션

CMS API는 오프셋 기반 페이지네이션을 사용합니다.

### 페이지네이션 파라미터

- `limit`: 페이지당 항목 수 (기본값: 10)
- `offset`: 페이지 오프셋

페이지네이션 응답 예시:
```json
{
  "count": 42,
  "next": "http://example.com/v1/cms/notice/?limit=10&offset=10",
  "previous": null,
  "results": [
    // 조회된 항목 목록
  ]
}
```

### 페이지네이션 사용 예시

1. 첫 페이지 조회:
```
GET /v1/cms/notice/?limit=10&offset=0
```

2. 다음 페이지 조회:
```
GET /v1/cms/notice/?limit=10&offset=10
```

3. 페이지 크기 변경:
```
GET /v1/cms/notice/?limit=20&offset=0
```

## 필터링

### 공지사항 및 이벤트 필터링

- 제목 검색: `?title__icontains=검색어`
- 정확한 제목 일치: `?title__exact=정확한 제목`
- 발행 날짜 범위 필터링: `?published_at__gte=2023-01-01T00:00:00Z&published_at__lte=2023-01-31T23:59:59Z`

### FAQ 필터링

- 카테고리 이름 검색: `?category_name=카테고리명`
- 발행 날짜 범위 필터링: `?published_at__gte=2023-01-01T00:00:00Z&published_at__lte=2023-01-31T23:59:59Z`

## CMS 데이터 모델

### 공지사항(Notice)

| 필드명 | 타입 | 설명 |
|-------|------|------|
| uuid | UUID | 고유 식별자 (uuid7 사용) |
| author | FK | 작성자 (User 모델 참조) |
| title | String | 제목 (최대 255자) |
| content | Text | 내용 |
| published_at | DateTime | 발행 일시 |
| start_at | DateTime | 시작 일시 (표시 기간 시작) |
| end_at | DateTime | 종료 일시 (표시 기간 종료, 선택 사항) |
| is_published | Boolean | 발행 여부 |
| created_at | DateTime | 생성 일시 (자동 생성) |
| updated_at | DateTime | 수정 일시 (자동 업데이트) |

### 이벤트(Event)

| 필드명 | 타입 | 설명 |
|-------|------|------|
| uuid | UUID | 고유 식별자 (uuid7 사용) |
| author | FK | 작성자 (User 모델 참조) |
| title | String | 제목 (최대 255자) |
| content | Text | 내용 |
| published_at | DateTime | 발행 일시 |
| start_at | DateTime | 시작 일시 (표시 기간 시작) |
| end_at | DateTime | 종료 일시 (표시 기간 종료, 선택 사항) |
| event_start_at | DateTime | 이벤트 시작 일시 (실제 이벤트 기간) |
| event_end_at | DateTime | 이벤트 종료 일시 (실제 이벤트 기간, 선택 사항) |
| is_published | Boolean | 발행 여부 |
| created_at | DateTime | 생성 일시 (자동 생성) |
| updated_at | DateTime | 수정 일시 (자동 업데이트) |

### FAQ 카테고리(FaqCategory)

| 필드명 | 타입 | 설명 |
|-------|------|------|
| uuid | UUID | 고유 식별자 (uuid7 사용) |
| name | String | 카테고리 이름 (최대 255자) |
| created_at | DateTime | 생성 일시 (자동 생성) |
| updated_at | DateTime | 수정 일시 (자동 업데이트) |

### FAQ(Faq)

| 필드명 | 타입 | 설명 |
|-------|------|------|
| uuid | UUID | 고유 식별자 (uuid7 사용) |
| author | FK | 작성자 (User 모델 참조) |
| category | FK | 카테고리 (FaqCategory 모델 참조) |
| title | String | 제목 (최대 255자) |
| content | Text | 내용 |
| published_at | DateTime | 발행 일시 |
| is_published | Boolean | 발행 여부 |
| created_at | DateTime | 생성 일시 (자동 생성) |
| updated_at | DateTime | 수정 일시 (자동 업데이트) |

## 관리자 기능

CMS 콘텐츠는 Django 관리자 페이지를 통해 관리됩니다. API를 통한 콘텐츠 생성/수정/삭제는 제공되지 않습니다.

### 공통 관리자 기능

- 항목 목록 조회 및 필터링
- 생성, 수정, 삭제 기능
- 일괄 발행/미발행 처리 (관리자 액션 사용)

### 공지사항 관리

관리자는 Django 관리자 페이지를 통해 다음 필드를 관리할 수 있습니다:

- 기본 정보: 제목, 작성자, 내용
- 발행 및 표시 설정: 발행 여부, 발행 일시, 시작/종료 일시
- 메타 정보 (읽기 전용): UUID, 생성/수정 일시

### 이벤트 관리

관리자는 Django 관리자 페이지를 통해 다음 필드를 관리할 수 있습니다:

- 기본 정보: 제목, 작성자, 내용
- 이벤트 기간: 이벤트 시작/종료 일시
- 발행 및 표시 설정: 발행 여부, 발행 일시, 시작/종료 일시
- 메타 정보 (읽기 전용): UUID, 생성/수정 일시

### FAQ 관리

관리자는 Django 관리자 페이지를 통해 다음 필드를 관리할 수 있습니다:

- 기본 정보: 제목, 작성자, 내용, 카테고리
- 발행 설정: 발행 여부, 발행 일시
- 메타 정보 (읽기 전용): UUID, 생성/수정 일시

## 보안 고려사항

- 모든 API 요청은 인증된 사용자만 접근 가능 (JWT 기반 인증)
- 공지사항, 이벤트, FAQ 조회만 가능하며, 생성/수정/삭제는 관리자 페이지에서만 가능
- 현재 활성화된 콘텐츠만 조회되므로 미래 또는 과거 콘텐츠는 접근할 수 없음
- is_published 필드를 통해 미발행 콘텐츠는 API 응답에서 제외됨

## 테스트 

CMS API는 다양한 테스트 케이스를 통해 검증되었습니다:

### 시리얼라이저 테스트
- 공지사항, 이벤트, FAQ, FAQ 카테고리 각 모델의 직렬화 검증
- 시간 포맷 검증 (ISO 8601 형식)
- 이벤트 종료 여부 계산 검증

### 뷰셋 테스트
- 인증 검증 (인증되지 않은 사용자 접근 거부)
- 활성화된 항목만 조회되는지 검증
- 필터링 기능 동작 검증
- 수정/삭제 API 요청 방지 검증

## 예시 사용 시나리오

### 공지사항 조회

1. 공지사항 리스트 조회:
```
GET /v1/cms/notice/?limit=10&offset=0
```

2. 공지사항 제목으로 검색:
```
GET /v1/cms/notice/?title__icontains=안내&limit=10&offset=0
```

3. 특정 공지사항 상세 조회:
```
GET /v1/cms/notice/123e4567-e89b-12d3-a456-426614174000/
```

### 이벤트 조회

1. 현재 진행 중인 이벤트 리스트 조회:
```
GET /v1/cms/event/?limit=10&offset=0
```

2. 이벤트 제목으로 검색:
```
GET /v1/cms/event/?title__icontains=할인&limit=10&offset=0
```

3. 특정 이벤트 상세 조회:
```
GET /v1/cms/event/123e4567-e89b-12d3-a456-426614174001/
```

4. 특정 기간 내 발행된 이벤트 조회:
```
GET /v1/cms/event/?published_at__gte=2023-01-01T00:00:00Z&published_at__lte=2023-01-31T23:59:59Z
```

### FAQ 조회

1. 전체 FAQ 리스트 조회:
```
GET /v1/cms/faq/?limit=10&offset=0
```

2. 특정 카테고리의 FAQ 조회:
```
GET /v1/cms/faq/?category_name=계정&limit=10&offset=0
```

3. 최근 발행된 FAQ 조회:
```
GET /v1/cms/faq/?published_at__gte=2023-01-01T00:00:00Z
```

## 구현 시 참고사항

### 인증 처리

- 모든 API 요청에는 유효한 JWT 액세스 토큰이 필요함
- Authorization 헤더에 `Bearer {액세스 토큰}` 형식으로 토큰 전달
- 토큰이 만료된 경우 리프레시 토큰으로 갱신 후 재요청 필요

### 콘텐츠 렌더링

- 콘텐츠(content) 필드는 HTML을 포함할 수 있으므로, 프론트엔드에서 렌더링 시 적절한 처리 필요
- React에서는 `dangerouslySetInnerHTML`을 사용하여 HTML 콘텐츠 렌더링 가능