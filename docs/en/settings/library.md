# Library Introduction

This guide introduces the main libraries installed in this project and how to use them. Each library provides specific functionality to facilitate the development of Django-based web applications.

## Core Framework

### Django (5.1.7)
A Python web framework based on the MVT (Model-View-Template) pattern.
- **Role**: Provides the basic structure and ORM for web applications
- **Usage**:
  ```python
  # Create a project
  django-admin startproject myproject
  
  # Create an app
  python manage.py startapp myapp
  
  # Run development server
  python manage.py runserver
  ```

### Django REST Framework (3.15.2)
A powerful tool for developing RESTful APIs based on Django.
- **Role**: Implements API endpoints, serializers, and authentication mechanisms
- **Usage**:
  ```python
  # views.py
  from rest_framework.views import APIView
  from rest_framework.response import Response
  
  class UserView(APIView):
      def get(self, request):
          return Response({"message": "Success"})
  ```

## Authentication and Security

### Django REST Framework Simple JWT (5.5.0)
Provides JWT (JSON Web Token) based authentication.
- **Role**: Provides token issuance, renewal, and validation functionality
- **Usage**:
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
A library that provides encryption and security-related functions.
- **Role**: Data encryption, hash functions, encryption key management
- **Usage**:
  ```python
  from Crypto.Cipher import AES
  from Crypto.Random import get_random_bytes
  
  key = get_random_bytes(16)
  cipher = AES.new(key, AES.MODE_EAX)
  ciphertext, tag = cipher.encrypt_and_digest(data)
  ```

## API Documentation and Development Tools

### DRF Spectacular (0.28.0)
An OpenAPI 3.0 schema generation tool for Django REST Framework.
- **Role**: Automatically generates API documentation, provides Swagger UI/Redoc
- **Usage**:
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
Provides various information for debugging in the development environment.
- **Role**: Visualizes SQL queries, request/response information, cache status, etc.
- **Usage**:
  ```python
  # settings.py (development environment)
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
Provides useful additional features for Django development.
- **Role**: Provides utility commands such as shell_plus, RunServerPlus, graph_models
- **Usage**:
  ```bash
  # Run enhanced shell
  python manage.py shell_plus
  
  # Generate model diagrams
  python manage.py graph_models -a -o my_project_models.png
  ```

## Web Server and Infrastructure

### Gunicorn (23.0.0)
A Python WSGI HTTP server that runs Django apps in production environments.
- **Role**: Serves Django apps with multiple worker processes
- **Usage**:
  ```bash
  # Basic execution
  gunicorn myproject.wsgi:application
  
  # Execution with options
  gunicorn --workers=4 --bind=0.0.0.0:8000 myproject.wsgi:application
  ```

### Whitenoise (6.9.0)
Efficiently serves static files in Django apps.
- **Role**: Serves static files without a web server, optimizes file caching
- **Usage**:
  ```python
  # settings.py
  MIDDLEWARE = [
      # ...
      'whitenoise.middleware.WhiteNoiseMiddleware',
  ]
  
  STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
  ```

## AWS Integration

### Boto3 (1.37.13)
AWS SDK for Python that interacts with AWS services.
- **Role**: Utilizes AWS services such as S3, SQS, DynamoDB
- **Usage**:
  ```python
  import boto3
  
  # S3 usage example
  s3 = boto3.resource('s3')
  for bucket in s3.buckets.all():
      print(bucket.name)
      
  # File upload
  s3.Bucket('my-bucket').upload_file('local/path/file.txt', 'remote/path/file.txt')
  ```

## Utilities and Tools

### Django CORS Headers (4.7.0)
Adds Cross-Origin Resource Sharing (CORS) support.
- **Role**: Allows API requests from different domains
- **Usage**:
  ```python
  # settings.py
  INSTALLED_APPS = [
      # ...
      'corsheaders',
  ]
  
  MIDDLEWARE = [
      'corsheaders.middleware.CorsMiddleware',
      # Other middleware...
  ]
  
  # Allow all domains (development environment)
  CORS_ALLOW_ALL_ORIGINS = True
  
  # Allow only specific domains (production environment)
  CORS_ALLOWED_ORIGINS = [
      "https://example.com",
      "https://api.example.com",
  ]
  ```

### Django Filter (25.1)
A library for filtering Django querysets.
- **Role**: Provides URL parameter-based filtering
- **Usage**:
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
Supports subdomain routing.
- **Role**: Provides URL routing based on hostname
- **Usage**:
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
A library for managing environment variables.
- **Role**: Loads environment variables from .env files
- **Usage**:
  ```python
  # settings.py
  from dotenv import load_dotenv
  import os
  
  load_dotenv()  # Load .env file
  
  SECRET_KEY = os.getenv('SECRET_KEY')
  DEBUG = os.getenv('DEBUG', 'False') == 'True'
  ```

### Pytz (2025.1)
A library for timezone support.
- **Role**: Manages and converts timezones worldwide
- **Usage**:
  ```python
  import pytz
  from datetime import datetime
  
  seoul_tz = pytz.timezone('Asia/Seoul')
  seoul_time = datetime.now(seoul_tz)
  
  # In Django, used in the TIME_ZONE setting in settings.py
  TIME_ZONE = 'Asia/Seoul'
  ```

### Requests (2.32.3)
A library that simplifies HTTP requests.
- **Role**: External API calls, web page scraping
- **Usage**:
  ```python
  import requests
  
  # GET request
  response = requests.get('https://api.example.com/data')
  data = response.json()
  
  # POST request
  response = requests.post('https://api.example.com/users',
                          json={'name': 'John', 'email': 'john@example.com'})
  ```

### Sentry SDK (2.22.0)
A library for error monitoring and logging.
- **Role**: Tracks errors and sends notifications in production environments
- **Usage**:
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
Provides time-ordered UUID version 7.
- **Role**: Generates sequential and time-based unique identifiers
- **Usage**:
  ```python
  from uuid_extensions import uuid7
  
  # Generate UUID7
  uuid = uuid7()
  
  # Use in model
  class MyModel(models.Model):
      id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
  ```

## Conclusion

The above libraries are essential tools for developing Django-based web applications and APIs. Each library is designed to solve specific problems or simplify the development process. Please use them appropriately according to your project requirements and scale to build an efficient development environment.
