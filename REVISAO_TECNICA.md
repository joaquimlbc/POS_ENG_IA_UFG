# Revisão Técnica - Core da API
## PG genIA MVP-01: REST Countries Dashboard

**Data:** 16 de Setembro de 2026  
**Revisor:** Arquiteto de Software Sênior  
**Status:** Análise Crítica

---

## 1️⃣ PONTOS DE ACOPLAMENTO ALTOS

### 🔴 Acoplamento Crítico Identificado

- [ ] **CountryService → Repository** (ALTO)
  - **Problema:** Service cria instâncias do Repository manualmente
  - **Impacto:** Difícil de testar (mock), acoplado à implementação
  - **Linha:** `app/service/country_service.py:39-41`
  - **Solução:** Injetar Repository no construtor do Service
  
- [ ] **API Routes → Service** (ALTO)
  - **Problema:** Cada endpoint cria nova instância de Service
  - **Impacto:** Código repetido, difícil de mudar lógica
  - **Linha:** `app/api/country_routes.py:50` (factory repetido)
  - **Solução:** Criar service factory centralizado como middleware

- [ ] **Connection → Base Models** (MÉDIO-ALTO)
  - **Problema:** Base importa de models em `connection.py:72`
  - **Impacto:** Importação circular potencial
  - **Linha:** `app/database/connection.py:72`
  - **Solução:** Lazy import dentro da função `init_db()`

- [ ] **Service → Logger Global** (MÉDIO)
  - **Problema:** Service usa logger singleton `get_logger(__name__)`
  - **Impacto:** Difícil de testar logs, dependência global
  - **Linha:** `app/service/country_service.py:26`
  - **Solução:** Injetar logger como dependência

- [ ] **API Routes → Models Pydantic** (MÉDIO)
  - **Problema:** Routes importam 10+ modelos Pydantic diferentes
  - **Impacto:** Mudança em um modelo quebra imports
  - **Linha:** `app/api/country_routes.py:10-20`
  - **Solução:** Usar schema factory ou namespace único

### ✅ Bom Acoplamento (Mantém)

- [x] **API → Service** via Dependency Injection (BAIXO)
- [x] **Service → Repository** (será injetado)
- [x] **Repository → ORM Models** (apropriado)
- [x] **Pydantic → SQLAlchemy Models** (one-way, OK)

---

## 2️⃣ VALIDAÇÕES FALTANDO

### 🔴 Críticas

- [ ] **ISO Codes Duplicação** (CRÍTICO)
  - **Onde falta:** `CountryService.create_country()` checa `iso2` apenas
  - **Problema:** Múltiplos países podem ter mesmo `iso3` se lógica falhar
  - **Arquivo:** `app/service/country_service.py:105-110`
  - **Solução:** Validar `iso2` E `iso3` juntos ou deixar banco enforçar
  ```python
  # Adicionar:
  existing_iso3 = self.country_repo.get_by_iso3(data.iso_code_3)
  if existing_iso3:
      raise DuplicateRecordError(...)
  ```

- [ ] **Region Enum Validation** (CRÍTICO)
  - **Onde falta:** Não valida se region é uma das 5 permitidas
  - **Problema:** Banco aceita qualquer string, quebra dashboard filters
  - **Arquivo:** `app/service/country_service.py:130` (list_countries)
  - **Solução:** Validar contra enum antes de query
  ```python
  VALID_REGIONS = {"Africa", "Americas", "Asia", "Europe", "Oceania"}
  if region and region not in VALID_REGIONS:
      raise ValidationError("region", f"Must be one of {VALID_REGIONS}")
  ```

- [ ] **Coordinate Validation** (ALTO)
  - **Onde falta:** Pydantic valida, mas API não valida update
  - **Problema:** `PUT /countries/{id}` sem validação coordenadas
  - **Arquivo:** `app/api/country_routes.py:169-180`
  - **Solução:** Adicionar validadores no `CountryUpdate` schema

- [ ] **Population Range Validation** (ALTO)
  - **Onde falta:** Não valida limites realistas (0 a 2B)
  - **Problema:** Aceita valores negativos ou > população mundial
  - **Arquivo:** `app/models/task.py:88` (only `ge=0`)
  - **Solução:** Adicionar `le=2000000000`

### 🟠 Altos

- [ ] **Empty Relationship Lists** (ALTO)
  - **Onde falta:** Aceita países sem nenhum idioma/moeda/fuso
  - **Problema:** Dashboard quebra se não há relacionamentos
  - **Arquivo:** `app/service/country_service.py` (sem validação)
  - **Solução:** Validar que pelo menos 1 idioma existe

- [ ] **Sync ID Uniqueness** (ALTO)
  - **Onde falta:** `POST /sync` gera timestamp sem verificar colisão
  - **Problema:** 2 syncs no mesmo segundo = mesmo ID
  - **Arquivo:** `app/api/country_routes.py:330-335`
  - **Solução:** Usar UUID em vez de timestamp

- [ ] **Database Connection Pool** (ALTO)
  - **Onde falta:** Não valida que pool está saudável antes de usar
  - **Problema:** Silentemente falha se DB desconecta
  - **Arquivo:** `app/database/connection.py:38`
  - **Solução:** Adicionar health check na inicialização

- [ ] **Batch Size Limit** (ALTO)
  - **Onde falta:** `sync_countries_batch()` sem limite de tamanho
  - **Problema:** 10k países = memory leak, timeout
  - **Arquivo:** `app/service/country_service.py:210`
  - **Solução:** Limitar a 1000 registros por batch

### 🟡 Médios

- [ ] **Pagination Boundary** (MÉDIO)
  - **Onde falta:** Não valida se `page` > total_pages
  - **Problema:** Retorna vazio silenciosamente
  - **Arquivo:** `app/api/country_routes.py:110-120`
  - **Solução:** Retornar 404 ou avisar que página não existe

- [ ] **Update Concurrency** (MÉDIO)
  - **Onde falta:** Sem versionamento (updated_at) para optimistic lock
  - **Problema:** 2 updates simultâneos podem sobrescrever
  - **Arquivo:** `app/service/country_service.py:155-165`
  - **Solução:** Implementar ETag ou versionamento

- [ ] **Delete Cascade Validation** (MÉDIO)
  - **Onde falta:** Delete not implemented para related entities
  - **Problema:** Pode deixar idiomas órfãos se falhar
  - **Arquivo:** `app/database/models.py:54` (cascade configurado, mas sem teste)
  - **Solução:** Testar cascade delete funciona

- [ ] **String Encoding** (MÉDIO)
  - **Onde falta:** Acentos em nomes podem falhar
  - **Problema:** Nomes com acentos (São Paulo) quebram em alguns DBs
  - **Arquivo:** `app/models/task.py:52` (sem encoding spec)
  - **Solução:** Adicionar `@field_validator` para normalizar

---

## 3️⃣ 5 TESTES PRIORITÁRIOS

### 🥇 PRIORIDADE 1 - CRÍTICO (Sprint Atual)

- [ ] **Teste: Duplicate Country Rejection**
  - **O que testar:** POST /api/v1/countries com ISO2 duplicado
  - **Esperado:** 409 Conflict + DuplicateRecordError
  - **Por quê:** Garante data integrity constraint
  - **Arquivo:** `tests/integration/test_country_crud.py`
  - **Código:**
  ```python
  def test_create_duplicate_country_iso2(service):
      data = CountryCreate(iso_code_2="BR", ...)
      service.create_country(data)
      
      with pytest.raises(DuplicateRecordError):
          service.create_country(data)  # Duplicado
  ```

- [ ] **Teste: Batch Upsert Consistency**
  - **O que testar:** sync_countries_batch() insere 250 países sem erros
  - **Esperado:** 250 inserted, 0 failed
  - **Por quê:** Validar ingestão completa funciona
  - **Arquivo:** `tests/integration/test_sync.py`
  - **Código:**
  ```python
  def test_batch_upsert_250_countries(service_with_db):
      countries = [CountryCreate(...) for _ in range(250)]
      result = service_with_db.sync_countries_batch(countries)
      
      assert result.total_processed == 250
      assert result.failed == 0
  ```

- [ ] **Teste: Pagination Correctness**
  - **O que testar:** list_countries() retorna correto número de itens
  - **Esperado:** page=1, limit=20 retorna 20 items
  - **Por quê:** Dashboard depende de paginação correta
  - **Arquivo:** `tests/integration/test_pagination.py`
  - **Código:**
  ```python
  def test_list_countries_pagination(service_with_250_countries):
      result = service_with_250_countries.list_countries(page=1, limit=20)
      
      assert len(result.items) == 20
      assert result.total == 250
      assert result.pages == 13
  ```

- [ ] **Teste: Cascade Delete**
  - **O que testar:** Deletar país remove idiomas/moedas/fusos
  - **Esperado:** Country deletado, relationships vazias
  - **Por quê:** Evita dados órfãos
  - **Arquivo:** `tests/integration/test_delete.py`
  - **Código:**
  ```python
  def test_delete_country_cascade(service_with_relationships):
      country = service_with_relationships.get_country(1)
      assert len(country.languages) > 0
      
      service_with_relationships.delete_country(1)
      
      with pytest.raises(RecordNotFoundError):
          service_with_relationships.get_country(1)
  ```

- [ ] **Teste: Service Layer Exception Handling**
  - **O que testar:** Service traduz DB errors para domain exceptions
  - **Esperado:** IntegrityError → DuplicateRecordError
  - **Por quê:** API exception handlers dependem disto
  - **Arquivo:** `tests/unit/test_service_errors.py`
  - **Código:**
  ```python
  def test_service_duplicate_error_conversion(service_with_mock_repo):
      service_with_mock_repo.country_repo.create.side_effect = \
          SQLAlchemyIntegrityError(None, None, None)
      
      with pytest.raises(DuplicateRecordError):
          service_with_mock_repo.create_country(data)
  ```

### 🥈 PRIORIDADE 2 - ALTO (Sprint +1)

- [ ] **Teste: Data Quality Scoring**
  - **O que testar:** PriorityAdvisor.assess_quality() retorna score 0-100
  - **Esperado:** Complete data = 90+, invalid = <50
  - **Por quê:** Validar lógica de priorização
  - **Arquivo:** `tests/unit/test_priority_advisor.py`

- [ ] **Teste: API Status Codes**
  - **O que testar:** Cada endpoint retorna status code correto
  - **Esperado:** POST=201, DELETE=204, GET=200, NotFound=404
  - **Por quê:** Contratos REST devem ser respeitados
  - **Arquivo:** `tests/integration/test_api_status_codes.py`

- [ ] **Teste: Connection Pooling**
  - **O que testar:** Database connection pool funciona corretamente
  - **Esperado:** 5 conexões mantidas, overflow handled
  - **Por quê:** Performance sob carga
  - **Arquivo:** `tests/integration/test_connection_pool.py`

- [ ] **Teste: Logging Events**
  - **O que testar:** Service loga eventos de negócio
  - **Esperado:** Create/Update/Delete geram log entries
  - **Por quê:** Auditoria e troubleshooting
  - **Arquivo:** `tests/unit/test_logging.py`

- [ ] **Teste: Dependency Injection**
  - **O que testar:** Service pode ser mockado em API routes
  - **Esperado:** Endpoint usa injected service, não cria novo
  - **Por quê:** Testabilidade do API layer
  - **Arquivo:** `tests/unit/test_dependency_injection.py`

### 🥉 PRIORIDADE 3 - MÉDIO (Sprint +2)

- [ ] **Teste: Concurrent Updates**
  - Validar que 2 updates simultâneos não causam data loss
  - **Arquivo:** `tests/integration/test_concurrency.py`

- [ ] **Teste: Empty Result Handling**
  - GET /api/v1/countries?region=NonExistent retorna lista vazia (200)
  - **Arquivo:** `tests/integration/test_empty_results.py`

- [ ] **Teste: Database Transaction Rollback**
  - Batch com erro no meio reverte todas as mudanças
  - **Arquivo:** `tests/integration/test_transactions.py`

- [ ] **Teste: Swagger Documentation**
  - Todos os endpoints documentados com descrições
  - **Arquivo:** `tests/integration/test_swagger.py`

- [ ] **Teste: Type Hints Coverage**
  - mypy validation 0 errors
  - **Arquivo:** CI/CD check

---

## 📊 RESUMO EXECUTIVO

### Acoplamento Atual

```
ALTO (⚠️):     3 pontos críticos
MÉDIO-ALTO:    2 pontos importantes
MÉDIO:         2 pontos
BAIXO (✅):    3 pontos bem arquitetados
```

### Validações Faltando

```
CRÍTICO:  4 validações (ISO, region, coordenadas, population)
ALTO:     4 validações (relacionamentos, sync ID, pool, batch size)
MÉDIO:    4 validações (pagination, concurrency, cascade, encoding)
```

### Testes Recomendados

```
Sprint 0 (Imediato):     5 testes críticos
Sprint +1:               5 testes altos
Sprint +2:               5 testes médios
TOTAL:                   15 testes prioritários
```

---

## 🔧 AÇÕES IMEDIATAS

### Para Release 0.1 - Fazer Agora

1. [ ] Refatorar `CountryService.__init__()` para injetar Repository
2. [ ] Adicionar validação de `iso_code_3` em `create_country()`
3. [ ] Validar region contra enum em `list_countries()`
4. [ ] Adicionar limite de 1000 registros em `upsert_batch()`
5. [ ] Usar UUID para sync_id em vez de timestamp

### Para Release 0.2 - Próxima Sprint

1. [ ] Implementar ETag/versionamento para updates
2. [ ] Adicionar database health check
3. [ ] Centralizar service factory em middleware
4. [ ] Injetar logger como dependência
5. [ ] Validar coordenadas antes de persist

### Para Release 0.3 - Futuro

1. [ ] Adicionar transaction logging
2. [ ] Implementar retry logic com exponential backoff
3. [ ] Add async/await para operações I/O
4. [ ] Implementar caching layer

---

## ✅ CONCLUSÃO

**Status:** 🟡 **BOAS FUNDAÇÕES, REQUER REFINAMENTO**

### Pontos Fortes
- ✅ Arquitetura em camadas bem definida
- ✅ Type hints 100%
- ✅ Exception handling estruturado
- ✅ Dependency injection parcialmente implementado

### Pontos Fracos
- ⚠️ Acoplamento service-repository (será refatorado)
- ⚠️ Validações faltando em 12+ locais
- ⚠️ Testes não escritos ainda
- ⚠️ Sem tratamento de concorrência

### Recomendação
**Implementar as 5 ações imediatas antes de Release 0.1**

Sem essas correções, riscos:
- 🔴 Data integrity (duplicatas)
- 🔴 Dashboard breaks (missing regions)
- 🔴 Performance degrada (sem batch limit)
- 🔴 Dificuldade de testes (acoplamento)

---

**Revisão completa | Data: 16/09/2026**  
**Próxima revisão:** Após implementação das ações imediatas
