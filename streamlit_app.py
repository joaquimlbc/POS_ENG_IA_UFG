"""Streamlit dashboard for REST Countries data.

Covers US-014 (setup), US-015 (KPIs), US-016 (region filter), US-017
(country table with search, pagination and detail view), US-018 (Top 10
bar charts) and US-019 (regional distribution pie charts). Reads directly
from the SQLite database populated by `python -m app.scripts.ingest`.

Run with: streamlit run streamlit_app.py
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from app.database.connection import SessionLocal
from app.service.country_service import CountryService

st.set_page_config(
    page_title="Dashboard de Países",
    page_icon="🌍",
    layout="wide",
)

REGIONS = ["Todas", "Africa", "Americas", "Asia", "Europe", "Oceania"]
PAGE_SIZE = 20

# Fixed categorical order/mapping (never cycled) - identity by region name,
# not by rank, so a color always means the same region across every chart.
REGION_COLORS = {
    "Africa": "#2a78d6",
    "Americas": "#eb6834",
    "Asia": "#1baf7a",
    "Europe": "#eda100",
    "Oceania": "#e87ba4",
}
REGION_ORDER = list(REGION_COLORS.keys())


@st.cache_data(ttl=300)
def load_countries() -> pd.DataFrame:
    """Load all countries from the database into a flat DataFrame."""
    session = SessionLocal()
    try:
        service = CountryService(session)
        countries = service.country_repo.get_all(limit=1000)
        return pd.DataFrame(
            [
                {
                    "Nome": c.name_common,
                    "Nome Oficial": c.name_official,
                    "ISO2": c.iso_code_2,
                    "ISO3": c.iso_code_3,
                    "Região": c.region,
                    "Sub-região": c.subregion,
                    "População": c.population,
                    # area/latitude/longitude are SQLAlchemy Numeric columns,
                    # which come back as decimal.Decimal; cast to float so
                    # pandas infers a numeric (not object) dtype.
                    "Área (km²)": float(c.area) if c.area is not None else None,
                    "Densidade": (c.population / float(c.area)) if c.area else None,
                    "Latitude": float(c.latitude) if c.latitude is not None else None,
                    "Longitude": float(c.longitude)
                    if c.longitude is not None
                    else None,
                    "Idiomas": ", ".join(lang.language_name for lang in c.languages),
                    "Moedas": ", ".join(cur.currency_code for cur in c.currencies),
                    "Fusos Horários": ", ".join(tz.timezone_name for tz in c.timezones),
                }
                for c in countries
            ]
        )
    finally:
        session.close()


def flag_emoji(iso2: str) -> str:
    """Convert an ISO 3166-1 alpha-2 code to its regional-indicator flag emoji."""
    if not iso2 or len(iso2) != 2 or not iso2.isalpha():
        return ""
    return "".join(chr(0x1F1E6 + ord(char) - ord("A")) for char in iso2.upper())


def format_number(value: float) -> str:
    """Format a number with '.' as the thousands separator (pt-BR style)."""
    return f"{value:,.0f}".replace(",", ".")


def render_kpis(df: pd.DataFrame) -> None:
    """Render the top-row KPI cards for the currently filtered data."""
    col1, col2, col3, col4 = st.columns(4)

    total_countries = len(df)
    total_population = int(df["População"].sum()) if total_countries else 0

    col1.metric("🌍 Total de Países", format_number(total_countries))
    col2.metric("👥 População Global", format_number(total_population))

    if total_countries and df["População"].sum() > 0:
        pop_by_region = df.groupby("Região")["População"].sum()
        top_region = pop_by_region.idxmax()
        col3.metric(
            "🏆 Região mais Populosa", top_region, format_number(pop_by_region.max())
        )
    else:
        col3.metric("🏆 Região mais Populosa", "-")

    if total_countries and df["Área (km²)"].notna().any():
        largest = df.loc[df["Área (km²)"].idxmax()]
        col4.metric(
            "📐 Maior País (Área)",
            largest["Nome"],
            f"{format_number(largest['Área (km²)'])} km²",
        )
    else:
        col4.metric("📐 Maior País (Área)", "-")


def render_bar_charts(df: pd.DataFrame) -> None:
    """Render Top 10 by population and Top 10 by area bar charts (US-018).

    Uses the currently filtered dataset so both charts update with the
    region selector. Color encodes magnitude (sequential, single hue,
    light->dark) - it is not a second, redundant categorical encoding.
    """
    st.subheader("📊 Top 10 Países")

    if df.empty:
        st.info("Nenhum país para exibir nos gráficos.")
        return

    col1, col2 = st.columns(2)

    with col1:
        top_pop = df.nlargest(10, "População").sort_values("População")
        fig_pop = px.bar(
            top_pop,
            x="População",
            y="Nome",
            orientation="h",
            color="População",
            color_continuous_scale="Blues",
            text="População",
            title="Top 10 por População",
        )
        fig_pop.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig_pop.update_layout(
            coloraxis_showscale=False,
            yaxis_title="",
            xaxis_title="População",
            margin=dict(l=0, r=0, t=40, b=0),
        )
        st.plotly_chart(fig_pop, use_container_width=True)

    with col2:
        top_area = (
            df.dropna(subset=["Área (km²)"])
            .nlargest(10, "Área (km²)")
            .sort_values("Área (km²)")
        )
        if top_area.empty:
            st.info("Sem dados de área para os países filtrados.")
        else:
            fig_area = px.bar(
                top_area,
                x="Área (km²)",
                y="Nome",
                orientation="h",
                color="Área (km²)",
                color_continuous_scale="Oranges",
                text="Área (km²)",
                title="Top 10 por Área",
            )
            fig_area.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
            fig_area.update_layout(
                coloraxis_showscale=False,
                yaxis_title="",
                xaxis_title="Área (km²)",
                margin=dict(l=0, r=0, t=40, b=0),
            )
            st.plotly_chart(fig_area, use_container_width=True)


def render_language_chart(df: pd.DataFrame) -> None:
    """Render the spoken-language chart pair: Top 10 idle tongues by estimated
    speaking population (summed country populations, may double count
    multilingual countries) and Top 10 by number of countries (US-018 style).

    Uses the currently filtered dataset so both charts update with the
    continent selector. Color encodes magnitude (sequential, single hue) as in
    the other top-10 charts.
    """
    st.subheader("🗣️ Idiomas mais falados")

    if df.empty:
        st.info("Nenhum país para exibir nos gráficos de idiomas.")
        return

    lang_df = (
        df[["Nome", "População", "Idiomas"]]
        .dropna(subset=["Idiomas"])
        .assign(Idioma=lambda d: d["Idiomas"].str.split(", "))
        .explode("Idioma")
    )
    lang_df["Idioma"] = lang_df["Idioma"].str.strip()
    lang_df = lang_df[lang_df["Idioma"].str.len() > 0]

    if lang_df.empty:
        st.info("Sem dados de idiomas para os países filtrados.")
        return

    col1, col2 = st.columns(2)

    with col1:
        top_lang_pop = (
            lang_df.groupby("Idioma")["População"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .sort_values()
        )
        fig_pop = px.bar(
            top_lang_pop,
            x=top_lang_pop.values,
            y=top_lang_pop.index,
            orientation="h",
            color=top_lang_pop.values,
            color_continuous_scale="Greens",
            text=top_lang_pop.values,
            title="Top 10 Idiomas por População Falante (estimativa)",
        )
        fig_pop.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig_pop.update_layout(
            coloraxis_showscale=False,
            yaxis_title="",
            xaxis_title="População",
            margin=dict(l=0, r=0, t=40, b=0),
        )
        st.plotly_chart(fig_pop, use_container_width=True)
        st.caption(
            "Números Estimados: soma da população falante; e sobrecontagem em países multilíngues."
        )

    with col2:
        top_lang_count = lang_df["Idioma"].value_counts().head(10).sort_values()
        fig_count = px.bar(
            top_lang_count,
            x=top_lang_count.values,
            y=top_lang_count.index,
            orientation="h",
            color=top_lang_count.values,
            color_continuous_scale="Greens",
            text=top_lang_count.values,
            title="Top 10 Idiomas por Nº de Países",
        )
        fig_count.update_traces(texttemplate="%{text}", textposition="outside")
        fig_count.update_layout(
            coloraxis_showscale=False,
            yaxis_title="",
            xaxis_title="Nº de países",
            margin=dict(l=0, r=0, t=40, b=0),
        )
        st.plotly_chart(fig_count, use_container_width=True)


def render_pie_charts(full_df: pd.DataFrame) -> None:
    """Render regional population/country-count distribution pies (US-019).

    Always uses the full, unfiltered dataset: a "distribution by region"
    chart filtered down to a single region would just show one 100% slice,
    so the region selector intentionally does not apply here. Colors are
    the same fixed per-region mapping used everywhere else, and labels are
    placed outside the slices so they never sit on top of a low-contrast
    fill (three of the five region colors fall under 3:1 against a light
    surface).
    """
    st.subheader("🥧 Distribuição Regional")

    pop_by_region = (
        full_df.groupby("Região")["População"].sum().reindex(REGION_ORDER).dropna()
    )
    count_by_region = full_df.groupby("Região").size().reindex(REGION_ORDER).dropna()

    if pop_by_region.empty:
        st.info("Sem dados regionais para exibir.")
        return

    col1, col2 = st.columns(2)

    with col1:
        fig_pop_pie = px.pie(
            values=pop_by_region.values,
            names=pop_by_region.index,
            color=pop_by_region.index,
            color_discrete_map=REGION_COLORS,
            category_orders={"names": REGION_ORDER},
            title="População por Região",
        )
        fig_pop_pie.update_traces(sort=False)
        fig_pop_pie.update_traces(textinfo="label+percent", textposition="outside")
        fig_pop_pie.update_layout(showlegend=True, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig_pop_pie, use_container_width=True)

    with col2:
        fig_count_pie = px.pie(
            values=count_by_region.values,
            names=count_by_region.index,
            color=count_by_region.index,
            color_discrete_map=REGION_COLORS,
            category_orders={"names": REGION_ORDER},
            title="Quantidade de Países por Região",
        )
        fig_count_pie.update_traces(sort=False)
        fig_count_pie.update_traces(textinfo="label+percent", textposition="outside")
        fig_count_pie.update_layout(showlegend=True, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig_count_pie, use_container_width=True)


def render_country_detail(detail: pd.Series) -> None:
    """Render a country's full profile in clear, hierarchical sections (US-020)."""
    area = detail["Área (km²)"]
    density = detail["Densidade"]
    has_coords = pd.notna(detail["Latitude"]) and pd.notna(detail["Longitude"])

    tab_id, tab_geo, tab_culture = st.tabs(
        ["🏷️ Identificação", "📊 Geografia & Demografia", "🌐 Cultura & Fusos"]
    )

    with tab_id:
        col1, col2 = st.columns(2)
        col1.metric("Nome oficial", detail["Nome Oficial"])
        col1.write(f"**Nome comum:** {detail['Nome']}")
        col2.write(f"**Código ISO2:** {detail['ISO2']}")
        col2.write(f"**Código ISO3:** {detail['ISO3']}")
        st.write(f"**Região:** {detail['Região']}")
        st.write(f"**Sub-região:** {detail['Sub-região'] or '-'}")

    with tab_geo:
        col1, col2, col3 = st.columns(3)
        col1.metric("População", format_number(detail["População"]))
        col2.metric("Área", f"{format_number(area)} km²" if pd.notna(area) else "-")
        col3.metric(
            "Densidade", f"{density:,.1f} hab/km²" if pd.notna(density) else "-"
        )
        st.write(
            f"**Coordenadas:** {detail['Latitude']:.4f}, {detail['Longitude']:.4f}"
            if has_coords
            else "**Coordenadas:** -"
        )

    with tab_culture:
        st.write(f"**Idiomas:** {detail['Idiomas'] or '-'}")
        st.write(f"**Moedas:** {detail['Moedas'] or '-'}")
        st.write(f"**Fusos horários:** {detail['Fusos Horários'] or '-'}")


def render_table(df: pd.DataFrame) -> None:
    """Render the searchable, paginated country table with a detail view."""
    search = st.text_input("🔎 Buscar por nome")
    if search:
        df = df[df["Nome"].str.contains(search, case=False, na=False)]

    st.caption(f"{len(df)} países encontrados")

    if df.empty:
        st.info("Nenhum país corresponde à busca.")
        return

    total_pages = max(1, (len(df) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = st.number_input(
        "Página", min_value=1, max_value=total_pages, value=1, step=1
    )

    start = (page - 1) * PAGE_SIZE
    page_df = (
        df.sort_values("Nome")
        .iloc[start : start + PAGE_SIZE]
        .reset_index(drop=True)
        .copy()
    )
    page_df.insert(0, "Bandeira", page_df["ISO2"].apply(flag_emoji))

    display_columns = [
        "Bandeira",
        "Nome",
        "População",
        "Área (km²)",
        "Região",
        "Densidade",
    ]
    event = st.dataframe(
        page_df[display_columns].style.format(
            {
                "População": "{:,.0f}",
                "Área (km²)": "{:,.0f}",
                "Densidade": "{:,.1f}",
            },
            na_rep="-",
        ),
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key=f"country_table_page_{page}",
    )

    selected_rows = event.selection.rows if event and event.selection else []

    if not selected_rows:
        st.caption("👆 Clique em uma linha da tabela para ver os detalhes do país.")
        return

    detail = page_df.iloc[selected_rows[0]]
    country_name = detail["Nome"]

    if st.session_state.get("_closed_detail_for") == (page, country_name):
        st.caption("👆 Clique em uma linha da tabela para ver os detalhes do país.")
        return

    with st.container(border=True):
        header_col, close_col = st.columns([10, 1])
        header_col.markdown(f"#### 📋 {country_name}")
        if close_col.button("✖", key=f"close_detail_{page}", help="Fechar detalhes"):
            st.session_state["_closed_detail_for"] = (page, country_name)
            st.rerun()
        render_country_detail(detail)


def main() -> None:
    """Dashboard entry point."""
    st.title("🌍 Dashboard de Países")

    full_df = load_countries()

    if full_df.empty:
        st.warning(
            "Nenhum país encontrado no banco de dados. Execute "
            "`python -m app.scripts.ingest` para popular os dados."
        )
        return

    region = st.selectbox("Filtrar por Continente", REGIONS, index=0, key="region_filter")
    df = full_df if region == "Todas" else full_df[full_df["Região"] == region]

    render_kpis(df)
    st.divider()
    render_bar_charts(df)
    st.divider()
    render_language_chart(df)
    st.divider()
    render_pie_charts(full_df)
    st.divider()
    render_table(df)


if __name__ == "__main__":
    main()
