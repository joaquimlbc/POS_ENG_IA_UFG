# Product Backlog
## PG genIA MVP-01: REST Countries Dashboard

**Versão:** 1.0  
**Data:** 15 de Setembro de 2026  
**Status:** Em Planejamento  
**Last Updated:** 15/09/2026  

---

## 📋 Legenda de Prioridades e Status

### Prioridades
- 🔴 **CRÍTICO:** Bloqueia outras atividades, MVP essential
- 🟠 **ALTO:** Importante, deve ser implementado no release
- 🟡 **MÉDIO:** Desejável, pode ser adiado
- 🟢 **BAIXO:** Nice-to-have, pode ser futuro

### Status
- ⏳ **Não Iniciado**
- 🔄 **Em Progresso**
- ✅ **Concluído**
- 🚫 **Bloqueado**

### Estimativas (Story Points)
- **1 SP** = 2-4 horas
- **2 SP** = 4-8 horas
- **3 SP** = 8-16 horas
- **5 SP** = 16-32 horas
- **8 SP** = 32-64 horas (pode ser quebrado)

---

## 🎯 RELEASE 0.1 - MVP (Set 2026)
**Objetivo:** Consumir API, armazenar dados, dashboard básico  
**Deadline:** 30 de Setembro de 2026  
**Status:** ✅ Em Desenvolvimento  

---

### EPIC E-001: Infraestrutura & Setup Inicial

#### US-001: Configuração Ambiente de Desenvolvimento ✅
- **Prioridade:** 🔴 CRÍTICO
- **Status:** ✅ Concluído
- **Story Points:** 2
- **Assignee:** [Dev Lead]
- **Descrição:** Preparar ambiente local com Python 3.11, venv, dependências
- **Critérios de Aceite:**
  - [ ] Python 3.11+ instalado
  - [ ] Virtual environment configurado (.venv)
  - [ ] requirements.txt com 28+ dependências
  - [ ] Todas as dependências instaláveis sem erro
  - [ ] Ambiente ativável com `.venv\Scripts\Activate.ps1` (Windows)

#### US-002: Setup Git & GitHub
- **Prioridade:** 🔴 CRÍTICO
- **Status:** ✅ Concluído
- **Story Points:** 1
- **Assignee:** [Dev Lead]
- **Descrição:** Inicializar repositório Git, configurar remote GitHub
- **Critérios de Aceite:**
  - [ ] Git repo inicializado localmente
  - [ ] Remote `origin` configurado para GitHub
  - [ ] .gitignore criado com seções comentadas
  - [ ] Pelo menos 1 commit inicial
  - [ ] Repo acessível em https://github.com/joaquimlbc/POS_ENG_IA_UFG

#### US-003: Estrutura de Pastas & Documentação Inicial
- **Prioridade:** 🔴 CRÍTICO
- **Status:** ✅ Concluído
- **Story Points:** 1
- **Assignee:** [Dev Lead]
- **Descrição:** Criar estrutura de diretórios conforme PRD
- **Critérios de Aceite:**
  - [ ] Pastas criadas: app/, database/, api/, utils/, prompts/, documentacoes/
  - [ ] README.md completo com instruções
  - [ ] Arquivo .gitignore testado
  - [ ] Estrutura documentada no README

---

### EPIC E-002: Backend - Ingestão de Dados da API

#### US-004: Cliente HTTP para REST Countries API 🔄
- **Prioridade:** 🔴 CRÍTICO
- **Status:** 🔄 Em Progresso
- **Story Points:** 5
- **Assignee:** [Backend Dev 1]
- **Dependências:** US-001, US-002
- **Descrição:** Implementar cliente HTTP para consumir https://restcountries.com/v3.1/all
- **Critérios de Aceite:**
  - [ ] Função `fetch_countries()` implementada em `api/rest_countries.py`
  - [ ] Retorna lista de dicts com dados de ~250 países
  - [ ] Tratamento de timeout (max 30s)
  - [ ] Retry automático (max 3 tentativas com backoff exponencial)
  - [ ] Logs estruturados (INFO, WARNING, ERROR)
  - [ ] Validação de resposta com Pydantic
  - [ ] Testes unitários com pytest (mock HTTP)
  - [ ] Coverage ≥ 80%

#### US-005: Modelos de Dados com SQLAlchemy
- **Prioridade:** 🔴 CRÍTICO
- **Status:** ⏳ Não Iniciado
- **Story Points:** 5
- **Assignee:** [Backend Dev 1]
- **Dependências:** US-001, US-004
- **Descrição:** Definir modelos SQLAlchemy para países e relacionamentos
- **Critérios de Aceite:**
  - [ ] Arquivo `database/models.py` criado
  - [ ] Modelo `Country` com campos: id, name_common, name_official, iso2, iso3, region, subregion, population, area, latitude, longitude
  - [ ] Modelos relacionados: `Language`, `Currency`, `Timezone`
  - [ ] Relacionamentos configurados (1:N com back_populates)
  - [ ] Type hints completos
  - [ ] Docstrings em todas as classes
  - [ ] Testes de modelo (instantiation, relationships)

#### US-006: Configuração de Banco de Dados SQLite
- **Prioridade:** 🔴 CRÍTICO
- **Status:** ⏳ Não Iniciado
- **Story Points:** 3
- **Assignee:** [Backend Dev 1]
- **Dependências:** US-005
- **Descrição:** Configurar conexão SQLAlchemy com SQLite
- **Critérios de Aceite:**
  - [ ] Arquivo `database/connection.py` implementado
  - [ ] Engine e Session factory criados
  - [ ] `.env` com `DATABASE_URL` configurada
  - [ ] Arquivo SQLite criado em `data/countries.db`
  - [ ] Índices criados em colunas de busca (iso2, iso3, region)
  - [ ] Connection pooling configurado
  - [ ] Testes de conexão bem-sucedidos

#### US-007: Normalização de Dados da API
- **Prioridade:** 🔴 CRÍTICO
- **Status:** ⏳ Não Iniciado
- **Story Points:** 5
- **Assignee:** [Backend Dev 2]
- **Dependências:** US-004, US-005
- **Descrição:** Transformar dados brutos da API em modelos de domínio
- **Critérios de Aceite:**
  - [ ] Função `normalize_countries(raw_data)` implementada em `api/rest_countries.py`
  - [ ] Extração de campos: name, ISO codes, região, população, área, idiomas, moedas, fusos horários
  - [ ] Tratamento de dados faltantes (None/null)
  - [ ] Validação com Pydantic v2
  - [ ] Logs de erros por país
  - [ ] Retorna lista de objetos Country validados
  - [ ] Testes com dados de exemplo (fixtures)
  - [ ] Coverage ≥ 85%

#### US-008: Persistência de Dados em Banco
- **Prioridade:** 🔴 CRÍTICO
- **Status:** ⏳ Não Iniciado
- **Story Points:** 5
- **Assignee:** [Backend Dev 2]
- **Dependências:** US-006, US-007
- **Descrição:** Salvar dados normalizados no SQLite
- **Critérios de Aceite:**
  - [ ] Função `save_countries(countries)` implementada em `database/`
  - [ ] Operação INSERT OR REPLACE (upsert)
  - [ ] Transações com rollback em caso de erro
  - [ ] Gera IDs corretamente
  - [ ] Valida integridade referencial
  - [ ] Logs de operação (quanytidade inserida/atualizada)
  - [ ] Testes: inserção, atualização, duplicatas
  - [ ] Coverage ≥ 80%

#### US-009: Script de Ingestão Completa (End-to-End)
- **Prioridade:** 🟠 ALTO
- **Status:** ⏳ Não Iniciado
- **Story Points:** 3
- **Assignee:** [Backend Dev 1]
- **Dependências:** US-004, US-007, US-008
- **Descrição:** Script que orquestra consumo → normalização → persistência
- **Critérios de Aceite:**
  - [ ] Função `ingest_countries()` implementada
  - [ ] Executável via CLI: `python -m app.scripts.ingest`
  - [ ] Logs estruturados (timestamp, operação, status)
  - [ ] Tratamento de exceções e retry
  - [ ] Finaliza com relatório (X países inseridos, Y atualizados)
  - [ ] Execução sem erros em ambiente local
  - [ ] Tempo de execução ≤ 30s

---

### EPIC E-003: Backend - Serviço FastAPI

#### US-010: Instância FastAPI com Configurações Básicas ✅
- **Prioridade:** 🔴 CRÍTICO
- **Status:** ✅ Concluído
- **Story Points:** 2
- **Assignee:** [Backend Dev 1]
- **Dependências:** US-001, US-002
- **Descrição:** Criar aplicação FastAPI com configurações iniciais
- **Critérios de Aceite:**
  - [ ] Arquivo `app/main.py` com instância FastAPI
  - [ ] Documentação automática habilitada (/docs, /redoc)
  - [ ] Título, descrição, versão configurados
  - [ ] CORS configurado (origem local + GitHub Pages)
  - [ ] Logging estruturado
  - [ ] Type hints completos

#### US-011: Rota de Health Check ✅
- **Prioridade:** 🔴 CRÍTICO
- **Status:** ✅ Concluído
- **Story Points:** 1
- **Assignee:** [Backend Dev 1]
- **Dependências:** US-010
- **Descrição:** Endpoint GET /health para orquestradores de infra
- **Critérios de Aceite:**
  - [ ] Rota GET /health implementada
  - [ ] Retorna JSON: `{status: "ok", version: "1.0.0", timestamp: "ISO-8601"}`
  - [ ] Status code 200
  - [ ] Schema Pydantic validando resposta
  - [ ] Documentado em Swagger
  - [ ] Testável manualmente: `curl http://localhost:8000/health`

#### US-012: Scheduler de Sincronização Automática
- **Prioridade:** 🟠 ALTO
- **Status:** ⏳ Não Iniciado
- **Story Points:** 5
- **Assignee:** [Backend Dev 2]
- **Dependências:** US-009, US-010
- **Descrição:** Task agendada diária para sincronizar dados com REST Countries
- **Critérios de Aceite:**
  - [ ] APScheduler instalado e integrado
  - [ ] Job agendado para 00:00 UTC diariamente
  - [ ] Executa função `ingest_countries()` automaticamente
  - [ ] Logs de início/sucesso/erro
  - [ ] Implementa fallback em caso de indisponibilidade da API
  - [ ] Endpoint para disparar sync manual (admin-only, v0.2)
  - [ ] Testes de agendamento (mock scheduler)

#### US-013: Documentação OpenAPI/Swagger
- **Prioridade:** 🟠 ALTO
- **Status:** ⏳ Não Iniciado
- **Story Points:** 2
- **Assignee:** [Backend Dev 1]
- **Dependências:** US-010, US-011
- **Descrição:** Gerar e disponibilizar documentação automática
- **Critérios de Aceite:**
  - [ ] Swagger UI acessível em `http://localhost:8000/docs`
  - [ ] ReDoc acessível em `http://localhost:8000/redoc`
  - [ ] Schema OpenJSON em `http://localhost:8000/openapi.json`
  - [ ] Todos os endpoints documentados
  - [ ] Exemplos de resposta inclusos
  - [ ] Descrições claras de cada endpoint

---

### EPIC E-004: Frontend - Dashboard Streamlit

#### US-014: Setup Inicial Streamlit & Estrutura Base
- **Prioridade:** 🟠 ALTO
- **Status:** ⏳ Não Iniciado
- **Story Points:** 3
- **Assignee:** [Frontend Dev 1]
- **Dependências:** US-001, US-006
- **Descrição:** Criar aplicação Streamlit com configuração básica
- **Critérios de Aceite:**
  - [ ] Arquivo `app.py` ou `streamlit_app.py` na raiz
  - [ ] Config Streamlit em `.streamlit/config.toml`
  - [ ] Tema configurado (light/dark mode support)
  - [ ] Título e ícone da página definidos
  - [ ] Importação de módulos de DB funcionando
  - [ ] Executável via: `streamlit run app.py`

#### US-015: KPIs & Métricas Principais
- **Prioridade:** 🔴 CRÍTICO
- **Status:** ⏳ Não Iniciado
- **Story Points:** 5
- **Assignee:** [Frontend Dev 1]
- **Dependências:** US-014, US-008
- **Descrição:** Renderizar cards com indicadores principais
- **Critérios de Aceite:**
  - [ ] Card: Total de Países (dinâmico com filtro)
  - [ ] Card: População Global (formatado com separadores)
  - [ ] Card: Região mais Populosa (nome + valor)
  - [ ] Card: Maior País por Área (nome + km²)
  - [ ] Cards com ícones/emojis
  - [ ] Layout responsivo em colunas
  - [ ] Atualização em tempo real quando filtro muda

#### US-016: Filtro por Região
- **Prioridade:** 🔴 CRÍTICO
- **Status:** ⏳ Não Iniciado
- **Story Points:** 3
- **Assignee:** [Frontend Dev 1]
- **Dependências:** US-014, US-015
- **Descrição:** Selector para filtrar países por região
- **Critérios de Aceite:**
  - [ ] Widget selectbox com opções: "Todas", "Africa", "Americas", "Asia", "Europe", "Oceania"
  - [ ] Default = "Todas"
  - [ ] Estado persistido na sessão Streamlit
  - [ ] Atualiza todos os componentes ao mudar
  - [ ] Sem delay perceptível (< 500ms)

#### US-017: Tabela de Países
- **Prioridade:** 🔴 CRÍTICO
- **Status:** ⏳ Não Iniciado
- **Story Points:** 5
- **Assignee:** [Frontend Dev 2]
- **Dependências:** US-014, US-016, US-008
- **Descrição:** Tabela interativa com dados dos países
- **Critérios de Aceite:**
  - [ ] Colunas: Flag, Nome, População, Área (km²), Região, Densidade
  - [ ] Ordenação funcional por coluna (click no header)
  - [ ] Busca por nome (case-insensitive, client-side)
  - [ ] Paginação (20 itens/página) com controles
  - [ ] Destaque de linha ao hover
  - [ ] Números formatados (1000 separator)
  - [ ] Popup/Modal ao clicar na linha (detalhes do país)

#### US-018: Gráficos de Barras (Top 10)
- **Prioridade:** 🟠 ALTO
- **Status:** ⏳ Não Iniciado
- **Story Points:** 4
- **Assignee:** [Frontend Dev 2]
- **Dependências:** US-014, US-017
- **Descrição:** Visualizações de Top 10 países por população e área
- **Critérios de Aceite:**
  - [ ] 2 gráficos de barras lado a lado (col layout)
  - [ ] Gráfico 1: Top 10 por população
  - [ ] Gráfico 2: Top 10 por área (km²)
  - [ ] Cores degradadas (maior = cor mais intensa)
  - [ ] Labels e valores visíveis
  - [ ] Responsivo em diferentes tamanhos de tela
  - [ ] Atualiza com filtro de região

#### US-019: Gráficos de Pizza (Distribuição Regional)
- **Prioridade:** 🟠 ALTO
- **Status:** ⏳ Não Iniciado
- **Story Points:** 3
- **Assignee:** [Frontend Dev 2]
- **Dependências:** US-014, US-016
- **Descrição:** Gráficos de pizza mostrando distribuições por região
- **Critérios de Aceite:**
  - [ ] 2 gráficos de pizza lado a lado
  - [ ] Gráfico 1: Distribuição de população por região (%)
  - [ ] Gráfico 2: Distribuição de quantidade de países por região
  - [ ] Legendas com cores consistentes
  - [ ] Percentuais exibidos nas fatias
  - [ ] Paleta de cores harmônica

#### US-020: Detalhes Expandidos do País (Modal/Expander)
- **Prioridade:** 🟠 ALTO
- **Status:** ⏳ Não Iniciado
- **Story Points:** 4
- **Assignee:** [Frontend Dev 1]
- **Dependências:** US-017, US-008
- **Descrição:** Informações completas de um país em popup/expander
- **Critérios de Aceite:**
  - [ ] Acionável ao clicar em linha da tabela
  - [ ] Exibe: nome oficial, ISO codes, região/subregião, população, área, densidade
  - [ ] Exibe: idiomas, moedas, fusos horários, coordenadas
  - [ ] Formatação clara e hierárquica
  - [ ] Botão de fechar funcional
  - [ ] Sem datas vencidas ou campos nulos

#### US-021: Layout Responsivo & Estilo
- **Prioridade:** 🟡 MÉDIO
- **Status:** ⏳ Não Iniciado
- **Story Points:** 2
- **Assignee:** [Frontend Dev 1]
- **Dependências:** US-015 até US-020
- **Descrição:** Garantir responsividade e consistência visual
- **Critérios de Aceite:**
  - [ ] Dashboard funciona em mobile (< 768px)
  - [ ] Fonte legível em todos os tamanhos
  - [ ] Cores com bom contraste (WCAG AA)
  - [ ] Padding/margin consistentes
  - [ ] Sem horizontal scroll em mobile
  - [ ] Paleta de cores documentada em `documentacoes/DESIGN_SYSTEM.md`

---

### EPIC E-005: Testes & Qualidade

#### US-022: Testes Unitários - Backend
- **Prioridade:** 🟠 ALTO
- **Status:** ⏳ Não Iniciado
- **Story Points:** 8
- **Assignee:** [QA / Dev 1]
- **Dependências:** US-004 até US-013
- **Descrição:** Suite completa de testes unitários para backend
- **Critérios de Aceite:**
  - [ ] Arquivo `tests/test_api_rest_countries.py` com ≥ 10 testes
  - [ ] Arquivo `tests/test_models.py` com ≥ 8 testes
  - [ ] Arquivo `tests/test_database.py` com ≥ 10 testes
  - [ ] Arquivo `tests/test_main.py` com ≥ 5 testes (healthcheck, etc)
  - [ ] Coverage ≥ 80% (verificado com `pytest --cov`)
  - [ ] Todos os testes passando (green)
  - [ ] Fixtures reutilizáveis em conftest.py
  - [ ] Sem warnings ao executar pytest

#### US-023: Testes de Integração
- **Prioridade:** 🟠 ALTO
- **Status:** ⏳ Não Iniciado
- **Story Points:** 5
- **Assignee:** [QA / Dev 2]
- **Dependências:** US-022
- **Descrição:** Testes fim-a-fim da ingestão de dados
- **Critérios de Aceite:**
  - [ ] Teste: fetch API → normalize → persist → query (OK)
  - [ ] Teste: Validação de dados persistidos
  - [ ] Teste: Integridade referencial (FK constraints)
  - [ ] Teste: Duplicate handling (upsert)
  - [ ] Todos os testes com SQLite em-memória (teste rápido)
  - [ ] Coverage ≥ 70%

#### US-024: Linting & Code Quality
- **Prioridade:** 🟡 MÉDIO
- **Status:** ⏳ Não Iniciado
- **Story Points:** 2
- **Assignee:** [Dev Lead]
- **Dependências:** US-004 até US-021
- **Descrição:** Validar código com Black, Flake8, mypy
- **Critérios de Aceite:**
  - [ ] Black: 100% do código formatado
  - [ ] Flake8: 0 warnings/errors
  - [ ] mypy: 0 type errors (strict mode)
  - [ ] Scripts de validação em `Makefile` ou `scripts/`
  - [ ] CI/CD executando verificações

---

### EPIC E-006: Documentação & Deployment

#### US-025: Documentação Completa
- **Prioridade:** 🟠 ALTO
- **Status:** 🔄 Em Progresso
- **Story Points:** 3
- **Assignee:** [Tech Writer / Dev Lead]
- **Dependências:** Todos os US anteriores
- **Descrição:** Documentação técnica e de usuário
- **Critérios de Aceite:**
  - [ ] README.md com setup e quick start
  - [ ] PRD em `documentacoes/PRD_PG_genIA_MVP-01.md` ✅
  - [ ] BACKLOG em `documentacoes/BACKLOG_PG_genIA_MVP-01.md` (este arquivo)
  - [ ] ARCHITECTURE.md explicando stack e fluxos
  - [ ] API.md com exemplos de requisições
  - [ ] CHANGELOG.md com releases
  - [ ] Docstrings em 100% das funções públicas
  - [ ] Exemplos de uso em README

#### US-026: Docker & Docker Compose
- **Prioridade:** 🟡 MÉDIO
- **Status:** ⏳ Não Iniciado
- **Story Points:** 3
- **Assignee:** [DevOps / Dev]
- **Dependências:** US-010, US-014
- **Descrição:** Containerização da aplicação
- **Critérios de Aceite:**
  - [ ] Dockerfile criado (Alpine Python 3.11)
  - [ ] docker-compose.yml com serviços: api, streamlit, db
  - [ ] Build bem-sucedido: `docker-compose up`
  - [ ] Volumes configurados para desenvolvimento
  - [ ] Env vars via `.env.example`
  - [ ] Documentação em `docs/DOCKER.md`

#### US-027: GitHub Actions CI/CD
- **Prioridade:** 🟠 ALTO
- **Status:** ⏳ Não Iniciado
- **Story Points:** 4
- **Assignee:** [DevOps]
- **Dependências:** US-022, US-023, US-024
- **Descrição:** Pipeline de automação para testes e deploy
- **Critérios de Aceite:**
  - [ ] Workflow: `test.yml` executando pytest em cada push
  - [ ] Workflow: `lint.yml` rodando Black/Flake8/mypy
  - [ ] Status badge no README
  - [ ] Cobertura de testes reportada
  - [ ] Deploy automático em merge para main (futuro)

#### US-028: Deployment em Produção (Staging)
- **Prioridade:** 🟡 MÉDIO
- **Status:** ⏳ Não Iniciado
- **Story Points:** 5
- **Assignee:** [DevOps / Dev Lead]
- **Dependências:** US-026, US-027
- **Descrição:** Deploy em ambiente de staging para validação
- **Critérios de Aceite:**
  - [ ] Escolha de plataforma (Heroku, Railway, Render, etc)
  - [ ] Variáveis de ambiente configuradas
  - [ ] Deploy bem-sucedido
  - [ ] Health check respondendo
  - [ ] Dashboard acessível via URL pública
  - [ ] Logs estruturados e acessíveis
  - [ ] Rollback plan documentado

---

### EPIC E-007: Validação & Aceite

#### US-029: Testes Funcionais (QA)
- **Prioridade:** 🟠 ALTO
- **Status:** ⏳ Não Iniciado
- **Story Points:** 5
- **Assignee:** [QA]
- **Dependências:** US-014 até US-021
- **Descrição:** Testes manuais de funcionalidades do dashboard
- **Critérios de Aceite:**
  - [ ] Teste: Dashboard carrega sem erros
  - [ ] Teste: Filtro por região funciona
  - [ ] Teste: Tabela exibe 250+ países
  - [ ] Teste: Gráficos renderizam corretamente
  - [ ] Teste: Detalhes do país exibem informações corretas
  - [ ] Teste: Performance aceitável (< 3s load)
  - [ ] Teste: Sem erros no console do navegador
  - [ ] Relatório de bugs/issues gerado

#### US-030: Teste de Carga (Performance)
- **Prioridade:** 🟡 MÉDIO
- **Status:** ⏳ Não Iniciado
- **Story Points:** 3
- **Assignee:** [QA / Performance]
- **Dependências:** US-027, US-028
- **Descrição:** Validar performance sob carga
- **Critérios de Aceite:**
  - [ ] Ferramentas: k6, Apache Bench, ou Locust configuradas
  - [ ] Teste: 100 requisições simultâneas ao /health
  - [ ] Teste: Latência P95 ≤ 500ms
  - [ ] Teste: Sem timeouts ou erros
  - [ ] Relatório de métricas gerado
  - [ ] Documentação de resultados

#### US-031: Aceite Final & Sign-off
- **Prioridade:** 🔴 CRÍTICO
- **Status:** ⏳ Não Iniciado
- **Story Points:** 1
- **Assignee:** [PO / Product Manager]
- **Dependências:** Todos os US acima
- **Descrição:** Validação formal e aprovação do MVP
- **Critérios de Aceite:**
  - [ ] Todos os requisitos funcionais implementados
  - [ ] Todos os testes passando (unit, integration, functional)
  - [ ] Coverage ≥ 80%
  - [ ] Documentação completa
  - [ ] Performance validada
  - [ ] Sign-off assinado por PO e Tech Lead
  - [ ] Release notes publicadas

---

## 🚀 RELEASE 0.2 - APIs & Analytics (Out 2026)

**Objetivo:** Endpoints completos, gráficos avançados, exportação de dados  
**Deadline:** 31 de Outubro de 2026  
**Status:** 📋 Planejado  

---

### EPIC E-008: APIs Completas

#### US-032: Endpoint GET /api/v1/countries (Listar) 
- **Prioridade:** 🟠 ALTO
- **Story Points:** 5
- **Dependências:** [Release 0.1 completa]
- **Descrição:** API para listar países com filtros e paginação
- **Critérios de Aceite:**
  - [ ] Rota GET `/api/v1/countries` implementada
  - [ ] Query params: `page`, `limit`, `region`, `search`
  - [ ] Resposta paginada com metadata (total, página_atual, próxima)
  - [ ] Default limit=20, max limit=100
  - [ ] Filtro por região funcional
  - [ ] Busca por nome (like)
  - [ ] Status 200/400/500 apropriados
  - [ ] Swagger documentado

#### US-033: Endpoint GET /api/v1/countries/{code}
- **Prioridade:** 🟠 ALTO
- **Story Points:** 3
- **Dependências:** [Release 0.1 completa]
- **Descrição:** API para obter detalhes de um país específico
- **Critérios de Aceite:**
  - [ ] Rota GET `/api/v1/countries/{code}` (ISO2 ou ISO3)
  - [ ] Retorna país completo com relacionamentos
  - [ ] Status 200 ou 404
  - [ ] Swagger documentado

#### US-034: Endpoint GET /api/v1/regions
- **Prioridade:** 🟡 MÉDIO
- **Story Points:** 2
- **Dependências:** [Release 0.1 completa]
- **Descrição:** Agrupar países por região com agregações
- **Critérios de Aceite:**
  - [ ] Rota GET `/api/v1/regions` 
  - [ ] Retorna lista de regiões com: nome, total_países, população_total, área_total
  - [ ] Ordenável por população/área

#### US-035: Endpoint GET /api/v1/statistics
- **Prioridade:** 🟡 MÉDIO
- **Story Points:** 3
- **Dependências:** [Release 0.1 completa]
- **Descrição:** Estatísticas globais
- **Critérios de Aceite:**
  - [ ] Total de países, população global, área total
  - [ ] Top 5 países por população
  - [ ] Média de população por país
  - [ ] Distribuição por região

#### US-036: Rate Limiting & Cache
- **Prioridade:** 🟠 ALTO
- **Story Points:** 3
- **Dependências:** [Release 0.1 completa]
- **Descrição:** Implementar rate limiting e caching
- **Critérios de Aceite:**
  - [ ] Rate limit: 100 req/min por IP
  - [ ] Cache em Redis (ou em-memória)
  - [ ] TTL configurável (default 3600s)
  - [ ] Headers de cache apropriados

---

### EPIC E-009: Dashboard Avançado

#### US-037: Gráficos Avançados (Heatmap, Scatter)
- **Prioridade:** 🟡 MÉDIO
- **Story Points:** 5
- **Dependências:** [Release 0.1 completa]
- **Descrição:** Visualizações mais sofisticadas
- **Critérios de Aceite:**
  - [ ] Heatmap: Densidade populacional por região
  - [ ] Scatter: Correlação entre população e área
  - [ ] Ambos interativos com seleção

#### US-038: Comparação entre Países
- **Prioridade:** 🟡 MÉDIO
- **Story Points:** 4
- **Dependências:** US-017
- **Descrição:** Seletor para comparar 2-3 países
- **Critérios de Aceite:**
  - [ ] Multi-select de países
  - [ ] Comparação lado-a-lado em tabela
  - [ ] Gráficos comparativos

---

### EPIC E-010: Exportação de Dados

#### US-039: Exportação para CSV
- **Prioridade:** 🟠 ALTO
- **Story Points:** 3
- **Dependências:** [Release 0.1 completa]
- **Descrição:** Download de dados como CSV
- **Critérios de Aceite:**
  - [ ] Botão "Download CSV" no dashboard
  - [ ] Arquivo contém: name, iso2, iso3, region, população, área
  - [ ] Encoding UTF-8
  - [ ] Nomeação: `countries_YYYY-MM-DD.csv`

#### US-040: Exportação para PDF
- **Prioridade:** 🟡 MÉDIO
- **Story Points:** 4
- **Dependências:** US-039
- **Descrição:** Gerar PDF com relatório
- **Critérios de Aceite:**
  - [ ] Botão "Download PDF" 
  - [ ] PDF contém tabela + gráficos principais
  - [ ] Header com data/hora
  - [ ] Formatação profissional

---

## 📊 RELEASE 0.3 - Auth & Intelligence (Nov 2026)

**Objetivo:** Autenticação, séries temporais, alertas, insights com IA  
**Deadline:** 30 de Novembro de 2026  
**Status:** 📋 Planejado  

---

### EPIC E-011: Autenticação & Autorização

#### US-041: Autenticação com JWT
- **Prioridade:** 🟠 ALTO
- **Story Points:** 5
- **Dependências:** [Release 0.1 + 0.2 completas]
- **Descrição:** Sistema de login com JWT
- **Critérios de Aceite:**
  - [ ] Tabela de usuários com hash de senha
  - [ ] POST `/auth/login` com email/senha
  - [ ] Retorna JWT token válido por 24h
  - [ ] Middleware de autenticação em rotas protegidas
  - [ ] Refresh token implementado

#### US-042: Permissões & RBAC
- **Prioridade:** 🟡 MÉDIO
- **Story Points:** 3
- **Dependências:** US-041
- **Descrição:** Controle de acesso baseado em papéis
- **Critérios de Aceite:**
  - [ ] Papéis: admin, analyst, viewer
  - [ ] Permissões por rota/endpoint
  - [ ] Admin pode gerenciar usuários
  - [ ] Viewer acesso read-only

---

### EPIC E-012: Histórico & Séries Temporais

#### US-043: Histórico de Mudanças de Dados
- **Prioridade:** 🟠 ALTO
- **Story Points:** 5
- **Dependências:** [Release 0.1 + 0.2 completas]
- **Descrição:** Rastrear mudanças de população/área
- **Critérios de Aceite:**
  - [ ] Tabela `country_history` com timestamp, campo, valor_antigo, valor_novo
  - [ ] Auditoria automática em UPDATE
  - [ ] Query: histórico por país/período

#### US-044: Visualização de Trends
- **Prioridade:** 🟡 MÉDIO
- **Story Points:** 4
- **Dependências:** US-043
- **Descrição:** Gráficos de séries temporais
- **Critérios de Aceite:**
  - [ ] Linha: Evolução de população ao longo do tempo
  - [ ] Comparação entre países
  - [ ] Filtro por período (1m, 3m, 6m, 1y)

---

### EPIC E-013: Alertas & Notificações

#### US-045: Sistema de Alertas
- **Prioridade:** 🟡 MÉDIO
- **Story Points:** 4
- **Dependências:** [Release 0.1 + 0.2 completas]
- **Descrição:** Alertas baseados em condições
- **Critérios de Aceite:**
  - [ ] Admin cria regra: "Se população > X, alertar"
  - [ ] Email/webhook ao disparar
  - [ ] Histórico de alertas

#### US-046: Notificações em Real-time
- **Prioridade:** 🟡 MÉDIO
- **Story Points:** 3
- **Dependências:** US-045
- **Descrição:** WebSocket para notificações live
- **Critérios de Aceite:**
  - [ ] Conexão WebSocket estabelecida
  - [ ] Alertas entregues em tempo real
  - [ ] Dashboard atualiza sem refresh

---

### EPIC E-014: IA Generativa & Insights

#### US-047: Integração com Claude API
- **Prioridade:** 🟡 MÉDIO
- **Story Points:** 5
- **Dependências:** [Release 0.1 + 0.2 completas]
- **Descrição:** Usar IA para gerar insights
- **Critérios de Aceite:**
  - [ ] Conexão com Claude API (Anthropic)
  - [ ] Prompts estruturados para análises
  - [ ] Cache de prompts para economia

#### US-048: Análise Inteligente de Dados
- **Prioridade:** 🟡 MÉDIO
- **Story Points:** 4
- **Dependências:** US-047
- **Descrição:** Gerar relatórios com IA
- **Critérios de Aceite:**
  - [ ] "Analisar região X" → IA fornece insights
  - [ ] "Comparar países A e B" → IA gera análise
  - [ ] Resultados salvos em histórico

#### US-049: Recomendações Personalizadas
- **Prioridade:** 🟢 BAIXO
- **Story Points:** 3
- **Dependências:** US-048
- **Descrição:** IA recomenda análises baseadas no histórico
- **Critérios de Aceite:**
  - [ ] Recomendações na dashboard
  - [ ] Baseadas em padrões de uso

---

## 📈 ROADMAP DE RELEASES

```
┌─────────────────────────────────────────────────────────┐
│ RELEASE 0.1 (Set 2026) - MVP                           │
│ ✅ API REST Countries                                  │
│ ✅ Banco de dados SQLite                               │
│ ✅ Dashboard básico (KPIs, filtros, tabelas, gráficos) │
│ ✅ Health check & Swagger                              │
│ ✅ Testes unitários (80%+ coverage)                    │
└─────────────────────────────────────────────────────────┘
              ↓ (30 Sep 2026)
┌─────────────────────────────────────────────────────────┐
│ RELEASE 0.2 (Out 2026) - APIs & Analytics              │
│ 🔄 Endpoints REST completos                            │
│ 🔄 Rate limiting & Cache                               │
│ 🔄 Gráficos avançados                                  │
│ 🔄 Exportação (CSV, PDF)                               │
│ 🔄 Comparação entre países                             │
└─────────────────────────────────────────────────────────┘
              ↓ (31 Oct 2026)
┌─────────────────────────────────────────────────────────┐
│ RELEASE 0.3 (Nov 2026) - Auth & Intelligence           │
│ 🔄 Autenticação JWT                                    │
│ 🔄 Histórico & Séries Temporais                        │
│ 🔄 Alertas & Notificações                              │
│ 🔄 Integração Claude API (IA Insights)                 │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 ESTATÍSTICAS DO BACKLOG

### Por Release

| Release | Total US | Story Points | Estimado (dias) |
|---------|----------|--------------|-----------------|
| **0.1** | 31 | 98 | 27 dias |
| **0.2** | 10 | 42 | 12 dias |
| **0.3** | 9 | 31 | 9 dias |
| **TOTAL** | 50 | 171 | 48 dias |

### Por Prioridade

| Prioridade | Count | % |
|-----------|-------|-----|
| 🔴 CRÍTICO | 10 | 20% |
| 🟠 ALTO | 20 | 40% |
| 🟡 MÉDIO | 14 | 28% |
| 🟢 BAIXO | 6 | 12% |

### Por Tipo

| Tipo | Count |
|------|-------|
| Infrastructure/Setup | 3 |
| Backend | 13 |
| Frontend | 9 |
| Testing/QA | 4 |
| Documentation/DevOps | 5 |
| Validation | 2 |
| APIs | 5 |
| Advanced (0.2+) | 9 |

---

## 🔄 DEPENDÊNCIAS & CRÍTICOS

### Caminho Crítico (Critical Path)

```
US-001 (Setup)
    ↓
US-002 (Git)
    ↓
US-010 (FastAPI)
    ↓
┌─────────────────────────────────┐
│ US-004 (REST API Client)        │
│ US-005 (Models)                 │
│ US-006 (DB Config)              │
│ US-007 (Normalize)              │
│ US-008 (Persist)                │
│ US-009 (Ingest Script)          │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ US-014 (Streamlit Setup)        │
│ US-015 (KPIs)                   │
│ US-016 (Filters)                │
│ US-017 (Table)                  │
│ US-018 (Charts)                 │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ US-022 (Unit Tests)             │
│ US-023 (Integration Tests)      │
│ US-029 (Functional Tests)       │
└─────────────────────────────────┘
    ↓
US-031 (Sign-off)
```

### Bloqueadores Conhecidos

- [ ] Indisponibilidade da API REST Countries (mitigado com cache)
- [ ] Mudanças no schema da API (mitigado com versionamento)
- [ ] Atrasos em validações do PO (mitigue com daily standups)

---

## 🎯 PRIORIZAÇÃO & PRÓXIMAS AÇÕES

### Próximas 2 Semanas (17-28 de Set)

- [ ] **US-004:** Cliente HTTP para REST Countries API
- [ ] **US-005:** Modelos SQLAlchemy
- [ ] **US-006:** Configuração SQLite
- [ ] **US-007:** Normalização de dados
- [ ] **US-008:** Persistência em banco

### Semanas 3-4 (29 Set - 12 Out)

- [ ] **US-009:** Script de ingestão
- [ ] **US-012:** Scheduler automático
- [ ] **US-014 a US-021:** Dashboard Streamlit

### Semanas 5+ (13 Out+)

- [ ] **US-022 a US-030:** Testes completos
- [ ] **US-025 a US-028:** Documentação e deployment
- [ ] **US-031:** Aceite final

---

## 📌 NOTAS IMPORTANTES

1. **Estimativas** em Story Points são orientativas e podem variar em ±20%
2. **Dependências** podem criar gargalos; planejar paralelismo onde possível
3. **Testes** (US-022+) devem ser desenvolvidos concorrentemente com features
4. **Documentação** deve ser atualizada incrementalmente, não deixar para o final
5. **Releases 0.2 e 0.3** estão planejadas mas podem ser ajustadas conforme feedback

---

## 🏁 TEMPLATE PARA DESENVOLVIMENTO

Cada história deve incluir:

```markdown
## US-XXX: [Título]
- **Prioridade:** [CRÍTICO/ALTO/MÉDIO/BAIXO]
- **Status:** [Não Iniciado/Em Progresso/Bloqueado/Concluído]
- **Story Points:** [1/2/3/5/8]
- **Assignee:** [Nome ou TBD]
- **Dependências:** [US-001, US-002]
- **Descrição:** [Narrativa clara do que precisa ser feito]
- **Critérios de Aceite:**
  - [ ] Critério 1
  - [ ] Critério 2
  - [ ] ...
- **Notas/Bloqueadores:** [Opcional]
```

---

**Documento versão 1.0 | Última atualização: 15/09/2026**  
**Responsável:** Product Owner / Tech Lead  
**Próxima revisão:** 22/09/2026
