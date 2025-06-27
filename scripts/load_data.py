import requests
import pandas as pd
import streamlit as st

BASE_URL = "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets"
HEADERS = {"Accept": "application/json"}

def fetch_api_data(endpoint, params=None, limit=100, max_records=10000):
    url = f"{BASE_URL}/{endpoint}/records"
    all_records = []
    offset = 0

    if params is None:
        params = {}

    # Pagination
    while offset < max_records:
        current_params = params.copy()
        current_params["limit"] = limit
        current_params["offset"] = offset

        print(f"Requête : {url} | offset = {offset}")

        try:
            response = requests.get(url, headers=HEADERS, params=current_params)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            if not results:
                print("Fin des résultats")
                break

            all_records.extend(results)

            if len(results) < limit:
                print("Moins de résultats que le 'limit' => Fin")
                break

            offset += limit

            if offset >= max_records:
                print("Offset limite atteint (10000 max)")
                break

        except Exception as e:
            print(f"Erreur API {endpoint} à l’offset {offset} : {e}")
            break

    return pd.DataFrame.from_records(all_records)

# Consommation annuelle par région
@st.cache_data
def load_annual_energy_consumption():
    return fetch_api_data("consommation-annuelle-brute-regionale")

# Production mensuelle par filière
@st.cache_data
def load_monthly_production_by_filiere():
    return fetch_api_data("production-regionale-mensuelle-filiere")

# Installations de production et stockage d'électricité
@st.cache_data
def load_energy_facilities():
    return fetch_api_data("registre-national-installation-production-stockage-electricite-agrege")

# Bornes de recharge IRVE
@st.cache_data
def load_ev_charging_stations():
    return fetch_api_data("bornes-irve")

# Chargement de toutes les données
def load_all():
    return {
        "monthly_production": load_monthly_production_by_filiere(),
        "facilities": load_energy_facilities(),
        "ev_charging": load_ev_charging_stations(),
        "annual_consumption": load_annual_energy_consumption()
    }
