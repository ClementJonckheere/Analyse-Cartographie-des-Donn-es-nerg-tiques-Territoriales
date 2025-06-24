import streamlit as st
import pandas as pd
import pydeck as pdk
from scripts import load_data, preprocess
import altair as alt

st.set_page_config(page_title="Analyse IRVE", layout="wide")

st.markdown("""
    <style>
    body {
        background-color: #f5f5f5;
        color: #333333;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        color: #222222;
    }
    .stDeckGlJsonChart {
        height: 700px;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_and_prepare():
    raw_data = load_data.load_all()
    return preprocess.clean_and_merge(raw_data)

clean_data = load_and_prepare()
ev_data = clean_data.get("ev_charging")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Production mensuelle par Région", "Conso en temps réel","Comparaison entre Région", "Carte des bornes", "Indicateurs borne IRVE"])

with tab1:
    st.header("Production mensuelle par filière et région")

    df_prod = clean_data.get("monthly_production")
    if df_prod is not None and not df_prod.empty:
        regions = sorted(df_prod["region"].dropna().unique())
        selected_region = st.selectbox("Choisissez une région", regions, key="region_prod")

        region_data = df_prod[df_prod["region"] == selected_region].copy()

        if not region_data.empty:
            region_data["year"] = region_data["mois"].dt.year
            region_data["month"] = region_data["mois"].dt.strftime("%Y-%m")

            selected_year = st.selectbox("Choisissez une année", sorted(region_data["year"].unique(), reverse=True))
            year_data = region_data[region_data["year"] == selected_year]

            st.subheader("Répartition mensuelle (en %)")
            monthly_total = year_data.groupby("month")["production_GWh"].sum().reset_index(name="total")
            merged = pd.merge(year_data, monthly_total, on="month")
            merged["production_pct"] = (merged["production_GWh"] / merged["total"] * 100).round(2)

            agg_pct = merged.groupby(["month", "filiere"])["production_pct"].mean().reset_index()

            pivot_pct = agg_pct.pivot(index="month", columns="filiere", values="production_pct").fillna(0)

            st.bar_chart(pivot_pct)

            st.subheader(" Répartition totale par filière (% de la production annuelle)")
            filiere_total = year_data.groupby("filiere")["production_GWh"].sum().reset_index()
            total_year = filiere_total["production_GWh"].sum()
            filiere_total["%"] = (filiere_total["production_GWh"] / total_year * 100).round(2)

            st.dataframe(filiere_total.sort_values("%", ascending=False))

            st.metric("Production totale en GWh", f"{total_year:,.1f}")
        else:
            st.warning("Aucune donnée dispo pour cette région.")
    else:
        st.warning("Les données ne sont pas disponibles.")

with tab2:
    st.header("⚡ Consommation annuelle par région (GWh)")

    df_annual = clean_data.get("annual_consumption")
    if df_annual is not None and not df_annual.empty:
        regions = sorted(df_annual["region"].unique())

        selected_region = st.selectbox("Choisissez une région", regions, key="region_select_tab2")
        region_data = df_annual[df_annual["region"] == selected_region].sort_values("année").copy()
        region_data["année"] = pd.to_numeric(region_data["année"], errors="coerce").astype("Int64")

        st.subheader(f"Consommation électrique annuelle – {selected_region}")
        st.line_chart(region_data.set_index("année")["conso_elec_GWh"])

        st.subheader("Répartition annuelle électricité vs gaz")
        st.bar_chart(region_data.set_index("année")[["conso_elec_GWh", "conso_gaz_GWh"]])

        st.subheader("⚖️ Répartition % Électricité vs Gaz")

        region_pct = region_data.copy()
        region_pct = region_pct.dropna(subset=["conso_elec_GWh", "conso_gaz_GWh"])
        region_pct["total"] = region_pct["conso_elec_GWh"] + region_pct["conso_gaz_GWh"]
        region_pct["elec_pct"] = (region_pct["conso_elec_GWh"] / region_pct["total"] * 100).round(2)
        region_pct["gaz_pct"] = (region_pct["conso_gaz_GWh"] / region_pct["total"] * 100).round(2)

        df_pct_plot = region_pct[["année", "elec_pct", "gaz_pct"]].set_index("année")
        st.area_chart(df_pct_plot)

        with st.expander("Interprétation des pourcentages"):
            st.markdown("""
            Ce graphique montre la **répartition relative entre l'électricité et le gaz** dans la consommation annuelle totale de la région sélectionnée :

            - Une part croissante d’électricité peut refléter une **transition énergétique** vers des sources bas carbone.
            - Une part importante du gaz peut traduire **une dépendance industrielle** ou **des usages thermiques anciens**.
            """)

        st.subheader("Données brutes")
        st.dataframe(region_data)
    else:
        st.warning("Données annuelles indisponibles.")

with tab3:
    st.header("Comparaison entre régions – Production & Consommation")

    df_annual = clean_data.get("annual_consumption")
    df_prod = clean_data.get("monthly_production")

    if df_annual is not None and not df_annual.empty and df_prod is not None and not df_prod.empty:
        st.subheader("🔌 Choix des régions")
        regions = sorted(set(df_annual["region"]).intersection(set(df_prod["region"])))
        selected_regions = st.multiselect("Sélectionnez les régions à comparer", regions, default=regions[:3])

        st.subheader("⚡ Consommation électrique annuelle (GWh)")
        df_conso = df_annual[df_annual["region"].isin(selected_regions)].copy()
        df_conso["année"] = pd.to_numeric(df_conso["année"], errors="coerce").astype("Int64")
        df_conso_pivot = df_conso.pivot(index="année", columns="region", values="conso_elec_GWh")
        st.line_chart(df_conso_pivot)

        st.subheader("🔋 Production annuelle totale (GWh)")
        df_prod["year"] = pd.to_numeric(df_prod["mois"].dt.year, errors="coerce").astype("Int64")
        df_prod_grouped = df_prod[df_prod["region"].isin(selected_regions)].groupby(["year", "region"])[
            "production_GWh"].sum().reset_index()
        df_prod_pivot = df_prod_grouped.pivot(index="year", columns="region", values="production_GWh")
        st.line_chart(df_prod_pivot)

        st.subheader("⚖️ Écart Production - Consommation")

        # Sélecteur pour une seule région
        selected_region_for_gap = st.selectbox(
            "Choisissez une région pour afficher l'écart production-consommation",
            sorted(df_conso["region"].unique()),
            key="region_gap"
        )

        # Calcul de l’écart uniquement pour cette région
        df_conso_gap = df_conso[df_conso["region"] == selected_region_for_gap]
        df_prod_gap = df_prod_grouped[df_prod_grouped["region"] == selected_region_for_gap].rename(
            columns={"year": "année", "production_GWh": "prod_GWh"})

        df_gap = pd.merge(
            df_conso_gap.groupby(["année", "region"])["conso_elec_GWh"].sum().reset_index(),
            df_prod_gap,
            on=["année", "region"],
            how="inner"
        )
        df_gap["écart_GWh"] = df_gap["prod_GWh"] - df_gap["conso_elec_GWh"]
        df_gap["année"] = df_gap["année"].astype(str)

        # Graphique simple, une seule barre par année
        chart_grouped = alt.Chart(df_gap).mark_bar().encode(
            x=alt.X('année:N', title="Année"),
            y=alt.Y('écart_GWh:Q', title="Écart Production - Consommation (GWh)"),
            color=alt.value("#007BFF"),
            tooltip=["année", "écart_GWh"]
        ).properties(
            width=600,
            height=400,
            title=f"⚖️ Écart Production - Consommation – {selected_region_for_gap}"
        )

        st.altair_chart(chart_grouped, use_container_width=True)

        st.markdown("""
        - Un **écart positif** signifie que la région **produit plus qu'elle ne consomme**, ce qui en fait un **territoire exportateur net**.
        - Un **écart négatif** indique une **dépendance à l'importation d'énergie**, souvent liée à une faible capacité de production locale.
        """)
    else:
        st.warning("Les données production ou consommation ne sont pas disponibles.")


with tab4:
    st.header("Carte des bornes de recharge pour véhicules électriques")
    st.write("Visualisez les bornes IRVE installées en France métropolitaine.")

    if ev_data is not None and not ev_data.empty:
        view_state = pdk.ViewState(
            latitude=ev_data["lat"].mean(),
            longitude=ev_data["lon"].mean(),
            zoom=6,
            pitch=0
        )

        layer = pdk.Layer(
            "ScatterplotLayer",
            data=ev_data,
            get_position='[lon, lat]',
            get_fill_color='[0, 0, 255, 180]',
            get_radius=5000,
            pickable=True
        )

        st.pydeck_chart(pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={"text": "Aménageur : {amenageur}\nRégion : {region}"},
            map_provider='carto',
            map_style='light'
        ))
    else:
        st.warning("Aucune donnée disponible pour les bornes IRVE.")

with tab5:
    st.header("Indicateurs simples sur les bornes IRVE")
    st.write("Quelques indicateurs clés sur les infrastructures de recharge.")

    if ev_data is not None and not ev_data.empty:
        st.metric("Nombre total de bornes", len(ev_data))
        puissance_moy = ev_data["puissance_kW"].mean()
        st.metric("Puissance moyenne (kW)", f"{puissance_moy:.1f}")

        st.subheader("Top 10 régions par nombre de bornes")
        top_regions = ev_data["region"].value_counts().head(10).reset_index()
        top_regions.columns = ["Région", "Nombre de bornes"]
        st.dataframe(top_regions)
    else:
        st.warning("Données non disponibles pour les statistiques.")
