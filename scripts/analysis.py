import pandas as pd

def compute_taux_couverture(df_rt):
    if df_rt.empty:
        return pd.DataFrame()

    df = df_rt.copy()
    df["taux_couverture"] = df["prod_totale_MW"] / df["conso_MW"]

    latest = df.groupby("region").agg({
        "prod_totale_MW": "last",
        "conso_MW": "last",
        "taux_couverture": "last"
    }).reset_index()

    return latest.sort_values("taux_couverture", ascending=False)

def detect_regions_excedentaires(df_rt):
    if df_rt.empty:
        return pd.DataFrame()

    df = df_rt.copy()
    latest = df.groupby("region_libelle").agg({
        "prod_MW": "last",
        "conso_MW": "last"
    }).reset_index()

    latest["excedentaire"] = latest["prod_MW"] > latest["conso_MW"]
    return latest[latest["excedentaire"]]

def top_filieres_productrices(df_monthly):
    if df_monthly.empty:
        return pd.DataFrame()

    return df_monthly.groupby("filiere")["production_GWh"] \
        .sum() \
        .sort_values(ascending=False) \
        .reset_index()

def charging_stations_stats(df_irve):
    if df_irve.empty:
        return pd.DataFrame()

    return df_irve.groupby("commune").agg(
        nb_bornes=("puissance_nominale", "count"),
        puissance_moyenne=("puissance_nominale", "mean")
    ).reset_index().sort_values("nb_bornes", ascending=False)

def compute_indicators(data: dict):
    return {
        "taux_couverture": compute_taux_couverture(data["eco2mix_rt"]),
        "regions_excedentaires": detect_regions_excedentaires(data["eco2mix_rt"]),
        "top_filieres": top_filieres_productrices(data["monthly_production"]),
        "stats_irve": charging_stations_stats(data["ev_charging"])
    }
