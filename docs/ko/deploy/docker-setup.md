## 🐳 Docker를 이용한 개발 및 배포

### 로컬 개발 환경 설정

Docker와 Docker Compose를 사용하면 복잡한 개발 환경을 쉽게 구성할 수 있습니다. 이 프로젝트는 웹 서버, Celery 워커, PostgreSQL, Redis를 포함한 전체 스택을 Docker Compose로 구성하고 있습니다.

#### 사전 요구사항

- [Docker](https://docs.docker.com/get-docker/) 설치
- [Docker Compose](https://docs.docker.com/compose/install/) 설치

#### 개발 환경 실행

```bash
# 프로젝트 루트 디렉토리에서
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 특정 서비스 로그만 확인
docker-compose logs -f web
```

#### 개발 환경 접속

- Django 웹 서버: http://localhost:8000
- 데이터베이스: PostgreSQL (localhost:5432)
- Redis: localhost:6379

#### 관리 명령어 실행

```bash
# Django 관리 명령어 실행
docker-compose exec web python manage.py [command]

# 예: 마이그레이션 생성
docker-compose exec web python manage.py makemigrations

# 예: 슈퍼유저 생성
docker-compose exec web python manage.py createsuperuser
```

### 온프레미스/서버 배포

#### 프로덕션 환경 설정

1. 프로덕션 환경 변수 설정

```bash
# .env 파일 생성
cp src/.env.example src/.env

# .env 파일을 프로덕션 환경에 맞게 수정
# 특히 다음 변수들을 꼭 변경하세요:
# - SECRET_KEY: 보안을 위해 긴 랜덤 문자열로 설정
# - DEBUG: False로 설정
# - ALLOWED_HOSTS: 실제 도메인 이름 설정
# - DATABASE_URL: 프로덕션 데이터베이스 연결 정보
```

2. docker-compose.yml 최적화 (선택사항)

```bash
# 프로덕션용 docker-compose 파일 생성
cp docker-compose.yml docker-compose.prod.yml

# docker-compose.prod.yml 편집:
# - 볼륨 설정 최적화
# - 환경 변수 DJANGO_SETTINGS_MODULE을 conf.settings.production으로 변경
# - 워커 수 및 스레드 수 조정
```

3. 배포 실행

```bash
# 프로덕션 배포
docker-compose -f docker-compose.prod.yml up -d

# 마이그레이션 실행
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# 정적 파일 수집
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

#### NGINX 프록시 설정 (권장)

프로덕션 환경에서는 NGINX를 앞단에 두어 정적 파일 서빙과 SSL 종료를 처리하는 것이 좋습니다.

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location /static/ {
        alias /path/to/your/static/files/;
    }
    
    location /media/ {
        alias /path/to/your/media/files/;
    }
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Docker 컨테이너 관리

#### 기본 명령어

```bash
# 전체 스택 시작
docker-compose up -d

# 전체 스택 중지
docker-compose down

# 특정 서비스만 재시작
docker-compose restart web

# 컨테이너 로그 확인
docker-compose logs -f [service_name]

# 컨테이너 내부 접속
docker-compose exec [service_name] bash
```

#### 데이터베이스 백업 및 복원

```bash
# PostgreSQL 데이터베이스 백업
docker-compose exec db pg_dump -U postgres postgres > backup.sql

# PostgreSQL 데이터베이스 복원
cat backup.sql | docker-compose exec -T db psql -U postgres postgres
```

#### 리소스 모니터링

```bash
# 실행 중인 컨테이너 확인
docker-compose ps

# 컨테이너 리소스 사용량 확인
docker stats
```

### 스케일링 및 성능 최적화

#### 웹 애플리케이션 스케일링

```bash
# 웹 서비스 인스턴스 수 조정
docker-compose up -d --scale web=3
```

#### 워커 스케일링

```bash
# Celery 워커 인스턴스 수 조정
docker-compose up -d --scale worker=5
```

#### Gunicorn 설정 최적화

웹 서비스 성능을 최적화하려면 Dockerfile이나 docker-compose.yml에서 Gunicorn 설정을 조정하세요:

```
# 워커 수 = (2 * CPU 코어 수) + 1
# 스레드 수 = 2-4
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "conf.wsgi:application", "--workers", "5", "--threads", "2"]
```
