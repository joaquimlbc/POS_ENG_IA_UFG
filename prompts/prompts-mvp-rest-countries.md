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