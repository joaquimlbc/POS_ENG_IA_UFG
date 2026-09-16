# Camada de Serviço - Arquitetura em Camadas
## PG genIA MVP-01: REST Countries Dashboard

**Versão:** 1.0  
**Data:** 16 de Setembro de 2026  
**Arquiteto:** Arquiteto de Software Sênior  
**Status:** Implementado

---

## 1. VISÃO GERAL DA ARQUITETURA EM CAMADAS

```
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA DE APRESENTAÇÃO                   │
│  (FastAPI Endpoints / Controllers)                          │
│  - HTTP routing                                             │
│  - Request/Response serialization                           │
│  - Dependency injection                                     │
└─────────────────────────┬───────────────────────────────────┘
                          ↓ Dependency Injection
┌─────────────────────────────────────────────────────────────┐
│                  CAMADA DE SERVIÇO (Business Logic)         │
│  (CountryService, PriorityAdvisor)                          │
│  - Domain business rules                                    │
│  - Orchestration of operations                              │
│  - Data validation and transformation                       │
│  - Cross-cutting concerns                                   │
│  - Error handling (domain-specific)                         │
└─────────────────────────┬───────────────────────────────────┘
                          ↓ SessionLocal
┌─────────────────────────────────────────────────────────────┐
│              CAMADA DE PERSISTÊNCIA (Data Access)           │
│  (CountryRepository, StatisticsRepository)                  │
│  - CRUD operations                                          │
│  - Query construction                                       │
│  - Transaction management                                   │
│  - Database abstraction                                     │
└─────────────────────────┬───────────────────────────────────┘
                          ↓ SQL
┌─────────────────────────────────────────────────────────────┐
│                   CAMADA DE DADOS (ORM)                     │
│  (SQLAlchemy Models)                                        │
│  - ORM mapping                                              │
│  - Model definitions                                        │
│  - Relationships                                            │
└─────────────────────────┬───────────────────────────────────┘
                          ↓ Database Driver
┌─────────────────────────────────────────────────────────────┐
│                      BANCO DE DADOS                         │
│  (SQLite / PostgreSQL)                                      │
└─────────────────────────────────────────────────────────────┘
```

### Fluxo de Requisição (Request → Response)

```
1. HTTP Request
   ↓
2. FastAPI Route/Endpoint
   - Parse request
   - Validate input (Pydantic)
   - Inject dependencies (session)
   ↓
3. Service Layer (CountryService)
   - Apply business rules
   - Validate domain constraints
   - Orchestrate operations
   - Log business events
   ↓
4. Repository Layer (CountryRepository)
   - Translate service request to SQL
   - Execute CRUD operations
   - Handle database errors
   ↓
5. ORM & Database
   - Map database rows to models
   - Execute SQL
   ↓
6. Return Response
   - Transform to response schema
   - Serialize to JSON
   ↓
7. HTTP Response
```

---

## 2. RESPONSABILIDADES POR CAMADA

### 2.1 Camada de Apresentação (API)

**Responsabilidades:**
- HTTP routing e método mapping
- Request serialization (JSON → Pydantic models)
- Response serialization (models → JSON)
- Status code management
- Error response formatting
- Dependency injection
- CORS, authentication (futuro)

**NÃO faz:**
- Business logic
- Database queries
- Data transformation (além de serialização)
- Validation (além de Pydantic)

**Exemplo:**
```python
@app.post("/api/v1/countries")
def create_country(
    country_data: CountryCreate,
    session: Session = Depends(get_db_session)
):
    """API endpoint responsibility: HTTP protocol handling."""
    service = CountryService(session)
    try:
        result = service.create_country(country_data)
        return result
    except DuplicateRecordError as e:
        raise HTTPException(status_code=409, detail=e.message)
```

### 2.2 Camada de Serviço (Business Logic)

**Responsabilidades:**
- Implementar regras de negócio
- Orquestrar múltiplas operações de repository
- Validar constraints do domínio
- Transformar dados entre modelos
- Logging de eventos de negócio
- Error handling e conversão de exceções
- Caching e otimizações de negócio
- Decisões de negócio (prioridades, qualidade)

**NÃO faz:**
- HTTP handling
- SQL queries (delega ao repository)
- ORM mapping (usa modelos do ORM)

**Exemplo:**
```python
def create_country(self, country_data: CountryCreate) -> CountryResponse:
    """Service responsibility: business rule enforcement."""
    
    # Business rule: Check uniqueness
    existing = self.country_repo.get_by_iso2(country_data.iso_code_2)
    if existing:
        raise DuplicateRecordError(...)
    
    # Delegate data persistence to repository
    country = self.country_repo.create(country_data)
    
    # Log business event
    logger.info(f"Country created: {country.name_common}")
    
    # Transform to response
    return CountryResponse.model_validate(country)
```

### 2.3 Camada de Persistência (Repository)

**Responsabilidades:**
- CRUD operations (Create, Read, Update, Delete)
- Query construction e execução
- Transaction management (commit, rollback)
- Database error handling e conversão
- Lazy loading decisions
- Batch operations
- Data aggregation queries

**NÃO faz:**
- Business logic
- HTTP handling
- Response formatting

**Exemplo:**
```python
def create(self, country_data: CountryCreate) -> Country:
    """Repository responsibility: data persistence."""
    try:
        country = Country(**country_data.model_dump())
        self.session.add(country)
        self.session.commit()
        self.session.refresh(country)
        return country
    except SQLAlchemyIntegrityError as e:
        self.session.rollback()
        raise IntegrityError(...)
```

### 2.4 Camada de Dados (ORM)

**Responsabilidades:**
- Model definition e mapping
- Relationship configuration
- Constraints e validações do banco
- Type hints

**NÃO faz:**
- Query logic
- Transaction handling
- Business rules

---

## 3. COMPONENTES DA CAMADA DE SERVIÇO

### 3.1 CountryService

Serviço principal para operações com países.

**Métodos Principais:**

```python
class CountryService:
    # CRUD Operations
    create_country(country_data) → CountryResponse
    get_country(country_id) → CountryDetailResponse
    get_country_by_iso(iso_code) → CountryDetailResponse
    list_countries(page, limit, region) → CountryListResponse
    update_country(country_id, update_data) → CountryResponse
    delete_country(country_id) → bool
    
    # Batch Operations
    sync_countries_batch(countries_data) → CountrySyncResult
    
    # Statistics & Analysis
    get_global_statistics() → GlobalStatistics
    get_regional_breakdown() → List[RegionStatistics]
    identify_data_gaps() → dict
    
    # Relationship Management
    add_languages(country_id, languages) → CountryDetailResponse
    add_currencies(country_id, currencies) → CountryDetailResponse
    add_timezones(country_id, timezones) → CountryDetailResponse
    
    # Validation
    validate_country_integrity(country_id) → dict
```

**Características:**
- ✅ Orquestra múltiplas operações
- ✅ Aplica regras de negócio
- ✅ Logging estruturado
- ✅ Error handling específico do domínio
- ✅ Transações ACID

### 3.2 PriorityAdvisor

Advisor para decisões de priorização baseadas em qualidade de dados.

**Métodos Principais:**

```python
class PriorityAdvisor:
    assess_quality(country) → CountryQualityScore
    prioritize_updates(countries) → List[CountryQualityScore]
    assess_batch_quality(countries) → dict
    should_update_country(country, new_data) → bool
```

**Enums:**
- `SyncPriority`: CRITICAL, HIGH, MEDIUM, LOW
- `DataQuality`: COMPLETE, PARTIAL, INCOMPLETE, INVALID

**Exemplo de uso:**
```python
advisor = PriorityAdvisor()
score = advisor.assess_quality(country)
# score.priority → SyncPriority.HIGH
# score.quality_level → DataQuality.PARTIAL
# score.missing_fields → ["area", "subregion"]
```

---

## 4. FLUXOS DE NEGÓCIO

### 4.1 Criar País

```
API Endpoint
    ↓
CountryService.create_country(CountryCreate)
    ├─ Validação Pydantic (feita antes do service)
    ├─ Check business rule: ISO2 já existe?
    │  └─ Se sim: DuplicateRecordError
    ├─ Delegue ao repository: repository.create()
    ├─ Log sucesso
    └─ Retorne CountryResponse
```

### 4.2 Sincronizar Lote (Batch Upsert)

```
API Endpoint (sync)
    ↓
CountryService.sync_countries_batch(List[CountryCreate])
    ├─ Delegue ao repository: repository.upsert_batch()
    ├─ Assess batch quality: advisor.assess_batch_quality()
    ├─ Generate CountrySyncResult
    │  ├─ total, inserted, updated
    │  ├─ quality_summary
    │  └─ status (success/partial_failure)
    ├─ Log resultado
    └─ Retorne CountrySyncResult
```

### 4.3 Obter Estatísticas

```
API Endpoint
    ↓
CountryService.get_global_statistics()
    ├─ Delegue ao repository: stats_repo.get_global_stats()
    ├─ Delegue ao repository: stats_repo.get_regional_stats()
    ├─ Enriqueça dados com business logic
    └─ Retorne GlobalStatistics
```

### 4.4 Identificar Gaps de Dados

```
API Endpoint
    ↓
CountryService.identify_data_gaps()
    ├─ Fetch all countries: repository.get_all()
    ├─ Assess each: advisor.assess_quality()
    ├─ Prioritize: advisor.prioritize_updates()
    ├─ Group by priority level
    └─ Retorne report dict
```

---

## 5. PADRÕES E PRINCÍPIOS

### 5.1 Dependency Injection

**Service layer recebe dependências no construtor:**

```python
# No endpoint FastAPI
service = CountryService(session)

# Service não cria suas próprias dependências
# Recebe do chamador
def __init__(self, session: Session):
    self.session = session
    self.country_repo = CountryRepository(session)
    self.stats_repo = StatisticsRepository(session)
```

**Benefícios:**
- Testabilidade (injetar mock repository)
- Flexibilidade (trocar implementação)
- Separação de responsabilidades

### 5.2 Exception Handling

**Tradução de exceções por camada:**

```
Repository layer (SQLAlchemy)
    ↓
Traduz para exceções de domínio
SQLAlchemyIntegrityError → IntegrityError
    ↓
Service layer
    ↓
Propaga ou converte para domain exception
IntegrityError → DuplicateRecordError
    ↓
API layer
    ↓
Converte para HTTP status code
DuplicateRecordError → HTTPException(409)
```

**Exemplo:**
```python
# Repository
except SQLAlchemyIntegrityError as e:
    raise IntegrityError("Failed to create", str(e))

# Service
except IntegrityError as e:
    raise DuplicateRecordError("Country", "iso2", value)

# API
except DuplicateRecordError as e:
    raise HTTPException(status_code=409, detail=e.message)
```

### 5.3 Single Responsibility Principle

**Service:**
- Responsável APENAS por orchestração e regras de negócio
- NÃO executa SQL
- NÃO manipula HTTP

**Repository:**
- Responsável APENAS por data access
- NÃO implementa business logic
- NÃO trata HTTP

**API:**
- Responsável APENAS por HTTP protocol
- NÃO implementa business logic
- NÃO faz queries diretas

---

## 6. EXEMPLOS DE USO

### 6.1 Em Endpoint FastAPI

```python
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.database import get_db_session
from app.service import CountryService
from app.models.task import CountryCreate, CountryResponse

app = FastAPI()

@app.post("/api/v1/countries", response_model=CountryResponse)
def create_country(
    country_data: CountryCreate,
    session: Session = Depends(get_db_session)
):
    """API endpoint using service layer."""
    service = CountryService(session)
    return service.create_country(country_data)
```

### 6.2 Em Script/CLI

```python
from app.database import SessionLocal
from app.service import CountryService
from app.models.task import CountryCreate

# Manual usage without FastAPI
session = SessionLocal()
service = CountryService(session)

try:
    # Sync batch of countries
    result = service.sync_countries_batch(countries_data)
    print(f"Synced: {result.inserted} inserted, {result.updated} updated")
finally:
    session.close()
```

### 6.3 Testes Unitários

```python
import pytest
from unittest.mock import Mock
from app.service import CountryService

@pytest.fixture
def mock_repository():
    return Mock()

@pytest.fixture
def service(mock_repository):
    service = CountryService(Mock())
    service.country_repo = mock_repository
    return service

def test_create_country_duplicate(service):
    """Test duplicate country rejection."""
    # Mock repository to return existing country
    service.country_repo.get_by_iso2.return_value = Mock()
    
    with pytest.raises(DuplicateRecordError):
        service.create_country(country_data)
```

---

## 7. REGRAS DE PRIORIZAÇÃO (PriorityAdvisor)

### 7.1 Scoring de Qualidade

```
Campos Obrigatórios:
  - name_common, name_official, iso2, iso3, region, population
  - Cada um faltando: -20 pontos

Campos de Qualidade:
  - area, latitude, longitude, subregion
  - Cada um faltando: -10 pontos

Validações de Range:
  - Population fora de range: -15 pontos
  - Area fora de range: -10 pontos
  - Latitude/Longitude inválidas: -10 pontos

Score Final: 0-100
  - 90+: COMPLETE
  - 70-89: PARTIAL
  - 50-69: INCOMPLETE
  - <50: INVALID
```

### 7.2 Prioridade de Sincronização

```
Quality Level     Priority    Reason
─────────────────────────────────────
INVALID           CRITICAL    Requer correção imediata
INCOMPLETE        HIGH        Faltam campos obrigatórios
PARTIAL + rels    LOW         Dados OK, relacionamentos OK
PARTIAL + sem rels MEDIUM     Faltam dados de qualidade
```

### 7.3 Decisão de Update

```
Deve atualizar se:
  ✅ Dados atuais INVALID ou INCOMPLETE
  ✅ Nova área ou coordenadas presentes e faltando
  ✅ População mudou >5%
```

---

## 8. LOGGING DE OPERAÇÕES

### 8.1 Níveis de Log

```
DEBUG  - Detalhes internos de operação
INFO   - Operações completadas com sucesso
WARNING - Situações incomuns (duplicata, missing data)
ERROR  - Falhas de operação (DB error, validation failed)
```

### 8.2 Exemplos

```python
# SUCCESS
logger.info(f"Country created: {country.name_common} (id={country.id})")

# WARNING
logger.warning(f"Duplicate country: {iso2}")

# ERROR
logger.error(f"Failed to upsert batch: {e}")

# Business event
logger.info(f"Batch sync {sync_id} completed: {inserted} inserted, {updated} updated")
```

---

## 9. PERFORMANCE & OTIMIZAÇÕES

### 9.1 Lazy Loading

**ORM configurado com `lazy="selectin"`:**
```python
languages: Mapped[List["Language"]] = relationship(
    lazy="selectin"  # Carrega relacionamentos em SELECT único
)
```

**Benefício:** Evita N+1 queries

### 9.2 Caching de Serviço

**Futuro: Implementar cache na service layer:**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_statistics(self):
    # Cache 100 últimas requisições
    return self.stats_repo.get_global_stats()
```

### 9.3 Batch Operations

**Inserção em lote (não 1 por 1):**
```python
# ✅ BOM: Single commit
session.add_all(countries)
session.commit()

# ❌ RUIM: N commits
for country in countries:
    session.add(country)
    session.commit()  # Lento!
```

---

## 10. TESTES

### 10.1 Estrutura de Testes

```
tests/
├── unit/
│   ├── test_country_service.py
│   └── test_priority_advisor.py
└── integration/
    └── test_country_service_integration.py
```

### 10.2 Teste Unitário (com Mocks)

```python
def test_create_country_duplicate(service_with_mocks):
    service_with_mocks.country_repo.get_by_iso2.return_value = Mock()
    
    with pytest.raises(DuplicateRecordError):
        service_with_mocks.create_country(data)
```

### 10.3 Teste de Integração (com DB)

```python
def test_create_country_real_db(service_with_real_db):
    result = service_with_real_db.create_country(data)
    
    assert result.id is not None
    assert result.name_common == "Test"
```

---

## 11. MIGRATION PATH

### Service Layer não muda ao migrar DB

Quando migrar SQLite → PostgreSQL:

```
ANTES (SQLite)
├─ App → Service → Repository → SQLite

DEPOIS (PostgreSQL)
├─ App → Service → Repository → PostgreSQL

# Service layer IDÊNTICO
# Repository layer (mínimas mudanças)
# Database URL muda em .env
```

---

## 12. CHECKLIST DE IMPLEMENTAÇÃO

- [x] CountryService com CRUD
- [x] CountryService com batch operations
- [x] CountryService com statistics
- [x] CountryService com validação de integridade
- [x] PriorityAdvisor com scoring
- [x] PriorityAdvisor com priorização
- [x] PriorityAdvisor com decisões de update
- [x] Exception handling (domain-specific)
- [x] Logging estruturado
- [x] Documentação completa

---

## 13. PRÓXIMOS PASSOS

### Para Release 0.1
1. [ ] Integrar CountryService em todos endpoints FastAPI
2. [ ] Escrever testes unitários (80%+ coverage)
3. [ ] Implementar exception handlers em FastAPI
4. [ ] Setup CI/CD para testes

### Para Release 0.2
1. [ ] Cache layer (Redis) na service
2. [ ] Query optimization com explain plans
3. [ ] Service para relacionamentos (Languages, Currencies)

### Para Release 0.3
1. [ ] Audit service (track changes)
2. [ ] Notification service
3. [ ] Search service

---

## 14. REFERÊNCIAS

- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
- [Service Layer Pattern](https://martinfowler.com/eaaCatalog/serviceLayer.html)
- [Dependency Injection](https://martinfowler.com/articles/injection.html)

---

**Documento versão 1.0 | Última atualização: 16/09/2026**  
**Responsável:** Arquiteto de Software Sênior  
**Status:** ✅ Implementado
