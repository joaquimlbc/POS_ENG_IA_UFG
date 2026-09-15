# Arquitetura Técnica
## PG genIA MVP-01: REST Countries Dashboard

**Versão:** 1.0  
**Data:** 15 de Setembro de 2026  
**Arquiteto:** Arquiteto de Software Sênior  
**Status:** Proposta Técnica  

---

## 1. VISÃO GERAL DA ARQUITETURA

### 1.1 Padrão Arquitetural

A solução segue um padrão **Client-Server com camadas** otimizado para MVP:

```
┌─────────────────────────────────────────────────────────┐
│                   CAMADA DE APRESENTAÇÃO                │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Frontend: Streamlit Dashboard (Browser)         │   │
│  │ - Visualização interativa                       │   │
│  │ - KPIs, Filtros, Tabelas, Gráficos             │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                        ↓ HTTP/REST
┌─────────────────────────────────────────────────────────┐
│                   CAMADA DE NEGÓCIO                      │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Backend: FastAPI Server (Uvicorn)              │   │
│  │ - Health Check (/health)                       │   │
│  │ - Data Ingestion Orchestrator                  │   │
│  │ - Scheduled Sync (APScheduler)                 │   │
│  │ - API Endpoints (v0.2+)                        │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                        ↓ SQL
┌─────────────────────────────────────────────────────────┐
│                   CAMADA DE DADOS                        │
│  ┌──────────────────────────┐                           │
│  │ ORM: SQLAlchemy 2.0      │                           │
│  │ - Modelos de dados       │                           │
│  │ - Relacionamentos        │                           │
│  │ - Migrations (Alembic)   │                           │
│  └──────────────────────────┘                           │
│            ↓                                             │
│  ┌──────────────────────────┐                           │
│  │ Database: SQLite         │                           │
│  │ - countries              │                           │
│  │ - languages              │                           │
│  │ - currencies             │                           │
│  │ - timezones              │                           │
│  └──────────────────────────┘                           │
└─────────────────────────────────────────────────────────┘
                        ↓ HTTP
┌─────────────────────────────────────────────────────────┐
│              INTEGRAÇÕES EXTERNAS                        │
│  ┌──────────────────────────┐                           │
│  │ REST Countries API       │                           │
│  │ https://restcountries.com│                           │
│  └──────────────────────────┘                           │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Decisões Arquiteturais Principais

| Decisão | Escolha | Justificativa |
|---------|---------|---------------|
| **Framework Web** | FastAPI | Performance (2x+ rápido que Django), async-native, OpenAPI automático |
| **ORM** | SQLAlchemy 2.0 | Type hints, relacionamentos, migrations com Alembic |
| **Banco de Dados** | SQLite | MVP rápido, sem infra, migration path para PostgreSQL |
| **Frontend** | Streamlit | Prototipagem rápida, sem HTML/CSS, Python-first |
| **Web Server** | Uvicorn | ASGI, performance, integração FastAPI nativa |
| **Scheduler** | APScheduler | Python-native, suporta agendamento complexo |
| **Deployment** | Docker + Docker Compose | Reprodutibilidade, separação de ambientes |

---

## 2. DIAGRAMA DE COMPONENTES

```mermaid
graph TB
    subgraph "Frontend Layer"
        STREAMLIT["🎨 Streamlit Dashboard<br/>(app.py)<br/>- KPIs<br/>- Filters<br/>- Tables<br/>- Charts"]
    end

    subgraph "Application Layer"
        FASTAPI["⚡ FastAPI Server<br/>(app/main.py)<br/>- Health Check<br/>- CORS<br/>- Swagger/ReDoc"]
        SCHEDULER["📅 APScheduler<br/>- Daily Sync<br/>- Retry Logic"]
        ORCHESTRATOR["🔄 Data Orchestrator<br/>- fetch_countries()<br/>- normalize_data()<br/>- save_to_db()"]
    end

    subgraph "Data Layer"
        SQLALCHEMY["🗄️ SQLAlchemy ORM<br/>(database/models.py)<br/>- Country<br/>- Language<br/>- Currency<br/>- Timezone"]
        ALEMBIC["🔧 Alembic<br/>- Schema Management<br/>- Migrations"]
    end

    subgraph "Persistence Layer"
        SQLITE["💾 SQLite Database<br/>(data/countries.db)<br/>- 4 tabelas normalizadas<br/>- Índices otimizados<br/>- Constraints"]
    end

    subgraph "External APIs"
        REST_API["🌐 REST Countries API<br/>https://restcountries.com<br/>GET /v3.1/all"]
    end

    subgraph "Utilities & Support"
        API_CLIENT["🔌 HTTP Client<br/>(api/rest_countries.py)<br/>- fetch_countries()<br/>- normalize_countries()<br/>- Error handling"]
        CONFIG["⚙️ Configuration<br/>(.env)<br/>- DB_URL<br/>- API_TIMEOUT<br/>- LOG_LEVEL"]
        LOGGER["📝 Logging<br/>- Structured logs<br/>- Error tracking"]
    end

    %% Connections
    STREAMLIT -->|Query Data| FASTAPI
    FASTAPI -->|Query| SQLALCHEMY
    SCHEDULER -->|Trigger| ORCHESTRATOR
    ORCHESTRATOR -->|Use| API_CLIENT
    API_CLIENT -->|Fetch| REST_API
    API_CLIENT -->|Normalize & Save| ORCHESTRATOR
    ORCHESTRATOR -->|Persist| SQLALCHEMY
    SQLALCHEMY -->|SQL| SQLITE
    SQLALCHEMY -->|Manage Schema| ALEMBIC
    ALEMBIC -->|Apply Migrations| SQLITE
    FASTAPI -.->|Config| CONFIG
    FASTAPI -.->|Log| LOGGER
    ORCHESTRATOR -.->|Log| LOGGER

    classDef frontend fill:#4A90E2,stroke:#2E5C8A,color:#fff
    classDef application fill:#7B68EE,stroke:#4A3FB5,color:#fff
    classDef data fill:#50C878,stroke:#2D7A4A,color:#fff
    classDef external fill:#FF6B6B,stroke:#CC5555,color:#fff
    classDef utility fill:#FFB347,stroke:#CC8A39,color:#000

    class STREAMLIT frontend
    class FASTAPI,SCHEDULER,ORCHESTRATOR application
    class SQLALCHEMY,ALEMBIC data
    class SQLITE persistence
    class REST_API external
    class API_CLIENT,CONFIG,LOGGER utility
```

---

## 3. DIAGRAMA DE FLUXO DE DADOS

### 3.1 Ingestão de Dados (ETL Pipeline)

```mermaid
graph LR
    A["📡 REST Countries API"] -->|HTTP GET /v3.1/all| B["🔌 HTTP Client<br/>rest_countries.py"]
    B -->|250+ registros brutos| C["🔄 Normalize Module<br/>Transformação"]
    C -->|Validação Pydantic| D{"Dados<br/>Válidos?"}
    D -->|Não| E["❌ Log Erro<br/>Rejeitar"]
    D -->|Sim| F["💾 Insert/Update<br/>SQLAlchemy"]
    F -->|SQL INSERT/UPDATE| G["🗄️ SQLite DB<br/>countries.db"]
    G -->|Commit| H["✅ Success Log<br/>X países inseridos"]
    E -->|⚠️ Error Log<br/>Continuar| H

    style A fill:#FF6B6B,stroke:#CC5555,color:#fff
    style B fill:#4A90E2,stroke:#2E5C8A,color:#fff
    style C fill:#7B68EE,stroke:#4A3FB5,color:#fff
    style D fill:#FFB347,stroke:#CC8A39,color:#000
    style F fill:#50C878,stroke:#2D7A4A,color:#fff
    style G fill:#2E9B57,stroke:#1A5A33,color:#fff
```

### 3.2 Scheduler de Sincronização

```mermaid
graph TB
    START["⏰ Agendador APScheduler"]
    CRON["00:00 UTC Diariamente"]
    CHECK["🔍 Verificar mudanças<br/>(timestamp, versão)"]
    FETCH["📡 Consumir API<br/>REST Countries"]
    NORMALIZE["🔄 Normalizar dados<br/>Validar schema"]
    MERGE["🔀 Merge Strategy<br/>INSERT OR REPLACE"]
    PERSIST["💾 Persistir em DB<br/>Transação"]
    LOG_OK["✅ Log sucesso<br/>Timestamp, quantidade"]
    LOG_FAIL["❌ Log falha<br/>Retentar (max 3x)"]
    FALLBACK["🔒 Usar cache local<br/>Última ingestão bem-sucedida"]

    START --> CRON
    CRON --> CHECK
    CHECK --> FETCH
    FETCH -->|API OK| NORMALIZE
    FETCH -->|API Indisponível| FALLBACK
    NORMALIZE -->|Dados válidos| MERGE
    NORMALIZE -->|Erro validação| LOG_FAIL
    MERGE --> PERSIST
    PERSIST -->|Sucesso| LOG_OK
    PERSIST -->|Erro DB| LOG_FAIL
    LOG_FAIL --> FALLBACK
    FALLBACK --> END["📊 Dashboard usa<br/>dados do cache"]

    style START fill:#FFB347,stroke:#CC8A39,color:#000
    style CRON fill:#FFB347,stroke:#CC8A39,color:#000
    style CHECK fill:#4A90E2,stroke:#2E5C8A,color:#fff
    style FETCH fill:#FF6B6B,stroke:#CC5555,color:#fff
    style NORMALIZE fill:#7B68EE,stroke:#4A3FB5,color:#fff
    style MERGE fill:#7B68EE,stroke:#4A3FB5,color:#fff
    style PERSIST fill:#50C878,stroke:#2D7A4A,color:#fff
    style LOG_OK fill:#2E9B57,stroke:#1A5A33,color:#fff
    style LOG_FAIL fill:#E74C3C,stroke:#B93C2A,color:#fff
    style FALLBACK fill:#F39C12,stroke:#C47E0B,color:#fff
```

### 3.3 Fluxo de Requisição do Dashboard

```mermaid
graph TB
    USER["👤 Usuário<br/>Browser"]
    STREAMLIT["🎨 Streamlit App<br/>Renderiza UI"]
    FILTER["🔍 Aplica Filtro<br/>Região/Busca"]
    QUERY["📖 Query DB<br/>SQLAlchemy"]
    SQLITEDB["🗄️ SQLite<br/>Retorna Dados"]
    PROCESS["⚙️ Processa<br/>Formata números"]
    RENDER["🎨 Renderiza<br/>KPIs, Tabelas, Gráficos"]
    DISPLAY["📊 Exibe Dashboard<br/>Atualizado"]

    USER -->|Interage| STREAMLIT
    STREAMLIT -->|onChange Filter| FILTER
    FILTER -->|Filtra países| QUERY
    QUERY -->|SELECT * FROM| SQLITEDB
    SQLITEDB -->|Retorna rows| PROCESS
    PROCESS -->|Formata dados| RENDER
    RENDER -->|Atualiza componentes| DISPLAY
    DISPLAY -->|Exibe para| USER

    style USER fill:#4A90E2,stroke:#2E5C8A,color:#fff
    style STREAMLIT fill:#7B68EE,stroke:#4A3FB5,color:#fff
    style FILTER fill:#FFB347,stroke:#CC8A39,color:#000
    style QUERY fill:#50C878,stroke:#2D7A4A,color:#fff
    style SQLITEDB fill:#2E9B57,stroke:#1A5A33,color:#fff
    style PROCESS fill:#50C878,stroke:#2D7A4A,color:#fff
    style RENDER fill:#7B68EE,stroke:#4A3FB5,color:#fff
    style DISPLAY fill:#4A90E2,stroke:#2E5C8A,color:#fff
```

---

## 4. DIAGRAMA DE SEQUÊNCIA - Ingestão Completa

```mermaid
sequenceDiagram
    participant Scheduler as APScheduler
    participant API_Client as REST Countries Client
    participant Normalize as Data Normalizer
    participant ORM as SQLAlchemy ORM
    participant DB as SQLite Database

    Scheduler->>API_Client: fetch_countries()
    activate API_Client
    API_Client->>API_Client: Retry Logic (max 3x)
    API_Client->>API_Client: Timeout 30s
    API_Client-->>Scheduler: 250+ raw countries (JSON)
    deactivate API_Client

    Scheduler->>Normalize: normalize_countries(raw_data)
    activate Normalize
    Normalize->>Normalize: Extract fields (name, iso, region...)
    Normalize->>Normalize: Validate Pydantic v2
    Normalize-->>Scheduler: [Country, Country, ...]
    deactivate Normalize

    Scheduler->>ORM: save_countries(normalized)
    activate ORM
    ORM->>ORM: Start Transaction
    ORM->>ORM: Build INSERT/UPDATE statements
    ORM->>DB: Execute SQL batch
    activate DB
    DB->>DB: Apply constraints (FK, unique)
    DB-->>ORM: Commit successful
    deactivate DB
    ORM-->>Scheduler: ✅ 250 inserted/updated
    deactivate ORM

    Scheduler->>Scheduler: Log success (timestamp, count)
    Note over Scheduler: Next run: tomorrow 00:00 UTC
```

---

## 5. DIAGRAMA DE SEQUÊNCIA - Dashboard Query

```mermaid
sequenceDiagram
    participant User as User<br/>Browser
    participant Streamlit as Streamlit<br/>Frontend
    participant FastAPI as FastAPI<br/>Backend
    participant ORM as SQLAlchemy<br/>ORM
    participant DB as SQLite<br/>Database

    User->>Streamlit: Seleciona região "Europe"
    activate Streamlit
    Streamlit->>Streamlit: Update session state
    Streamlit->>Streamlit: Build query params

    Streamlit->>FastAPI: GET /api/countries?region=Europe (v0.2+)
    activate FastAPI
    FastAPI->>ORM: Query countries WHERE region='Europe'
    activate ORM
    ORM->>DB: SELECT * FROM countries WHERE region='Europe'
    activate DB
    DB-->>ORM: 50 rows
    deactivate DB
    ORM->>ORM: Hydrate Country objects
    ORM-->>FastAPI: [Country(...), ...]
    deactivate ORM

    FastAPI->>FastAPI: Convert to JSON
    FastAPI-->>Streamlit: JSON response (50 countries)
    deactivate FastAPI

    Streamlit->>Streamlit: Process data
    Streamlit->>Streamlit: Format (numbers, dates)
    Streamlit->>Streamlit: Update DataFrame
    Streamlit->>Streamlit: Render KPIs (atualizar)
    Streamlit->>Streamlit: Render Table
    Streamlit->>Streamlit: Render Charts

    Streamlit-->>User: Dashboard atualizado
    deactivate Streamlit
```

---

## 6. DIAGRAMA DE DEPLOYMENT

### 6.1 Ambiente Local (Desenvolvimento)

```mermaid
graph TB
    subgraph "Local Developer Machine"
        VSCode["📝 VS Code<br/>Git + Claude Code"]
        VENV["🐍 Virtual Env<br/>Python 3.11"]
        FASTAPI["⚡ FastAPI Dev<br/>http://localhost:8000<br/>Reload automático"]
        STREAMLIT["🎨 Streamlit Dev<br/>http://localhost:8501<br/>Reload automático"]
        SQLITE["💾 SQLite Dev<br/>data/countries.db"]
    end

    VSCode -->|Código Python| VENV
    VENV -->|pip install -r requirements.txt| FASTAPI
    VENV -->|pip install -r requirements.txt| STREAMLIT
    FASTAPI -->|Read/Write| SQLITE
    STREAMLIT -->|Query| FASTAPI

    style VSCode fill:#2E2E2E,stroke:#666,color:#fff
    style VENV fill:#4A90E2,stroke:#2E5C8A,color:#fff
    style FASTAPI fill:#7B68EE,stroke:#4A3FB5,color:#fff
    style STREAMLIT fill:#FF6B6B,stroke:#CC5555,color:#fff
    style SQLITE fill:#50C878,stroke:#2D7A4A,color:#fff
```

### 6.2 Ambiente Staging/Produção (Docker Compose)

```mermaid
graph TB
    subgraph "Docker Host"
        subgraph "Docker Compose"
            NGINX["🔀 Nginx Reverse Proxy<br/>Port 80/443<br/>- Rota /api → FastAPI<br/>- Rota / → Streamlit"]
            
            FASTAPI_CONTAINER["⚡ FastAPI Container<br/>Port 8000<br/>- uvicorn app.main:app<br/>- Health check"]
            
            STREAMLIT_CONTAINER["🎨 Streamlit Container<br/>Port 8501<br/>- streamlit run app.py<br/>- Port 8501"]
            
            SQLITE_VOLUME["💾 SQLite Volume<br/>data/countries.db<br/>- Persistido entre restarts<br/>- Backup diário"]
        end
        
        ENV[".env Configuration<br/>- DATABASE_URL<br/>- STREAMLIT_CONFIG<br/>- API_TIMEOUT"]
    end

    NGINX -->|:8000| FASTAPI_CONTAINER
    NGINX -->|:8501| STREAMLIT_CONTAINER
    FASTAPI_CONTAINER -->|Read/Write| SQLITE_VOLUME
    ENV -.->|Config| FASTAPI_CONTAINER
    ENV -.->|Config| STREAMLIT_CONTAINER

    style NGINX fill:#FF6B6B,stroke:#CC5555,color:#fff
    style FASTAPI_CONTAINER fill:#7B68EE,stroke:#4A3FB5,color:#fff
    style STREAMLIT_CONTAINER fill:#4A90E2,stroke:#2E5C8A,color:#fff
    style SQLITE_VOLUME fill:#50C878,stroke:#2D7A4A,color:#fff
    style ENV fill:#FFB347,stroke:#CC8A39,color:#000
```

### 6.3 CI/CD Pipeline (GitHub Actions)

```mermaid
graph LR
    GIT["📦 Push to<br/>main/master<br/>GitHub"]
    LINT["🔍 Lint Stage<br/>- Black<br/>- Flake8<br/>- mypy"]
    TEST["🧪 Test Stage<br/>- pytest<br/>- coverage ≥80%<br/>- integration"]
    BUILD["🐳 Build Stage<br/>- docker build<br/>- tag image"]
    DEPLOY["🚀 Deploy Stage<br/>- docker push<br/>- deploy staging"]
    NOTIFY["📢 Notify<br/>Slack/Email<br/>Success/Failure"]

    GIT -->|Trigger| LINT
    LINT -->|✅ Pass| TEST
    LINT -->|❌ Fail| NOTIFY
    TEST -->|✅ Pass| BUILD
    TEST -->|❌ Fail| NOTIFY
    BUILD -->|✅ Success| DEPLOY
    BUILD -->|❌ Fail| NOTIFY
    DEPLOY -->|✅ Success| NOTIFY

    style GIT fill:#FF6B6B,stroke:#CC5555,color:#fff
    style LINT fill:#FFB347,stroke:#CC8A39,color:#000
    style TEST fill:#50C878,stroke:#2D7A4A,color:#fff
    style BUILD fill:#4A90E2,stroke:#2E5C8A,color:#fff
    style DEPLOY fill:#7B68EE,stroke:#4A3FB5,color:#fff
    style NOTIFY fill:#2E9B57,stroke:#1A5A33,color:#fff
```

---

## 7. DIAGRAMA DE ENTIDADES (ER Model)

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

---

## 8. DECISÕES TÉCNICAS PRINCIPAIS

### 8.1 Por que FastAPI?

```
┌──────────────────────────────────────────────────────┐
│ FastAPI vs Alternativas (Release 0.1)               │
├──────────────────┬─────────┬─────────┬──────────────┤
│ Critério         │ FastAPI │ Django  │ Flask        │
├──────────────────┼─────────┼─────────┼──────────────┤
│ Startup Time     │ ⚡⚡⚡   │ ⚡      │ ⚡⚡⚡       │
│ Performance      │ ⚡⚡⚡   │ ⚡      │ ⚡⚡         │
│ Type Hints       │ ⚡⚡⚡   │ ⚡      │ ❌           │
│ OpenAPI Auto     │ ⚡⚡⚡   │ ⚡      │ ❌           │
│ Async Native     │ ⚡⚡⚡   │ ⚡      │ ⚡⚡         │
│ Learning Curve   │ ⚡⚡     │ ⚡      │ ⚡⚡⚡       │
│ Ecosystem        │ ⚡⚡     │ ⚡⚡⚡   │ ⚡⚡⚡       │
└──────────────────┴─────────┴─────────┴──────────────┘

✅ VENCEDOR: FastAPI (performance + DX)
```

### 8.2 Por que SQLite em MVP?

```
┌──────────────────────────────────────────────────────┐
│ SQLite vs Alternativas (Release 0.1)                │
├──────────────────┬──────────┬──────────┬────────────┤
│ Critério         │ SQLite   │ Postgres │ MySQL      │
├──────────────────┼──────────┼──────────┼────────────┤
│ Setup Tempo      │ ⚡⚡⚡    │ ⚡       │ ⚡         │
│ Dependências     │ ⚡⚡⚡    │ ⚡       │ ⚡         │
│ Custo (Dev)      │ ⚡⚡⚡    │ ⚡       │ ⚡         │
│ Escalabilidade   │ ⚡ (MVP) │ ⚡⚡⚡    │ ⚡⚡⚡      │
│ Migration Path   │ ⚡⚡⚡    │ ⚡⚡⚡    │ ⚡⚡⚡      │
│ Características  │ ⚡⚡     │ ⚡⚡⚡    │ ⚡⚡       │
└──────────────────┴──────────┴──────────┴────────────┘

✅ MVP: SQLite (rápido + simplicidade)
🔜 Produção: PostgreSQL (escalabilidade)
```

### 8.3 Por que Streamlit?

```
┌──────────────────────────────────────────────────────┐
│ Streamlit vs Alternativas (Release 0.1)             │
├──────────────────┬───────────┬──────────┬──────────┤
│ Critério         │ Streamlit │ Plotly   │ Dash     │
├──────────────────┼───────────┼──────────┼──────────┤
│ Setup Tempo      │ ⚡⚡⚡     │ ⚡⚡      │ ⚡       │
│ Time-to-MVP      │ ⚡⚡⚡     │ ⚡⚡      │ ⚡       │
│ Code Simplicity  │ ⚡⚡⚡     │ ⚡⚡      │ ⚡       │
│ Customização     │ ⚡         │ ⚡⚡⚡     │ ⚡⚡⚡     │
│ Performance      │ ⚡⚡       │ ⚡⚡⚡     │ ⚡⚡      │
│ HTML/CSS Required│ ❌        │ ⚡⚡⚡     │ ⚡⚡⚡     │
└──────────────────┴───────────┴──────────┴──────────┘

✅ MVP: Streamlit (Python-first, rápido)
🔜 Produção: React + Recharts (customização)
```

---

## 9. FLUXOS DE INTEGRAÇÃO

### 9.1 Integração Frontend-Backend

```mermaid
graph TB
    subgraph "Frontend (Streamlit)"
        IMPORT["import requests"]
        CONFIG["BACKEND_URL<br/>= http://localhost:8000"]
    end
    
    subgraph "Backend (FastAPI)"
        CORS["@app.middleware<br/>CORS"]
        ENDPOINTS["@app.get('/api/v1/...')<br/>Endpoints"]
    end
    
    IMPORT -->|requests.get| CONFIG
    CONFIG -->|HTTP Request| CORS
    CORS -->|Allow-Origin| ENDPOINTS
    ENDPOINTS -->|JSON Response| IMPORT

    style IMPORT fill:#4A90E2,stroke:#2E5C8A,color:#fff
    style CONFIG fill:#FFB347,stroke:#CC8A39,color:#000
    style CORS fill:#7B68EE,stroke:#4A3FB5,color:#fff
    style ENDPOINTS fill:#50C878,stroke:#2D7A4A,color:#fff
```

### 9.2 Integração Externa (REST Countries)

```mermaid
graph LR
    APP["FastAPI App<br/>app/rest_countries.py"]
    CLIENT["requests.get<br/>timeout=30s<br/>retry=3x"]
    API["REST Countries API<br/>https://restcountries.com<br/>GET /v3.1/all"]
    FALLBACK["Cache Local<br/>Última ingestão<br/>bem-sucedida"]

    APP -->|Fetch| CLIENT
    CLIENT -->|HTTP GET| API
    API -->|200 OK| CLIENT
    CLIENT -->|raw_data| APP
    
    API -->|Timeout/Error| FALLBACK
    FALLBACK -->|Cached data| APP

    style APP fill:#7B68EE,stroke:#4A3FB5,color:#fff
    style CLIENT fill:#4A90E2,stroke:#2E5C8A,color:#fff
    style API fill:#FF6B6B,stroke:#CC5555,color:#fff
    style FALLBACK fill:#F39C12,stroke:#C47E0B,color:#000
```

---

## 10. PADRÕES DE CÓDIGO E DESIGN

### 10.1 Estrutura de Módulos

```
app/
├── main.py                    # FastAPI app instance + routes
├── __init__.py
├── api/
│   ├── __init__.py
│   ├── rest_countries.py      # HTTP client + normalizer
│   └── schemas.py             # Pydantic models (v0.2)
├── database/
│   ├── __init__.py
│   ├── connection.py          # DB session + engine
│   ├── models.py              # SQLAlchemy models
│   └── crud.py                # Database operations (v0.2)
├── utils/
│   ├── __init__.py
│   ├── helpers.py             # Utility functions
│   ├── logger.py              # Logging config
│   └── constants.py           # Constants
├── scripts/
│   ├── __init__.py
│   └── ingest.py              # CLI for manual ingest
└── streamlit/
    ├── app.py                 # Main Streamlit app
    └── components/            # Reusable components (v0.2)

tests/
├── __init__.py
├── conftest.py                # Pytest fixtures
├── unit/
│   ├── test_api.py
│   ├── test_models.py
│   └── test_database.py
└── integration/
    └── test_ingest_e2e.py

documentacoes/
├── PRD_PG_genIA_MVP-01.md
├── BACKLOG_PG_genIA_MVP-01.md
├── ARCHITECTURE.md            # (este arquivo)
├── API.md
└── CHANGELOG.md
```

### 10.2 Padrões Design (OOP)

```python
# ✅ BOAS PRÁTICAS

# 1. Type Hints + Docstrings
def fetch_countries(timeout: int = 30) -> List[dict]:
    """Fetch all countries from REST Countries API.
    
    Args:
        timeout: Request timeout in seconds (default: 30)
        
    Returns:
        List of country dictionaries from API
        
    Raises:
        httpx.TimeoutException: If request exceeds timeout
        httpx.HTTPStatusError: If API returns error status
    """

# 2. Error Handling + Logging
try:
    response = httpx.get(url, timeout=timeout)
    response.raise_for_status()
    logger.info(f"Fetched {len(response.json())} countries")
    return response.json()
except httpx.HTTPError as e:
    logger.error(f"API fetch failed: {e}")
    raise

# 3. Pydantic Validation
class CountrySchema(BaseModel):
    name_common: str
    name_official: str
    iso_code_2: str
    region: str
    population: int
    
    model_config = ConfigDict(str_strip_whitespace=True)

# 4. SQLAlchemy with Type Hints
class Country(Base):
    __tablename__ = "countries"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name_common: Mapped[str] = mapped_column(String(255), unique=True)
    population: Mapped[int] = mapped_column(BigInteger)
    languages: Mapped[List["Language"]] = relationship(back_populates="country")
```

### 10.3 Padrão: Dependency Injection (FastAPI)

```python
# Database session dependency
def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

# Use em rotas
@app.get("/countries")
def get_countries(
    session: Session = Depends(get_db_session),
    region: Optional[str] = None
) -> List[CountrySchema]:
    query = session.query(Country)
    if region:
        query = query.filter(Country.region == region)
    return query.all()
```

---

## 11. PERFORMANCE & OTIMIZAÇÕES

### 11.1 Database Optimization

```sql
-- Índices críticos
CREATE INDEX idx_iso_code_2 ON countries(iso_code_2);
CREATE INDEX idx_iso_code_3 ON countries(iso_code_3);
CREATE INDEX idx_region ON countries(region);
CREATE INDEX idx_subregion ON countries(subregion);

-- Análise esperada
-- SELECT * FROM countries WHERE region='Europe' → ~2ms (com índice)
-- vs ~50ms (sem índice)

-- Query Planning
EXPLAIN QUERY PLAN
SELECT * FROM countries WHERE region = 'Europe';
```

### 11.2 Caching Strategy (v0.2)

```
Level 1: Application Cache (Memory)
    |── Duração: 1 hora
    |── Tamanho: ~10MB
    |── Tecnologia: Python dict + TTL

Level 2: Redis Cache (v0.2)
    |── Duração: 3-6 horas
    |── Tamanho: 50MB
    |── Tecnologia: Redis

Level 3: Database
    |── Persistência durável
    |── Queries com índices
    |── Atualização 1x/dia (scheduler)

Cache Hit Rate Target: > 80%
```

### 11.3 Load Testing (v0.2)

```
Ferramentas: k6 / Apache Bench / Locust

Cenários:
1. Health Check
   - 100 req/s por 1 minuto
   - Target P95: < 10ms

2. Country List Query
   - 50 req/s por 5 minutos
   - Target P95: < 500ms
   - Memory: stable, sem leak

3. Concurrent Users
   - 100 usuarios simultâneos
   - Simular filtro + scroll tabela
   - Target: 0 errors
```

---

## 12. CHECKLIST DE VALIDAÇÃO ARQUITETURAL

```
✅ Separação de Responsabilidades
    [✓] Frontend (Streamlit)
    [✓] Backend (FastAPI)
    [✓] Database (SQLAlchemy + SQLite)
    [✓] Scheduler (APScheduler)

✅ Escalabilidade
    [✓] Stateless backend (fácil horizontal scaling)
    [✓] Database migration path (PostgreSQL ready)
    [✓] Cache layer designed (implementar v0.2)
    [✓] Containerizado (Docker ready)

✅ Confiabilidade
    [✓] Retry logic (HTTP client, 3x max)
    [✓] Fallback (local cache em caso de API down)
    [✓] Logging estruturado (rastreabilidade)
    [✓] Health checks (/health endpoint)

✅ Segurança
    [✓] Input validation (Pydantic)
    [✓] CORS configurado
    [✓] Variáveis de ambiente (.env)
    [✓] Sem hardcoded secrets

✅ Manutenibilidade
    [✓] Type hints (100%)
    [✓] Docstrings (Google style)
    [✓] Testes (unit + integration, 80%+)
    [✓] CI/CD (GitHub Actions)
    [✓] Documentação (README + ARCHITECTURE)

✅ Performance
    [✓] Database indexes
    [✓] Connection pooling
    [✓] Async where possible
    [✓] Cache design (v0.2)

```

---

## 13. ROADMAP TÉCNICO

### Release 0.1 (Set 2026) - Core
- ✅ FastAPI + Streamlit integrados
- ✅ SQLite com relacionamentos
- ✅ Scheduler de sincronização
- ✅ 80%+ test coverage

### Release 0.2 (Out 2026) - APIs & Scale
- 🔄 Endpoints REST completos
- 🔄 Cache layer (Redis)
- 🔄 Rate limiting
- 🔄 Advanced visualizations

### Release 0.3 (Nov 2026) - Auth & Intelligence
- 🔄 JWT authentication
- 🔄 Time-series data
- 🔄 Claude API integration
- 🔄 Migration to PostgreSQL (optional)

---

## 14. DOCUMENTOS RELACIONADOS

- **PRD:** `documentacoes/PRD_PG_genIA_MVP-01.md`
- **BACKLOG:** `documentacoes/BACKLOG_PG_genIA_MVP-01.md`
- **API Spec:** `documentacoes/API.md` (a criar)
- **CHANGELOG:** `documentacoes/CHANGELOG.md` (a criar)

---

**Documento versão 1.0 | Última atualização: 15/09/2026**  
**Arquiteto de Software:** [Nome]  
**Revisor Técnico:** [Nome]  
**Aprovação:** ⏳ Pendente
