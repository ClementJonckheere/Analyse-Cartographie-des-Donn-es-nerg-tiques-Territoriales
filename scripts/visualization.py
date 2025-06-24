# scripts/visualization.py

import os
import matplotlib.pyplot as plt
import seaborn as sns

OUTPUT_DIR = "outputs/graphs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

sns.set(style="whitegrid")

def plot_taux_couverture(df):
    if df.empty:
        return
    plt.figure(figsize=(12, 6))
    sns.barplot(data=df, x="region_libelle", y="taux_couverture", palette="viridis")
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Taux de couverture (production / consommation)")
    plt.title("Taux de couverture énergétique par région")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/taux_couverture.png")
    plt.close()

def plot_top_filieres(df):
    if df.empty:
        return
    plt.figure(figsize=(10, 6))
    sns.barplot(data=df.head(10), x="production_GWh", y="filiere", palette="mako")
    plt.xlabel("Production totale (GWh)")
    plt.title("Top 10 des filières productrices")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/top_filieres.png")
    plt.close()

def plot_irve_distribution(df):
    if df.empty:
        return
    df_top = df.head(15)
    plt.figure(figsize=(12, 6))
    sns.barplot(data=df_top, x="commune", y="nb_bornes", palette="rocket")
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Nombre de bornes")
    plt.title("Top 15 des communes en nombre de bornes IRVE")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/top_irve_communes.png")
    plt.close()

def generate_all(indicators):
    plot_taux_couverture(indicators.get("taux_couverture"))
    plot_top_filieres(indicators.get("top_filieres"))
    plot_irve_distribution(indicators.get("stats_irve"))
