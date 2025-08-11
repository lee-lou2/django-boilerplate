# Django Enterprise Boilerplate

[한국어](README.md) | [English](README.en.md)

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Django](https://img.shields.io/badge/Django-5.1%2B-green)
![DRF](https://img.shields.io/badge/DRF-3.15%2B-yellow)
![Celery](https://img.shields.io/badge/Celery-5.2%2B-orange)
![License](https://img.shields.io/badge/License-MIT-blue)

실제 프로덕션 환경에서 바로 사용할 수 있는 엔터프라이즈급 Django 보일러플레이트입니다. 사용자 관리, 컨텐츠 생성, 소셜 기능, 알림 시스템 등 현대적인 웹 서비스에 필수적인 모든 기능이 구현되어 있습니다.

## 🌟 주요 기능

### 사용자 관리
- [x] 회원가입, 이메일 인증, 로그인 (JWT)
- [x] 소셜 로그인 (Google)
- [x] 사용자 프로필 관리
- [ ] 권한 및 역할 기반 접근 제어
- [x] 멀티 디바이스 관리

### 컨텐츠 관리
- [x] 피드 관리
- [ ] 사용자 기반 구독
- [x] 피드 및 댓글 좋아요, 신고
- [x] 대용량 파일 업로드 및 관리

### 커뮤니케이션
- [x] 이메일 발송 시스템
- [ ] 푸시 알림
- [ ] 1:1 문의
- [x] FAQ 및 공지사항

### 게임 기능
- [x] 출석 체크

### 유틸리티
- [x] 숏링크 생성 및 관리
- [ ] 통계 및 분석
- [x] 어드민 대시보드
- [x] API 버전 관리

### 인프라
- [x] 비동기 작업 처리 (Celery)
- [ ] 검색 최적화 (Elasticsearch)
- [x] 캐시 관리 (Redis, Memcached)
- [ ] 미디어 저장소 (AWS S3)
- [x] 로깅 및 모니터링

## 🚀 시작하기

### 요구사항

- Python 3.11+
- Django 5.1+

### 설치

```bash
# 저장소 클론
git clone https://github.com/lee-lou2/django-boilerplate.git
cd django-boilerplate

# uv 설치 (미설치 시)
# macOS (Homebrew 권장):
#   brew install uv
# 기타 환경: https://docs.astral.sh/uv/getting-started/ 참고

# 의존성 동기화 (자동으로 .venv 생성)
uv sync

# 소스 폴더로 이동
cd src

# logs 폴더 생성
mkdir -p logs

# 환경 변수 설정
cp .env.example .env
# .env 파일 편집하여 데이터베이스, 이메일, S3 등 설정

# 마이그레이션 실행
uv run python manage.py migrate

# 개발 서버 실행
uv run python manage.py runserver
```

## 📚 문서

각 기능별로 상세한 문서를 제공합니다. 문서는 한국어와 영어로 제공됩니다.

### 앱

- [계정 관리](docs/ko/apps/account.md) - 회원 가입, 로그인, 소셜 로그인, 이메일 인증 등
- [사용자 관리](./docs/ko/apps/user.md) - 사용자 프로필 관리
- [디바이스 관리](./docs/ko/apps/device.md) - 디바이스/푸시 토큰 등록
- [숏링크 관리](./docs/ko/apps/short-url.md) - 숏링크 생성 및 관리
- [피드 관리](./docs/ko/apps/feed.md) - 피드 관리
- [콘텐츠 관리](./docs/ko/apps/cms.md) - 공지사항, 이벤트, FAQ 등 관리
- [게임](./docs/ko/apps/game.md) - 출석 체크

### 보안

- [데이터 암호화](./docs/ko/security/encryption.md)

### 설정 및 배포

- [Docker 설정 및 배포](./docs/ko/deploy/docker-setup.md)
- [서버 배포 가이드](./docs/ko/deploy/deployment.md) (준비 중)
- [CI/CD 파이프라인](./docs/ko/deploy/ci-cd.md) (준비 중)


## 📂 프로젝트 구조

```
django-boilerplate/
├── src/                       # 소스 폴더
│   ├── apps/                  # 앱 모듈
│   │   ├── account/           # 계정 관리
│   │   ├── agreement/         # 약관 관리
│   │   ├── benefit/           # 혜택 관리
│   │   ├── cms/               # 콘텐츠 관리
│   │   ├── device/            # 디바이스 관리
│   │   ├── feed/              # 피드 시스템
│   │   ├── file/              # 파일 관리
│   │   ├── game/              # 게임
│   │   ├── short_url/         # 숏링크 관리
│   │   └── user/              # 사용자 관리
│   ├── base/                  # 공통 모듈
│   │   ├── enums              # 열거형
│   │   ├── utils              # 공통 유틸
│   │   └── fields             # 필드 클래스
│   ├── conf/                  # 프로젝트 설정
│   │   ├── settings/          # 환경별 설정
│   │   │   ├── base.py        # 기본 설정
│   │   │   ├── dev.py         # 개발 환경
│   │   │   ├── test.py        # 테스트 환경
│   │   │   └── prod.py        # 운영 환경
│   │   ├── urls/              # URL 설정
│   │   │   ├── admin.py       # 관리자 URL 설정
│   │   │   ├── api.py         # API URL 설정
│   │   │   └── url.py         # URL Shorter 설정
│   │   ├── authentications.py # 인증 설정
│   │   ├── caches.py          # 캐시 설정
│   │   ├── celery.py          # Celery 설정
│   │   ├── exceptions.py      # 예외 처리
│   │   ├── filters.py         # 필터 설정
│   │   ├── hosts.py           # 호스트 설정
│   │   ├── routers.py         # 라우터 설정
│   │   ├── schedules.py       # 스케줄러 설정
│   │   ├── utils.py           # 공통 유틸리티 함수
│   │   └── wsgi.py            # WSGI 설정
│   ├── static/                # 정적 파일
│   ├── templates/             # 템플릿 파일
│   ├── .env.emample           # 환경 변수 예제
│   ├── Makefile               # 명령어 파일
│   └── manage.py              # Django 관리 명령어
├── docs/                      # 문서
│   ├── files/                 # 파일
│   ├── ko/                    # 한국어 문서
│   └── en/                    # 영어 문서
├── docker-compose.yml         # Docker Compose 설정
├── Dockerfile                 # Docker 이미지 설정
├── pyproject.toml             # 프로젝트 설정 및 의존성 관리 (uv)
├── uv.lock                    # 의존성 잠금 파일
└── README.md                  # 프로젝트 소개
```

## 🧩 앱 구조

각 앱은 다음과 같은 구조를 따릅니다:

```
app_name/
├── v1/                        # API 버전 1
│   ├── filters.py             # 필터셋 클래스
│   ├── serializers.py         # 시리얼라이저
│   ├── views.py               # 뷰 함수/클래스
│   ├── urls.py                # URL 패턴
│   ├── utils.py               # 유틸리티 함수
│   ├── tasks.py               # 비동기 작업
│   └── tests.py               # 테스트
├── migrations/                # DB 마이그레이션
├── management/                # 관리 명령어
│   └── commands/              # 사용자 정의 명령어
├── admin.py                   # 관리자 인터페이스
├── apps.py                    # 앱 설정
├── models.py                  # 데이터 모델
└── signals.py                 # 시그널 처리
```

## 🛠️ 기술 스택

### 백엔드
- Django 5.1+: 웹 프레임워크
- Django REST Framework 3.15+: API 개발
- Celery 5.2+: 비동기 작업 처리
- Sentry: 오류 모니터링
- JWT: 인증

### 인프라
- Docker: 컨테이너화
- Nginx: 웹 서버
- AWS S3: 파일 스토리지
- GitHub Actions: CI/CD
- AWS: 클라우드 호스팅

## 📈 성능 최적화

- 데이터베이스 쿼리 최적화
- Redis 캐싱 전략
- Celery를 이용한 비동기 작업 처리
- 대용량 파일 처리를 위한 청크 업로드
- 페이지네이션 및 필터링 최적화

## 🔒 보안

- JWT 기반 인증
- 사용자 권한 관리
- CSRF/XSS 보호
- API 요청 제한
- 데이터 암호화
- OAuth2 보안 설정
- 환경 변수를 통한 민감 정보 관리

## 📝 개발 가이드라인

- 코드 리뷰 프로세스
- 테스트 주도 개발 (TDD)
- 지속적 통합 및 배포 (CI/CD)
- 코드 품질 관리 (linting, formatting)
- 깃 브랜치 전략 ([자체 브랜치 전략](https://lee-lou2.notion.site/Git-Branch-78a65eecaa2d4070ad19221681a96a00?pvs=4))

## 📸 스크린샷

### 백오피스
![backoffice_login.png](docs/files/backoffice_login.png)
![backoffice_dashboard.png](docs/files/backoffice_dashboard.png)

## 🧪 테스트

```bash
# 모든 테스트 실행
python manage.py test

# 특정 앱 테스트
python manage.py test apps.account
```

## 🤝 기여하기

1. 이 저장소를 Fork합니다
2. Feature 브랜치를 생성합니다 (`git checkout -b feature/amazing-feature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add some amazing feature'`)
4. 브랜치에 푸시합니다 (`git push origin feature/amazing-feature`)
5. Pull Request를 생성합니다

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 📮 연락처

- 프로젝트 관리자: [JAKE](mailto:lee@lou2.kr)
- 이슈 트래커: [GitHub Issues](https://github.com/lee-lou2/django-boilerplate/issues)
