# CMS API Documentation

## Overview

This document is a guide to CMS (Content Management System) related API functions. The system provides functions to manage and query notices, events, and FAQs. Users can view active content after authentication.

## API Endpoints

| Path                       | Method | Description                 |
|---------------------------|--------|---------------------|
| `/v1/cms/notice/`         | GET    | Query notice list   |
| `/v1/cms/notice/{uuid}/`  | GET    | Query notice details     |
| `/v1/cms/event/`          | GET    | Query event list     |
| `/v1/cms/event/{uuid}/`   | GET    | Query event details       |
| `/v1/cms/faq/`            | GET    | Query FAQ list       |

## CMS Flow Diagrams

### 1. Notice Query Flow

```mermaid
flowchart TD
    classDef userAction fill:#f9d6d6,stroke:#e88e8e,stroke-width:2px,color:#333
    classDef systemAction fill:#d6e5f9,stroke:#8eb5e8,stroke-width:2px,color:#333
    classDef success fill:#d6f9d6,stroke:#8ee88e,stroke-width:2px,color:#333
    classDef error fill:#f9f9d6,stroke:#e8e88e,stroke-width:2px,color:#333
    classDef decision fill:#d6f9f9,stroke:#8ee8e8,stroke-width:2px,color:#333
    
    Start([Notice Query Start]) --> AuthCheck{Authentication Check}:::systemAction
    
    AuthCheck -->|Authentication Failed| Unauthorized[Authentication Error Response]:::error
    Unauthorized --> End1([Query Failed])
    
    AuthCheck -->|Authentication Successful| ListOrDetail{List/Detail<br>Request Type}:::decision
    
    ListOrDetail -->|List Query| GetActiveNotices[Filter Currently<br>Active Notices]:::systemAction
    ListOrDetail -->|Detail Query| GetNoticeDetail[Query Notice<br>by UUID]:::systemAction
    
    GetActiveNotices --> ApplyFilters[Apply Filters<br>(Title, Publication Date)]:::systemAction
    GetActiveNotices --> ListNotice[Notice List Response]:::success
    ListNotice --> End2([List Query Complete])
    
    GetNoticeDetail --> NoticeExists{Notice<br>Exists}:::decision
    NoticeExists -->|Not Found| NotFound[404 Not Found Response]:::error
    NotFound --> End3([Query Failed])
    
    NoticeExists -->|Exists| DetailNotice[Notice Detail Response]:::success
    DetailNotice --> End4([Detail Query Complete])
    
    class AuthCheck,GetActiveNotices,ApplyFilters,GetNoticeDetail systemAction
    class ListOrDetail,NoticeExists decision
    class Unauthorized,NotFound error
    class ListNotice,DetailNotice success
```

### 2. Event Query Flow

```mermaid
flowchart TD
    classDef userAction fill:#f9d6d6,stroke:#e88e8e,stroke-width:2px,color:#333
    classDef systemAction fill:#d6e5f9,stroke:#8eb5e8,stroke-width:2px,color:#333
    classDef success fill:#d6f9d6,stroke:#8ee88e,stroke-width:2px,color:#333
    classDef error fill:#f9f9d6,stroke:#e8e88e,stroke-width:2px,color:#333
    classDef decision fill:#d6f9f9,stroke:#8ee8e8,stroke-width:2px,color:#333
    
    Start([Event Query Start]) --> AuthCheck{Authentication Check}:::systemAction
    
    AuthCheck -->|Authentication Failed| Unauthorized[Authentication Error Response]:::error
    Unauthorized --> End1([Query Failed])
    
    AuthCheck -->|Authentication Successful| ListOrDetail{List/Detail<br>Request Type}:::decision
    
    ListOrDetail -->|List Query| GetActiveEvents[Filter Currently<br>Active Events]:::systemAction
    ListOrDetail -->|Detail Query| GetEventDetail[Query Event<br>by UUID]:::systemAction
    
    GetActiveEvents --> ApplyFilters[Apply Filters<br>(Title, Publication Date)]:::systemAction
    GetActiveEvents --> CheckEventStatus[Check Event End Status<br>(is_event_ended)]:::systemAction
    
    CheckEventStatus --> ListEvent[Event List Response]:::success
    ListEvent --> End2([List Query Complete])
    
    GetEventDetail --> EventExists{Event<br>Exists}:::decision
    EventExists -->|Not Found| NotFound[404 Not Found Response]:::error
    NotFound --> End3([Query Failed])
    
    EventExists -->|Exists| CheckEndStatus[Check Event End Status<br>(is_event_ended)]:::systemAction
    CheckEndStatus --> DetailEvent[Event Detail Response]:::success
    DetailEvent --> End4([Detail Query Complete])
    
    class AuthCheck,GetActiveEvents,ApplyFilters,CheckEventStatus,GetEventDetail,CheckEndStatus systemAction
    class ListOrDetail,EventExists decision
    class Unauthorized,NotFound error
    class ListEvent,DetailEvent success
```

### 3. FAQ Query Flow

```mermaid
flowchart TD
    classDef userAction fill:#f9d6d6,stroke:#e88e8e,stroke-width:2px,color:#333
    classDef systemAction fill:#d6e5f9,stroke:#8eb5e8,stroke-width:2px,color:#333
    classDef success fill:#d6f9d6,stroke:#8ee88e,stroke-width:2px,color:#333
    classDef error fill:#f9f9d6,stroke:#e8e88e,stroke-width:2px,color:#333
    classDef decision fill:#d6f9f9,stroke:#8ee8e8,stroke-width:2px,color:#333
    
    Start([FAQ Query Start]) --> AuthCheck{Authentication Check}:::systemAction
    
    AuthCheck -->|Authentication Failed| Unauthorized[Authentication Error Response]:::error
    Unauthorized --> End1([Query Failed])
    
    AuthCheck -->|Authentication Successful| GetPublishedFAQs[Filter Published<br>FAQs]:::systemAction
    
    GetPublishedFAQs --> CategoryFilter{Category<br>Filter Specified}:::decision
    
    CategoryFilter -->|Not Specified| AllFAQs[Query All FAQs]:::systemAction
    CategoryFilter -->|Specified| FilterByCategory[Filter FAQs<br>by Category]:::systemAction
    
    AllFAQs --> ApplyPagination[Apply Pagination]:::systemAction
    FilterByCategory --> ApplyPagination
    
    ApplyPagination --> ListFAQ[FAQ List Response<br>(Including Category Info)]:::success
    ListFAQ --> End2([Query Complete])
    
    class AuthCheck,GetPublishedFAQs,AllFAQs,FilterByCategory,ApplyPagination systemAction
    class CategoryFilter decision
    class Unauthorized error
    class ListFAQ success
```

## API Detailed Description

### 1. Notice List Query API

Query the list of notices.

**URL**: `/v1/cms/notice/`

**Method**: `GET`

**Authentication**: Required (JWT access token)

**Query Parameters**:
- `title__icontains`: Title search (case-insensitive)
- `title__exact`: Exact title match search
- `published_at__gte`: Notices published after a specific date (ISO 8601 format, e.g.: 2023-01-01T00:00:00Z)
- `published_at__lte`: Notices published before a specific date (ISO 8601 format, e.g.: 2023-01-31T23:59:59Z)
- `limit`: Items per page (default: 10)
- `offset`: Page offset

**Response (200 OK)**:
```json
{
  "count": 1,
  "next": "http://example.com/v1/cms/notice/?limit=10&offset=10",
  "previous": null,
  "results": [
    {
      "uuid": "123e4567-e89b-12d3-a456-426614174000",
      "title": "Notice Title",
      "content": "Notice Content",
      "published_at": "2023-01-01T00:00:00.000000Z",
      "start_at": "2023-01-01T00:00:00.000000Z",
      "end_at": "2023-01-08T00:00:00.000000Z",
      "created_at": "2023-01-01T00:00:00.000000Z",
      "updated_at": "2023-01-01T00:00:00.000000Z"
    }
  ]
}
```

**Filtering Conditions**:
- Only notices where the start time (start_at) has passed and the end time (end_at) has not passed based on the current time
- Notices with null end time (end_at) are considered unexpired
- Only notices with publication status (is_published) set to true are queried

**Response Codes**:
- `200 OK`: Success
- `401 Unauthorized`: Authentication failed

### 2. Notice Detail Query API

Query detailed information for a specific notice.

**URL**: `/v1/cms/notice/{uuid}/`

**Method**: `GET`

**Authentication**: Required (JWT access token)

**URL Parameters**:
- `uuid`: UUID of the notice to query

**Response (200 OK)**:
```json
{
  "uuid": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Notice Title",
  "content": "Notice Content",
  "published_at": "2023-01-01T00:00:00.000000Z",
  "start_at": "2023-01-01T00:00:00.000000Z",
  "end_at": "2023-01-08T00:00:00.000000Z",
  "created_at": "2023-01-01T00:00:00.000000Z",
  "updated_at": "2023-01-01T00:00:00.000000Z"
}
```

**Response Codes**:
- `200 OK`: Success
- `401 Unauthorized`: Authentication failed
- `404 Not Found`: Notice does not exist

### 3. Event List Query API

Query the list of events.

**URL**: `/v1/cms/event/`

**Method**: `GET`

**Authentication**: Required (JWT access token)

**Query Parameters**:
- `title__icontains`: Title search (case-insensitive)
- `title__exact`: Exact title match search
- `published_at__gte`: Events published after a specific date (ISO 8601 format)
- `published_at__lte`: Events published before a specific date (ISO 8601 format)
- `limit`: Items per page (default: 10)
- `offset`: Page offset

**Response (200 OK)**:
```json
{
  "count": 1,
  "next": "http://example.com/v1/cms/event/?limit=10&offset=10",
  "previous": null,
  "results": [
    {
      "uuid": "123e4567-e89b-12d3-a456-426614174001",
      "title": "Event Title",
      "content": "Event Content",
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

**Filtering Conditions**:
- Only events where the start time (start_at) has passed and the end time (end_at) has not passed based on the current time
- Events with null end time (end_at) are considered unexpired
- Only events with publication status (is_published) set to true are queried

**Response Codes**:
- `200 OK`: Success
- `401 Unauthorized`: Authentication failed

### 4. Event Detail Query API

Query detailed information for a specific event.

**URL**: `/v1/cms/event/{uuid}/`

**Method**: `GET`

**Authentication**: Required (JWT access token)

**URL Parameters**:
- `uuid`: UUID of the event to query

**Response (200 OK)**:
```json
{
  "uuid": "123e4567-e89b-12d3-a456-426614174001",
  "title": "Event Title",
  "content": "Event Content",
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

**Response Fields**:
- `is_event_ended`: Event end status based on current time (compared with event_end_at)

**Response Codes**:
- `200 OK`: Success
- `401 Unauthorized`: Authentication failed
- `404 Not Found`: Event does not exist

### 5. FAQ List Query API

Query the list of FAQs.

**URL**: `/v1/cms/faq/`

**Method**: `GET`

**Authentication**: Required (JWT access token)

**Query Parameters**:
- `category_name`: Category name filter (case-insensitive)
- `published_at__gte`: FAQs published after a specific date (ISO 8601 format)
- `published_at__lte`: FAQs published before a specific date (ISO 8601 format)
- `limit`: Items per page (default: 10)
- `offset`: Page offset

**Response (200 OK)**:
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
        "name": "General",
        "created_at": "2023-01-01T00:00:00.000000Z",
        "updated_at": "2023-01-01T00:00:00.000000Z"
      },
      "title": "FAQ Title",
      "content": "FAQ Content",
      "published_at": "2023-01-01T00:00:00.000000Z",
      "created_at": "2023-01-01T00:00:00.000000Z",
      "updated_at": "2023-01-01T00:00:00.000000Z"
    }
  ]
}
```

**Filtering Conditions**:
- Only FAQs with publication status (is_published) set to true are queried
- Can be filtered by category name (category_name)

**Notes**:
- The FAQ API only supports list querying and does not provide detail querying
- Category information is included in the response in a nested format

**Response Codes**:
- `200 OK`: Success
- `401 Unauthorized`: Authentication failed

## Error Response Format

CMS API error responses follow this format:

```json
{
  "detail": "Error message"
}
```

### Example Error Responses

**Unauthenticated User Access**:
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Non-existent Resource Request**:
```json
{
  "detail": "Not found."
}
```

## Pagination

CMS API uses offset-based pagination.

### Pagination Parameters

- `limit`: Items per page (default: 10)
- `offset`: Page offset

Pagination response example:
```json
{
  "count": 42,
  "next": "http://example.com/v1/cms/notice/?limit=10&offset=10",
  "previous": null,
  "results": [
    // List of queried items
  ]
}
```

### Pagination Usage Examples

1. Query first page:
```
GET /v1/cms/notice/?limit=10&offset=0
```

2. Query next page:
```
GET /v1/cms/notice/?limit=10&offset=10
```

3. Change page size:
```
GET /v1/cms/notice/?limit=20&offset=0
```

## Filtering

### Notice and Event Filtering

- Title search: `?title__icontains=search_term`
- Exact title match: `?title__exact=exact_title`
- Publication date range filtering: `?published_at__gte=2023-01-01T00:00:00Z&published_at__lte=2023-01-31T23:59:59Z`

### FAQ Filtering

- Category name search: `?category_name=category_name`
- Publication date range filtering: `?published_at__gte=2023-01-01T00:00:00Z&published_at__lte=2023-01-31T23:59:59Z`

## CMS Data Models

### Notice

| Field Name | Type | Description |
|-------|------|------|
| uuid | UUID | Unique identifier (using uuid7) |
| author | FK | Author (references User model) |
| title | String | Title (max 255 characters) |
| content | Text | Content |
| published_at | DateTime | Publication datetime |
| start_at | DateTime | Start datetime (display period start) |
| end_at | DateTime | End datetime (display period end, optional) |
| is_published | Boolean | Publication status |
| created_at | DateTime | Creation datetime (auto-generated) |
| updated_at | DateTime | Modification datetime (auto-updated) |

### Event

| Field Name | Type | Description |
|-------|------|------|
| uuid | UUID | Unique identifier (using uuid7) |
| author | FK | Author (references User model) |
| title | String | Title (max 255 characters) |
| content | Text | Content |
| published_at | DateTime | Publication datetime |
| start_at | DateTime | Start datetime (display period start) |
| end_at | DateTime | End datetime (display period end, optional) |
| event_start_at | DateTime | Event start datetime (actual event period) |
| event_end_at | DateTime | Event end datetime (actual event period, optional) |
| is_published | Boolean | Publication status |
| created_at | DateTime | Creation datetime (auto-generated) |
| updated_at | DateTime | Modification datetime (auto-updated) |

### FAQ Category

| Field Name | Type | Description |
|-------|------|------|
| uuid | UUID | Unique identifier (using uuid7) |
| name | String | Category name (max 255 characters) |
| created_at | DateTime | Creation datetime (auto-generated) |
| updated_at | DateTime | Modification datetime (auto-updated) |

### FAQ

| Field Name | Type | Description |
|-------|------|------|
| uuid | UUID | Unique identifier (using uuid7) |
| author | FK | Author (references User model) |
| category | FK | Category (references FaqCategory model) |
| title | String | Title (max 255 characters) |
| content | Text | Content |
| published_at | DateTime | Publication datetime |
| is_published | Boolean | Publication status |
| created_at | DateTime | Creation datetime (auto-generated) |
| updated_at | DateTime | Modification datetime (auto-updated) |

## Admin Features

CMS content is managed through the Django admin page. Content creation/modification/deletion via API is not provided.

### Common Admin Features

- Item list query and filtering
- Create, update, delete functions
- Batch publish/unpublish processing (using admin actions)

### Notice Management

Administrators can manage the following fields through the Django admin page:

- Basic information: title, author, content
- Publication and display settings: publication status, publication datetime, start/end datetime
- Meta information (read-only): UUID, creation/modification datetime

### Event Management

Administrators can manage the following fields through the Django admin page:

- Basic information: title, author, content
- Event period: event start/end datetime
- Publication and display settings: publication status, publication datetime, start/end datetime
- Meta information (read-only): UUID, creation/modification datetime

### FAQ Management

Administrators can manage the following fields through the Django admin page:

- Basic information: title, author, content, category
- Publication settings: publication status, publication datetime
- Meta information (read-only): UUID, creation/modification datetime

## Security Considerations

- All API requests are accessible only to authenticated users (JWT-based authentication)
- Only notice, event, and FAQ queries are available; creation/modification/deletion is only possible through the admin page
- Only currently active content can be queried, so future or past content cannot be accessed
- Unpublished content is excluded from API responses through the is_published field

## Testing 

The CMS API has been validated through various test cases:

### Serializer Tests
- Serialization validation for each model: notice, event, FAQ, FAQ category
- Time format validation (ISO 8601 format)
- Event end status calculation validation

### ViewSet Tests
- Authentication validation (deny access to unauthenticated users)
- Validation that only active items are queried
- Filtering functionality validation
- Prevention of modification/deletion API request validation

## Example Usage Scenarios

### Notice Querying

1. Query notice list:
```
GET /v1/cms/notice/?limit=10&offset=0
```

2. Search by notice title:
```
GET /v1/cms/notice/?title__icontains=guide&limit=10&offset=0
```

3. Query specific notice details:
```
GET /v1/cms/notice/123e4567-e89b-12d3-a456-426614174000/
```

### Event Querying

1. Query list of currently ongoing events:
```
GET /v1/cms/event/?limit=10&offset=0
```

2. Search by event title:
```
GET /v1/cms/event/?title__icontains=discount&limit=10&offset=0
```

3. Query specific event details:
```
GET /v1/cms/event/123e4567-e89b-12d3-a456-426614174001/
```

4. Query events published within a specific period:
```
GET /v1/cms/event/?published_at__gte=2023-01-01T00:00:00Z&published_at__lte=2023-01-31T23:59:59Z
```

### FAQ Querying

1. Query complete FAQ list:
```
GET /v1/cms/faq/?limit=10&offset=0
```

2. Query FAQs in a specific category:
```
GET /v1/cms/faq/?category_name=account&limit=10&offset=0
```

3. Query recently published FAQs:
```
GET /v1/cms/faq/?published_at__gte=2023-01-01T00:00:00Z
```

## Implementation Notes

### Authentication Processing

- All API requests require a valid JWT access token
- Token is passed in the Authorization header in the format `Bearer {access_token}`
- If the token is expired, refresh with a refresh token and retry the request

### Content Rendering

- The content field may include HTML, so appropriate processing is needed when rendering in the frontend
- In React, HTML content can be rendered using `dangerouslySetInnerHTML`