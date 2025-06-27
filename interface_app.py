import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from scripts import load_data, preprocess
import plotly.express as px
import altair as alt
import requests




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

tab1, tab2, tab3, tab4 = st.tabs(["Production mensuelle par Région", "Conso en temps réel","Comparaison entre Région", "Bornes IRVE"])

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
    st.header("Consommation annuelle par région (GWh)")

    df_annual = clean_data.get("annual_consumption")
    if df_annual is not None and not df_annual.empty:
        regions = sorted(df_annual["region"].unique())

        selected_region = st.selectbox("Choisissez une région", regions, key="region_select_tab2")
        region_data = df_annual[df_annual["region"] == selected_region].copy()

        region_data["année"] = pd.to_datetime(region_data["année"], unit="ns", errors="coerce").dt.year
        region_data = region_data.dropna(subset=["année"]).sort_values("année")
        region_data["année"] = region_data["année"].astype(int).astype(str)

        st.subheader(f"Consommation électrique annuelle – {selected_region}")
        st.line_chart(region_data.set_index("année")["conso_elec_GWh"])

        st.subheader("Répartition annuelle électricité vs gaz")
        st.bar_chart(region_data.set_index("année")[["conso_elec_GWh", "conso_gaz_GWh"]])

        st.subheader("Répartition % Électricité vs Gaz")

        region_pct = region_data.dropna(subset=["conso_elec_GWh", "conso_gaz_GWh"]).copy()
        region_pct["total"] = region_pct["conso_elec_GWh"] + region_pct["conso_gaz_GWh"]
        region_pct["elec_pct"] = (region_pct["conso_elec_GWh"] / region_pct["total"] * 100).round(2)
        region_pct["gaz_pct"] = (region_pct["conso_gaz_GWh"] / region_pct["total"] * 100).round(2)

        df_pct_plot = region_pct[["année", "elec_pct", "gaz_pct"]].melt(
            id_vars="année",
            value_vars=["elec_pct", "gaz_pct"],
            var_name="Énergie",
            value_name="Part (%)"
        )

        fig = px.line(
            df_pct_plot,
            x="année",
            y="Part (%)",
            color="Énergie",
            markers=True,
            labels={"année": "Année"},
            title="Évolution comparée de la part Électricité vs Gaz (%)"
        )
        fig.update_layout(legend_title_text="Source d'énergie", xaxis_type='category')
        st.plotly_chart(fig, use_container_width=True)

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

        # Conversion propre de l'année depuis timestamp
        df_annual["année"] = pd.to_datetime(df_annual["année"], unit="ns", errors="coerce").dt.year.astype(str)

        st.subheader("Consommation électrique annuelle (GWh)")
        df_conso = df_annual[df_annual["region"].isin(selected_regions)].copy()
        df_conso_pivot = df_conso.pivot(index="année", columns="region", values="conso_elec_GWh")
        st.line_chart(df_conso_pivot)

        st.subheader("Production annuelle totale (GWh)")
        df_prod["year"] = df_prod["mois"].dt.year.astype(str)
        df_prod_grouped = df_prod[df_prod["region"].isin(selected_regions)].groupby(["year", "region"])[
            "production_GWh"].sum().reset_index()
        df_prod_pivot = df_prod_grouped.pivot(index="year", columns="region", values="production_GWh")
        st.line_chart(df_prod_pivot)

        st.subheader("Écart Production - Consommation")

        selected_region_for_gap = st.selectbox(
            "Choisissez une région pour afficher l'écart production-consommation",
            sorted(df_conso["region"].unique()),
            key="region_gap"
        )

        df_conso_gap = df_conso[df_conso["region"] == selected_region_for_gap]
        df_prod_gap = df_prod_grouped[df_prod_grouped["region"] == selected_region_for_gap].rename(
            columns={"year": "année", "production_GWh": "prod_GWh"}
        )

        df_gap = pd.merge(
            df_conso_gap.groupby(["année", "region"])["conso_elec_GWh"].sum().reset_index(),
            df_prod_gap,
            on=["année", "region"],
            how="inner"
        )
        df_gap["écart_GWh"] = df_gap["prod_GWh"] - df_gap["conso_elec_GWh"]

        df_national_gap = pd.merge(
            df_conso.groupby(["année", "region"])["conso_elec_GWh"].sum().reset_index(),
            df_prod_grouped.rename(columns={"year": "année", "production_GWh": "prod_GWh"}),
            on=["année", "region"],
            how="inner"
        )
        df_national_gap["écart_GWh"] = df_national_gap["prod_GWh"] - df_national_gap["conso_elec_GWh"]
        df_mean = df_national_gap.groupby("année")["écart_GWh"].mean().reset_index()

        bar_chart = alt.Chart(df_gap).mark_bar().encode(
            x=alt.X('année:N', title="Année"),
            y=alt.Y('écart_GWh:Q', title="Écart Production - Consommation (GWh)"),
            color=alt.condition(
                alt.datum.écart_GWh > 0,
                alt.value("#2E86DE"),
                alt.value("#E74C3C")
            ),
            tooltip=["année", "écart_GWh"]
        )

        line_chart = alt.Chart(df_mean).mark_line(strokeDash=[5, 5], color='black').encode(
            x='année:N',
            y='écart_GWh:Q',
            tooltip=["année", alt.Tooltip("écart_GWh", title="Moyenne nationale")]
        )

        final_chart = (bar_chart + line_chart).properties(
            width=700,
            height=400,
            title=f"Écart Production - Consommation – {selected_region_for_gap} (avec moyenne nationale)"
        )

        st.altair_chart(final_chart, use_container_width=True)

        st.markdown("""
        - Un **écart positif** signifie que la région **produit plus qu'elle ne consomme**, ce qui en fait un **territoire exportateur net**.
        - Un **écart négatif** indique une **dépendance à l'importation d'énergie**, souvent liée à une faible capacité de production locale.
        - La **ligne pointillée** représente la **moyenne nationale** de l’écart, ce qui permet de situer chaque région par rapport à l’ensemble du pays.
        """)
    else:
        st.warning("Les données production ou consommation ne sont pas disponibles.")

    st.subheader("Visualisation cartographique")

    geojson_url = "https://france-geojson.gregoiredavid.fr/repo/regions.geojson"
    geojson_data = requests.get(geojson_url).json()

    # Préparation des données
    df_conso_mean = df_annual.groupby("region")["conso_elec_GWh"].mean().reset_index()
    df_prod["year"] = df_prod["mois"].dt.year
    df_prod_annual = df_prod.groupby(["region", "year"])["production_GWh"].sum().reset_index()
    df_prod_mean = df_prod_annual.groupby("region")["production_GWh"].mean().reset_index()

    # Merge pour liaison nom -> valeur
    conso_dict = dict(zip(df_conso_mean["region"], df_conso_mean["conso_elec_GWh"]))
    prod_dict = dict(zip(df_prod_mean["region"], df_prod_mean["production_GWh"]))


    # Création des cartes Folium
    def create_choropleth(data_dict, legend_name, color_scale):
        fmap = folium.Map(location=[46.5, 2.5], zoom_start=5, tiles="cartodb positron")
        folium.Choropleth(
            geo_data=geojson_data,
            name="choropleth",
            data=data_dict,
            columns=["region", "value"],
            key_on="feature.properties.nom",
            fill_color=color_scale,
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name=legend_name,
            highlight=True
        ).add_to(fmap)

        folium.GeoJson(
            geojson_data,
            name="labels",
            style_function=lambda x: {"color": "transparent", "fillOpacity": 0},
            tooltip=folium.GeoJsonTooltip(fields=["nom"], aliases=["Région :"])
        ).add_to(fmap)

        return fmap

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Consommation moyenne (GWh)")
        conso_data = pd.DataFrame({"region": list(conso_dict.keys()), "value": list(conso_dict.values())})
        map_conso = create_choropleth(conso_dict, "Consommation (GWh)", "Reds")
        st_folium(map_conso, width=500, height=550)

    with col2:
        st.markdown("### Production moyenne (GWh)")
        prod_data = pd.DataFrame({"region": list(prod_dict.keys()), "value": list(prod_dict.values())})
        map_prod = create_choropleth(prod_dict, "Production (GWh)", "Reds")
        st_folium(map_prod, width=500, height=550)

with tab4:
    st.header("Carte des bornes de recharge pour véhicules électriques")
    st.write("Visualisez les bornes IRVE installées en France métropolitaine.")

    ev_data = clean_data.get("ev_charging")

    if ev_data is not None and not ev_data.empty:
        # Choix de la région pour filtrer la carte uniquement
        available_regions = sorted(ev_data["region"].dropna().unique())
        selected_region_map = st.selectbox("Sélectionnez une région à afficher sur la carte", available_regions)

        region_ev_data = ev_data[ev_data["region"] == selected_region_map].dropna(subset=["lat", "lon"])

        if not region_ev_data.empty:
            lat_center = region_ev_data["lat"].mean()
            lon_center = region_ev_data["lon"].mean()

            m = folium.Map(location=[lat_center, lon_center], zoom_start=8, control_scale=True)
            marker_cluster = MarkerCluster().add_to(m)

            for _, row in region_ev_data.iterrows():
                folium.Marker(
                    location=[row["lat"], row["lon"]],
                    popup=folium.Popup(
                        f"<b>Aménageur :</b> {row['amenageur']}<br><b>Région :</b> {row['region']}",
                        max_width=250
                    ),
                    icon=folium.Icon(color="blue", icon="bolt", prefix="fa")
                ).add_to(marker_cluster)

            # Correction du bug d'espace blanc
            with st.container():
                with st.spinner("Chargement de la carte..."):
                    st_folium(m, height=500)

            st.write("Quelques indicateurs clés sur les infrastructures de recharge.")
            st.metric("Nombre de bornes dans la région", len(region_ev_data))
            st.metric("Puissance moyenne (kW)", f"{region_ev_data['puissance_kW'].mean():.1f}")

        else:
            st.warning("Aucune donnée valide pour cette région.")
    else:
        st.warning("Aucune donnée disponible pour les bornes IRVE.")

    st.header("Bornes IRVE & Corrélation énergétique")

    df_annual = clean_data.get("annual_consumption")
    ev_data = clean_data.get("ev_charging")

    if df_annual is not None and not df_annual.empty and ev_data is not None and not ev_data.empty:

        if "date_maj" in ev_data.columns:
            ev_data["annee_installation"] = pd.to_datetime(ev_data["date_maj"], errors="coerce").dt.year
        else:
            st.error("La colonne `date_maj` est absente de vos données de bornes IRVE.")
            st.stop()

        df_bornes = ev_data.groupby(["region", "annee_installation"]).size().reset_index(name="n_bornes")
        df_bornes = df_bornes.dropna(subset=["annee_installation"])
        df_bornes = df_bornes[df_bornes["annee_installation"] >= 2010]

        st.subheader("Évolution du nombre de bornes IRVE installées")
        fig = px.bar(
            df_bornes,
            x="annee_installation",
            y="n_bornes",
            color="region",
            barmode="group",
            title="Nombre de bornes installées par an et par région",
            labels={"annee_installation": "Année", "n_bornes": "Nombre de bornes"}
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("""
        Cette visualisation permet de voir **la dynamique d’installation des bornes de recharge** selon les régions.

        Une corrélation avec l’augmentation de la consommation électrique pourrait indiquer l’impact du développement de la mobilité électrique sur la demande énergétique.
        """)
    else:
        st.warning("Les données de consommation ou de bornes IRVE ne sont pas disponibles.")
