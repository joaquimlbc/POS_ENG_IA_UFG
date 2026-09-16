# Documentação - Rotas REST da API
## PG genIA MVP-01: REST Countries Dashboard

**Versão:** 1.0  
**Data:** 16 de Setembro de 2026  
**Status:** ✅ Implementado

---

## 📋 RESUMO DE ENDPOINTS

### CRUD Operations

| Método | Endpoint | Descrição | Status |
|--------|----------|-----------|--------|
| POST | `/api/v1/countries` | Criar país | 201 |
| GET | `/api/v1/countries` | Listar com paginação | 200 |
| GET | `/api/v1/countries/{id}` | Obter por ID | 200 |
| GET | `/api/v1/countries/iso/{code}` | Obter por ISO code | 200 |
| PUT | `/api/v1/countries/{id}` | Atualizar | 200 |
| DELETE | `/api/v1/countries/{id}` | Deletar | 204 |

### Relationships

| Método | Endpoint | Descrição | Status |
|--------|----------|-----------|--------|
| POST | `/api/v1/countries/{id}/languages` | Adicionar idiomas | 201 |
| POST | `/api/v1/countries/{id}/currencies` | Adicionar moedas | 201 |
| POST | `/api/v1/countries/{id}/timezones` | Adicionar fusos | 201 |

### Batch & Sync

| Método | Endpoint | Descrição | Status |
|--------|----------|-----------|--------|
| POST | `/api/v1/sync` | Sincronizar dados | 200 |

### Statistics & Analytics

| Método | Endpoint | Descrição | Status |
|--------|----------|-----------|--------|
| GET | `/api/v1/statistics` | Estatísticas globais | 200 |
| GET | `/api/v1/regions` | Breakdown por região | 200 |
| GET | `/api/v1/data-gaps` | Problemas de dados | 200 |
| GET | `/api/v1/countries/{id}/validate` | Validar qualidade | 200 |

### Health

| Método | Endpoint | Descrição | Status |
|--------|----------|-----------|--------|
| GET | `/api/v1/health` | Health check | 200 |

---

## 📖 DOCUMENTAÇÃO DETALHADA

### 1. CREATE - POST /api/v1/countries

**Descrição:** Criar um novo país

**Request:**
```json
{
  "name_common": "Brazil",
  "name_official": "Federative Republic of Brazil",
  "iso_code_2": "BR",
  "iso_code_3": "BRA",
  "region": "Americas",
  "subregion": "South America",
  "population": 215000000,
  "area": 8514876.5,
  "latitude": -14.235,
  "longitude": -51.9253
}
```

**Response (201):**
```json
{
  "id": 1,
  "name_common": "Brazil",
  "name_official": "Federative Republic of Brazil",
  "iso_code_2": "BR",
  "iso_code_3": "BRA",
  "region": "Americas",
  "subregion": "South America",
  "population": 215000000,
  "area": 8514876.5,
  "latitude": -14.235,
  "longitude": -51.9253,
  "created_at": "2026-09-16T10:30:00Z",
  "updated_at": "2026-09-16T10:30:00Z"
}
```

**Errors:**
- 409: Country already exists
- 422: Validation error
- 500: Internal server error

---

### 2. READ - GET /api/v1/countries

**Descrição:** Listar países com paginação

**Query Parameters:**
```
page=1          (default: 1, min: 1)
limit=20        (default: 20, max: 100)
region=Americas (optional: Africa, Americas, Asia, Europe, Oceania)
```

**Example:** `GET /api/v1/countries?page=1&limit=20&region=Europe`

**Response (200):**
```json
{
  "items": [
    {
      "id": 1,
      "name_common": "Austria",
      "iso_code_2": "AT",
      "iso_code_3": "AUT",
      "region": "Europe",
      "population": 9000000,
      "area": 83858.0,
      "created_at": "2026-09-16T10:30:00Z",
      "updated_at": "2026-09-16T10:30:00Z"
    }
  ],
  "total": 250,
  "page": 1,
  "limit": 20,
  "pages": 13
}
```

**Errors:**
- 500: Internal server error

---

### 3. READ - GET /api/v1/countries/{country_id}

**Descrição:** Obter país com todos os relacionamentos

**Path Parameters:**
```
country_id=1 (required, must be > 0)
```

**Example:** `GET /api/v1/countries/1`

**Response (200):**
```json
{
  "id": 1,
  "name_common": "Brazil",
  "name_official": "Federative Republic of Brazil",
  "iso_code_2": "BR",
  "iso_code_3": "BRA",
  "region": "Americas",
  "population": 215000000,
  "area": 8514876.5,
  "created_at": "2026-09-16T10:30:00Z",
  "updated_at": "2026-09-16T10:30:00Z",
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

**Errors:**
- 404: Country not found
- 500: Internal server error

---

### 4. READ - GET /api/v1/countries/iso/{iso_code}

**Descrição:** Obter país por ISO code (2 ou 3 letras)

**Path Parameters:**
```
iso_code=BR  (ISO2) ou iso_code=BRA (ISO3)
```

**Examples:**
- `GET /api/v1/countries/iso/BR`
- `GET /api/v1/countries/iso/BRA`

**Response:** Igual ao endpoint anterior (200)

**Errors:**
- 404: Country not found
- 500: Internal server error

---

### 5. UPDATE - PUT /api/v1/countries/{country_id}

**Descrição:** Atualizar país (todos os campos são opcionais)

**Path Parameters:**
```
country_id=1
```

**Request (apenas campos a atualizar):**
```json
{
  "population": 216000000,
  "area": 8515000.0,
  "subregion": "South America"
}
```

**Response (200):** País atualizado (sem relacionamentos)

**Errors:**
- 404: Country not found
- 409: Duplicate field value
- 500: Internal server error

---

### 6. DELETE - DELETE /api/v1/countries/{country_id}

**Descrição:** Deletar país (cascade deleta relacionamentos)

**Path Parameters:**
```
country_id=1
```

**Response:** 204 No Content (sem body)

**Errors:**
- 404: Country not found
- 500: Internal server error

---

### 7. RELATIONSHIPS - POST /api/v1/countries/{country_id}/languages

**Descrição:** Adicionar idiomas a um país

**Path Parameters:**
```
country_id=1
```

**Request:**
```json
[
  {
    "language_code": "pt",
    "language_name": "Portuguese"
  },
  {
    "language_code": "en",
    "language_name": "English"
  }
]
```

**Response (201):** País com novos idiomas

**Errors:**
- 404: Country not found
- 500: Internal server error

---

### 8. STATISTICS - GET /api/v1/statistics

**Descrição:** Obter estatísticas globais

**Example:** `GET /api/v1/statistics`

**Response (200):**
```json
{
  "total_countries": 250,
  "total_population": 8000000000,
  "total_area": 510100000.0,
  "average_population": 32000000.0,
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
      "total_area": 42000000.0
    }
  ]
}
```

---

### 9. REGIONS - GET /api/v1/regions

**Descrição:** Breakdown de estatísticas por região

**Example:** `GET /api/v1/regions`

**Response (200):**
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
    "total_area": 42000000.0
  }
]
```

---

### 10. DATA GAPS - GET /api/v1/data-gaps

**Descrição:** Identificar países com problemas de dados

**Example:** `GET /api/v1/data-gaps`

**Response (200):**
```json
{
  "total_countries": 250,
  "countries_with_issues": 15,
  "by_priority": {
    "critical": [
      {
        "id": 5,
        "name": "Afghanistan",
        "reason": "Invalid data: population (out of range), area (out of range)",
        "missing_fields": ["area", "latitude", "longitude"]
      }
    ],
    "high": [
      {
        "id": 10,
        "name": "Albania",
        "reason": "Missing: area, subregion"
      }
    ]
  }
}
```

---

### 11. VALIDATE - GET /api/v1/countries/{country_id}/validate

**Descrição:** Validar qualidade de dados de um país

**Path Parameters:**
```
country_id=1
```

**Example:** `GET /api/v1/countries/1/validate`

**Response (200):**
```json
{
  "country_id": 1,
  "name": "Brazil",
  "quality_score": 95.0,
  "quality_level": "complete",
  "priority": "low",
  "missing_fields": [],
  "relationships": {
    "languages": 1,
    "currencies": 1,
    "timezones": 3
  },
  "validation_reason": "All required and quality fields present"
}
```

**Errors:**
- 404: Country not found
- 500: Internal server error

---

### 12. SYNC - POST /api/v1/sync

**Descrição:** Disparar sincronização manual

**Example:** `POST /api/v1/sync`

**Response (200):**
```json
{
  "sync_id": "sync_manual",
  "status": "pending",
  "timestamp": "2026-09-16T10:30:00Z",
  "countries_inserted": 0,
  "countries_updated": 0,
  "countries_skipped": 0,
  "message": "Sync operation queued for background processing"
}
```

---

### 13. HEALTH - GET /api/v1/health

**Descrição:** Health check para monitoramento

**Example:** `GET /api/v1/health`

**Response (200):**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2026-09-16T10:30:00Z"
}
```

---

## 🔐 CÓDIGOS HTTP

| Código | Significado |
|--------|------------|
| 200 | OK - Requisição bem-sucedida |
| 201 | Created - Recurso criado com sucesso |
| 204 | No Content - Deletado com sucesso |
| 400 | Bad Request - Erro na requisição |
| 404 | Not Found - Recurso não encontrado |
| 409 | Conflict - Recurso já existe (duplicado) |
| 422 | Unprocessable Entity - Erro de validação |
| 500 | Internal Server Error - Erro do servidor |

---

## 🧪 EXEMPLOS DE USO (cURL)

### Criar país
```bash
curl -X POST http://localhost:8000/api/v1/countries \
  -H "Content-Type: application/json" \
  -d '{
    "name_common": "Brazil",
    "name_official": "Federative Republic of Brazil",
    "iso_code_2": "BR",
    "iso_code_3": "BRA",
    "region": "Americas",
    "population": 215000000,
    "area": 8514876.5,
    "latitude": -14.235,
    "longitude": -51.9253
  }'
```

### Listar países da Europa
```bash
curl "http://localhost:8000/api/v1/countries?page=1&limit=20&region=Europe"
```

### Obter país por ID
```bash
curl "http://localhost:8000/api/v1/countries/1"
```

### Obter país por ISO code
```bash
curl "http://localhost:8000/api/v1/countries/iso/BR"
```

### Atualizar população
```bash
curl -X PUT http://localhost:8000/api/v1/countries/1 \
  -H "Content-Type: application/json" \
  -d '{"population": 216000000}'
```

### Deletar país
```bash
curl -X DELETE http://localhost:8000/api/v1/countries/1
```

### Obter estatísticas
```bash
curl "http://localhost:8000/api/v1/statistics"
```

### Validar qualidade
```bash
curl "http://localhost:8000/api/v1/countries/1/validate"
```

### Health check
```bash
curl "http://localhost:8000/api/v1/health"
```

---

## 📚 SWAGGER AUTOMÁTICO

A documentação interativa está disponível em:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI Schema:** http://localhost:8000/openapi.json

---

## ⚡ BOAS PRÁTICAS

### Request Headers
```
Content-Type: application/json
Accept: application/json
```

### Status Code Pattern
- **2xx:** Sucesso
- **4xx:** Erro do cliente (validation, not found, conflict)
- **5xx:** Erro do servidor

### Pagination
- Default: page=1, limit=20
- Max limit: 100

### Filtering
- Suportado: region parameter
- Case-insensitive para ISO codes

---

## 🔧 INTEGRAÇÃO

### Em main.py
```python
from app.api.country_routes import router as country_router

app.include_router(country_router)
```

### Estrutura
```
app/
├── api/
│   ├── __init__.py
│   ├── country_routes.py    # Todos os endpoints
│   └── main_example.py      # Exemplo de integração
├── service/
├── database/
└── models/
```

---

**Documento versão 1.0 | Última atualização: 16/09/2026**  
**Status:** ✅ Implementado e Documentado
