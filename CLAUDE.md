# CLAUDE.md - Django Boilerplate Project Guide

This document provides comprehensive guidance for AI assistants working with this Django boilerplate codebase.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Project Structure](#project-structure)
3. [Technology Stack](#technology-stack)
4. [Architecture Patterns](#architecture-patterns)
5. [Coding Style Guide](#coding-style-guide)
6. [Naming Conventions](#naming-conventions)
7. [Testing Guide](#testing-guide)
8. [Comment Style Guide](#comment-style-guide)
9. [Important Implementation Details](#important-implementation-details)
10. [Common Commands](#common-commands)

---

## Project Overview

This is a production-ready Django REST Framework boilerplate designed for scalable web applications. It features:

- **Multi-environment support**: Local, Develop, Stage, Production
- **Multi-host architecture**: Separate hosts for API, Admin, and URL shortener
- **Modern authentication**: JWT with lazy loading, OTP (2FA), OAuth2 (Google)
- **Async task processing**: Celery with Redis
- **Database read replica support**: Primary/Replica routing pattern
- **Comprehensive API documentation**: OpenAPI/Swagger via drf-spectacular

---

## Project Structure

```
/home/user/django-boilerplate/
├── src/                              # Main application source code
│   ├── manage.py                     # Django management script
│   ├── conf/                         # Project configuration
│   │   ├── settings/                 # Environment-specific settings
│   │   │   ├── base.py              # Base configuration (shared)
│   │   │   ├── local.py             # Local development (SQLite)
│   │   │   ├── develop.py           # Development (PostgreSQL + Replica)
│   │   │   ├── stage.py             # Staging environment
│   │   │   └── prod.py              # Production environment
│   │   ├── urls/                     # URL configurations
│   │   │   ├── api.py               # Main API URLs (v1 versioning)
│   │   │   ├── admin.py             # Admin interface URLs
│   │   │   └── url.py               # URL shortening service URLs
│   │   ├── authentications.py       # JWT authentication with lazy loading
│   │   ├── celery.py                # Celery task queue configuration
│   │   ├── exceptions.py            # Custom DRF exception handler
│   │   ├── filters.py               # Logging filters (sensitive data masking)
│   │   ├── routers.py               # Database router for read replicas
│   │   ├── hosts.py                 # Multi-host configuration
│   │   ├── firebase_config.py       # Firebase configuration
│   │   ├── utils.py                 # Utility functions
│   │   ├── wsgi.py                  # WSGI application entry point
│   │   └── caches.py                # Cache configuration
│   ├── apps/                         # Django applications
│   │   ├── user/                     # User management (custom auth model)
│   │   ├── account/                  # Authentication (Login, Register, Password)
│   │   ├── feed/                     # Social feed system
│   │   ├── file/                     # File management with S3
│   │   ├── device/                   # Device and push notifications
│   │   ├── agreement/                # Terms and conditions management
│   │   ├── cms/                      # Content management (Notice, Event, FAQ)
│   │   ├── game/                     # Game/gamification features
│   │   ├── short_url/                # URL shortening service
│   │   └── common/                   # Common utilities and commands
│   ├── base/                         # Base utilities and enums
│   │   ├── enums/
│   │   │   ├── base.py              # DjangoEnvironment enum
│   │   │   └── errors.py            # Error code definitions
│   │   ├── fields/
│   │   │   └── encrypt.py           # EncryptedCharField for PII
│   │   └── utils/
│   │       └── aes_chipher.py       # AES encryption utilities
│   ├── templates/                    # Email and admin templates
│   ├── static/                       # Static files
│   └── tests/
│       └── locust/                   # Load testing
├── docs/                             # Documentation
├── Dockerfile                        # Docker image for web service
├── Dockerfile.celery                 # Docker image for Celery worker
├── docker-compose.yml                # Multi-container orchestration
├── pyproject.toml                    # Project metadata and dependencies
└── .pylintrc                         # Pylint configuration
```

### App Structure Pattern

Each app follows a consistent versioned structure:

```
apps/{app_name}/
├── models.py                         # Database models
├── admin.py                          # Admin configuration
├── v1/                               # API version 1
│   ├── views.py                      # ViewSets
│   ├── serializers.py                # DRF serializers
│   ├── urls.py                       # URL routing
│   ├── filters.py                    # FilterSets (if needed)
│   ├── paginations.py                # Custom pagination (if needed)
│   ├── services.py                   # Business logic (if needed)
│   ├── adapters.py                   # External service adapters (if needed)
│   ├── tasks.py                      # Celery tasks (if needed)
│   └── tests.py                      # Unit and integration tests
└── migrations/                       # Database migrations
```

---

## Technology Stack

### Core Framework
| Package | Version | Purpose |
|---------|---------|---------|
| Django | 5.2.5 | Web framework |
| Python | 3.11+ | Runtime |
| Django REST Framework | 3.16.1 | REST API |
| djangorestframework-simplejwt | 5.5.1 | JWT authentication |
| drf-spectacular | 0.28.0 | OpenAPI documentation |

### Database & Caching
| Package | Version | Purpose |
|---------|---------|---------|
| PostgreSQL | - | Primary database (develop/prod) |
| SQLite | - | Local development database |
| psycopg2-binary | 2.9.10 | PostgreSQL adapter |
| django-redis | 6.0.0 | Redis cache backend |
| Redis | - | Cache and Celery broker |

### Authentication & Security
| Package | Version | Purpose |
|---------|---------|---------|
| django-otp | 1.6.1 | Two-factor authentication |
| pycryptodome | 3.23.0 | AES encryption for PII |
| firebase-admin | 7.1.0 | Push notifications |

### Task Queue
| Package | Version | Purpose |
|---------|---------|---------|
| Celery | 5.5.3 | Background task processing |

### Admin & UI
| Package | Version | Purpose |
|---------|---------|---------|
| django-unfold | 0.63.0 | Modern admin interface |

### Code Quality
| Package | Version | Purpose |
|---------|---------|---------|
| Black | 25.1.0 | Code formatting |
| Pylint | - | Linting |

### Deployment
| Package | Version | Purpose |
|---------|---------|---------|
| Gunicorn | 23.0.0 | WSGI server |
| WhiteNoise | 6.9.0 | Static file serving |
| Docker | - | Containerization |

---

## Architecture Patterns

### 1. API Versioning

All APIs are versioned under `/v1/` prefix:

```python
# URL pattern: /v1/{resource}/
# Example: /v1/account/login/

# In urls.py
urlpatterns = [
    path("v1/account/", include("apps.account.v1.urls")),
    path("v1/user/", include("apps.user.v1.urls")),
    path("v1/feed/", include("apps.feed.v1.urls")),
]
```

### 2. JWT Authentication with Lazy Loading

```python
# conf/authentications.py
class JWTLazyUserAuthentication(JWTAuthentication):
    """
    Custom authentication that loads user lazily.
    User database query only happens when request.user is accessed.
    """
    def authenticate(self, request):
        # Token validation without DB lookup
        # Returns SimpleLazyObject wrapping user
```

### 3. Database Read Replica Pattern

```python
# conf/routers.py
class DefaultRouter:
    def db_for_read(self, model, **hints):
        return "replica"  # Route reads to replica

    def db_for_write(self, model, **hints):
        return "default"  # Route writes to primary
```

### 4. Multi-Host Architecture

```python
# conf/hosts.py
host_patterns = [
    host(r"api", "conf.urls.api", name="api"),
    host(r"admin", "conf.urls.admin", name="admin"),
    host(r"url", "conf.urls.url", name="url"),
]
```

### 5. ViewSet Pattern with Dynamic Configuration

```python
class MyViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Model.objects.all()
    serializer_class = DefaultSerializer

    def get_serializer_class(self):
        """Dynamic serializer based on action"""
        if self.action == "list":
            return ListSerializer
        return self.serializer_class

    def get_permissions(self):
        """Dynamic permissions based on action"""
        if self.action in ["create", "update", "destroy"]:
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_throttles(self):
        """Dynamic throttling based on action"""
        if self.action == "create":
            self.throttle_scope = "resource:create"
            return [ScopedRateThrottle()]
        return []
```

### 6. Centralized Error Handling

```python
# base/enums/errors.py
E001_INVALID_EMAIL_FORMAT = {
    "message": "Invalid email format",
    "error_code": "E0010001",
}

# conf/exceptions.py
def default_exception_handler(exc, context):
    """Normalizes all errors to consistent format"""
    # Converts DRF ValidationError to standardized response
```

---

## Coding Style Guide

### Formatting Rules

- **Line Length**: 88 characters (Black default)
- **Indentation**: 4 spaces
- **Formatter**: Black
- **Linter**: Pylint with Django plugin

### Import Order

```python
# 1. Standard library imports
import json
import logging
from datetime import datetime

# 2. Third-party imports
from django.db import models
from rest_framework import serializers
from rest_framework.viewsets import GenericViewSet

# 3. Local application imports
from apps.user.models import User
from base.enums.errors import E001_INVALID_EMAIL_FORMAT
```

### Class Structure Order

```python
class MyViewSet(GenericViewSet):
    # 1. Class attributes
    queryset = Model.objects.all()
    serializer_class = MySerializer
    permission_classes = [IsAuthenticated]

    # 2. Django/DRF override methods
    def get_queryset(self):
        pass

    def get_serializer_class(self):
        pass

    def get_permissions(self):
        pass

    # 3. Action methods (list, create, retrieve, update, destroy)
    def list(self, request, *args, **kwargs):
        pass

    # 4. Custom action methods
    @action(detail=True, methods=["post"])
    def custom_action(self, request, pk=None):
        pass

    # 5. Private helper methods
    def _helper_method(self):
        pass
```

### Model Structure Order

```python
class MyModel(models.Model):
    # 1. Primary key field (if custom)
    uuid = models.UUIDField(primary_key=True, default=uuid7, editable=False)

    # 2. Foreign key fields
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # 3. Regular fields
    title = models.CharField(max_length=100)
    content = models.TextField()
    status = models.PositiveSmallIntegerField(choices=StatusEnum)

    # 4. Boolean flags
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    # 5. Timestamp fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 6. Meta class
    class Meta:
        db_table = "my_model"
        verbose_name = "My Model"
        verbose_name_plural = "My Models"
        indexes = [
            models.Index(fields=["created_at"]),
        ]
        ordering = ["-created_at"]

    # 7. __str__ method
    def __str__(self):
        return self.title

    # 8. Property methods
    @property
    def display_name(self):
        return f"{self.title} ({self.status})"

    # 9. Instance methods
    def activate(self):
        self.is_active = True
        self.save(update_fields=["is_active", "updated_at"])

    # 10. Class methods
    @classmethod
    def get_active_items(cls):
        return cls.objects.filter(is_active=True)
```

---

## Naming Conventions

### Python Naming

| Type | Convention | Example |
|------|------------|---------|
| Variables | snake_case | `user_profile`, `is_active` |
| Functions | snake_case | `get_user_by_email()`, `validate_token()` |
| Classes | PascalCase | `UserProfile`, `FeedSerializer` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`, `DEFAULT_PAGE_SIZE` |
| Private | _prefix | `_helper_method()`, `_internal_cache` |
| Protected | _prefix | `_validate_input()` |

### Django-Specific Naming

| Type | Convention | Example |
|------|------------|---------|
| Models | Singular PascalCase | `User`, `Feed`, `Agreement` |
| ViewSets | Resource + ViewSet | `UserViewSet`, `FeedViewSet` |
| Serializers | Model + Serializer | `UserSerializer`, `FeedListSerializer` |
| URLs | kebab-case in URL, snake_case in name | `path("push-token/", ..., name="push_token")` |
| Filters | Model + FilterSet | `FeedFilterSet` |
| Permissions | Is + Action + Resource | `IsOwnerOrReadOnly` |
| Tasks | task_ + action | `task_delete_expired_files` |

### Database Naming

| Type | Convention | Example |
|------|------------|---------|
| Tables | snake_case (explicit) | `db_table = "user_profile"` |
| Columns | snake_case | `created_at`, `is_verified` |
| Foreign Keys | related_model_id | `user_id`, `feed_id` |
| Many-to-Many | model1_model2 | `feed_tag` |
| Indexes | idx_table_column | `idx_feed_created_at` |

### API Naming

| Type | Convention | Example |
|------|------------|---------|
| Endpoints | Plural nouns | `/feeds/`, `/users/`, `/agreements/` |
| Actions | Verb phrases | `/feeds/{id}/like/`, `/account/login/` |
| Query params | snake_case | `?page_size=10&created_after=2024-01-01` |

### Error Codes

```python
# Format: E{category}{sequence}
# Category:
#   001 = Validation errors
#   002 = Authentication errors
#   003 = Permission errors
#   004 = Resource errors

E001_INVALID_EMAIL_FORMAT = {
    "message": "Invalid email format",
    "error_code": "E0010001",  # E + 001 (category) + 0001 (sequence)
}
```

---

## Testing Guide

### Test File Location

Tests are located in each app's version directory:
```
apps/{app_name}/v1/tests.py
```

### Test Class Naming

```python
# Pattern: {Target}Test or {Target}TestCase
class RegisterSerializerTest(TestCase):
    """Tests for RegisterSerializer"""
    pass

class FeedViewSetTest(APITestCase):
    """Tests for FeedViewSet"""
    pass
```

### Test Method Naming

Use descriptive Korean names for clarity (project convention):

```python
class RegisterSerializerTest(TestCase):
    def test_실패__이메일_없음(self):
        """Test failure when email is missing"""
        pass

    def test_실패__비밀번호_형식_불일치(self):
        """Test failure when password format is invalid"""
        pass

    def test_성공__회원가입_완료(self):
        """Test successful registration"""
        pass
```

Alternative English naming pattern:
```python
def test_should_fail_when_email_is_missing(self):
    pass

def test_should_succeed_with_valid_data(self):
    pass
```

### Test Structure (AAA Pattern)

```python
def test_실패__이메일_형식_불일치(self):
    # Arrange - Setup test data
    data = {
        "email": "invalid-email",
        "password": "ValidPass123!",
    }

    # Act - Execute the action
    serializer = RegisterSerializer(data=data)
    is_valid = serializer.is_valid()

    # Assert - Verify results
    self.assertFalse(is_valid)
    self.assertIn("email", serializer.errors)
```

### API Test Pattern

```python
class FeedViewSetTest(APITestCase):
    def setUp(self):
        """Setup test fixtures"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="TestPass123!",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_리스트_조회_성공(self):
        """Test successful feed list retrieval"""
        # Arrange
        Feed.objects.create(user=self.user, content="Test feed")

        # Act
        response = self.client.get("/v1/feed/")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_생성_실패__미인증(self):
        """Test feed creation fails without authentication"""
        # Arrange
        self.client.force_authenticate(user=None)

        # Act
        response = self.client.post("/v1/feed/", {"content": "Test"})

        # Assert
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
```

### Mocking External Services

```python
from unittest.mock import patch, MagicMock

class GoogleLoginTest(APITestCase):
    @patch("apps.account.v1.adapters.GoogleLoginAdapter.get_user_info")
    def test_구글_로그인_성공(self, mock_get_user_info):
        # Arrange
        mock_get_user_info.return_value = {
            "email": "google@example.com",
            "name": "Google User",
        }

        # Act
        response = self.client.post("/v1/account/google/", {
            "access_token": "fake_token"
        })

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_get_user_info.assert_called_once()
```

### Running Tests

```bash
# Run all tests
python src/manage.py test

# Run specific app tests
python src/manage.py test apps.account.v1.tests

# Run specific test class
python src/manage.py test apps.account.v1.tests.RegisterSerializerTest

# Run specific test method
python src/manage.py test apps.account.v1.tests.RegisterSerializerTest.test_실패__이메일_없음

# Run with coverage
coverage run --source='src' src/manage.py test
coverage report
```

---

## Comment Style Guide

### When to Comment

1. **Complex Business Logic**: Explain the "why" behind non-obvious decisions
2. **External Dependencies**: Document API contracts and assumptions
3. **Workarounds**: Explain temporary fixes with TODO/FIXME
4. **Algorithm Explanations**: Describe complex algorithms

### When NOT to Comment

1. **Self-explanatory Code**: Good naming eliminates need for comments
2. **Obvious Operations**: Don't comment what the code clearly does
3. **Version History**: Use git commit messages instead

### Comment Formats

#### Inline Comments
```python
# Calculate expiry time (5 minutes from now)
expire_at = timezone.now() + timedelta(minutes=5)

# Skip soft-deleted records
queryset = queryset.filter(is_deleted=False)
```

#### Block Comments for Complex Logic
```python
# [Why]
# Q. Why use GenericForeignKey here?
# A. File model needs to be associated with multiple different models
#    (Feed, User, Comment, etc.) without creating separate foreign keys
#    for each relationship.
content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
object_id = models.UUIDField()
content_object = GenericForeignKey("content_type", "object_id")
```

#### Docstrings

```python
class FeedViewSet(viewsets.GenericViewSet):
    """
    ViewSet for managing social feeds.

    Supports CRUD operations with the following permissions:
    - List/Retrieve: Public access
    - Create/Update/Delete: Authenticated users only (owner)

    Throttling:
    - Create: 1 request/second
    - Like: 2 requests/second
    """

    def create(self, request, *args, **kwargs):
        """
        Create a new feed post.

        Args:
            request: DRF Request object containing:
                - content (str): Feed content text
                - tags (list[str]): Optional list of tag names

        Returns:
            Response with created feed data (201) or validation errors (400)

        Raises:
            ValidationError: If content is empty or exceeds max length
        """
        pass
```

#### TODO/FIXME Comments
```python
# TODO: Implement pagination for large result sets
# TODO(username): Add caching layer for frequently accessed feeds

# FIXME: Race condition when multiple users like simultaneously
# FIXME(#123): Temporary workaround for upstream bug
```

### Korean Comments (Project Convention)

This project uses Korean comments for context-specific documentation:

```python
class Agreement(models.Model):
    """약관 모델"""

    # 이전 버전 참조 (버전 관리용)
    previous_version = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def save(self, *args, **kwargs):
        # 기존 약관이 수정되면 새 버전 생성
        if self.pk:
            # 재동의 알림 발송 태스크 실행
            task_send_re_agreement_notification.apply_async()
        super().save(*args, **kwargs)
```

---

## Important Implementation Details

### 1. UUID7 Primary Keys

All models use UUID7 for distributed-friendly primary keys:

```python
from uuid_extensions import uuid7

class MyModel(models.Model):
    uuid = models.UUIDField(
        primary_key=True,
        default=uuid7,
        editable=False,
    )
```

### 2. Soft Deletes

Use `is_deleted` flag instead of hard deletes:

```python
class Feed(models.Model):
    is_deleted = models.BooleanField(default=False)

    class Meta:
        # Always filter out deleted records
        pass

# In queryset
Feed.objects.filter(is_deleted=False)
```

### 3. Encrypted Fields for PII

```python
from base.fields.encrypt import EncryptedCharField

class UserVerification(models.Model):
    # PII fields are encrypted at rest
    name = EncryptedCharField(max_length=100)
    phone = EncryptedCharField(max_length=20)
```

### 4. Celery Task Pattern

```python
# apps/{app}/v1/tasks.py
from conf.celery import app

@app.task
def task_delete_expired_files():
    """
    Delete files that have exceeded their expiry time.
    Scheduled to run periodically via Celery Beat.
    """
    from apps.file.models import File
    from django.utils import timezone

    expired_files = File.objects.filter(
        expire_at__lt=timezone.now(),
        status=FileStatus.SUCCESS_UPLOAD,
    )

    for file in expired_files:
        file.status = FileStatus.DELETE
        file.save(update_fields=["status", "updated_at"])
```

### 5. Email Verification Flow

```python
# Generate verification token
token = get_random_string(length=32)
hashed_email = hashlib.sha256(email.encode()).hexdigest()

# Store in cache
cache.set(f"email_verify:{hashed_email}", token, timeout=600)  # 10 min

# Verification URL
url = f"{base_url}/v1/account/register/confirm/?email={hashed_email}&token={token}"
```

### 6. Pagination Patterns

```python
# Default: LimitOffsetPagination
# For feeds: CursorPagination (more efficient for large datasets)

class FeedCursorPagination(CursorPagination):
    page_size = 20
    ordering = "-created_at"
    cursor_query_param = "cursor"
```

### 7. Throttling Configuration

```python
# conf/settings/base.py
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_RATES": {
        "feed:create": "1/sec",
        "feed:like": "2/sec",
        "feed:report": "5/min",
    }
}

# In ViewSet
def get_throttles(self):
    if self.action == "create":
        self.throttle_scope = "feed:create"
        return [ScopedRateThrottle()]
    return []
```

### 8. Environment Detection

```python
from base.enums.base import DjangoEnvironment

# Check current environment
if DjangoEnvironment.is_local():
    # Local development specific code
    pass

if DjangoEnvironment.is_production():
    # Production specific code
    pass
```

---

## Common Commands

### Development

```bash
# Start development server
python src/manage.py runserver

# Create migrations
python src/manage.py makemigrations

# Apply migrations
python src/manage.py migrate

# Create superuser
python src/manage.py createsuperuser

# Collect static files
python src/manage.py collectstatic

# Create new app from template
python src/manage.py startapp {app_name} --template=apps/common/management/commands/app_template
```

### Docker

```bash
# Build and start all services
docker-compose up --build

# Start specific service
docker-compose up web

# Run migrations in container
docker-compose exec web python manage.py migrate

# View logs
docker-compose logs -f web
```

### Testing

```bash
# Run all tests
python src/manage.py test

# Run with verbosity
python src/manage.py test -v 2

# Run specific app tests
python src/manage.py test apps.account.v1.tests
```

### Code Quality

```bash
# Format code with Black
black src/

# Lint with Pylint
pylint src/apps/

# Check formatting without changes
black --check src/
```

### Celery

```bash
# Start Celery worker
celery -A conf.celery worker -l info

# Start Celery Beat (scheduler)
celery -A conf.celery beat -l info
```

---

## Quick Reference

### Adding a New API Endpoint

1. Create/update model in `apps/{app}/models.py`
2. Create migrations: `python manage.py makemigrations`
3. Create serializer in `apps/{app}/v1/serializers.py`
4. Create ViewSet in `apps/{app}/v1/views.py`
5. Register URL in `apps/{app}/v1/urls.py`
6. Add tests in `apps/{app}/v1/tests.py`
7. Update API documentation with `@extend_schema` decorators

### Adding a New Celery Task

1. Create task in `apps/{app}/v1/tasks.py`
2. Import task in app's `__init__.py` if needed
3. Call with `task_name.delay()` or `task_name.apply_async()`

### Adding a New Model Field

1. Add field to model class
2. Run `python manage.py makemigrations`
3. Review migration file
4. Run `python manage.py migrate`
5. Update serializers if needed
6. Update tests

---

## File-Specific Notes

| File | Purpose | Key Points |
|------|---------|------------|
| `conf/authentications.py` | JWT auth | Lazy user loading for performance |
| `conf/routers.py` | DB routing | Read replica support |
| `conf/exceptions.py` | Error handling | Centralized error formatting |
| `base/enums/errors.py` | Error codes | All error messages defined here |
| `base/fields/encrypt.py` | PII encryption | AES encryption for sensitive data |

---

*Last updated: 2024*
