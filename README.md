# PG genIA MVP-01: REST Countries Dashboard

## Objetivo

Desenvolver uma aplicação que consome dados da API REST Countries, armazena informações demográficas em banco de dados relacional e apresenta métricas populacionais e regionais através de um dashboard interativo.

## Tech Stack

### Backend
- **Python 3.11** - Linguagem principal
- **SQLAlchemy 2.0** - ORM para gerenciamento de banco de dados
- **SQLite** - Banco de dados relacional

### Frontend
- **Streamlit** - Dashboard interativo e apresentação de dados

### Ferramentas
- **Git** - Versionamento
- **pip** - Gerenciador de dependências
- **venv** - Ambiente virtual Python

## Pré-requisitos

- Python 3.11 ou superior
- pip (gerenciador de pacotes Python)
- Git

## Como Rodar Localmente

### 1. Clonar o repositório
```bash
git clone <url-do-repositorio>
cd PG_genIA_MVP-01
```

### 2. Criar e ativar ambiente virtual
```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# macOS/Linux (bash)
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

### 4. Executar o dashboard
```bash
streamlit run app.py
```

A aplicação estará disponível em `http://localhost:8501`

## Estrutura do Projeto

```
PG_genIA_MVP-01/
├── .gitignore              # Arquivo de exclusão do Git
├── README.md              # Este arquivo
├── requirements.txt       # Dependências do projeto
├── app.py                 # Aplicação Streamlit principal
├── .venv/                 # Ambiente virtual (não versionado)
├── database/              # Módulos de banco de dados
│   ├── __init__.py
│   ├── models.py          # Modelos SQLAlchemy
│   └── connection.py      # Configuração de conexão
├── api/                   # Módulos de integração com API
│   ├── __init__.py
│   └── rest_countries.py  # Cliente REST Countries
├── utils/                 # Utilitários gerais
│   ├── __init__.py
│   └── helpers.py
└── prompts/               # Documentação e especificações
    ├── prompts-mvp-rest-countries.md
    └── etapas_realizadas.txt
```

## Funcionalidades Planejadas

### MVP - Release 0.1 (Em Desenvolvimento)
- ✅ Consumir API REST Countries
- ✅ Armazenar dados em SQLite
- 🔄 Dashboard básico com métricas populacionais
- 🔄 Filtros por região

### Release 0.2
- Gráficos de comparação entre países
- Análise de densidade populacional
- Exportação de relatórios (CSV/PDF)

### Release 0.3
- Autenticação de usuários
- Histórico de dados (séries temporais)
- Alertas e notificações

## Roadmap de Releases

| Versão | Status | Data Estimada | Descrição |
|--------|--------|---------------|-----------|
| 0.1    | 🔄 Em Desenvolvimento | Setembro 2026 | MVP com dashboard básico |
| 0.2    | 📋 Planejado | Outubro 2026 | Análises avançadas e exportação |
| 0.3    | 📋 Planejado | Novembro 2026 | Autenticação e séries temporais |

## Desenvolvimento

### Padrões de Código
- Seguir PEP 8 para estilo Python
- Adicionar type hints nas funções
- Manter testes unitários para novas features

### Fluxo de Git
1. Criar branch feature: `git checkout -b feature/descricao`
2. Realizar commits significativos
3. Push e criar Pull Request
4. Review e merge para `main`

## Documentação

Consulte a pasta `prompts/` para:
- `prompts-mvp-rest-countries.md` - Especificações técnicas detalhadas
- `etapas_realizadas.txt` - Histórico de atividades

## Suporte e Dúvidas

Para dúvidas técnicas ou reportar bugs, abra uma issue no repositório ou entre em contato com a equipe de desenvolvimento.

---

**Última atualização:** Setembro 2026  
**Versão atual:** 0.1-alpha
