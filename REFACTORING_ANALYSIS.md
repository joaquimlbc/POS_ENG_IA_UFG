# Análise de Refatoração - DRY e SRP

**Data:** 17/09/2026  
**Foco:** country_service.py e repository.py  
**Objetivo:** Reduzir duplicação (DRY) e melhorar responsabilidades (SRP)  
**Impacto:** Sem mudança de comportamento externo

---

## 🔴 Violações DRY Identificadas

### 1. Verificação de Existência de País (7 repetições)

| Método | Linhas | Padrão |
|--------|--------|--------|
| get_country | 142-144 | country = get_by_id(); if not; raise |
| update_country | 227-229 | country = get_by_id(); if not; raise |
| delete_country | 251-254 | country = get_by_id(); if not; return |
| add_languages | 469-471 | country = get_by_id(); if not; raise |
| add_currencies | 505-507 | country = get_by_id(); if not; raise |
| add_timezones | 541-543 | country = get_by_id(); if not; raise |
| validate_country_integrity | 580-582 | country = get_by_id(); if not; raise |

**Solução:** Extract method `_ensure_country_exists(country_id)`

---

### 2. Adição de Relacionamentos (3 repetições)

Métodos: `add_languages` (454-488), `add_currencies` (490-524), `add_timezones` (526-560)

**Padrão repetido:**
```python
country = self.country_repo.get_by_id(country_id)
if not country:
    raise RecordNotFoundError(...)

for data in items:
    entity = EntityClass(country_id=country_id, **data.model_dump())
    self.session.add(entity)

self.session.commit()
self.session.refresh(country)
logger.info(f"Added {len(items)} ...")
return CountryDetailResponse.model_validate(country)
```

**Solução:** Extract generic method `_add_related_entities(country_id, entity_class, items_data, log_msg)`

---

### 3. Queries Repetidas no Repository

**get_by_iso2 (linha 94) vs get_by_iso3 (linha 105):**
```python
# Ambos fazem:
self.session.query(Country).filter(Country.{field} == code.upper()).first()
```

**get_all (linha 118) vs get_by_region (linha 137):**
```python
# Padrão: query → filter (optional) → order → limit → offset → all()
```

**Solução:** Extract `_query_countries(filter=None, limit=100, offset=0)` helper

---

### 4. Conversão para Response (5 repetições)

| Linha | Padrão |
|-------|--------|
| 128 | CountryResponse.model_validate(country) |
| 146 | CountryDetailResponse.model_validate(country) |
| 168 | CountryDetailResponse.model_validate(country) |
| 238 | CountryResponse.model_validate(updated) |
| 169 (repository) | CountryResponse.model_validate(c) |

**Solução:** Extract `_to_response(country)` e `_to_detail_response(country)`

---

### 5. Sincronização de Resultado (2 repetições)

Criação de `CountrySyncResult` em 2 lugares:
- Sucesso (linha 313-325)
- Falha parcial (linha 333-345)

**Padrão:** Duplicação de inicialização de dataclass

**Solução:** Extract `_create_sync_result(status, messages, counts, quality)`

---

## 🟠 Violações SRP Identificadas

### 1. CountryService - 5 Responsabilidades

| Responsabilidade | Métodos |
|-----------------|---------|
| **Validação** | create_country (ISO uniqueness check) |
| **Orquestração** | Todas (delegam para repos) |
| **Transformação** | get_country, update_country (model_validate) |
| **Logging** | Todas |
| **Qualidade de Dados** | sync_countries_batch, identify_data_gaps (priority_advisor) |

**SRP Ideal:**
- Service: Orquestração de negócio apenas
- Validator: Validações de regra
- ResponseMapper: Conversões de modelo
- Logger: Logging centralizado (talvez middleware)

---

### 2. CountryRepository - Responsabilidades Misturadas

```
Responsabilidades atuais:
├── CRUD (create, read, update, delete) ✅ SRP
├── Batch Operations (upsert_batch) ✅ OK (ainda data-access)
├── Pydantic Conversion (model_validate) ❌ VIOLAÇÃO
└── Query Building (get_paginated) ✅ OK
```

**Problema:** Repository converte para Pydantic (linha 169 no get_paginated)

**Solução:** Repository retorna modelos ORM; Service faz conversão

---

### 3. Repository Query Methods - Duplicação de Lógica

- `get_by_id`: query + filter + first
- `get_by_iso2`: query + filter + first  
- `get_by_iso3`: query + filter + first
- `get_all`: query + order + limit + offset
- `get_by_region`: query + filter + order + limit + offset

Todas compartilham o padrão base

---

## ✅ Mudanças Propostas (sem quebrar contrato externo)

### **Arquivo: app/service/country_service.py**

#### Mudança 1: Extract `_ensure_country_exists`

**Antes (7 locais):**
```python
country = self.country_repo.get_by_id(country_id)
if not country:
    raise RecordNotFoundError("Country", f"id={country_id}")
```

**Depois:**
```python
def _ensure_country_exists(self, country_id: int) -> Country:
    """Internal helper: ensure country exists or raise."""
    country = self.country_repo.get_by_id(country_id)
    if not country:
        raise RecordNotFoundError("Country", f"id={country_id}")
    return country
```

**Aplicar em:** linhas 142, 227, 469, 505, 541, 580

---

#### Mudança 2: Extract `_add_related_entities`

**Antes (3 métodos):**
```python
def add_languages(self, country_id: int, languages: List[LanguageCreate]):
    country = self.country_repo.get_by_id(country_id)
    if not country:
        raise RecordNotFoundError(...)
    for lang_data in languages:
        language = Language(country_id=country_id, **lang_data.model_dump())
        self.session.add(language)
    self.session.commit()
    self.session.refresh(country)
    logger.info(f"Added {len(languages)} languages to {country.name_common}")
    return CountryDetailResponse.model_validate(country)
```

**Depois:**
```python
def _add_related_entities(
    self, 
    country_id: int,
    entity_class: type,
    items_data: List,
    entity_type: str
) -> CountryDetailResponse:
    """Internal: generic related entity adder (DRY)."""
    country = self._ensure_country_exists(country_id)
    
    for item_data in items_data:
        entity = entity_class(
            country_id=country_id,
            **item_data.model_dump()
        )
        self.session.add(entity)
    
    self.session.commit()
    self.session.refresh(country)
    logger.info(
        f"Added {len(items_data)} {entity_type} to {country.name_common}"
    )
    return self._to_detail_response(country)

def add_languages(self, country_id: int, languages: List[LanguageCreate]):
    return self._add_related_entities(country_id, Language, languages, "languages")

def add_currencies(self, country_id: int, currencies: List[CurrencyCreate]):
    return self._add_related_entities(country_id, Currency, currencies, "currencies")

def add_timezones(self, country_id: int, timezones: List[TimezoneCreate]):
    return self._add_related_entities(country_id, Timezone, timezones, "timezones")
```

**Benefícios:** 50+ linhas removidas, lógica unificada

---

#### Mudança 3: Extract Response Mappers

**Antes:**
```python
CountryResponse.model_validate(country)  # 5 lugares
CountryDetailResponse.model_validate(country)  # 3 lugares
```

**Depois:**
```python
def _to_response(self, country: Country) -> CountryResponse:
    """Convert Country ORM to response (SRP)."""
    return CountryResponse.model_validate(country)

def _to_detail_response(self, country: Country) -> CountryDetailResponse:
    """Convert Country ORM to detail response (SRP)."""
    return CountryDetailResponse.model_validate(country)

# Uso:
return self._to_response(country)  # Em vez de model_validate
return self._to_detail_response(country)
```

**Benefícios:** Centralização, facilita testes, reutilizável

---

#### Mudança 4: Extract Sync Result Creation

**Antes (2 locais):**
```python
# Sucesso
result = CountrySyncResult(
    sync_id=sync_id,
    total_processed=total,
    inserted=inserted,
    updated=updated,
    failed=0,
    quality_summary=quality_summary,
    status="success",
    message=f"...",
    started_at=started_at,
    completed_at=completed_at,
)

# Falha
result = CountrySyncResult(
    sync_id=sync_id,
    total_processed=len(countries_data),
    inserted=e.successful,
    updated=0,
    failed=e.failed,
    quality_summary={},
    status="partial_failure",
    message=f"...",
    started_at=started_at,
    completed_at=completed_at,
)
```

**Depois:**
```python
def _create_sync_result(
    self,
    sync_id: str,
    status: str,
    total: int,
    inserted: int,
    updated: int,
    failed: int,
    message: str,
    started_at: datetime,
    quality_summary: dict = None,
) -> CountrySyncResult:
    """Internal: create sync result (DRY)."""
    return CountrySyncResult(
        sync_id=sync_id,
        total_processed=total,
        inserted=inserted,
        updated=updated,
        failed=failed,
        quality_summary=quality_summary or {},
        status=status,
        message=message,
        started_at=started_at,
        completed_at=datetime.now(timezone.utc),
    )

# Uso:
return self._create_sync_result(
    sync_id=sync_id,
    status="success",
    total=total,
    inserted=inserted,
    updated=updated,
    failed=0,
    message=f"Synced {total} countries...",
    started_at=started_at,
    quality_summary=quality_summary,
)
```

---

### **Arquivo: app/database/repository.py**

#### Mudança 1: Extract Query Builder

**Antes:**
```python
# get_by_id
self.session.query(Country).filter(Country.id == id).first()

# get_by_iso2
self.session.query(Country).filter(Country.iso_code_2 == code).first()

# get_by_iso3
self.session.query(Country).filter(Country.iso_code_3 == code).first()

# get_all
self.session.query(Country).order_by(...).limit(...).offset(...)

# get_by_region
self.session.query(Country).filter(...).order_by(...).limit(...)
```

**Depois:**
```python
def _base_query(self):
    """Base query for all country queries."""
    return self.session.query(Country)

def _get_single_by_field(self, field, value) -> Optional[Country]:
    """Generic single record fetch (DRY)."""
    return self._base_query().filter(field == value.upper() if isinstance(value, str) else value).first()

def _get_paginated_query(self, filter_field=None, limit=100, offset=0):
    """Generic paginated query builder (DRY)."""
    query = self._base_query()
    if filter_field is not None:
        query = query.filter(filter_field)
    return query.order_by(Country.name_common).limit(limit).offset(offset).all()

# Refactor métodos existentes:
def get_by_id(self, country_id: int):
    return self._get_single_by_field(Country.id, country_id)

def get_by_iso2(self, iso_code: str):
    return self._get_single_by_field(Country.iso_code_2, iso_code)

def get_by_iso3(self, iso_code: str):
    return self._get_single_by_field(Country.iso_code_3, iso_code)

def get_all(self, limit=100, offset=0):
    return self._get_paginated_query(limit=limit, offset=offset)

def get_by_region(self, region: str, limit=100, offset=0):
    return self._get_paginated_query(
        filter_field=Country.region == region,
        limit=limit,
        offset=offset
    )
```

**Benefícios:** -30 linhas, uniformidade, manutenção

---

#### Mudança 2: Move Pydantic Conversion (SRP)

**Antes (linha 169 em repository):**
```python
def get_paginated(self, ...):
    ...
    return CountryListResponse(
        items=[CountryResponse.model_validate(c) for c in countries],  # ❌ SRP violation
        ...
    )
```

**Depois - no repository:**
```python
def get_paginated(self, ...):
    ...
    return {
        "countries": countries,  # Retorna ORM diretamente
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }
```

**Depois - no service:**
```python
def list_countries(self, page=1, limit=20, region=None):
    result = self.country_repo.get_paginated(page, limit, region)
    
    return CountryListResponse(
        items=[self._to_response(c) for c in result["countries"]],
        total=result["total"],
        page=result["page"],
        limit=result["limit"],
        pages=result["pages"],
    )
```

**Benefícios:** Repository puro (sem Pydantic), separação de responsabilidades

---

## 📊 Resumo de Impacto

| Métrica | Antes | Depois | Ganho |
|---------|-------|--------|-------|
| Linhas country_service.py | 608 | ~480 | -20% |
| Linhas repository.py | 381 | ~300 | -21% |
| Métodos repetidos | 7+ | 1 | -85% |
| Violações DRY | 5 | 0 | 100% |
| SRP violations | 2 | 0 | 100% |
| Testabilidade | Média | Alta | ↑↑ |

---

## 🎯 Implementação Recomendada

**Ordem (sem quebrar testes):**

1. ✅ Extract `_ensure_country_exists` → Re-run tests
2. ✅ Extract `_to_response` helpers → Re-run tests
3. ✅ Extract `_create_sync_result` → Re-run tests
4. ✅ Extract `_add_related_entities` → Re-run tests
5. ✅ Extract repository query helpers → Re-run tests
6. ✅ Move Pydantic conversions → Update tests if needed

**Commits:** 1 commit por mudança = 6 commits atomicos

**Tests:** Todos os 48 testes devem passar após cada step

---

## 🚀 Benefícios Finais

- ✅ **DRY:** 85% redução em duplicação
- ✅ **SRP:** Cada classe/método tem 1 responsabilidade
- ✅ **Testabilidade:** Métodos pequenos e focados
- ✅ **Manutenibilidade:** Menos código = menos bugs
- ✅ **Refactoring posterior:** Base sólida para novas features
- ✅ **Zero mudança externa:** Contrato de API intacto

---

**Próxima Ação:** Implementar em Sprint 18/09 (antes de staging)
