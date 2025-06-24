import streamlit as st
import pydeck as pdk
import pandas as pd
from scripts import preprocess

st.set_page_config(layout="wide")


# 📥 Chargement des données nettoyées
@st.cache_data
def load_and_prepare():
    return preprocess.clean_and_merge()


clean_data, indicators = load_and_prepare()

# 🧭 Navigation
tab1, tab2 = st.tabs(["🔌 Bornes IRVE (carte)", "📊 Indicateurs simples"])

with tab1:
    st.header("Carte des bornes de recharge pour véhicules électriques")

    ev_data = clean_data.get("ev_charging")
    if ev_data is not None and not ev_data.empty:
        st.map(ev_data.rename(columns={"latitude": "lat", "longitude": "lon"}))
    else:
        st.warning("Aucune donnée de bornes de recharge disponible.")

with tab2:
    st.header("Indicateurs simples sur les bornes IRVE")

    ev_data = clean_data.get("ev_charging")
    if ev_data is not None and not ev_data.empty:
        st.metric("Nombre total de bornes", len(ev_data))
        puissance_moy = ev_data["puissance_kW"].mean()
        st.metric("Puissance moyenne (kW)", f"{puissance_moy:.2f}")

        top_regions = ev_data["region"].value_counts().head(10)
        st.subheader("Top 10 régions par nombre de bornes")
        st.dataframe(top_regions)
    else:
        st.warning("Aucune donnée disponible pour les statistiques.")
