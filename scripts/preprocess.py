# scripts/preprocess.py

import pandas as pd

def clean_eco2mix_real_time(df):
    """Nettoie les données temps réel éCO2mix"""
    if df.empty:
        return df

    df["date_heure"] = pd.to_datetime(df["date_heure"])

    # Création de la production totale
    df["prod_totale_MW"] = df[[
        "thermique", "nucleaire", "eolien", "solaire", "hydraulique", "bioenergies"
    ]].sum(axis=1, skipna=True)

    # Renommage cohérent avec le reste de ton projet
    df = df.rename(columns={
        "libelle_region": "region",
        "consommation": "conso_MW"
    })

    return df[["date_heure", "region", "conso_MW", "prod_totale_MW"]].sort_values("date_heure")

def clean_eco2mix_definitif(df):
    if df.empty:
        return df

    df["date"] = pd.to_datetime(df["date"])

    # Vérifie les noms de colonnes avant renommage
    expected_columns = df.columns.tolist()
    print("Colonnes disponibles dans eco2mix_def:", expected_columns)

    # Sécurise le renommage avec des colonnes présentes
    df = df.rename(columns={
        "libelle_region": "region",
        "consommation": "conso_MW",
        "production_total": "prod_MW"  # <- Vérifie si c’est bien ce nom
    })

    if "prod_MW" not in df.columns:
        # Essaye une alternative si la colonne "production_total" n’existe pas
        if "production" in df.columns:
            df["prod_MW"] = df["production"]
        else:
            df["prod_MW"] = pd.NA  # ou df["prod_MW"] = 0 si tu préfères un nombre

    return df[["date", "region", "conso_MW", "prod_MW"]].sort_values("date")


def clean_monthly_production(df):
    if df.empty:
        return df

    # Vérifie les colonnes disponibles
    print("Colonnes disponibles dans monthly_production:", df.columns.tolist())

    df["mois"] = pd.to_datetime(df["mois"])

    # Restructuration en format long pour avoir une colonne 'filiere' et 'production_GWh'
    df_long = df.melt(
        id_vars=["mois", "region"],
        value_vars=[
            "production_nucleaire",
            "production_thermique",
            "production_hydraulique",
            "production_eolienne",
            "production_solaire",
            "production_bioenergies"
        ],
        var_name="filiere",
        value_name="production_GWh"
    )

    # Nettoyage du nom des filières
    df_long["filiere"] = df_long["filiere"].str.replace("production_", "", regex=False)

    return df_long.dropna(subset=["production_GWh"])

def clean_energy_facilities(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["region", "commune", "filiere", "puissance_MW"])
    return df.rename(columns={
        "puismaxinstallee": "puissance_MW"
    })[["region", "commune", "filiere", "puissance_MW"]]


def clean_ev_charging(df):
    expected_cols = ["n_amenageur", "region", "puiss_max", "xlongitude", "ylatitude"]
    missing = set(expected_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes dans les bornes IRVE : {missing}")

    df_clean = df[expected_cols].copy()
    df_clean.rename(columns={
        "n_amenageur": "amenageur",
        "puiss_max": "puissance_kW",
        "xlongitude": "longitude",
        "ylatitude": "latitude"
    }, inplace=True)
    return df_clean


def clean_and_merge(data: dict):
    cleaned = {
        "eco2mix_rt": clean_eco2mix_real_time(data.get("eco2mix_rt")),
        "eco2mix_def": clean_eco2mix_definitif(data.get("eco2mix_def")),
        "monthly_production": clean_monthly_production(data.get("monthly_production")),
        "facilities": clean_energy_facilities(data.get("facilities")),
        "ev_charging": clean_ev_charging(data.get("ev_charging")),
    }

    return cleaned
