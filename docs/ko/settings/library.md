# 라이브러리 소개

이 프로젝트에 설치된 주요 라이브러리에 대한 소개와 활용 방법을 안내합니다. 각 라이브러리는 특정 기능을 제공하여 Django 기반 웹 애플리케이션 개발을 용이하게 합니다.

## 핵심 프레임워크

### Django (5.1.7)
Python 웹 프레임워크로, MVT(Model-View-Template) 패턴을 기반으로 합니다.
- **역할**: 웹 애플리케이션의 기본 구조 및 ORM 제공
- **사용방법**:
  ```python
  # 프로젝트 생성
  django-admin startproject myproject
  
  # 앱 생성
  python manage.py startapp myapp
  
  # 개발 서버 실행
  python manage.py runserver
  ```

### Django REST Framework (3.15.2)
Django 기반 RESTful API 개발을 위한 강력한 도구입니다.
- **역할**: API 엔드포인트 구현, 시리얼라이저, 인증 메커니즘 제공
- **사용방법**:
  ```python
  # views.py
  from rest_framework.views import APIView
  from rest_framework.response import Response
  
  class UserView(APIView):
      def get(self, request):
          return Response({"message": "Success"})
  ```

## 인증 및 보안

### Django REST Framework Simple JWT (5.5.0)
JWT(JSON Web Token) 기반 인증을 제공합니다.
- **역할**: 토큰 발급, 갱신, 검증 기능 제공
- **사용방법**:
  ```python
  # settings.py
  REST_FRAMEWORK = {
      'DEFAULT_AUTHENTICATION_CLASSES': (
          'rest_framework_simplejwt.authentication.JWTAuthentication',
      )
  }
  
  # urls.py
  from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
  
  urlpatterns = [
      path('api/token/', TokenObtainPairView.as_view()),
      path('api/token/refresh/', TokenRefreshView.as_view()),
  ]
  ```

### PyCryptodome (3.22.0)
암호화 및 보안 관련 기능을 제공하는 라이브러리입니다.
- **역할**: 데이터 암호화, 해시 함수, 암호화 키 관리
- **사용방법**:
  ```python
  from Crypto.Cipher import AES
  from Crypto.Random import get_random_bytes
  
  key = get_random_bytes(16)
  cipher = AES.new(key, AES.MODE_EAX)
  ciphertext, tag = cipher.encrypt_and_digest(data)
  ```

## API 문서화 및 개발 도구

### DRF Spectacular (0.28.0)
Django REST Framework용 OpenAPI 3.0 스키마 생성 도구입니다.
- **역할**: API 문서 자동 생성, Swagger UI/Redoc 제공
- **사용방법**:
  ```python
  # settings.py
  INSTALLED_APPS = [
      # ...
      'drf_spectacular',
  ]
  
  REST_FRAMEWORK = {
      'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
  }
  
  # urls.py
  from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
  
  urlpatterns = [
      path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
      path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema')),
  ]
  ```

### Django Debug Toolbar (5.0.1)
개발 환경에서 디버깅을 위한 다양한 정보를 제공합니다.
- **역할**: SQL 쿼리, 요청/응답 정보, 캐시 상태 등 시각화
- **사용방법**:
  ```python
  # settings.py (개발 환경)
  INSTALLED_APPS = [
      # ...
      'debug_toolbar',
  ]
  
  MIDDLEWARE = [
      # ...
      'debug_toolbar.middleware.DebugToolbarMiddleware',
  ]
  
  INTERNAL_IPS = ['127.0.0.1']
  ```

### Django Extensions (3.2.3)
Django 개발 시 유용한 추가 기능을 제공합니다.
- **역할**: shell_plus, RunServerPlus, graph_models 등 유틸리티 명령어 제공
- **사용방법**:
  ```bash
  # 향상된 쉘 실행
  python manage.py shell_plus
  
  # 모델 다이어그램 생성
  python manage.py graph_models -a -o my_project_models.png
  ```

## 웹 서버 및 인프라

### Gunicorn (23.0.0)
Python WSGI HTTP 서버로, 프로덕션 환경에서 Django 앱을 실행합니다.
- **역할**: 다중 작업자 프로세스로 Django 앱 제공
- **사용방법**:
  ```bash
  # 기본 실행
  gunicorn myproject.wsgi:application
  
  # 옵션 지정 실행
  gunicorn --workers=4 --bind=0.0.0.0:8000 myproject.wsgi:application
  ```

### Whitenoise (6.9.0)
Django 앱에서 정적 파일을 효율적으로 제공합니다.
- **역할**: 웹 서버 없이 정적 파일 제공, 파일 캐싱 최적화
- **사용방법**:
  ```python
  # settings.py
  MIDDLEWARE = [
      # ...
      'whitenoise.middleware.WhiteNoiseMiddleware',
  ]
  
  STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
  ```

## AWS 통합

### Boto3 (1.37.13)
AWS SDK for Python으로 AWS 서비스와 상호작용합니다.
- **역할**: S3, SQS, DynamoDB 등 AWS 서비스 활용
- **사용방법**:
  ```python
  import boto3
  
  # S3 사용 예시
  s3 = boto3.resource('s3')
  for bucket in s3.buckets.all():
      print(bucket.name)
      
  # 파일 업로드
  s3.Bucket('my-bucket').upload_file('local/path/file.txt', 'remote/path/file.txt')
  ```

## 유틸리티 및 도구

### Django CORS Headers (4.7.0)
교차 출처 리소스 공유(CORS) 지원을 추가합니다.
- **역할**: 다른 도메인에서의 API 요청 허용
- **사용방법**:
  ```python
  # settings.py
  INSTALLED_APPS = [
      # ...
      'corsheaders',
  ]
  
  MIDDLEWARE = [
      'corsheaders.middleware.CorsMiddleware',
      # 다른 미들웨어...
  ]
  
  # 모든 도메인 허용 (개발 환경)
  CORS_ALLOW_ALL_ORIGINS = True
  
  # 특정 도메인만 허용 (프로덕션 환경)
  CORS_ALLOWED_ORIGINS = [
      "https://example.com",
      "https://api.example.com",
  ]
  ```

### Django Filter (25.1)
Django 쿼리셋 필터링을 위한 라이브러리입니다.
- **역할**: URL 매개변수 기반 필터링 제공
- **사용방법**:
  ```python
  # views.py
  from django_filters.rest_framework import DjangoFilterBackend
  
  class UserViewSet(viewsets.ModelViewSet):
      queryset = User.objects.all()
      serializer_class = UserSerializer
      filter_backends = [DjangoFilterBackend]
      filterset_fields = ['username', 'email']
  ```

### Django Hosts (6.0)
하위 도메인 라우팅을 지원합니다.
- **역할**: 호스트 이름에 따른 URL 라우팅 제공
- **사용방법**:
  ```python
  # settings.py
  INSTALLED_APPS = [
      # ...
      'django_hosts',
  ]
  
  MIDDLEWARE = [
      'django_hosts.middleware.HostsRequestMiddleware',
      # ...
      'django_hosts.middleware.HostsResponseMiddleware',
  ]
  
  ROOT_HOSTCONF = 'myproject.hosts'
  DEFAULT_HOST = 'www'
  
  # hosts.py
  from django_hosts import patterns, host
  
  host_patterns = patterns('',
      host(r'www', 'myproject.urls', name='www'),
      host(r'api', 'myproject.api_urls', name='api'),
  )
  ```

### Python-dotenv (1.0.1)
환경 변수 관리를 위한 라이브러리입니다.
- **역할**: .env 파일에서 환경 변수 로드
- **사용방법**:
  ```python
  # settings.py
  from dotenv import load_dotenv
  import os
  
  load_dotenv()  # .env 파일 로드
  
  SECRET_KEY = os.getenv('SECRET_KEY')
  DEBUG = os.getenv('DEBUG', 'False') == 'True'
  ```

### Pytz (2025.1)
시간대 지원을 위한 라이브러리입니다.
- **역할**: 전 세계 시간대 관리 및 변환
- **사용방법**:
  ```python
  import pytz
  from datetime import datetime
  
  seoul_tz = pytz.timezone('Asia/Seoul')
  seoul_time = datetime.now(seoul_tz)
  
  # Django에서는 settings.py의 TIME_ZONE 설정에 사용
  TIME_ZONE = 'Asia/Seoul'
  ```

### Requests (2.32.3)
HTTP 요청을 간편하게 만들어주는 라이브러리입니다.
- **역할**: 외부 API 호출, 웹 페이지 스크래핑
- **사용방법**:
  ```python
  import requests
  
  # GET 요청
  response = requests.get('https://api.example.com/data')
  data = response.json()
  
  # POST 요청
  response = requests.post('https://api.example.com/users',
                          json={'name': 'John', 'email': 'john@example.com'})
  ```

### Sentry SDK (2.22.0)
오류 모니터링 및 로깅을 위한 라이브러리입니다.
- **역할**: 프로덕션 환경에서 오류 추적 및 알림
- **사용방법**:
  ```python
  # settings.py
  import sentry_sdk
  from sentry_sdk.integrations.django import DjangoIntegration
  
  sentry_sdk.init(
      dsn="https://examplePublicKey@o0.ingest.sentry.io/0",
      integrations=[DjangoIntegration()],
      traces_sample_rate=1.0,
      send_default_pii=True
  )
  ```

### UUID7 (0.1.0)
시간 순서가 보장된 UUID 버전 7을 제공합니다.
- **역할**: 순차적이고 시간 기반의 고유 식별자 생성
- **사용방법**:
  ```python
  from uuid_extensions import uuid7
  
  # UUID7 생성
  uuid = uuid7()
  
  # 모델에 사용
  class MyModel(models.Model):
      id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
  ```

## 결론

위 라이브러리들은 Django 기반 웹 애플리케이션 및 API 개발에 필수적인 도구들입니다. 각 라이브러리는 특정 문제를 해결하거나 개발 과정을 간소화하기 위해 설계되었습니다. 프로젝트의 요구사항과 규모에 따라 적절히, 활용하여 효율적인 개발 환경을 구축하시기 바랍니다.