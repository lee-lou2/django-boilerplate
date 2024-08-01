# Django Boilerplate 🔥

## ⭐️ 사이트
🏠 홈페이지 : 준비중

## 🚘 프로젝트 소개

- Language : Python(3.10>)
- Framework : Django(5.0>)
- DB : Sqlite3, Postgresql, MongoDB
- CACHE : Redis, RabbitMQ

## 🎛️ 개발 중점 사항

1. 보안
    - 민감한 정보 암호화
    - CSRF, XSS 등 공격 방어
    - scope, permission 등 권한 관리
    - 로깅시 민감한 정보 마스킹
2. 성능
    - 캐싱 및 비동기 처리
    - ORM/DB 쿼리 최적화
3. 확장성
    - 모듈화
4. 유지/보수
5. 테스트

## 🛠️ 서버 구성

- API Server : API 서버
- Admin Server : 관리자 서버
- Celery Worker : 비동기 작업 처리
- Celery Beat : 스케쥴링 작업 처리

## 🗄️ 프로젝트 구조

### 1. 폴더 구조
```
/django-boilerplate
├── src
│   ├── app
│   │   ├── celery_log
│   │   │   ├── migrations
│   │   │   └── ...
│   │   ├── common
│   │   │   ├── debug
│   │   │   ├── management
│   │   │   ├── utils
│   │   │   └── ...
│   │   ├── device
│   │   │   ├── migrations
│   │   │   └── ...
│   │   ├── file
│   │   │   ├── migrations
│   │   │   ├── v1
│   │   │   └── ...
│   │   ├── log
│   │   │   ├── migrations
│   │   │   └── ...
│   │   ├── user
│   │   │   ├── migrations
│   │   │   ├── templates
│   │   │   ├── v1
│   │   │   └── ...
│   │   ├── verifier
│   │   │   ├── migrations
│   │   │   ├── v1
│   │   │   └── ...
│   │   ├── common
│   │   │   ├── migrations
│   │   │   └── ...
│   │   └── withdrawal_user
│   │       ├── migrations
│   │       └── ...
│   ├── conf
│   │   ├── settings
│   │   │   ├── base.py
│   │   │   ├── develop.py
│   │   │   ├── local.py
│   │   │   ├── prod.py
│   │   │   ├── stage.py
│   │   │   └── test.py
│   │   ├── urls
│   │   │   ├── admin.py
│   │   │   └── api.py
│   │   ├── aws.py
│   │   ├── cache.py
│   │   ├── celery.py
│   │   ├── enums.py
│   │   ├── exceptions.py
│   │   ├── filters.py
│   │   ├── hosts.py
│   │   ├── openapi.py
│   │   ├── routers.py
│   │   ├── schedules.py
│   │   ├── spectacular_hooks.py
│   │   └── wsgi.py
│   ├── logs
│   │   └── ...
│   ├── static
│   │   └── ...
│   ├── staticfiles
│   │   └── ...
│   ├── templates
│   │   └── ...
│   ├── .env
│   └── manage.py
├── README.md
└── requirements.txt
```

### 2. 앱 상세

| app            | 설명                        |
|----------------|---------------------------|
| celery_log     | 샐러리 로그 저장                 |
| common         | 통합 패키지 관리                 |
| device         | 디바이스 관리                   |
| file           | Presigned URL 을 이용한 파일 관리 |
| log            | 로그 관리                     |
| user           | 사용자                       |
| verifier       | 사용자 검증                    |
| withdrawal_user | 탈퇴 사용자                    |

## 🎬 로컬 실행

파이썬(3.10 버전 이상) 설치 후 아래 명령어를 실행

### 1. 환경 설정

```shell
$ pip install -r requirements.txt
```

### 2. 데이터 마이그레이트 및 정적 파일 생성

```shell
$ python manage.py migrate
$ python manage.py collectstatic
```

### 3. 서버 실행

```shell
$ python manage.py runserver
```
