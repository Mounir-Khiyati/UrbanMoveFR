import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

st.set_page_config(page_title="UrbanMoveFR", layout="wide")
st.title("🚲 UrbanMoveFR – Dashboard Vélib")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

# KPIs
heures = pd.read_csv(os.path.join(OUTPUT_DIR, "kpi_heures_de_pointe.csv"))
saturation = pd.read_csv(os.path.join(OUTPUT_DIR, "kpi_saturation_arrondissement.csv"))

# Graphiques
col1, col2 = st.columns(2)
with col1:
    st.subheader("Heures de pointe")
    st.line_chart(heures.set_index("hour")[["total_bikes"]])
with col2:
    st.subheader("Saturation par arrondissement")
    st.bar_chart(saturation.set_index("arrdt")[["is_empty"]])

# Carte
st.subheader("Carte des stations (50 affichées)")
df_map = pd.read_parquet(os.path.join(DATA_DIR, "historique_hourly.parquet"))
df_map["empty_pct"] = (df_map["bikes_mean"] == 0) * 100
map_df = df_map.groupby(["stationcode", "name", "lat", "lon", "arrdt"]).agg({"empty_pct": "mean"}).reset_index()

arrondissement = st.selectbox("Choisis un arrondissement", ["Tous"] + sorted(map_df["arrdt"].unique()))
if arrondissement != "Tous":
    map_df = map_df[map_df["arrdt"] == arrondissement]

m = folium.Map(location=[48.8566, 2.3522], zoom_start=12)
for _, r in map_df.head(50).iterrows():
    color = "red" if r["empty_pct"] > 50 else "orange" if r["empty_pct"] > 20 else "green"
    folium.CircleMarker(
        location=[r["lat"], r["lon"]],
        radius=6,
        color=color,
        fill=True,
        popup=f"{r['name']} – {r['empty_pct']:.0f} % vide"
    ).add_to(m)

st_folium(m, width=700, height=400)