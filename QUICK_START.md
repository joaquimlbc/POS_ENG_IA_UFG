# Quick Start Guide - REST Countries Dashboard

**Última Atualização:** 2026-09-19  
**Status:** ✅ MVP 0.1 Production Ready

---

## 🚀 Iniciar em 5 Minutos

### Pré-requisitos
- Python 3.11+
- Git
- Terminal/PowerShell

### 1️⃣ Clonar e Preparar Ambiente

```bash
# Clonar repositório
git clone https://github.com/joaquimlbc/POS_ENG_IA_UFG.git
cd PG_genIA_MVP-01

# Criar ambiente virtual
python -m venv .venv

# Ativar (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Ativar (macOS/Linux)
source .venv/bin/activate
```

### 2️⃣ Instalar Dependências

```bash
# Instalar tudo
pip install -r requirements.txt

# Ou apenas essencial (sem Streamlit)
pip install fastapi uvicorn sqlalchemy pydantic requests
```

### 3️⃣ Inicializar Banco de Dados

```bash
# Criar tabelas e popular com 250 países
python -m app.scripts.ingest
```

### 4️⃣ Executar Serviços

#### Opção A: API + Dashboard (Recomendado)

**Terminal 1 - API:**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Dashboard:**
```bash
streamlit run streamlit_app.py
```

#### Opção B: Apenas API

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Opção C: Apenas Dashboard

```bash
streamlit run streamlit_app.py
```

---

## 📊 Acessar Aplicações

### API REST (http://localhost:8000)

| Recurso | URL |
|---------|-----|
| **Swagger UI** (Documentação Interativa) | http://localhost:8000/docs |
| **ReDoc** (Documentação Alternativa) | http://localhost:8000/redoc |
| **OpenAPI Schema** | http://localhost:8000/openapi.json |
| **Health Check** | http://localhost:8000/health |

### Dashboard Streamlit (http://localhost:8501)

| Recurso | URL |
|---------|-----|
| **Dashboard Principal** | http://localhost:8501 |
| **Página de Status** | http://localhost:8501/?page=home |

---

## 🧪 Testar Endpoints

### Com cURL

```bash
# Health check
curl http://localhost:8000/health

# Listar países (página 1, 20 por página)
curl "http://localhost:8000/api/v1/countries?page=1&limit=20"

# Filtrar por região
curl "http://localhost:8000/api/v1/countries?region=Americas"

# Obter país por ID
curl http://localhost:8000/api/v1/countries/1

# Obter país por ISO code
curl http://localhost:8000/api/v1/countries/iso/BR

# Estatísticas globais
curl http://localhost:8000/api/v1/statistics

# Estatísticas por região
curl http://localhost:8000/api/v1/regions

# Sincronizar dados
curl -X POST http://localhost:8000/api/v1/sync
```

### Com Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Health check
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# Listar países
response = requests.get(f"{BASE_URL}/api/v1/countries", params={"page": 1, "limit": 20})
countries = response.json()
print(f"Total: {countries['total']}, Página: {countries['page']}")

# Obter estatísticas
response = requests.get(f"{BASE_URL}/api/v1/statistics")
stats = response.json()
print(f"Total de países: {stats['total_countries']}")
print(f"População global: {stats['total_population']:,}")
```

---

## 📚 Documentação Completa

Consulte os documentos técnicos:

| Documento | Conteúdo |
|-----------|----------|
| [ARCHITECTURE.md](documentacoes/ARCHITECTURE.md) | Arquitetura de 4 camadas |
| [API_ROUTES.md](documentacoes/API_ROUTES.md) | Detalhes de todos os 17 endpoints |
| [OPENAPI_DOCUMENTATION.md](documentacoes/OPENAPI_DOCUMENTATION.md) | Documentação OpenAPI/Swagger (US-013) |
| [BACKLOG_PG_genIA_MVP-01.md](documentacoes/BACKLOG_PG_genIA_MVP-01.md) | Roadmap do projeto |
| [DESIGN_SYSTEM.md](documentacoes/DESIGN_SYSTEM.md) | Sistema de cores e design |

---

## 🔧 Troubleshooting

### Erro: "Port 8000 already in use"
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :8000
kill -9 <PID>
```

### Erro: "No module named 'app'"
```bash
# Certifique-se que está na pasta correta
pwd  # Deve estar em PG_genIA_MVP-01/

# Tente adicionar ao PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Banco de dados vazio
```bash
# Reinicializar banco de dados
rm data/countries.db

# Repopular com 250 países
python -m app.scripts.ingest
```

### Dashboard não carrega
```bash
# Limpar cache do Streamlit
streamlit cache clear

# Reiniciar
streamlit run streamlit_app.py
```

---

## 📊 Dados do Projeto

**Banco de Dados:**
- Total de Países: **250**
- Database: SQLite (`data/countries.db`)
- Tabelas: Country, Language, Currency, Timezone

**API Endpoints:**
- Total: **17 endpoints**
- Documentados: **100%** (US-013 ✅)
- Testados: **269 testes** ✅

**Dashboard:**
- KPIs: 4 cards com métricas
- Filtros: Region selector
- Tabelas: Dados interativos com paginação
- Gráficos: Top 10 populações, Top 10 áreas, Distribuição regional

---

## 🎯 Próximos Passos

### Após executar:
1. Explorar Swagger UI em `/docs`
2. Testar alguns endpoints (GET `/api/v1/countries`)
3. Visualizar dashboard em http://localhost:8501
4. Verificar dados de população/área por região

### Para desenvolvimento:
1. Consultar [ARCHITECTURE.md](documentacoes/ARCHITECTURE.md) para entender a estrutura
2. Verificar [BACKLOG_PG_genIA_MVP-01.md](documentacoes/BACKLOG_PG_genIA_MVP-01.md) para US em progresso
3. Executar testes: `pytest tests/ -v`
4. Verificar qualidade: `black . && flake8 . && mypy app/`

---

## 📞 Suporte

- **Issues:** GitHub Issues
- **Documentação Técnica:** Ver pasta `documentacoes/`
- **Logs:** Verificar saída do terminal (structured logs com timestamp)
- **Coverage:** `pytest --cov=app`

---

**Versão:** 1.0  
**Data:** 2026-09-19  
**Status:** ✅ Production Ready (Release 0.1-beta)
