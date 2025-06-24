# scripts/mapping.py

import folium
import pandas as pd
from folium.plugins import MarkerCluster

def create_interactive_map(indicators, output_path="outputs/map.html"):
    print("🗺️ Génération de la carte interactive...")

    # Centre de la carte sur la France
    m = folium.Map(location=[46.6, 2.5], zoom_start=6, tiles="CartoDB positron")

    # 1. Couche : taux de couverture énergétique par région
    taux_df = indicators.get("taux_couverture")
    if taux_df is not None and not taux_df.empty:
        for _, row in taux_df.iterrows():
            popup_text = (
                f"<b>Région :</b> {row['region_libelle']}<br>"
                f"<b>Taux de couverture :</b> {row['taux_couverture']:.2f}<br>"
                f"<b>Production :</b> {row['prod_MW']} MW<br>"
                f"<b>Consommation :</b> {row['conso_MW']} MW"
            )
            # Tu pourrais améliorer ceci avec des coordonnées régionales précises si disponibles
            folium.Marker(
                location=[46.6, 2.5],  # Placeholder — à remplacer par centroid de la région
                popup=popup_text,
                icon=folium.Icon(color='green' if row['taux_couverture'] >= 1 else 'red')
            ).add_to(m)

    # 2. Couche : bornes de recharge IRVE
    irve_df = indicators.get("stats_irve")
    if irve_df is not None and not irve_df.empty:
        marker_cluster = MarkerCluster(name="Bornes IRVE").add_to(m)
        for _, row in irve_df.iterrows():
            # Tu dois disposer de la latitude/longitude dans les données brutes
            lat = row.get("ylatitude", None)
            lon = row.get("xlongitude", None)
            if lat is not None and lon is not None:
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=4,
                    popup=f"Commune : {row['commune']}<br>Bornes : {row['nb_bornes']}",
                    color="blue",
                    fill=True,
                    fill_opacity=0.7
                ).add_to(marker_cluster)

    folium.LayerControl().add_to(m)
    m.save(output_path)
    print(f"✅ Carte sauvegardée : {output_path}")
