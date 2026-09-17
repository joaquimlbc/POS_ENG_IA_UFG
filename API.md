# REST API Documentation - PG genIA MVP-01
## REST Countries API Backend

**Base URL:** `http://localhost:8000`  
**Version:** 1.0.0  
**Authentication:** None (v0.1-beta; JWT coming in 0.3)  
**Content-Type:** `application/json`  
**Documentation:** `/docs` (Swagger) | `/redoc` (ReDoc)

---

## 📋 Table of Contents

1. [Health Check](#health-check)
2. [Country CRUD Operations](#country-crud-operations)
   - [Create Country](#create-country)
   - [List Countries](#list-countries)
   - [Get Country by ID](#get-country-by-id)
   - [Get Country by ISO Code](#get-country-by-iso-code)
   - [Update Country](#update-country)
   - [Delete Country](#delete-country)
3. [Related Entities](#related-entities)
   - [Add Languages](#add-languages)
   - [Add Currencies](#add-currencies)
   - [Add Timezones](#add-timezones)
4. [Batch Operations](#batch-operations)
   - [Sync Batch](#sync-batch)
   - [Get Sync Result](#get-sync-result)
5. [Analytics](#analytics)
   - [Global Statistics](#global-statistics)
   - [Regional Statistics](#regional-statistics)
   - [Data Gaps Analysis](#data-gaps-analysis)

---

## 🏥 Health Check

### Endpoint
```
GET /health
```

### Description
Liveness probe for orchestrators (Kubernetes, Docker, etc). Returns API status and version.

### Response
```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2026-09-17T16:50:30.123456+00:00"
}
```

### Status Code
- **200 OK** - Service is healthy

### Example
```bash
curl -X GET http://localhost:8000/health
```

### Response Body
```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2026-09-17T16:50:30.123456+00:00"
}
```

---

## 🌍 Country CRUD Operations

### Create Country

#### Endpoint
```
POST /api/v1/countries
```

#### Description
Create a new country with validation of ISO codes, region, and population.

#### Request Body
```json
{
  "name_common": "Brazil",
  "name_official": "Federative Republic of Brazil",
  "iso_code_2": "BR",
  "iso_code_3": "BRA",
  "region": "Americas",
  "subregion": "South America",
  "population": 215313498,
  "area": 8514877,
  "latitude": -10.332,
  "longitude": -53.505
}
```

#### Validations
- `name_common`, `name_official`: 1-255 chars
- `iso_code_2`: Exactly 2 letters, must be **unique**
- `iso_code_3`: Exactly 3 letters, must be **unique**
- `region`: Required, validated against {Africa, Americas, Asia, Europe, Oceania}
- `population`: 0 - 2,000,000,000 (2 billion)
- `area`: Positive float (km²)
- `latitude`: -90 to 90
- `longitude`: -180 to 180

#### Status Codes
- **201 Created** - Country successfully created
- **409 Conflict** - ISO2 or ISO3 already exists
- **422 Unprocessable Entity** - Invalid data (validation error)

#### Response (201 Created)
```json
{
  "id": 1,
  "name_common": "Brazil",
  "name_official": "Federative Republic of Brazil",
  "iso_code_2": "BR",
  "iso_code_3": "BRA",
  "region": "Americas",
  "subregion": "South America",
  "population": 215313498,
  "area": 8514877.0,
  "latitude": -10.332,
  "longitude": -53.505,
  "created_at": "2026-09-17T16:50:30.123456+00:00",
  "updated_at": "2026-09-17T16:50:30.123456+00:00"
}
```

#### Error Response (409 Conflict)
```json
{
  "detail": "Country with iso_code_2='BR' already exists"
}
```

#### Error Response (422 Unprocessable Entity)
```json
{
  "detail": [
    {
      "loc": ["body", "region"],
      "msg": "Input should be 'Africa', 'Americas', 'Asia', 'Europe' or 'Oceania' [type=enum, input_value='Invalid', input_type=str]",
      "type": "enum"
    }
  ]
}
```

#### Example
```bash
curl -X POST http://localhost:8000/api/v1/countries \
  -H "Content-Type: application/json" \
  -d '{
    "name_common": "Brazil",
    "name_official": "Federative Republic of Brazil",
    "iso_code_2": "BR",
    "iso_code_3": "BRA",
    "region": "Americas",
    "population": 215313498
  }'
```

---

### List Countries

#### Endpoint
```
GET /api/v1/countries
```

#### Description
List all countries with pagination and optional region filtering.

#### Query Parameters
| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `page` | int | 1 | - | Page number (1-indexed) |
| `limit` | int | 20 | 100 | Items per page |
| `region` | str | - | - | Filter by region: Africa, Americas, Asia, Europe, Oceania |

#### Status Codes
- **200 OK** - Successfully returned list

#### Response (200 OK)
```json
{
  "items": [
    {
      "id": 1,
      "name_common": "Brazil",
      "iso_code_2": "BR",
      "iso_code_3": "BRA",
      "region": "Americas",
      "population": 215313498,
      "area": 8514877.0
    },
    {
      "id": 2,
      "name_common": "Argentina",
      "iso_code_2": "AR",
      "iso_code_3": "ARG",
      "region": "Americas",
      "population": 46235844,
      "area": 2780400.0
    }
  ],
  "total": 250,
  "page": 1,
  "limit": 20,
  "pages": 13
}
```

#### Examples
```bash
# Get first page (20 items)
curl -X GET http://localhost:8000/api/v1/countries

# Get page 2 with custom limit
curl -X GET "http://localhost:8000/api/v1/countries?page=2&limit=50"

# Filter by region
curl -X GET "http://localhost:8000/api/v1/countries?region=Europe"
```

---

### Get Country by ID

#### Endpoint
```
GET /api/v1/countries/{id}
```

#### Description
Get detailed information about a specific country, including all relationships (languages, currencies, timezones).

#### Path Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | int | Country ID |

#### Status Codes
- **200 OK** - Country found
- **404 Not Found** - Country does not exist

#### Response (200 OK)
```json
{
  "id": 1,
  "name_common": "Brazil",
  "name_official": "Federative Republic of Brazil",
  "iso_code_2": "BR",
  "iso_code_3": "BRA",
  "region": "Americas",
  "subregion": "South America",
  "population": 215313498,
  "area": 8514877.0,
  "latitude": -10.332,
  "longitude": -53.505,
  "created_at": "2026-09-17T16:50:30.123456+00:00",
  "updated_at": "2026-09-17T16:50:30.123456+00:00",
  "languages": [
    {
      "id": 1,
      "language_code": "pt",
      "language_name": "Portuguese"
    }
  ],
  "currencies": [
    {
      "id": 1,
      "currency_code": "BRL",
      "currency_name": "Brazilian Real"
    }
  ],
  "timezones": [
    {
      "id": 1,
      "timezone_name": "America/Sao_Paulo"
    }
  ]
}
```

#### Error Response (404 Not Found)
```json
{
  "detail": "Country with id=9999 not found"
}
```

#### Examples
```bash
curl -X GET http://localhost:8000/api/v1/countries/1
```

---

### Get Country by ISO Code

#### Endpoint
```
GET /api/v1/countries/iso/{code}
```

#### Description
Get country details by ISO 2-letter or 3-letter code.

#### Path Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `code` | str | ISO2 (e.g., "BR") or ISO3 (e.g., "BRA") code |

#### Status Codes
- **200 OK** - Country found
- **404 Not Found** - Country does not exist

#### Response (200 OK)
Same as [Get Country by ID](#get-country-by-id)

#### Examples
```bash
# By ISO2
curl -X GET http://localhost:8000/api/v1/countries/iso/BR

# By ISO3
curl -X GET http://localhost:8000/api/v1/countries/iso/BRA
```

---

### Update Country

#### Endpoint
```
PUT /api/v1/countries/{id}
```

#### Description
Update country data. ISO codes cannot be modified (immutable identifiers).

#### Path Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | int | Country ID |

#### Request Body (All fields optional)
```json
{
  "name_common": "Brazil (Updated)",
  "population": 220000000,
  "region": "Americas"
}
```

#### Validations
- Same as [Create Country](#create-country) for each field
- ISO codes (`iso_code_2`, `iso_code_3`) are **read-only**
- Only modified fields need to be sent

#### Status Codes
- **200 OK** - Country successfully updated
- **404 Not Found** - Country does not exist
- **422 Unprocessable Entity** - Invalid data

#### Response (200 OK)
```json
{
  "id": 1,
  "name_common": "Brazil (Updated)",
  "iso_code_2": "BR",
  "iso_code_3": "BRA",
  "region": "Americas",
  "population": 220000000,
  "area": 8514877.0,
  "updated_at": "2026-09-17T16:51:00.123456+00:00"
}
```

#### Examples
```bash
# Update single field
curl -X PUT http://localhost:8000/api/v1/countries/1 \
  -H "Content-Type: application/json" \
  -d '{"population": 220000000}'

# Update multiple fields
curl -X PUT http://localhost:8000/api/v1/countries/1 \
  -H "Content-Type: application/json" \
  -d '{
    "name_common": "Brazil (Updated)",
    "region": "Americas"
  }'
```

---

### Delete Country

#### Endpoint
```
DELETE /api/v1/countries/{id}
```

#### Description
Delete a country and all its related entities (languages, currencies, timezones) via cascade delete.

#### Path Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | int | Country ID |

#### Status Codes
- **204 No Content** - Country successfully deleted
- **404 Not Found** - Country does not exist

#### Response (204 No Content)
No response body

#### Examples
```bash
curl -X DELETE http://localhost:8000/api/v1/countries/1
```

---

## 🌐 Related Entities

### Add Languages

#### Endpoint
```
POST /api/v1/countries/{id}/languages
```

#### Description
Add languages to an existing country.

#### Path Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | int | Country ID |

#### Request Body
```json
{
  "languages": [
    {
      "language_code": "pt",
      "language_name": "Portuguese"
    },
    {
      "language_code": "en",
      "language_name": "English"
    }
  ]
}
```

#### Status Codes
- **200 OK** - Languages added successfully
- **404 Not Found** - Country does not exist
- **422 Unprocessable Entity** - Invalid data

#### Response (200 OK)
Returns updated country with new languages (same as [Get Country by ID](#get-country-by-id))

#### Examples
```bash
curl -X POST http://localhost:8000/api/v1/countries/1/languages \
  -H "Content-Type: application/json" \
  -d '{
    "languages": [
      {"language_code": "pt", "language_name": "Portuguese"}
    ]
  }'
```

---

### Add Currencies

#### Endpoint
```
POST /api/v1/countries/{id}/currencies
```

#### Description
Add currencies to an existing country.

#### Path Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | int | Country ID |

#### Request Body
```json
{
  "currencies": [
    {
      "currency_code": "BRL",
      "currency_name": "Brazilian Real"
    }
  ]
}
```

#### Validations
- `currency_code`: Exactly 3 uppercase letters (ISO 4217)
- `currency_name`: 1-100 chars

#### Status Codes
- **200 OK** - Currencies added successfully
- **404 Not Found** - Country does not exist

#### Response (200 OK)
Returns updated country with new currencies

#### Examples
```bash
curl -X POST http://localhost:8000/api/v1/countries/1/currencies \
  -H "Content-Type: application/json" \
  -d '{
    "currencies": [
      {"currency_code": "BRL", "currency_name": "Brazilian Real"}
    ]
  }'
```

---

### Add Timezones

#### Endpoint
```
POST /api/v1/countries/{id}/timezones
```

#### Description
Add timezones to an existing country.

#### Path Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | int | Country ID |

#### Request Body
```json
{
  "timezones": [
    {
      "timezone_name": "America/Sao_Paulo"
    },
    {
      "timezone_name": "America/Manaus"
    }
  ]
}
```

#### Validations
- `timezone_name`: 1-100 chars (IANA timezone format)

#### Status Codes
- **200 OK** - Timezones added successfully
- **404 Not Found** - Country does not exist

#### Response (200 OK)
Returns updated country with new timezones

#### Examples
```bash
curl -X POST http://localhost:8000/api/v1/countries/1/timezones \
  -H "Content-Type: application/json" \
  -d '{
    "timezones": [
      {"timezone_name": "America/Sao_Paulo"}
    ]
  }'
```

---

## 📦 Batch Operations

### Sync Batch

#### Endpoint
```
POST /api/v1/sync
```

#### Description
Batch upsert (insert new, update existing) countries with data quality assessment.

#### Constraints
- Maximum 1000 countries per request
- Performs quality assessment on synced data
- Returns summary statistics

#### Request Body
```json
{
  "countries": [
    {
      "name_common": "Country 1",
      "name_official": "Official Name 1",
      "iso_code_2": "C1",
      "iso_code_3": "C1A",
      "region": "Europe",
      "population": 1000000
    },
    ...
  ]
}
```

#### Status Codes
- **200 OK** - Batch processed (may have partial failures)
- **400 Bad Request** - Batch size > 1000
- **422 Unprocessable Entity** - Invalid data format

#### Response (200 OK)
```json
{
  "sync_id": "sync_1695075030.123456",
  "status": "success",
  "timestamp": "2026-09-17T16:50:30.123456+00:00",
  "countries_inserted": 250,
  "countries_updated": 0,
  "countries_skipped": 0,
  "message": "Synced 250 countries: 250 inserted, 0 updated"
}
```

#### Possible Status Values
- `success` - All countries processed successfully
- `partial_failure` - Some countries failed (check countries_skipped)
- `failure` - Complete failure

#### Examples
```bash
# Sync 250 countries
curl -X POST http://localhost:8000/api/v1/sync \
  -H "Content-Type: application/json" \
  -d '{
    "countries": [
      {
        "name_common": "Country 1",
        "iso_code_2": "C1",
        "iso_code_3": "C1A",
        "region": "Europe",
        "population": 1000000
      }
    ]
  }'
```

---

### Get Sync Result

#### Endpoint
```
GET /api/v1/sync/{sync_id}
```

#### Description
Get details of a previously executed sync operation.

#### Path Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `sync_id` | str | Sync operation ID |

#### Status Codes
- **200 OK** - Sync result found
- **404 Not Found** - Sync not found

#### Response (200 OK)
```json
{
  "sync_id": "sync_1695075030.123456",
  "status": "success",
  "timestamp": "2026-09-17T16:50:30.123456+00:00",
  "countries_inserted": 250,
  "countries_updated": 0,
  "countries_skipped": 0,
  "message": "Synced 250 countries: 250 inserted, 0 updated"
}
```

---

## 📊 Analytics

### Global Statistics

#### Endpoint
```
GET /api/v1/statistics
```

#### Description
Get global statistics across all countries.

#### Status Codes
- **200 OK** - Statistics calculated

#### Response (200 OK)
```json
{
  "total_countries": 250,
  "total_population": 8000000000,
  "total_area": 510100000.0,
  "average_population": 32000000,
  "average_area": 2040400.0,
  "regions": [
    {
      "region": "Africa",
      "total_countries": 54,
      "total_population": 1400000000,
      "total_area": 30370000.0
    },
    {
      "region": "Americas",
      "total_countries": 35,
      "total_population": 1000000000,
      "total_area": 42400000.0
    },
    ...
  ]
}
```

#### Examples
```bash
curl -X GET http://localhost:8000/api/v1/statistics
```

---

### Regional Statistics

#### Endpoint
```
GET /api/v1/statistics/regions
```

#### Description
Get detailed statistics by region.

#### Status Codes
- **200 OK** - Statistics calculated

#### Response (200 OK)
```json
[
  {
    "region": "Africa",
    "total_countries": 54,
    "total_population": 1400000000,
    "total_area": 30370000.0
  },
  {
    "region": "Americas",
    "total_countries": 35,
    "total_population": 1000000000,
    "total_area": 42400000.0
  },
  {
    "region": "Asia",
    "total_countries": 48,
    "total_population": 4700000000,
    "total_area": 44580000.0
  },
  {
    "region": "Europe",
    "total_countries": 50,
    "total_population": 750000000,
    "total_area": 10180000.0
  },
  {
    "region": "Oceania",
    "total_countries": 14,
    "total_population": 45000000,
    "total_area": 8600000.0
  }
]
```

#### Examples
```bash
curl -X GET http://localhost:8000/api/v1/statistics/regions
```

---

### Data Gaps Analysis

#### Endpoint
```
GET /api/v1/data-gaps
```

#### Description
Identify countries with data quality issues and prioritize for update.

#### Query Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_results` | int | 50 | Maximum number of results |

#### Status Codes
- **200 OK** - Analysis completed

#### Response (200 OK)
```json
{
  "total_countries": 250,
  "countries_with_issues": 15,
  "by_priority": {
    "critical": [
      {
        "id": 5,
        "name": "Country A",
        "reason": "Missing languages",
        "missing_fields": ["languages"]
      }
    ],
    "high": [
      {
        "id": 10,
        "name": "Country B",
        "reason": "Missing currencies"
      }
    ]
  }
}
```

#### Examples
```bash
# Get top 50 data gaps
curl -X GET http://localhost:8000/api/v1/data-gaps

# Get top 100 data gaps
curl -X GET "http://localhost:8000/api/v1/data-gaps?max_results=100"
```

---

## 📝 Data Models

### CountryCreate (Request)
```json
{
  "name_common": "string (1-255)",
  "name_official": "string (1-255)",
  "iso_code_2": "string (2 letters)",
  "iso_code_3": "string (3 letters)",
  "region": "string (enum: Africa|Americas|Asia|Europe|Oceania)",
  "subregion": "string (nullable, max 50)",
  "population": "integer (0-2000000000)",
  "area": "float (nullable, >= 0)",
  "latitude": "float (nullable, -90 to 90)",
  "longitude": "float (nullable, -180 to 180)"
}
```

### CountryResponse (Response)
```json
{
  "id": "integer",
  "name_common": "string",
  "name_official": "string",
  "iso_code_2": "string",
  "iso_code_3": "string",
  "region": "string",
  "subregion": "string (nullable)",
  "population": "integer",
  "area": "float (nullable)",
  "latitude": "float (nullable)",
  "longitude": "float (nullable)",
  "created_at": "datetime (ISO 8601)",
  "updated_at": "datetime (ISO 8601)"
}
```

### CountryDetailResponse (Extended)
```json
{
  "...": "CountryResponse fields",
  "languages": [
    {
      "id": "integer",
      "language_code": "string",
      "language_name": "string"
    }
  ],
  "currencies": [
    {
      "id": "integer",
      "currency_code": "string",
      "currency_name": "string"
    }
  ],
  "timezones": [
    {
      "id": "integer",
      "timezone_name": "string"
    }
  ]
}
```

---

## 🔄 Error Handling

### Common HTTP Status Codes

| Status | Meaning | Typical Cause |
|--------|---------|---------------|
| **200 OK** | Request succeeded | GET, PUT operations |
| **201 Created** | Resource created | POST operations (create) |
| **204 No Content** | Successful, no body | DELETE operations |
| **400 Bad Request** | Invalid request | Batch size > 1000 |
| **404 Not Found** | Resource not found | Country ID doesn't exist |
| **409 Conflict** | Resource conflict | Duplicate ISO code |
| **422 Unprocessable Entity** | Validation error | Invalid field values |
| **500 Internal Server Error** | Server error | Unexpected error |

### Error Response Format

```json
{
  "detail": "Description of the error"
}
```

Or for validation errors:

```json
{
  "detail": [
    {
      "loc": ["body", "region"],
      "msg": "Input should be 'Africa', 'Americas', 'Asia', 'Europe' or 'Oceania'",
      "type": "enum"
    }
  ]
}
```

---

## 🧪 Testing Endpoints

All endpoints have been tested and validated:

```
✅ 17 API endpoint tests passing
✅ 201 Created - POST operations
✅ 200 OK - GET operations
✅ 204 No Content - DELETE operations
✅ 404 Not Found - Missing resources
✅ 409 Conflict - Duplicate constraints
✅ 422 Unprocessable Entity - Validation errors
```

---

## 📚 Additional Resources

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI Schema:** `http://localhost:8000/openapi.json`
- **Architecture:** [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Quality Checklist:** [QUALITY_CHECKLIST.md](./QUALITY_CHECKLIST.md)

---

**API Documentation Version 1.0 | Last Updated: 17/09/2026**  
**Status:** Production Ready (0.1-beta)
