# Checklist - Revisão Técnica da API
## PG genIA MVP-01: REST Countries Dashboard

---

## ❌ 1. PONTOS DE ACOPLAMENTO ALTOS

### Críticos

- [ ] CountryService ↔ Repository - Service cria instâncias manualmente
  - Localização: `app/service/country_service.py:39-41`
  - Solução: Injetar Repository no construtor

- [ ] API Routes → Service Factory - Factory repetida em cada endpoint
  - Localização: `app/api/country_routes.py:50` (repetido 14x)
  - Solução: Criar middleware centralizado

- [ ] Connection ↔ Base Models - Importação circular potencial
  - Localização: `app/database/connection.py:72`
  - Solução: Lazy import dentro de init_db()

### Médios

- [ ] Service → Logger Global - Logger singleton sem injeção
  - Localização: `app/service/country_service.py:26`
  - Solução: Injetar logger como dependência

- [ ] API Routes → Múltiplos Modelos Pydantic - 10+ imports
  - Localização: `app/api/country_routes.py:10-20`
  - Solução: Usar schema factory único

---

## ❌ 2. VALIDAÇÕES FALTANDO

### Críticas (IMPLEMENTAR AGORA)

- [ ] ISO Code Duplicação - Valida iso2, não iso3
  - Onde: `CountryService.create_country()` linha 105-110
  - Solução: Validar iso2 AND iso3

- [ ] Region Enum Validation - Aceita qualquer string
  - Onde: `CountryService.list_countries()` linha 130
  - Solução: Validar contra {Africa, Americas, Asia, Europe, Oceania}

- [ ] Coordinate Validation - Não valida em UPDATE
  - Onde: `PUT /api/v1/countries/{id}` sem validadores
  - Solução: Adicionar validadores em CountryUpdate

- [ ] Population Range - Sem limite máximo
  - Onde: `app/models/task.py:88` apenas ge=0
  - Solução: Adicionar le=2000000000

### Altos (IMPLEMENTAR SPRINT +1)

- [ ] Empty Relationships - Aceita países sem idioma/moeda
  - Onde: `CountryService` sem validação
  - Solução: Validar mínimo 1 idioma

- [ ] Sync ID Uniqueness - Usa timestamp sem validação
  - Onde: `POST /api/v1/sync` linha 330-335
  - Solução: Usar UUID em vez de timestamp

- [ ] Database Connection Pool Health - Sem validação
  - Onde: `app/database/connection.py:38`
  - Solução: Adicionar health check na inicialização

- [ ] Batch Size Limit - Sem limite de tamanho
  - Onde: `CountryService.sync_countries_batch()` linha 210
  - Solução: Limitar a 1000 registros por batch

### Médios (IMPLEMENTAR SPRINT +2)

- [ ] Pagination Boundary - Não valida page > total_pages
  - Solução: Retornar 404 ou avisar página inexistente

- [ ] Update Concurrency - Sem versionamento/ETag
  - Solução: Implementar ETag ou versionamento

- [ ] Delete Cascade Validation - Sem testes
  - Solução: Testar cascade delete funciona

- [ ] String Encoding - Sem normalização de acentos
  - Solução: Adicionar field_validator

---

## ❌ 3. 5 TESTES PRIORITÁRIOS

### 🥇 PRIORIDADE 1 - SPRINT ATUAL (Crítico)

- [ ] Teste: Duplicate Country Rejection
  - Descrição: POST /api/v1/countries com ISO2 duplicado → 409
  - Arquivo: tests/integration/test_country_crud.py
  - Tempo: 30 min

- [ ] Teste: Batch Upsert Consistency
  - Descrição: sync_countries_batch() insere 250 = 250 success
  - Arquivo: tests/integration/test_sync.py
  - Tempo: 45 min

- [ ] Teste: Pagination Correctness
  - Descrição: list_countries(page=1, limit=20) retorna 20 items
  - Arquivo: tests/integration/test_pagination.py
  - Tempo: 30 min

- [ ] Teste: Cascade Delete
  - Descrição: DELETE /api/v1/countries/{id} remove relacionamentos
  - Arquivo: tests/integration/test_delete.py
  - Tempo: 30 min

- [ ] Teste: Service Exception Translation
  - Descrição: Service traduz IntegrityError → DuplicateRecordError
  - Arquivo: tests/unit/test_service_errors.py
  - Tempo: 30 min

**Total Sprint 0:** 165 minutos (2.75 horas)

---

### 🥈 PRIORIDADE 2 - SPRINT +1 (Alto)

- [ ] Teste: Data Quality Scoring (30 min)
  - tests/unit/test_priority_advisor.py

- [ ] Teste: API HTTP Status Codes (45 min)
  - tests/integration/test_api_status_codes.py

- [ ] Teste: Connection Pool (45 min)
  - tests/integration/test_connection_pool.py

- [ ] Teste: Business Event Logging (30 min)
  - tests/unit/test_logging.py

- [ ] Teste: Dependency Injection (30 min)
  - tests/unit/test_dependency_injection.py

**Total Sprint +1:** 180 minutos (3 horas)

---

### 🥉 PRIORIDADE 3 - SPRINT +2 (Médio)

- [ ] Teste: Concurrent Updates
  - tests/integration/test_concurrency.py

- [ ] Teste: Empty Result Handling
  - tests/integration/test_empty_results.py

- [ ] Teste: Transaction Rollback
  - tests/integration/test_transactions.py

- [ ] Teste: Swagger Documentation
  - tests/integration/test_swagger.py

- [ ] Teste: Type Hints (mypy)
  - CI/CD check

---

## 📊 SUMMARY

### Ações Imediatas (Release 0.1)

- [ ] Refatorar CountryService.__init__() para injetar Repository
- [ ] Adicionar validação de iso_code_3 em create_country()
- [ ] Validar region contra enum em list_countries()
- [ ] Adicionar limite de 1000 registros em upsert_batch()
- [ ] Usar UUID para sync_id em vez de timestamp
- [ ] Escrever 5 testes PRIORIDADE 1

### Acoplamento - Refatorações

- [ ] Criar service factory middleware centralizado
- [ ] Injetar Repository no construtor de Service
- [ ] Lazy import em init_db()
- [ ] Injetar logger como dependência

### Validações - Implementar

- [ ] ISO2 + ISO3 duplication check
- [ ] Region enum validation
- [ ] Coordinate validation em UPDATE
- [ ] Population range (0-2B)
- [ ] Batch size limit (max 1000)
- [ ] Sync ID uniqueness (UUID)

---

## ⚠️ CONCLUSÃO

**Status:** 🟡 BOAS FUNDAÇÕES, REQUER REFINAMENTO

**Riscos sem correção:**
- Data integrity (duplicatas)
- Dashboard breaks (missing validation)
- Performance (sem batch limits)
- Testabilidade (alto acoplamento)

**Recomendação:** Implementar ações imediatas + 5 testes PRIORIDADE 1 antes de Release 0.1
