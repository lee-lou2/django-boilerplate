# Short URL API Documentation

## Overview

This document serves as a guide to the short URL generation and redirection API functionality. This service converts long URLs into short URLs for users, and redirects to the appropriate URL based on the user's device type. It features innovative URL generation methods and various technical characteristics.

## API Endpoints

| Path | Method | Description |
|------|--------|-------------|
| `/v1/short-url/` | POST | Generate short URL |
| `url.{host}/{short_key}/` | GET | Short URL redirect |

## Technical Features

### 1. Innovative Short Key Generation Method

Common short URL services generate random keys, check for duplicates in the database, and then add them. This method requires database lookups each time and can cause performance degradation.

This service uses an innovative approach that guarantees unique short keys **without database lookups**:

1. Generate a 4-character random string (`random_key`)
2. Convert the table's auto-incrementing PK (Primary Key) to a string using custom encoding (`id_to_key` function)
   - Uses lowercase letters, uppercase letters, and numbers (total of 62 characters) to convert PK values to unique strings
3. Create the final short key by placing part of the random key at the front and the rest at the back, wrapping the PK-based key

```
Final short key = random_key[:2] + id_to_key(id) + random_key[2:]
```

This method ensures unique short keys without duplicate checking.

### 2. URL Hashing to Prevent Duplication

To prevent duplicate short URLs for the same URL combinations, a URL hashing approach is applied:

1. Concatenate all input URLs (iOS/Android deep links, fallback URLs, etc.)
2. Generate a hash value using the SHA-256 hash algorithm
3. Check if the same hash value exists in the database to prevent duplicate creation

This efficiently manages resources and always provides the same short URL for identical URL combinations.

### 3. Device Detection and Adaptive Redirection

Automatically detects the user's device type (iOS, Android, other) to provide an optimized experience:

1. Device identification through User-Agent analysis
2. iOS users → Redirect to iOS deep link or iOS fallback URL
3. Android users → Redirect to Android deep link or Android fallback URL
4. Other devices → Redirect to default fallback URL

### 4. Deep Link Support and Fallback Mechanism

Provides intelligent redirection based on app installation status:

1. Attempts to launch the app via deep link
2. If the app is not installed, automatically redirects to the fallback URL after 2 seconds
3. Supports device-specific fallback URLs

### 5. OG Tag Support

Supports Open Graph tags to provide rich previews when shared on social media:

```json
{
  "og:title": "Website Title",
  "og:description": "Website Description",
  "og:image": "Image URL"
}
```

### 6. User Visit Tracking and Analytics

Tracks all visit records in detail for analysis:

1. IP address tracking (supports X-Forwarded-For header)
2. User agent information recording
3. Referrer tracking
4. Timestamp recording

### 7. Architecture Separation

Domain-based service separation using Django Hosts:

1. Main domain → Short URL generation API service
2. `url.{host}` subdomain → Redirection service

This structure allows each service to be scaled and managed independently.

## Flow Diagram

```mermaid
flowchart TD
    classDef userAction fill:#f9d6d6,stroke:#e88e8e,stroke-width:2px,color:#333
    classDef systemAction fill:#d6e5f9,stroke:#8eb5e8,stroke-width:2px,color:#333
    classDef success fill:#d6f9d6,stroke:#8ee88e,stroke-width:2px,color:#333
    
    Start([Start]) --> CreateRequest[Short URL Creation Request]
    CreateRequest --> GenerateHash[Generate URL Combination Hash]
    GenerateHash --> CheckHash{Check Hash Duplication}
    
    CheckHash -->|Duplicate Exists| ReturnExisting[Return Existing Short URL]
    ReturnExisting --> End([End])
    
    CheckHash -->|No Duplicate| GenerateRandom[Generate 4-character Random Key]
    GenerateRandom --> SaveURL[Save in Database]
    SaveURL --> EncodePK[Convert PK to String]
    EncodePK --> CombineKeys[Combine Random Key and Converted PK]
    CombineKeys --> ReturnShortURL[Return Short URL]
    ReturnShortURL --> End
    
    Start2([Start]) --> AccessShortURL[Access Short URL]
    AccessShortURL --> ExtractKey[Extract Short Key]
    ExtractKey --> ExtractPK[Extract Converted PK]
    ExtractPK --> DecodePK[Restore PK to Number]
    DecodePK --> FetchURL[Fetch URL Information from Database]
    FetchURL --> DetectDevice[Detect User Device]
    
    DetectDevice -->|iOS| iOSPath[Select iOS Path]
    DetectDevice -->|Android| AndroidPath[Select Android Path]
    DetectDevice -->|Other| DefaultPath[Select Default Path]
    
    iOSPath --> CheckiOSDeeplink{Deep Link Exists?}
    CheckiOSDeeplink -->|Yes| TryiOSApp[Attempt to Launch iOS App]
    CheckiOSDeeplink -->|No| iOSFallback[Redirect to iOS Fallback URL]
    
    TryiOSApp --> iOSAppCheck{App Launch Successful?}
    iOSAppCheck -->|Yes| iOSSuccess[Display Content in App]
    iOSAppCheck -->|No| iOSFallback
    
    AndroidPath --> CheckAndroidDeeplink{Deep Link Exists?}
    CheckAndroidDeeplink -->|Yes| TryAndroidApp[Attempt to Launch Android App]
    CheckAndroidDeeplink -->|No| AndroidFallback[Redirect to Android Fallback URL]
    
    TryAndroidApp --> AndroidAppCheck{App Launch Successful?}
    AndroidAppCheck -->|Yes| AndroidSuccess[Display Content in App]
    AndroidAppCheck -->|No| AndroidFallback
    
    DefaultPath --> DefaultRedirect[Redirect to Default Fallback URL]
    
    iOSFallback --> RecordVisit[Save Visit Record]
    AndroidFallback --> RecordVisit
    DefaultRedirect --> RecordVisit
    iOSSuccess --> RecordVisit
    AndroidSuccess --> RecordVisit
    
    RecordVisit --> End2([End])
    
    class CreateRequest,AccessShortURL userAction
    class GenerateHash,CheckHash,GenerateRandom,SaveURL,EncodePK,CombineKeys,ExtractKey,ExtractPK,DecodePK,FetchURL,DetectDevice,RecordVisit systemAction
    class ReturnShortURL,iOSSuccess,AndroidSuccess,iOSFallback,AndroidFallback,DefaultRedirect success
```

## API Detailed Description

### 1. Short URL Generation API

Authenticated users can provide URL information to generate a short URL.

**URL**: `/v1/short-url/`

**Method**: `POST`

**Authentication**: Access token required (Authorization header)

**Request Body**:
```json
{
  "ios_deep_link": "appscheme://path",
  "ios_fallback_url": "https://example.com/ios",
  "android_deep_link": "appscheme://path",
  "android_fallback_url": "https://example.com/android",
  "default_fallback_url": "https://example.com",
  "og_tag": {
    "og:title": "Title",
    "og:description": "Description",
    "og:image": "https://example.com/image.jpg"
  }
}
```

**Response (201 Created)**:
```json
{
  "id": 123,
  "short_key": "ab1Xcd",
  "ios_deep_link": "appscheme://path",
  "ios_fallback_url": "https://example.com/ios",
  "android_deep_link": "appscheme://path",
  "android_fallback_url": "https://example.com/android",
  "default_fallback_url": "https://example.com",
  "og_tag": {
    "og:title": "Title",
    "og:description": "Description",
    "og:image": "https://example.com/image.jpg"
  }
}
```

**Required Fields**:
- `default_fallback_url`: Default fallback URL (valid URL format)

**Optional Fields**:
- `ios_deep_link`: iOS app deep link
- `ios_fallback_url`: iOS fallback URL (valid URL format)
- `android_deep_link`: Android app deep link
- `android_fallback_url`: Android fallback URL (valid URL format)
- `og_tag`: Open Graph tags (JSON object)

### 2. Short URL Redirect API

Accessing a short URL redirects to the appropriate URL.

**URL**: `url.{host}/{short_key}/`

**Method**: `GET`

**Authentication**: Not required

**Parameters**:
- `short_key`: Short URL key
- `referrer`: (Optional) Referrer information

**Operation**:
1. Extract the PK from the short key to look up URL information
2. Analyze the user agent to detect device type
3. Redirect to the appropriate deep link or fallback URL
4. Record visit information (IP, agent, referrer, timestamp)

## Short Key Generation Algorithm

The short key generation consists of the following steps:

1. **Generate Random Key**:
   ```python
   def generate_random_key():
       return "".join(random.choices(string.ascii_letters + string.digits, k=4))
   ```

2. **Convert ID to String Key**:
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

3. **Convert Key to ID** (during redirection):
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

4. **Final Short Key Combination**:
   ```python
   def to_representation(self, instance):
       short_key = id_to_key(instance.id)
       random_key = instance.random_key
       instance.short_key = f"{random_key[:2]}{short_key}{random_key[2:]}"
       return super().to_representation(instance)
   ```

## URL Hashing Algorithm

Hashing for URL duplication prevention is implemented as follows:

```python
def validate(self, attrs):
    # Create hashed_value
    concatenated = "".join(
        [
            attrs.get("ios_deep_link", ""),
            attrs.get("ios_fallback_url", ""),
            attrs.get("android_deep_link", ""),
            attrs.get("android_fallback_url", ""),
            attrs.get("default_fallback_url", ""),
        ]
    )

    # Generate SHA-256 hash
    hasher = hashlib.sha256()
    hasher.update(concatenated.encode("utf-8"))
    hashed_value = hasher.hexdigest()

    if ShortUrl.objects.filter(hashed_value=hashed_value).exists():
        raise serializers.ValidationError(E005_HASHED_VALUE_ALREADY_EXISTS)
    attrs["hashed_value"] = hashed_value
    return attrs
```

## Usage Examples

### Short URL Generation

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
    "og:title": "Great Product",
    "og:description": "This product is really great",
    "og:image": "https://example.com/images/product123.jpg"
  }
}
```

**Response**:
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
    "og:title": "Great Product",
    "og:description": "This product is really great",
    "og:image": "https://example.com/images/product123.jpg"
  }
}
```

### Accessing Short URL

When a user accesses `https://url.example.com/xy1Zab/`:

1. The server extracts the `1Zab` part and converts it to database ID `42`
2. Looks up URL information corresponding to ID `42`
3. Detects the user's device and redirects to the appropriate URL:
   - iOS users: `myapp://product/123` (if app installed) or `https://example.com/ios/product/123` (if not installed)
   - Android users: `myapp://product/123` (if app installed) or `https://example.com/android/product/123` (if not installed)
   - Other devices: `https://example.com/product/123`

## Error Response Format

**Validation Failure (400 Bad Request)**:
```json
{
  "field_name": [
    {
      "message": "Error message",
      "error_code": "Error code"
    }
  ]
}
```

For errors not related to fields, the `non_field` key is used:
```json
{
  "non_field": [
    {
      "message": "Error message",
      "error_code": "Error code"
    }
  ]
}
```

### Example Error Responses

**Hash Value Duplication**:
```json
{
  "non_field": [
    {
      "message": "A short URL with the same URL combination already exists",
      "error_code": "E005"
    }
  ]
}
```

**Invalid URL Format**:
```json
{
  "default_fallback_url": [
    {
      "message": "Enter a valid URL",
      "error_code": "E001"
    }
  ]
}
```

**Invalid OG Tag Format**:
```json
{
  "og_tag": [
    {
      "message": "Not a valid JSON format",
      "error_code": "E005"
    }
  ]
}
```

## Error Codes

| Error Code | Description | Field |
|------------|-------------|-------|
| E005 | A short URL with the same URL combination already exists | non_field |
| E005 | Invalid OG tag format | og_tag |
| E001 | Invalid URL format | ios_fallback_url, android_fallback_url, default_fallback_url |

## Admin Features

The short URL system supports the following operations through the admin interface:

1. Look up and filter short URLs
2. Modify URL information (automatically updates hash value)
3. Prevent duplicate URL creation
4. View and analyze visit records

However, creating new short URLs and modifying/deleting visit records is not possible through the admin interface; only viewing is allowed.

## Security Considerations

- Short URL creation is only available to authenticated users
- URL redirection is accessible without authentication
- Compliance with privacy laws is necessary when storing IP addresses in visit records
- All API requests should be made via HTTPS

This API provides a fast and reliable short URL service while optimizing the user experience.
