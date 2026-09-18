# Guia de Prompts CO-STAR: MVP REST Countries API & Dashboard

## O Framework CO-STAR Aplicado à Engenharia de Software

Cada prompt neste documento foi estruturado seguindo rigorosamente os seis pilares do modelo **CO-STAR**:

*   **C - Contexto (Context):** Apresenta o ecossistema do projeto, stack tecnológica, arquitetura atual e contexto do módulo.
*   **O - Objetivo (Objective):** Define de forma clara, direta e sem ambiguidades a tarefa a ser executada pela IA.
*   **S - Estilo (Style):** Especifica os padrões de codificação (PEP 8, Clean Code, SOLID), bibliotecas e convenções de design.
*   **T - Tonalidade (Tone):** Determina a postura das mensagens de erro, logs, documentação e respostas da IA.
*   **A - Audiência (Audience):** Define quem usará ou revisará o código/artefato (desenvolvedores juniores, revisores, ferramentas de CI/CD, usuários).
*   **R - Resposta (Response):** Delimita o formato exato de saída esperado (apenas código Python, Markdown, JSON, sem explicações redundantes).

---

Prompt 1 - .gitignore

Contexto: Estou desenvolvendo o backend e frontend de um MVP em Python 3.11 que consome a API REST Countries (https://restcountries.com/v3.1/all), armazena os dados de países em um banco de dados relacional (SQLite) usando SQLAlchemy 2.0 e apresenta métricas populacionais e regionais em um dashboard Streamlit.
Objetivo: Gere um arquivo .gitignore para Python, ambiente virtual, banco de dados, cache de testes e configurações locais do editor.
Tonalidade: Claro e objetivo.
Audiência: Desenvolvedores e especialistas técnicos.
Estilo: Organize por seções com comentários.
Resposta: Forneça o conteúdo e crie do arquivo .gitignore.

-----------------------

Prompt 2 - .README inicial

Contexto: Estou desenvolvendo o backend e frontend de um MVP em Python 3.11 que consome a API REST Countries (https://restcountries.com/v3.1/all), armazena os dados de países em um banco de dados relacional (SQLite) usando SQLAlchemy 2.0 e apresenta métricas populacionais e regionais em um dashboard Streamlit.
Objetivo: Escrever um README inicial com objetivo, stacks, como rodar localmente e roadmap de realeases.
Tonalidade: Claro e objetivo.
Audiência: Desenvolvedores, especialistas técnicos, testes e POs.
Estilo: Markdown simples, direto e profissional.
Resposta: Forneça e crie o README completo.

-----------------------

Prompt 3 - Endpoint de healthcheck

Contexto: Estou desenvolvendo o backend de uma API RESTful em Python 3.11 utilizando o framework FastAPI para ingestão e consulta de dados da REST Countries API (`https://restcountries.com/`). Preciso criar o ponto de entrada principal da aplicação no arquivo `app/main.py` e disponibilizar uma rota de verificação de saúde do serviço (healthcheck).
Objetivo: Criar o arquivo `app/main.py` contendo a instância do FastAPI e a rota `GET /health`. A rota deve retornar um objeto JSON indicando o status operacional (`"status": "ok"`), a versão da API (`"version": "1.0.0"`) e o timestamp atual do servidor em formato ISO 8601 UTC (`datetime.now(timezone.utc)`).
Estilo: Código em Python 3.11+, aderente às diretrizes da PEP 8, com tipagem estática completa (`typing`), uso de `Pydantic v2` para o esquema de resposta do healthcheck, configuração do FastAPI com título/descrição para a documentação automática (OpenAPI/Swagger) e docstring no formato Google. 
Tonalidade: Técnica, direta e padronizada para ambiente corporativo/produção 
Audiência: Desenvolvedores backend, revisores de código e orquestradores de infraestrutura (como Kubernetes ou Docker healthchecks).
Resposta: Forneça apenas o código Python completo do arquivo `app/main.py`, pode conter textos explicativos antes ou depois do bloco de código.

-----------------------

Prompt 4 - Revisão crítica

Como um especilista desenvolvedor python analise o código gerado para app/main.py e responda:
1.  Quais riscos técnicos existem?
2. O que pode quebrar em produção?
3. Quais testes mínimos devo criar agora?
Resposta curta em checklist.

-----------------------

Prompt 5 - Mensagem de commit

Contexto: Alterações realizadas nos arquivos do projeto.
Objetivo: Gerar uma mensaghem de commit no padrão Conventional Commits.
Resposta: Apenas uma linha de commit.

-----------------------

Prompt 6 - Escopo MVP

Contexto: Desenvolvimento de MVP baseado no consumo da REST Countries API, com o objetivo de obter dados de países, normalizar e persistir essas informações em banco de dados e disponibilizar indicadores por meio de um dashboard interativo.
Objetivo: Gerar documento de escopo com objetivo, requisitos funcionais, não funcionais e fora do escopo, separado em base backend com persistencia de dados e front-end (dashboar).
Estilo: Profissional, objetivo, técnico mais compreensível, estruturado, sem excesso de texto narrativo, orientada à execução do projeto.
Tom: Analista de negógio Sr, Product Owner, Arquiteto de software, QA/Quality Assurance.
Audiencia: Product Manager, Product Owner,Analistas de requisitos, Desenvolvedores, 
QA/Quality Assurance, Arquitetos de software,
profissionais que estejam utilizando IA Generativa durante o ciclo de desenvolvimento.
Resposta: Fornece o conteúdo completo do documento em modelo PRD, e disponibilize no diretório documentacoes dentro da estrutura do projeto.

-----------------------

Prompt 7 - Backlog por releases

Contexto: Você está analisando um projeto de desenvolvimento de software e precisa transformar as informações fornecidas sobre o projeto em um backlog estruturado e priorizado por releases, conforme documento PRD.
Objetivo: Criar backlog mínimo com identificação dos requisitos (Funcionais, não-funcionais e técnicos) e critérios de aceite.
Estilo: Checklist Markdown.
Tom: Analista de negógio Sr, Product Owner, Arquiteto de software, QA/Quality Assurance.
Audiencia: Product Manager, Product Owner,Analistas de requisitos, Desenvolvedores, 
QA/Quality Assurance, Arquitetos de software,
profissionais que estejam utilizando IA Generativa durante o ciclo de desenvolvimento.
Resposta: Fornece o conteúdo completo do documento de backlog, e disponibilize no diretório documentacoes dentro da estrutura do projeto.

-----------------------

Prompt 8 - Arquitetura Mermaid

Contexto: Você está analisando um projeto de desenvolvimento de software e precisa transformar os requisitos, backlog e informações técnicas fornecidas em uma representação visual da arquitetura do sistema utilizando Mermaid.
Objetivo: Atue como um Arquiteto de Software Sênior e produza uma proposta de arquitetura técnica para o sistema, contemplanto diagrama Mermaid de componentes e fluxo de dados, integrações.
Estilo: Arquiteto de Software Sênior.
Tom: técnico, objetivo, analítico, pragmático,
orientado à decisão.
Resposta: gere a arquitetura Mermaid.

-----------------------

Prompt 9 - Conventional Commits

Contexto: Adicionados documentos PRD, Backlog e de arquiterura.
Objetivo: Sugerir 3 mensagens de commit padrão Conventional Commits.
Resposta: Apenas 3 linhas de commit.

-----------------------

Prompt 11 - Modelo Pydantic

Contexto: Você está analisando o projeto de desenvolvimento de software e precisa transformar os requisitos funcionais, regras de negócio, backlog e arquitetura fornecidos em modelos de dados utilizando Pydantic.
Objetivo: Atue como um Desenvolvedor Python Sênior e Arquiteto de Software, responsável por criar os modelos Pydantic necessários para o projeto.
Estilo: Utilizando boas práticas modernas de desenvolvimento em Pydantic v2, código limpo e docstrings curtas.
Tom: Utilize um tom técnico, objetivo, pragmático, didático e orientado à implementação.
Audiencia: O resultado será utilizado principalmente por: Desenvolvedores Python,
Backend Developers, Tech Leads, Arquitetos,
QA, Desenvolvedores de APIs, Product Owners em atividades de validação de contrato.
Resposta: Apenas código, criar o arquivo task.py, na estrutura de pastas app/models.

-----------------------

Prompt 12 - Camada de Persistência

Contexto: Estou desenvolvendo uma aplicação em Python 3.11+ que consome dados da REST Countries API, valida e normaliza essas informações e disponibiliza posteriormente os dados em um dashboard.
Objetivo: Crie a camada completa de persistência do projeto.
Estilo: Atue como um engenheiro de software backend sênior especializado em Python, SQLAlchemy e arquitetura de sistemas.
Tom: Utilize um tom técnico, objetivo, pragmático, orientado à implementação e crítico em relação a decisões de arquitetura..
Audiencia: Desenvolvedores Python,
Backend Developers, Arquitetos,
QA, profissionais utilizando IA Generativa no desenvolvimento de software.
Resposta: Organize a resposta nas seguintes etapas: 
- Análise da Persistência
- Modelo de Dados
- Estrutura de Diretórios
- Configuração do Banco
- Modelos SQLAlchemy
- Schemas Pydantic
- Repository
- Persistência em Lote
- Tratamento de erros
Evitar duplicidades na estrutura do projeto.

-----------------------

Prompt 13 - Service com regra de prioridade

Contexto: Estou desenvolvendo uma aplicação em Python 3.11+ que consome dados da REST Countries API, quero separar corretamente as responsabilidades entre as camadas de API, serviço, persistência e regras de negócio.
Objetivo: Criar taskService que use TaskRepository e PriorityAdvisor.
Estilo: Atue como um engenheiro de software backend sênior, com experiência Python, FastAPI, Arquitetura em camadas.
Tom: Utilize um tom técnico, objetivo, pragmático, orientado à implementação e crítico em relação a decisões de arquitetura.
Audiencia: Desenvolvedores Python,
Backend Developers, Arquitetos,
QA, profissionais utilizando IA Generativa no desenvolvimento de software.
Resposta: Criar o arquivo task_service.py com conteúdo das regras de prioridades de camadas, no repositório app/service/.

-----------------------

Prompt 14 - Criação das Rotas da API de Tasks

Contexto: Estou desenvolvendo uma aplicação em Python 3.11+ que consome dados da REST Countries API, quero criação das Rotas da API de Tasks.
Objetivo: Crie as rotas REST da API de Tasks, utilizando FastAPI.
Estilo: Atue como um desenvolvedor de software backend sênior, com experiência em APIs REST e FastAPI.
Tom: Utilize um tom técnico, objetivo, pragmático, orientado às boas práticas de API REST. Não deve complicar a implemtação.
Audiencia: Backend Developers, Arquitetos,
QA, profissionais utilizando IA Generativa no desenvolvimento de software.
Resposta: Criar apenas o código do arquivo task_routes.py no diretório App/API.

-----------------------

Prompt 15 - Revisão técnica

Revise os arquivos do core da API e responda:
1. Quais pontos de acoplamento estão altos?
2. Onde faltam validações:
3. Quais 5 testes devo priorizar nas próximas releases?
Resposta em checklist.

-----------------------

Prompt 16 - Conventional Commits

Contexto: Adicionados vários cógidos, pastas e alterações nos arquivos do projeto e deve realizar o commit no Github.
Objetivo: Sugerir 3 mensagens de commit padrão Conventional Commits.
Resposta: Apenas 3 linhas de commit.

-----------------------

Prompt 17 - Implementar os testes

Contexto: Estou desenvolvendo uma aplicação em Python 3.11+ que consome dados da REST Countries API, e precisamos garantir os testes da aplicação.
Objetivo: Criar suite completa de testes automatizados utilizando Pytest.
Estilo: Atue como um QA Engineer / SDET sênior especializado em Python, Pytest e testes de APIs FastAPI.
Tom: Testes claros, nomes descritivos e fixtures simples. 
Audiencia: Developers, Arquitetos,
QA, profissionais utilizando IA Generativa no desenvolvimento de software.
Resposta: Não crie testes apenas para aumentar artificialmente o percentual de cobertura.
Cada teste deve validar um comportamento relevante. Quando identificar um comportamento que não está especificado no projeto, marque como "A definir", em vez de inventar regra. Criar arquivo e disponibilizar no diretorio tests/.

-----------------------

Prompt 18 - Testes PriorityAdvisor

Contexto: Estou desenvolvendo uma aplicação em Python 3.11+ que consome dados da REST Countries API, e temos que ter os testes do PriorityAdvisor.
Objetivo: Criar os testes do PriorityAdvisor.
Estilo: Atue como um QA Engineer / SDET sênior especializado em Python, Pytest e testes de APIs FastAPI.
Tom: Testes claros, nomes descritivos e fixtures simples. 
Audiencia: Developers, Arquitetos,
QA, profissionais utilizando IA Generativa no desenvolvimento de software.
Resposta: criar os testes PriorityAdvisor.

-----------------------

Prompt 19 - Testes de API

Contexto: Estou desenvolvendo uma aplicação em Python 3.11+ que consome dados da REST Countries API.
Objetivo: Criar os testes de rotas com TestClient para status 200, 201, 204 e 404
Estilo: Atue como um QA Engineer / SDET sênior especializado em Python, Pytest e testes de APIs FastAPI.
Tom: Testes claros, nomes descritivos e fixtures simples. 
Audiencia: Developers, Arquitetos,
QA, profissionais utilizando IA Generativa no desenvolvimento de software.
Resposta: codigo de teste para routes, e Isolar dependencias de repositórios para evitar estado global entre testes.

-----------------------

Prompt 20 - Refatoração DRY/SRP

Analise os arquivos app/services/task_service.py e app/repositories/task_repository.
Objetivo: Sugerir refatoração com foco em Dry e SRP sem mudar comportamento externos.
Resposta: 
1. Lista de mudanças propostas. 
2. patch sugerido por arquivo.

-----------------------

Prompt 22 - README final técnico

Contexto: MVP de API com prioridade assistida por IA.
Objetivo: Atualizar README completo com instalação, execução, testes, uso de IA, limitações, proximos passos.
Tom: Tem técnico já utlizado no documento. 
Audiencia: Developers, Arquitetos, POs, PMs,
QA, profissionais utilizando IA Generativa no desenvolvimento de software.
Resposta: Atualização do README por inteiro.

-----------------------

Prompt 23 - Revisão de Qualidade

Com base no codigo e testes atuais, gere um cheklist com:
- riscos técnicos restantes
-Gaps de cobertura de teste
- Melhorias prioritárias para a próxima release
Responda em bullets curtos.

-----------------------

Prompt 24 - Próximas atividades

Verifique qual atividade podemos realizar.

-----------------------

Prompt 25 - Status das Atividades

Analisando o Backlog do projeto, quais entregas já foram realizadas?
Listar sucintamente e indicar na frente com icone indicativo:
exemplo de resposta:
US-001: Configuração Ambiente de Desenvolvimento ✅
US-004: Cliente HTTP para REST Countries API 🔄
US-006: Configuração de Banco de Dados SQLite ⏳

-----------------------

Prompt 26 - Implementar US-004

Implementar US-004 - HTTP Client para REST Countries API (dados reais)

-----------------------
