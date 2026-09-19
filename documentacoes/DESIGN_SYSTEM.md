# Design System — Dashboard Streamlit

**Escopo:** `streamlit_app.py` e `.streamlit/config.toml`
**Última atualização:** 19/09/2026 (US-021)

Este documento registra a paleta de cores, tipografia e convenções de layout
usadas no dashboard, e a justificativa de acessibilidade por trás de cada
escolha. As cores categóricas e a escala sequencial foram escolhidas e
**validadas** com a skill `dataviz` (script `validate_palette.js`), não
"no olho" — os números abaixo vêm direto da validação.

---

## 1. Tema base (`.streamlit/config.toml`)

| Papel | Hex | Contraste vs. fundo | Uso |
|---|---|---|---|
| `primaryColor` | `#256abf` | 5.39:1 sobre `#FFFFFF` (AA para texto normal) | Widgets ativos, foco, botões, links |
| `backgroundColor` | `#FFFFFF` | — | Fundo principal |
| `secondaryBackgroundColor` | `#F0F2F6` | — | Cards, inputs, containers |
| `textColor` | `#262730` | 14.84:1 sobre `#FFFFFF` / 13.24:1 sobre `#F0F2F6` (AA) | Texto padrão |

`primaryColor` é o **step 500** da mesma rampa sequencial azul usada no
gráfico "Top 10 por População" (seção 3) — a cor de UI e a cor de dado
vêm da mesma família, não são escolhas independentes.

Fonte: `system-ui, sans-serif` (padrão do Streamlit), sem fonte display/serif.

O tema custom convive com os temas nativos "Light"/"Dark" do Streamlit —
o usuário pode trocar pelo menu ⋮ → Settings → Theme; a paleta categórica
(seção 2) foi validada nos dois modos.

---

## 2. Paleta categórica — Regiões

Mapeamento **fixo** região → cor (nunca muda com filtro, ranking ou
tamanho de fatia). Usado nos gráficos de pizza (US-019) e disponível para
qualquer encoding futuro por região.

| Região | Light | Dark |
|---|---|---|
| Africa | `#2a78d6` | `#3987e5` |
| Americas | `#eb6834` | `#d95926` |
| Asia | `#1baf7a` | `#199e70` |
| Europe | `#eda100` | `#c98500` |
| Oceania | `#e87ba4` | `#d55181` |

**Validação** (`validate_palette.js`, 5 slots, categórico):

- Light: banda de luminosidade ✅, piso de croma ✅, separação CVD pior-par
  ΔE 9.1 ✅ (piso ≥ 8), normal-vision pior-par ΔE 19.6 ✅ (piso ≥ 15).
  ⚠️ 3 das 5 cores (`#1baf7a`, `#eda100`, `#e87ba4`) ficam abaixo de 3:1 de
  contraste contra o fundo claro — por isso os rótulos das fatias são
  renderizados **fora** da pizza (`textposition="outside"`), nunca em cima
  da cor, e uma legenda com o nome da região acompanha sempre o gráfico.
- Dark: todos os 5 checks passam, incluindo contraste (≥ 3:1).

Ordem fixa (`REGION_ORDER` em `streamlit_app.py`): Africa, Americas, Asia,
Europe, Oceania — a mesma ordem é usada nos dois gráficos de pizza
(`category_orders` + `sort=False`), então a legenda nunca reordena com o
tamanho da fatia.

---

## 3. Escala sequencial — Magnitude (gráficos de barra, US-018)

Codifica valor absoluto (população, área), não identidade — por isso é
sequencial de um hue só, não a paleta categórica da seção 2.

- **População:** azul (`Blues`), mesma família do `primaryColor`.
- **Área:** laranja (`Oranges`) — quando dois contextos sequenciais
  aparecem lado a lado, o segundo usa o próximo slot categórico (laranja é
  o slot 2 da paleta de regiões).

Ambas claras→escuras (maior valor = cor mais intensa), rótulo de valor
sempre visível sobre a barra (`texttemplate`), sem depender só da cor.

---

## 4. Ícones dos KPIs

| Card | Ícone |
|---|---|
| Total de Países | 🌍 |
| População Global | 👥 |
| Região mais Populosa | 🏆 |
| Maior País (Área) | 📐 |

Ícones acompanham o rótulo (nunca substituem o texto), consistente com a
regra de "nunca cor/ícone sozinho" do restante do dashboard.

---

## 5. Layout & responsividade

- `layout="wide"`, conteúdo organizado em `st.columns` — o grid do
  Streamlit empilha as colunas verticalmente abaixo de ~640px sem CSS
  extra.
- Validado com Chromium headless em viewport 375×812 (iPhone-ish):
  `document.documentElement.scrollWidth == clientWidth` — **sem scroll
  horizontal de página**. A tabela de países mantém seu próprio scroll
  horizontal interno (comportamento padrão e esperado de um componente de
  tabela em tela estreita, não da página).
- Espaçamento entre seções: `st.divider()` fixo entre KPIs → gráficos de
  barra → gráficos de pizza → tabela; margem interna dos gráficos Plotly
  padronizada (`margin=dict(l=0, r=0, t=40, b=0)`).
- Detalhe do país (US-020): `st.tabs` com 3 seções (Identificação,
  Geografia & Demografia, Cultura & Fusos) — hierarquia clara em vez de
  uma lista plana de campos; botão de fechar (✖) explícito.

---

## 6. Referência

- Paleta de origem e o script de validação:
  `dataviz` skill (`references/palette.md`, `scripts/validate_palette.js`).
- Para trocar a paleta (ex.: rebranding), edite os hex nas tabelas acima e
  **rode o validador de novo** — nunca ajuste "no olho".
