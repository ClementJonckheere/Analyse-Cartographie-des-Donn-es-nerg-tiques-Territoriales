import pandas as pd


def clean_monthly_production(df):
    if df.empty:
        return df

    df["mois"] = pd.to_datetime(df["mois"])
    df_long = df.melt(
        id_vars=["mois", "region"],
        value_vars=[
            "production_nucleaire", "production_thermique",
            "production_hydraulique", "production_eolienne",
            "production_solaire", "production_bioenergies"
        ],
        var_name="filiere",
        value_name="production_GWh"
    )
    df_long["filiere"] = df_long["filiere"].str.replace("production_", "", regex=False)
    return df_long.dropna(subset=["production_GWh"])


def clean_energy_facilities(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["region", "commune", "filiere", "puissance_MW"])

    return df.rename(columns={
        "puismaxinstallee": "puissance_MW"
    })[["region", "commune", "filiere", "puissance_MW"]]


def clean_ev_charging(df):
    if df.empty:
        return pd.DataFrame(columns=[
            "amenageur", "region", "departement", "commune",
            "puissance_kW", "lat", "lon"
        ])

    def extract_lat(x):
        return x.get("lat") if isinstance(x, dict) else None

    def extract_lon(x):
        return x.get("lon") if isinstance(x, dict) else None

    df["lat"] = df["geo_point_borne"].apply(extract_lat)
    df["lon"] = df["geo_point_borne"].apply(extract_lon)

    df_clean = df.rename(columns={
        "n_amenageur": "amenageur",
        "puiss_max": "puissance_kW",
        "code_insee_commune": "commune"
    })

    return df_clean[[
        "amenageur", "region", "departement", "commune",
        "puissance_kW", "lat", "lon"
    ]].dropna(subset=["lat", "lon"])

def clean_annual_consumption(df):
    if df.empty:
        return df

    df = df.rename(columns={
        "annee": "année",
        "region": "region",
        "consommation_brute_electricite_rte": "conso_elec_GWh",
        "consommation_brute_gaz_totale": "conso_gaz_GWh",
        "consommation_brute_totale": "conso_totale_GWh"
    })

    df["année"] = pd.to_numeric(df["année"], errors="coerce")
    df = df.dropna(subset=["année", "region", "conso_elec_GWh"])
    return df[["année", "region", "conso_elec_GWh", "conso_gaz_GWh", "conso_totale_GWh"]]


def clean_and_merge(data: dict):
    return {
        "monthly_production": clean_monthly_production(data.get("monthly_production")),
        "facilities": clean_energy_facilities(data.get("facilities")),
        "ev_charging": clean_ev_charging(data.get("ev_charging")),
        "annual_consumption": clean_annual_consumption(data.get("annual_consumption")),
    }

