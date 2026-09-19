# Arquitetura Técnica — PG genIA MVP-01
## REST Countries API & Dashboard

**Versão:** 2.0 (consolidada)
**Data:** 19/09/2026
**Status:** Backend em produção (0.1-beta) · Dashboard e automação em roadmap
**Documento anterior:** substitui e unifica `documentacoes/ARCHITECTURE.md` v1.0 (15/09) e `ARCHITECTURE.md` (raiz) v1.0 (17/09) — este arquivo é a **única fonte de verdade** para arquitetura do projeto (o stub de redirecionamento que existia na raiz foi removido em 19/09/2026; este é o único `ARCHITECTURE.md` do repositório).

---

## 0. Como ler este documento

Cada seção distingue explicitamente:
- ✅ **Implementado** — existe no código hoje e é validado por testes.
- 🔜 **Planejado** — decisão arquitetural tomada, ainda não implementado.

Isso evita a ambiguidade da versão anterior, em que dois documentos descreviam estados diferentes do sistema sem indicar qual era o real.

---

## 1. Visão Geral da Arquitetura

O backend implementado segue uma **arquitetura em camadas com padrão Repository**:

```
┌─────────────────────────────────────────────────────────┐
│                    HTTP CLIENT                           │
│         (curl, Postman, browser, futura dashboard)      │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│ API LAYER (FastAPI)                            ✅        │
│  • 15 endpoints REST (app/api/country_routes.py)         │
│  • Status codes: 200/201/204/404/409/422/500             │
│  • Validação Pydantic (input/output)                     │
│  • Swagger/OpenAPI (/docs, /redoc)                       │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│ SERVICE LAYER                                  ✅        │
│  • CountryService (regras de negócio)                    │
│  • PriorityAdvisor (quality scoring)                      │
│  • Tradução de exceções (DB → Domínio → HTTP)             │
│  • Injeção de dependência (FastAPI Depends)               │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│ REPOSITORY LAYER                               ✅        │
│  • CountryRepository (CRUD, queries, upsert em lote)      │
│  • StatisticsRepository (agregações)                      │
│  • Query builders (_base_query, _get_single_by_field)     │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│ DATA ACCESS (SQLAlchemy 2.0 ORM)               ✅        │
│  • Country, Language, Currency, Timezone                  │
│  • Relacionamentos 1:N (back_populates, cascade delete)    │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│ PERSISTENCE LAYER                              ✅        │
│  • SQLite (data/countries.db) — MVP                        │
│  • Índices: iso2, iso3, region, subregion                  │
│  • Migration path para PostgreSQL (não implementado)  🔜  │
└─────────────────────────────────────────────────────────┘
```

Componentes fora dessa cadeia (ingestão externa e apresentação) existem parcialmente:

- ✅ **Cliente HTTP de ingestão** (`app/api/rest_countries.py`) — busca e normaliza dados da REST Countries API, mas **não está conectado** ao endpoint `/api/v1/sync` nem a um agendador.
- 🔜 **Orquestração de ingestão fim-a-fim** (script CLI ligando fetch → normalize → `sync_countries_batch`) — não implementado (US-009 no backlog).
- 🔜 **Scheduler (APScheduler)** e **Dashboard (Streamlit)** — não implementados; ver Seção 10 (Roadmap).

---

## 2. C4 Model — Nível 1: Diagrama de Contexto

```mermaid
C4Context
    title Diagrama de Contexto — PG genIA MVP-01

    Person(user, "Usuário/Cliente", "Consome dados de países via HTTP (curl, Postman, browser, futura dashboard)")
    System(sistema, "PG genIA MVP-01", "API REST que ingere, persiste e expõe dados de países do mundo")
    System_Ext(restCountries, "REST Countries API", "https://restcountries.com — fonte pública de dados de países")

    Rel(user, sistema, "Consome/gerencia dados", "HTTPS/JSON")
    Rel(sistema, restCountries, "Busca dados de países", "HTTPS/JSON — GET /v3.1/all")
```

---

## 3. C4 Model — Nível 2: Diagrama de Contêineres

```mermaid
C4Container
    title Diagrama de Contêineres — PG genIA MVP-01

    Person(user, "Usuário/Cliente", "curl, Postman, browser")

    System_Boundary(sys, "PG genIA MVP-01") {
        Container(api, "API Backend", "FastAPI + Uvicorn", "15 endpoints REST, validação Pydantic, Swagger/ReDoc [IMPLEMENTADO]")
        Container(service, "Service Layer", "Python", "Regras de negócio, tradução de exceções [IMPLEMENTADO]")
        Container(repo, "Repository Layer", "SQLAlchemy 2.0", "Acesso a dados, queries, upsert em lote [IMPLEMENTADO]")
        ContainerDb(db, "Banco de Dados", "SQLite", "countries, languages, currencies, timezones [IMPLEMENTADO]")
        Container(ingest, "Cliente de Ingestão", "requests + Pydantic", "Fetch + normalize de países [IMPLEMENTADO, desconectado do sync]")
        Container(scheduler, "Scheduler", "APScheduler", "Sincronização diária automática [PLANEJADO — Release 0.2]")
        Container(dashboard, "Dashboard Web", "Streamlit", "KPIs, filtros, tabelas, gráficos [PLANEJADO — Release 0.2]")
    }

    System_Ext(restCountries, "REST Countries API", "Fonte externa de dados")

    Rel(user, api, "Requisições REST", "HTTP/JSON")
    Rel(user, dashboard, "Interação visual (planejado)", "HTTP")
    Rel(dashboard, api, "Consulta dados (planejado)", "HTTP/JSON")
    Rel(api, service, "Delega lógica de negócio")
    Rel(service, repo, "Consulta/persiste dados")
    Rel(repo, db, "SQL via ORM")
    Rel(scheduler, ingest, "Aciona ingestão (planejado)")
    Rel(scheduler, service, "Aciona sync_countries_batch (planejado)")
    Rel(ingest, restCountries, "GET /v3.1/all")
```

---

## 4. Diagrama de Componentes (Nível 3 — Backend Implementado)

```mermaid
graph TB
    subgraph "API Layer"
        ROUTES["FastAPI Routes<br/>(country_routes.py)"]
        HEALTH["Health Check<br/>(/health)"]
    end

    subgraph "Service Layer"
        SERVICE["CountryService<br/>(business logic)"]
        ADVISOR["PriorityAdvisor<br/>(quality scoring)"]
    end

    subgraph "Repository Layer"
        COUNTRY_REPO["CountryRepository<br/>(CRUD, queries, upsert)"]
        STATS_REPO["StatisticsRepository<br/>(aggregations)"]
    end

    subgraph "Data Access"
        ORM["SQLAlchemy Models<br/>(Country, Language, Currency, Timezone)"]
    end

    subgraph "Persistence"
        DB["SQLite Database<br/>(countries.db)"]
    end

    subgraph "Ingestão (desconectada do fluxo acima)"
        CLIENT["HTTP Client<br/>(rest_countries.py)"]
        EXT["REST Countries API<br/>(externa)"]
    end

    ROUTES -->|depends on| SERVICE
    HEALTH -->|depends on| SERVICE
    SERVICE -->|orchestrates| COUNTRY_REPO
    SERVICE -->|uses| ADVISOR
    SERVICE -->|uses| STATS_REPO
    COUNTRY_REPO -->|maps to| ORM
    STATS_REPO -->|queries via| ORM
    ORM -->|persists in| DB
    CLIENT -->|fetch| EXT
    CLIENT -.->|"não conectado ainda<br/>(gap: US-009)"| SERVICE

    classDef implemented fill:#50C878,stroke:#2D7A4A,color:#fff
    classDef gap fill:#F39C12,stroke:#C47E0B,color:#000

    class ROUTES,HEALTH,SERVICE,ADVISOR,COUNTRY_REPO,STATS_REPO,ORM,DB,CLIENT,EXT implemented
```

---

## 5. Diagrama de Sequência — Create Country (Implementado)

```mermaid
sequenceDiagram
    participant Client as HTTP Client
    participant API as API Layer
    participant Service as Service Layer
    participant Repo as Repository
    participant DB as SQLite DB

    Client->>API: POST /api/v1/countries
    Note over API: Validação Pydantic

    API->>Service: create_country(CountryCreate)
    Note over Service: Checa duplicidade ISO2/ISO3<br/>Aplica regras de negócio

    Service->>Repo: create(country_data)
    Note over Repo: Executa INSERT

    Repo->>DB: INSERT Country
    DB-->>Repo: Retorna com ID
    Repo-->>Service: Instância ORM Country
    Note over Service: Converte para schema<br/>usando _to_response()

    Service-->>API: CountryResponse
    API-->>Client: 201 Created + JSON
```

---

## 6. Diagrama de Sequência — Pipeline de Ingestão (Estado Real)

Mostra o estado atual: os dois metades do pipeline existem, mas **não há orquestração automática** conectando-as (gap coberto pela US-009 no roadmap).

```mermaid
sequenceDiagram
    participant Ext as REST Countries API
    participant Client as HTTP Client<br/>(rest_countries.py)
    participant Norm as Normalizer<br/>(mesmo módulo)
    participant Service as CountryService
    participant Repo as CountryRepository
    participant DB as SQLite DB

    rect rgb(220, 245, 225)
    Note over Ext,Norm: ✅ Implementado e testado
    Client->>Ext: GET /v3.1/all (retry 3x, timeout 30s)
    Ext-->>Client: JSON (250+ países)
    Client->>Norm: normalize_countries(raw_data)
    Norm-->>Client: List[NormalizedCountry]
    end

    rect rgb(255, 243, 205)
    Note over Client,Service: 🔜 Gap: sem orquestração automática (US-009)
    end

    rect rgb(220, 245, 225)
    Note over Service,DB: ✅ Implementado e testado (chamada manual/via testes)
    Service->>Repo: upsert_batch(countries_data)
    Repo->>DB: INSERT/UPDATE em lote
    DB-->>Repo: total, inserted, updated
    Repo-->>Service: resultado do batch
    end

    Note over Service: Endpoint POST /api/v1/sync hoje<br/>retorna apenas placeholder — não<br/>chama o Client nem o upsert_batch
```

---

## 7. Diagrama de Entidades (ER Model) — Implementado

```mermaid
erDiagram
    COUNTRIES ||--o{ LANGUAGES : speaks
    COUNTRIES ||--o{ CURRENCIES : uses
    COUNTRIES ||--o{ TIMEZONES : has

    COUNTRIES {
        int id PK
        string name_common UK
        string name_official
        string iso_code_2 UK
        string iso_code_3 UK
        string region
        string subregion
        bigint population
        decimal area
        decimal latitude
        decimal longitude
        timestamp created_at
        timestamp updated_at
    }

    LANGUAGES {
        int id PK
        int country_id FK
        string language_code
        string language_name
    }

    CURRENCIES {
        int id PK
        int country_id FK
        string currency_code
        string currency_name
    }

    TIMEZONES {
        int id PK
        int country_id FK
        string timezone_name
    }
```

Cascade delete habilitado (`ON DELETE CASCADE`) em todas as relações filhas.

---

## 8. Stack Tecnológico

### ✅ Implementado e em uso

| Camada | Tecnologia | Versão |
|---|---|---|
| Framework Web | FastAPI | 0.109.0 |
| Servidor ASGI | Uvicorn | 0.27.0 |
| ORM | SQLAlchemy | 2.0.23 |
| Banco de Dados | SQLite | built-in (sqlite3) |
| Validação de Dados | Pydantic | 2.5.0 |
| Configuração | pydantic-settings | 2.1.0 |
| Cliente HTTP (ingestão) | requests | 2.31.0 |
| Variáveis de Ambiente | python-dotenv | 1.0.0 |
| Utilitário de Datas | python-dateutil | 2.8.2 |
| Testes | pytest / pytest-cov / pytest-mock | 7.4.3 / 7.1.0 / 3.12.0 |
| Cliente de teste HTTP | httpx | 0.26.0 |
| Geração de dados de teste | Faker | 20.1.0 |
| Formatação | Black | 23.12.0 |
| Lint | Flake8 | 6.1.0 |
| Type Checking | mypy | 1.7.1 |

### 🔜 Instalado mas não integrado / planejado

| Camada | Tecnologia | Observação |
|---|---|---|
| Migrations | Alembic | 1.12.1 — listado em `requirements.txt`, sem migrations criadas; hoje o schema é criado via `Base.metadata.create_all()` |
| Frontend | Streamlit | 1.28.1 — listado em `requirements.txt`, nenhum módulo `app/streamlit/` existe ainda |
| Scheduler | APScheduler | não incluído em `requirements.txt` ainda; a incluir na Release 0.2 |
| Cache | Redis | não incluído; planejado para Release 0.2 |
| Banco (produção) | PostgreSQL | migration path preparado em `app/database/connection.py` (branch de configuração já existe), sem uso real |
| Deploy | Docker / Docker Compose / Nginx | não implementado |
| CI/CD | GitHub Actions | não implementado |
| Autenticação | JWT | não implementado |

---

## 9. Padrões de Design Implementados

### 9.1 Repository Pattern
Abstrai o acesso a dados da lógica de negócio.
```python
class CountryRepository:
    def _base_query(self):
        """Query base para todas as consultas de país."""
        return self.session.query(Country)

    def get_by_id(self, country_id: int) -> Optional[Country]:
        return self._get_single_by_field(Country.id, country_id)
```
Benefícios: testabilidade (mock do repository em testes de serviço), independência de banco (troca SQLite→PostgreSQL sem alterar service), responsabilidade única.

### 9.2 Service Layer Pattern
Orquestra lógica de negócio e repositórios; traduz exceções de banco em exceções de domínio.
```python
class CountryService:
    def create_country(self, country_data: CountryCreate) -> CountryResponse:
        existing = self.country_repo.get_by_iso2(country_data.iso_code_2)
        if existing:
            raise DuplicateRecordError("Country", "iso_code_2", country_data.iso_code_2)
        country = self.country_repo.create(country_data)
        return self._to_response(country)
```

### 9.3 Dependency Injection (FastAPI `Depends`)
```python
@router.post("/api/v1/countries")
def create_country(
    country_data: CountryCreate,
    service: CountryService = Depends(get_country_service),
):
    return service.create_country(country_data)
```

### 9.4 Query Builder Pattern (DRY)
`_base_query()`, `_get_single_by_field()`, `_get_paginated_query()` eliminam duplicação nas consultas do repository.

### 9.5 Response Mapper Pattern (SRP)
`_to_response()` e `_to_detail_response()` centralizam a conversão ORM → Pydantic no service layer; o repository sempre retorna objetos ORM crus.

---

## 10. Tratamento de Erros — Contrato HTTP

Hierarquia de exceções de domínio (`app/utils/errors.py`), todas derivadas de `ApplicationError`:

```
ApplicationError (base, error_code padrão)
├── DatabaseError
│   ├── DuplicateRecordError   → error_code DUPLICATE_RECORD
│   ├── RecordNotFoundError    → error_code NOT_FOUND
│   ├── IntegrityError         → error_code INTEGRITY_ERROR
│   └── TransactionError       → error_code TRANSACTION_ERROR
├── ValidationError            → error_code VALIDATION_ERROR
├── BatchProcessError          → error_code BATCH_ERROR
├── ExternalAPIError           → error_code EXTERNAL_API_ERROR
└── ConfigurationError         → error_code CONFIG_ERROR
```

Mapeamento para HTTP, aplicado em `app/api/country_routes.py` (try/except por endpoint):

| Exceção de domínio | HTTP Status | Quando ocorre |
|---|---|---|
| `DuplicateRecordError` | 409 Conflict | ISO2/ISO3 já existe |
| `RecordNotFoundError` | 404 Not Found | ID ou ISO code inexistente |
| Erro de validação Pydantic (schema) | 422 Unprocessable Entity | payload inválido |
| `ValidationError` (regra de negócio, ex: batch > 1000) | 422 Unprocessable Entity | ✅ corrigido em 19/09/2026 — tratado explicitamente em todas as rotas que chamam métodos de serviço capazes de lançá-lo |
| Qualquer outra exceção não tratada | 500 Internal Server Error | erro inesperado |

**Gap de contrato de erro:** a resposta de erro não segue um schema padronizado (`{error_code, message, details}`); hoje é apenas `{"detail": "<mensagem>"}` via `HTTPException`. Recomenda-se, na Release 0.2, criar um `ErrorResponse` (Pydantic) e um exception handler global (`@app.exception_handler(ApplicationError)`) para uniformizar o corpo de erro em todos os 15 endpoints.

---

## 11. Validações e Regras de Negócio

### Nível de Schema (Pydantic)
```python
iso_code_2: str = Field(..., min_length=2, max_length=2)
iso_code_3: str = Field(..., min_length=3, max_length=3)
population: int = Field(..., ge=0, le=2000000000)
latitude: Optional[float] = Field(None, ge=-90, le=90)
longitude: Optional[float] = Field(None, ge=-180, le=180)
# region validado via @field_validator -> {Africa, Americas, Asia, Europe, Oceania}
```

### Nível de Serviço
- Unicidade de ISO2/ISO3 antes de criar/atualizar.
- Limite de lote: máximo 1000 países por `sync_countries_batch`.
- Quality scoring via `PriorityAdvisor` (CRITICAL/HIGH/MEDIUM/LOW).

### Nível de Banco de Dados
```sql
UNIQUE (iso_code_2)
UNIQUE (iso_code_3)
CHECK (population >= 0)
CHECK (area >= 0)
CREATE INDEX idx_countries_iso2 ON Country(iso_code_2)
CREATE INDEX idx_countries_iso3 ON Country(iso_code_3)
CREATE INDEX idx_countries_region ON Country(region)
```

---

## 12. Configuração & Ambiente

### Variáveis de ambiente ativas (`.env`, ver `.env.example`)
```bash
DATABASE_URL=sqlite:///./data/countries.db
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=true
SQL_ECHO=false
LOG_LEVEL=INFO
LOG_DIR=./logs
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
FASTAPI_RELOAD=true
API_TIMEOUT=30
API_MAX_RETRIES=3
ENVIRONMENT=development
DEBUG=true
```

🔜 `STREAMLIT_SERVER_PORT` e `STREAMLIT_SERVER_HEADLESS` já constam em `.env.example` mas não têm consumidor no código (aguardando implementação do dashboard).

### Conexão com banco (`app/database/connection.py`)
Suporta dois perfis de engine, selecionados por prefixo da `DATABASE_URL`:
- **SQLite (atual):** `check_same_thread=False`, `PRAGMA foreign_keys=ON` habilitado via event listener.
- **PostgreSQL (preparado, não usado):** connection pooling completo (`pool_size`, `max_overflow`, `pool_recycle`, `pool_pre_ping`).

### FastAPI (`app/main.py`)
```python
app = FastAPI(
    title="REST Countries API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)
```

✅ **Corrigido em 19/09/2026:** `CORSMiddleware` configurado em `app/main.py`, com origens permitidas via variável de ambiente `CORS_ORIGINS` (lista separada por vírgula). Default cobre os servidores de desenvolvimento local (`localhost:8000` e `localhost:8501`, incluindo variantes `127.0.0.1`), pronto para a futura dashboard Streamlit.

---

## 13. Segurança & Autenticação

- ✅ Validação de entrada via Pydantic em todos os endpoints.
- ✅ Sem segredos hardcoded; configuração via `.env` (não versionado — ver `.gitignore`).
- ✅ **CORS:** configurado via `CORSMiddleware` (Seção 12), origens controladas por `CORS_ORIGINS`.
- 🔜 **Autenticação/Autorização:** nenhuma hoje — todos os 15 endpoints são públicos. API adequada apenas para uso interno/dev. Planejado JWT na Release 0.3 (ver Roadmap).
- 🔜 **Rate limiting:** não implementado; planejado para Release 0.2 junto com Redis cache.

Este é um gap crítico caso a API seja exposta fora do ambiente de desenvolvimento antes da Release 0.3 — deve ser tratado antes de qualquer deploy externo.

---

## 14. Testabilidade

Estado real na data deste documento (19/09/2026):

- **150 testes coletados** (`pytest --collect-only`), cobrindo unit (CRUD, cascade delete, paginação, batch sync, PriorityAdvisor, tratamento de erros de serviço) e integration (endpoints via `TestClient`).
- **Última medição de cobertura registrada:** 72% (COVERAGE_REPORT.md, 17/09/2026, quando havia 65 testes). Como a suíte cresceu para 150 testes desde então, **recomenda-se rodar `pytest --cov` novamente antes de reportar métricas** em vez de reusar o número de 17/09.
- Isolamento: banco SQLite in-memory por teste + rollback de transação.

---

## 15. Diagrama de Deployment

### 15.1 Ambiente Local (Atual) ✅

```mermaid
graph TB
    subgraph "Máquina do Desenvolvedor"
        VENV["Virtual Env<br/>Python 3.12.7"]
        FASTAPI["Uvicorn Dev Server<br/>http://localhost:8000<br/>Reload automático"]
        SQLITE["SQLite<br/>data/countries.db"]
    end

    VENV -->|pip install -r requirements.txt| FASTAPI
    FASTAPI -->|Read/Write| SQLITE

    style VENV fill:#4A90E2,stroke:#2E5C8A,color:#fff
    style FASTAPI fill:#7B68EE,stroke:#4A3FB5,color:#fff
    style SQLITE fill:#50C878,stroke:#2D7A4A,color:#fff
```

### 15.2 Ambiente Staging/Produção (Planejado — Release 0.2) 🔜

```mermaid
graph TB
    subgraph "Docker Host"
        subgraph "Docker Compose"
            NGINX["Nginx Reverse Proxy<br/>Port 80/443"]
            FASTAPI_C["FastAPI Container<br/>Port 8000"]
            STREAMLIT_C["Streamlit Container<br/>Port 8501"]
            SQLITE_V["SQLite Volume<br/>Persistido entre restarts"]
        end
        ENV[".env Configuration"]
    end

    NGINX -->|:8000| FASTAPI_C
    NGINX -->|:8501| STREAMLIT_C
    FASTAPI_C -->|Read/Write| SQLITE_V
    ENV -.->|Config| FASTAPI_C
    ENV -.->|Config| STREAMLIT_C

    style NGINX fill:#FF6B6B,stroke:#CC5555,color:#fff
    style FASTAPI_C fill:#7B68EE,stroke:#4A3FB5,color:#fff
    style STREAMLIT_C fill:#4A90E2,stroke:#2E5C8A,color:#fff
    style SQLITE_V fill:#50C878,stroke:#2D7A4A,color:#fff
    style ENV fill:#FFB347,stroke:#CC8A39,color:#000
```

### 15.3 CI/CD (Planejado — Release 0.2) 🔜

```mermaid
graph LR
    GIT["Push to main/master"]
    LINT["Lint: Black, Flake8, mypy"]
    TEST["Test: pytest, coverage >=80%"]
    BUILD["Build: docker build"]
    DEPLOY["Deploy: staging"]
    NOTIFY["Notify: Slack/Email"]

    GIT --> LINT
    LINT -->|Pass| TEST
    LINT -->|Fail| NOTIFY
    TEST -->|Pass| BUILD
    TEST -->|Fail| NOTIFY
    BUILD -->|Success| DEPLOY
    BUILD -->|Fail| NOTIFY
    DEPLOY --> NOTIFY

    style GIT fill:#FF6B6B,stroke:#CC5555,color:#fff
    style LINT fill:#FFB347,stroke:#CC8A39,color:#000
    style TEST fill:#50C878,stroke:#2D7A4A,color:#fff
    style BUILD fill:#4A90E2,stroke:#2E5C8A,color:#fff
    style DEPLOY fill:#7B68EE,stroke:#4A3FB5,color:#fff
    style NOTIFY fill:#2E9B57,stroke:#1A5A33,color:#fff
```

---

## 16. Roadmap Técnico (fonte única — substitui roadmaps divergentes anteriores)

### Release 0.1 — Backend Core (em andamento, ~40% do total de histórias)
- ✅ FastAPI com 15 endpoints REST (CRUD + estatísticas + quality scoring)
- ✅ SQLAlchemy 2.0 com relacionamentos e cascade delete
- ✅ Repository + Service layer com tratamento de exceções
- ✅ Cliente HTTP de ingestão (fetch + normalize) da REST Countries API
- 🔄 US-008/US-009: conectar ingestão → `sync_countries_batch` em um script/endpoint funcional (bloqueador atual)
- ✅ CORS configurado e mapeamento `ValidationError` → 422 corrigido (19/09/2026)
- 🔜 Padronizar contrato de erro HTTP unificado (`ErrorResponse` + exception handler global — Seção 10)

### Release 0.2 — Automação, Dashboard & Escala
- 🔜 Scheduler (APScheduler) para sincronização diária
- 🔜 Dashboard Streamlit (KPIs, filtros, tabelas, gráficos) consumindo a API
- 🔜 CORS configurado para suportar o dashboard
- 🔜 Cache (Redis) e rate limiting
- 🔜 Docker + Docker Compose + Nginx
- 🔜 CI/CD via GitHub Actions
- 🔜 Ajustar `CORS_ORIGINS` em produção para o domínio real do dashboard (hoje aponta para `localhost`)

### Release 0.3 — Segurança & Inteligência
- 🔜 Autenticação JWT
- 🔜 Histórico de mudanças (time-series)
- 🔜 Integração com Claude API (insights de IA)
- 🔜 Avaliar migração para PostgreSQL (opcional, path já preparado em `connection.py`)

---

## 17. Riscos Identificados

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Lentidão/instabilidade da REST Countries API | Média | Alto | Retry 3x + timeout já implementados no cliente; cache local ainda não |
| API exposta sem autenticação | Alta (se deploy antecipado) | Alto | Não expor externamente antes da Release 0.3 (JWT); CORS já restrito por origem (Seção 12) |
| Ingestão sem orquestração automática | Alta | Médio | Priorizar US-009 antes de qualquer sync em produção |
| Cobertura de testes desatualizada (72% de 17/09 para 150 testes atuais) | Certa | Baixo | Rodar `pytest --cov` e atualizar métricas antes do próximo reporte |

---

## 18. Documentos Relacionados

- **PRD:** `documentacoes/PRD_PG_genIA_MVP-01.md`
- **Backlog:** `documentacoes/BACKLOG_PG_genIA_MVP-01.md`
- **Rotas da API:** `documentacoes/API_ROUTES.md`
- **Camada de Serviço:** `documentacoes/SERVICE_LAYER.md`
- **Persistência:** `documentacoes/PERSISTENCE.md`
- **Histórico do projeto** (relatórios pontuais de sprints anteriores — status, cobertura, revisões técnicas, resumos de sessão): `documentacoes/historico/`

> O arquivo `ARCHITECTURE.md` na raiz do projeto foi convertido em um redirecionamento para este documento, eliminando a duplicidade anterior. Em 19/09/2026, os arquivos `.md` redundantes ou desatualizados que estavam soltos na raiz (API.md, PERSISTENCE_EXAMPLES/SUMMARY.md, SERVICE_LAYER_EXAMPLES/SUMMARY.md, COVERAGE_REPORT.md, QUALITY_CHECKLIST.md, REFACTORING_ANALYSIS.md, REVISAO_CHECKLIST.md, REVISAO_TECNICA.md, SESSION_SUMMARY_17-09-2026.md, STATUS_PROJECT.md, TESTS_SUMMARY.md) foram movidos para `documentacoes/historico/`. A raiz do projeto mantém apenas `README.md` e este redirecionamento de `ARCHITECTURE.md`.

---

## 19. Referências Externas

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Repository Pattern — Martin Fowler](https://martinfowler.com/eaaCatalog/repository.html)
- [C4 Model](https://c4model.com/)

---

**Documento versão 2.0 | Consolidado em: 19/09/2026**
**Substitui:** `documentacoes/ARCHITECTURE.md` v1.0 (15/09) e `ARCHITECTURE.md` raiz v1.0 (17/09)
**Próxima revisão:** ao concluir US-009 (orquestração de ingestão) ou início da Release 0.2
