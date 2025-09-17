import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="UrbanMoveFR", layout="wide")
st.title("🚲 UrbanMoveFR – Dashboard Vélib")

# 🔧 Chemins
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

# 📊 Chargement des KPIs
heures = pd.read_csv(os.path.join(OUTPUT_DIR, "kpi_heures_de_pointe.csv"))
saturation = pd.read_csv(os.path.join(OUTPUT_DIR, "kpi_saturation_arrondissement.csv"))

# 📈 Affichage
st.subheader("Heures de pointe")
st.line_chart(heures.set_index("hour")[["total_bikes"]])

st.subheader("Saturation par arrondissement")
st.bar_chart(saturation.set_index("arrdt")[["is_empty"]])