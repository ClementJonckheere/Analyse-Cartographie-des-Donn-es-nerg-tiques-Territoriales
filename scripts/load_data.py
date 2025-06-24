import requests
import pandas as pd

BASE_URL = "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets"
HEADERS = {"Accept": "application/json"}

def fetch_api_data(endpoint, params=None, limit=100, max_pages=20):
    url = f"{BASE_URL}/{endpoint}/records"
    all_records = []
    offset = 0

    if params is None:
        params = {}

    while True:
        current_params = params.copy()
        current_params["limit"] = limit
        current_params["offset"] = offset

        print(f"🔄 Requête : {url} | offset = {offset}")

        try:
            response = requests.get(url, headers=HEADERS, params=current_params)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            if not results:
                break
            all_records.extend(results)

            if len(results) < limit or offset >= limit * max_pages:
                break

            offset += limit
        except Exception as e:
            print(f"Erreur API {endpoint} à l’offset {offset} : {e}")
            break

    return pd.DataFrame.from_records(all_records)

def load_eco2mix_regional_real_time():
    df = fetch_api_data("eco2mix-regional-tr")
    return df

def load_eco2mix_regional_definitif():
    df = fetch_api_data("eco2mix-regional-cons-def")
    return df

def load_monthly_production_by_filiere():
    df = fetch_api_data("production-regionale-mensuelle-filiere")
    return df

def load_energy_facilities():
    return fetch_api_data("registre-national-installation-production-stockage-electricite-agrege")

def load_ev_charging_stations():
    return fetch_api_data("bornes-irve")

def load_all():
    return {
        "eco2mix_rt": load_eco2mix_regional_real_time(),
        "eco2mix_def": load_eco2mix_regional_definitif(),
        "monthly_production": load_monthly_production_by_filiere(),
        "facilities": load_energy_facilities(),
        "ev_charging": load_ev_charging_stations(),
    }
