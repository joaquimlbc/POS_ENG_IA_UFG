# Product Requirements Document (PRD)
## PG genIA MVP-01: REST Countries Dashboard

**Versão:** 1.0  
**Data:** 15 de Setembro de 2026  
**Status:** Em Desenvolvimento  
**Proprietário do Produto:** Product Owner  
**Arquiteto de Software:** Arquiteto Técnico  

---

## 1. VISÃO GERAL DO PRODUTO

### 1.1 Descrição Executiva
Desenvolvimento de MVP que consome dados da API REST Countries, persistindo informações demográficas em banco de dados relacional e apresentando indicadores populacionais e regionais através de dashboard interativo, viabilizando análises rápidas de dados de países.

### 1.2 Valor do Produto
- **Para o Negócio:** Demonstração de capacidade de integração de APIs externas com visualização de dados
- **Para o Usuário:** Acesso rápido a informações estruturadas de países com filtros e análises regionais
- **Para a Tecnologia:** Validação de arquitetura com FastAPI, SQLAlchemy e Streamlit

### 1.3 Contexto Estratégico
- Fase: MVP (Produto Mínimo Viável)
- Público-alvo inicial: Analistas de dados, pesquisadores, desenvolvedores
- Escopo de lançamento: Americas + Europa
- Dados: API pública REST Countries (https://restcountries.com/v3.1/all)

---

## 2. OBJETIVOS DO PRODUTO

### 2.1 Objetivos Primários
1. Consumir dados de todos os países via REST Countries API
2. Armazenar informações em banco de dados normalizado (SQLite)
3. Fornecer dashboard interativo com filtros regionais
4. Exposição de endpoints REST para consultas programáticas

### 2.2 Métricas de Sucesso
| Métrica | Target | Baseline |
|---------|--------|----------|
| Taxa de Disponibilidade | ≥ 99.5% | - |
| Tempo de Resposta (P95) | ≤ 500ms | - |
| Cobertura de Países | 100% | 0% |
| Dashboard Load Time | ≤ 3s | - |

---

## 3. REQUISITOS FUNCIONAIS

### 3.1 Backend - Ingestão e Persistência de Dados

#### RF-BE-001: Consumo da API REST Countries
- **Descrição:** Sistema deve realizar requisição HTTP GET para https://restcountries.com/v3.1/all
- **Critério de Aceição:**
  - Retorna lista completa de países (~250 registros)
  - Tratamento de timeout (max 30s)
  - Retry automático em caso de falha (max 3 tentativas)
  - Validação de integridade de dados (schema Pydantic)

#### RF-BE-002: Normalização de Dados
- **Descrição:** Extrair e transformar dados brutos da API em modelo de domínio
- **Campos Obrigatórios:**
  - Nome (comum + oficial)
  - Código ISO (2 e 3 dígitos)
  - Região/Subregião
  - População
  - Área (km²)
  - Idiomas
  - Moedas
  - Zonas de Fuso Horário
  - Coordenadas Geográficas (lat/lon)
- **Critério de Aceição:**
  - 100% dos campos obrigatórios preenchidos
  - Validação de tipos de dados
  - Logs de transformação por país

#### RF-BE-003: Persistência em SQLite
- **Descrição:** Armazenar dados normalizados em banco de dados relacional
- **Tabelas Principais:**
  - `countries` (id, name_common, name_official, iso2, iso3, region, subregion, population, area)
  - `country_languages` (id, country_id, language_code, language_name)
  - `country_currencies` (id, country_id, currency_code, currency_name)
  - `country_timezones` (id, country_id, timezone_name)
- **Critério de Aceição:**
  - Relacionamentos entre tabelas definidos
  - Índices em colunas de busca frequente (iso2, iso3, region)
  - Integridade referencial com constraints
  - Migrations com Alembic

#### RF-BE-004: Endpoints REST de Saúde e Metadata
- **Descrição:** Fornecer rota de healthcheck e metadados do serviço
- **Endpoints:**
  - `GET /health` → retorna status, versão, timestamp
  - `GET /` → mensagem de boas-vindas com documentação
- **Resposta JSON:**
  ```json
  {
    "status": "ok",
    "version": "1.0.0",
    "timestamp": "2026-09-15T10:30:00+00:00"
  }
  ```

#### RF-BE-005: API de Consulta de Países (v0.2+)
- **Escopo:** Planejado para Release 0.2
- **Endpoints Futuros:**
  - `GET /api/v1/countries` (listar com paginação)
  - `GET /api/v1/countries/{code}` (detalhes por código ISO)
  - `GET /api/v1/regions` (agrupar por região)
  - `GET /api/v1/statistics` (estatísticas globais)

### 3.2 Backend - Serviço de Aplicação

#### RF-BE-006: Scheduled Data Sync
- **Descrição:** Sincronizar dados da API em intervalos regulares
- **Frequência:** Diária (00:00 UTC) - configurável
- **Comportamento:**
  - Verificar versão de dados (timestamp)
  - Atualizar apenas registros modificados
  - Gerar logs de sincronização
  - Notificar em caso de falha
- **Critério de Aceição:**
  - Execução automática sem intervenção
  - Fallback em caso de indisponibilidade da API

#### RF-BE-007: Documentação OpenAPI/Swagger
- **Descrição:** Documentação automática dos endpoints
- **Critério de Aceição:**
  - Swagger UI acessível em `/docs`
  - ReDoc em `/redoc`
  - Schema JSON em `/openapi.json`

### 3.3 Frontend - Dashboard Streamlit

#### RF-FE-001: Dashboard Principal
- **Descrição:** Interface interativa com KPIs e visualizações
- **Componentes:**
  - Card com total de países (filtro dinâmico)
  - Card com população global
  - Card com região mais populosa
  - Card com maior país por área
- **Critério de Aceição:**
  - Renderização em < 3s
  - Responsivo (mobile-friendly recomendado)
  - Atualização de dados sem refresh manual

#### RF-FE-002: Filtro por Região
- **Descrição:** Usuário seleciona região para filtrar países
- **Regiões Suportadas:**
  - Africa, Americas, Asia, Europe, Oceania
  - Suporte a "Todas" (default)
- **Critério de Aceição:**
  - Filtro atualiza KPIs e tabelas em tempo real
  - Estado de filtro persistido na sessão Streamlit

#### RF-FE-003: Tabela de Países
- **Descrição:** Exibir lista de países com informações principais
- **Colunas:**
  - Flag (emoji ou ícone)
  - Nome
  - População
  - Área (km²)
  - Região
  - Densidade Populacional
- **Funcionalidades:**
  - Ordenação por coluna
  - Busca por nome (client-side)
  - Paginação (20 itens/página)
  - Destaque de linhas ao hover

#### RF-FE-004: Visualizações Gráficas
- **Gráficos de Barras:**
  - Top 10 países por população
  - Top 10 países por área
- **Gráficos de Pizza:**
  - Distribuição de população por região
  - Distribuição de países por região
- **Critério de Aceição:**
  - Gráficos renderizam em < 1s
  - Labels legíveis
  - Tooltips informativos

#### RF-FE-005: Detalhes do País
- **Descrição:** Visualizar informações completas de um país específico
- **Informações Exibidas:**
  - Nome (comum e oficial)
  - Códigos ISO (2 e 3)
  - Região/Subregião
  - População, Área, Densidade
  - Capital (se disponível)
  - Idiomas e Moedas
  - Fusos Horários
  - Coordenadas Geográficas
- **Implementação:** Card expansível ou modal ao clicar na linha

#### RF-FE-006: Exportação de Dados
- **Escopo:** Planejado para Release 0.2
- **Formatos:** CSV e PDF

---

## 4. REQUISITOS NÃO-FUNCIONAIS

### 4.1 Performance
| Aspecto | Requisito | Método de Validação |
|---------|-----------|-------------------|
| Tempo de Resposta API | P95 ≤ 500ms | Load Test (pytest + locust) |
| Dashboard Load | ≤ 3s (cold start) | Browser DevTools |
| Consumo de Memória | ≤ 512MB (steady state) | Memory Profiler |
| Throughput API | ≥ 100 req/s | k6 / Apache Bench |

### 4.2 Confiabilidade
- **Disponibilidade:** 99.5% (max 3.6h downtime/mês)
- **MTBF (Mean Time Between Failures):** ≥ 720h
- **MTTR (Mean Time To Recovery):** ≤ 1h
- **Retry Logic:** Max 3 tentativas com backoff exponencial

### 4.3 Segurança
- **Dados em Trânsito:** HTTPS/TLS 1.2+
- **Validação de Entrada:** Pydantic + Custom Validators
- **Rate Limiting:** 100 req/min por IP (v0.2+)
- **CORS:** Whitelist de domínios permitidos
- **Secrets Management:** Variáveis de ambiente (.env)

### 4.4 Escalabilidade
- **Banco de Dados:** SQLite compat com PostgreSQL (migration path)
- **Cache:** Implementação com Redis (v0.3+)
- **Containerização:** Docker + Docker Compose pronto para uso
- **Arquitetura:** Stateless para facilitar horizontal scaling

### 4.5 Manutenibilidade
- **Linguagem:** Python 3.11+
- **Code Style:** PEP 8 (Black formatter)
- **Type Hints:** 100% de cobertura de tipos (mypy)
- **Documentação:** Docstrings (Google Style) + comentários em lógica complexa
- **Logging:** Estruturado com níveis INFO, WARNING, ERROR
- **Versionamento:** Semantic Versioning (major.minor.patch)

### 4.6 Compatibilidade
- **Navegadores:** Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Sistemas Operacionais:** Windows 10+, macOS 10.15+, Ubuntu 20.04+
- **Python:** 3.11, 3.12 (beta)

### 4.7 Compliance & Data
- **Retenção de Dados:** 365 dias (policy configurável)
- **Backup:** Daily snapshots do banco (v0.2+)
- **Logs de Auditoria:** Todas as operações críticas registradas
- **GDPR:** Conformidade com direito ao esquecimento (v0.3+)

---

## 5. REQUISITOS FORA DO ESCOPO (Release 0.1)

### 5.1 Explicitamente Excluído
- ❌ Autenticação e Autorização de Usuários
- ❌ Histórico de Mudanças de Dados (séries temporais)
- ❌ Alertas e Notificações
- ❌ Integração com outras APIs geográficas
- ❌ Suporte a idiomas múltiplos (i18n) no dashboard
- ❌ Modo offline ou sync local
- ❌ Mobile app nativa
- ❌ Relatórios agendados por email
- ❌ API GraphQL (apenas REST)
- ❌ Testes de carga e stress (fase beta)

### 5.2 Planejado para Releases Futuros
- 🔄 **0.2 (Out/2026):** APIs completas, gráficos avançados, exportação
- 🔄 **0.3 (Nov/2026):** Auth, séries temporais, alertas
- 🔄 **0.4 (Dez/2026):** Multi-idioma, mobile, relatórios

---

## 6. CRITÉRIOS DE ACEITAÇÃO GLOBAIS

### 6.1 Funcionalidade
- [ ] Todos os RF implementados e testados (unit + integration)
- [ ] API retorna dados válidos 100% das vezes
- [ ] Dashboard exibe informações corretas para todos os 250+ países
- [ ] Filtros funcionam sem erros
- [ ] Nenhuma data faltante ou inválida

### 6.2 Qualidade
- [ ] Code Coverage ≥ 80% (pytest)
- [ ] 0 erros críticos de segurança (SAST)
- [ ] Performance dentro dos limites especificados
- [ ] Sem memory leaks (detectado por profiler)

### 6.3 Documentação
- [ ] README completo com instruções de setup
- [ ] API documentada com Swagger
- [ ] Docstrings em 100% das funções públicas
- [ ] Arquivo CHANGELOG atualizado

### 6.4 Deployment
- [ ] Docker image criada e testada
- [ ] CI/CD pipeline configurado (GitHub Actions)
- [ ] Deployment em staging bem-sucedido
- [ ] Plano de rollback definido

---

## 7. ARQUITETURA E TECNOLOGIA

### 7.1 Stack Técnico
```
┌─────────────────────────────────────────────┐
│            Frontend (Streamlit)              │
│  - Dashboard interativo                      │
│  - Filtros e visualizações                   │
└──────────────────┬──────────────────────────┘
                   │ HTTP/REST
┌──────────────────▼──────────────────────────┐
│         Backend (FastAPI)                    │
│  - Health Check                              │
│  - Data Sync Scheduler                       │
│  - Future: Query APIs (v0.2)                 │
└──────────────────┬──────────────────────────┘
                   │ SQL
┌──────────────────▼──────────────────────────┐
│   Database (SQLAlchemy + SQLite)             │
│  - countries, languages, currencies, timezones │
└──────────────────────────────────────────────┘
                   │ HTTP
┌──────────────────▼──────────────────────────┐
│      External API (REST Countries)           │
│  - https://restcountries.com/v3.1/all        │
└──────────────────────────────────────────────┘
```

### 7.2 Componentes Principais

| Componente | Responsabilidade | Tecnologia |
|-----------|-----------------|-----------|
| API Server | Ingestão, healthcheck, futuras queries | FastAPI 0.104.1 |
| ORM | Mapeamento de dados | SQLAlchemy 2.0 |
| Database | Persistência de dados | SQLite 3.x |
| Dashboard | Interface de visualização | Streamlit 1.28.1 |
| Web Server | Deploy e produção | Uvicorn 0.24.0 |
| Scheduler | Sincronização automática | APScheduler (v0.2) |

### 7.3 Dependências Principais
```
FastAPI==0.104.1          # Web framework
uvicorn[standard]==0.24.0 # App server
sqlalchemy==2.0.23        # ORM
streamlit==1.28.1         # Dashboard
requests==2.31.0          # HTTP client
pydantic==2.5.0           # Data validation
python-dotenv==1.0.0      # Environment config
pytest==7.4.3             # Testing
```

---

## 8. CRONOGRAMA E ROADMAP

### 8.1 Release 0.1 - MVP (Set 2026)
**Status:** ✅ Em Desenvolvimento

| Atividade | Duração | Status |
|-----------|---------|--------|
| Setup inicial e estrutura | 2d | ✅ Concluído |
| Backend: Consumo API | 3d | 🔄 Em Progresso |
| Backend: Persistência | 3d | ⏳ Não Iniciado |
| Scheduler de Sync | 2d | ⏳ Não Iniciado |
| Dashboard: KPIs | 3d | ⏳ Não Iniciado |
| Dashboard: Tabelas | 2d | ⏳ Não Iniciado |
| Dashboard: Gráficos | 3d | ⏳ Não Iniciado |
| Testes Unitários | 3d | ⏳ Não Iniciado |
| Documentação | 2d | 🔄 Em Progresso |
| Deployment + CI/CD | 2d | ⏳ Não Iniciado |
| **Total** | **27 dias** | - |

**Deadline:** 30 de Setembro de 2026

### 8.2 Release 0.2 - APIs & Analytics (Out 2026)
- [ ] Endpoints completos de consulta (`GET /countries`, `/regions`, etc.)
- [ ] Rate limiting e cache
- [ ] Gráficos avançados (density, correlation, trends)
- [ ] Exportação (CSV, PDF)
- [ ] APScheduler para sync automático

### 8.3 Release 0.3 - Auth & Intelligence (Nov 2026)
- [ ] Authentication (JWT)
- [ ] User preferences
- [ ] Histórico de dados (séries temporais)
- [ ] Alertas baseados em condições
- [ ] Integração com IA para insights

---

## 9. RISCOS E MITIGAÇÃO

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|--------|-----------|
| API REST Countries indisponível | Média | Alto | Implementar retry + cache local |
| Performance inadequada em produção | Média | Alto | Load testing proativo, índices DB |
| Mudança de schema da API | Baixa | Médio | Versionamento de API, tests |
| Dados inconsistentes após ingestão | Baixa | Alto | Validação Pydantic + unit tests |
| Equipe reduzida | Média | Médio | Documentação detalhada, pairing |

---

## 10. SUCESSO E VALIDAÇÃO

### 10.1 Critérios de Release
- [ ] Todos os requisitos funcionais implementados (RF-BE-001 até RF-FE-005)
- [ ] Performance dentro dos limites (P95 ≤ 500ms)
- [ ] Code coverage ≥ 80%
- [ ] Zero erros críticos de segurança
- [ ] Documentação 100% completa
- [ ] Aprovado por PO e Arquiteto

### 10.2 Métricas de Sucesso Pós-Lançamento (OKRs)
| OKR | Target | Período |
|-----|--------|---------|
| Disponibilidade do Dashboard | 99.5% uptime | 30 dias |
| Tempo de Resposta | P95 ≤ 500ms | Continuous |
| Sincronização de Dados | 99% de sucesso | 30 dias |
| Cobertura de Países | 250+ (100%) | Release |
| Satisfação de Usuários | NPS ≥ 7.0 | 60 dias |

---

## 11. GLOSSÁRIO

| Termo | Definição |
|-------|-----------|
| **REST Countries** | API pública que fornece dados sobre países em JSON |
| **MVP** | Produto mínimo viável com features essenciais |
| **SQLite** | Banco de dados relacional embarcado, ideal para MVP |
| **ORM** | Object-Relational Mapping (SQLAlchemy) |
| **Streamlit** | Framework Python para criar dashboards web rapidamente |
| **FastAPI** | Framework web Python moderno e de alta performance |
| **CORS** | Cross-Origin Resource Sharing |
| **MTTR/MTBF** | Mean Time To Recovery / Mean Time Between Failures |
| **P95** | 95º percentil (95% das requisições abaixo deste tempo) |

---

## 12. ASSINATURAS

| Papel | Nome | Data | Aprovação |
|-------|------|------|-----------|
| Product Owner | [PO Name] | 15/09/2026 | ⏳ |
| Arquiteto de Software | [Architect Name] | 15/09/2026 | ⏳ |
| Tech Lead | [TL Name] | 15/09/2026 | ⏳ |
| QA Lead | [QA Name] | 15/09/2026 | ⏳ |

---

## APÊNDICE A: Estrutura do Banco de Dados

```sql
-- Tabela principal de países
CREATE TABLE countries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_common VARCHAR(255) NOT NULL UNIQUE,
    name_official VARCHAR(255),
    iso_code_2 VARCHAR(2) NOT NULL UNIQUE,
    iso_code_3 VARCHAR(3) NOT NULL UNIQUE,
    region VARCHAR(50),
    subregion VARCHAR(50),
    population BIGINT,
    area DECIMAL(10, 2),
    latitude DECIMAL(10, 6),
    longitude DECIMAL(10, 6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de relacionamento com idiomas
CREATE TABLE country_languages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    country_id INTEGER NOT NULL,
    language_code VARCHAR(10),
    language_name VARCHAR(100),
    FOREIGN KEY (country_id) REFERENCES countries(id)
);

-- Tabela de relacionamento com moedas
CREATE TABLE country_currencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    country_id INTEGER NOT NULL,
    currency_code VARCHAR(3),
    currency_name VARCHAR(100),
    FOREIGN KEY (country_id) REFERENCES countries(id)
);

-- Tabela de relacionamento com fusos horários
CREATE TABLE country_timezones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    country_id INTEGER NOT NULL,
    timezone_name VARCHAR(100),
    FOREIGN KEY (country_id) REFERENCES countries(id)
);

-- Índices para performance
CREATE INDEX idx_iso_code_2 ON countries(iso_code_2);
CREATE INDEX idx_iso_code_3 ON countries(iso_code_3);
CREATE INDEX idx_region ON countries(region);
CREATE INDEX idx_subregion ON countries(subregion);
```

---

**Documento versão 1.0 | Última atualização: 15/09/2026**
