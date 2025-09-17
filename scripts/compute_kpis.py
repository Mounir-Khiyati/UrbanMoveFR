import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR   = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

df = pd.read_parquet(os.path.join(DATA_DIR, "historique_hourly.parquet"))
print(f"📥 Chargé : {len(df):,} lignes")

# 1️⃣ Heures de pointe
df["hour"] = df["ts_hour"].dt.hour
heures = df.groupby("hour")[["bikes_mean", "docks_mean"]].mean()
heures["total_bikes"] = heures["bikes_mean"]
heures.to_csv(os.path.join(OUTPUT_DIR, "kpi_heures_de_pointe.csv"))
print("✅ Heures de pointe → kpi_heures_de_pointe.csv")

# 2️⃣ Saturation
df["total_bikes"] = df["bikes_mean"]
df["is_empty"] = df["total_bikes"] == 0
saturation = df.groupby("arrdt")["is_empty"].mean() * 100
saturation.to_csv(os.path.join(OUTPUT_DIR, "kpi_saturation_arrondissement.csv"))
print("✅ Saturation → kpi_saturation_arrondissement.csv")

# 3️⃣ Top stations vides
station_sat = df.groupby("stationcode")["is_empty"].mean() * 100
station_sat = station_sat.sort_values(ascending=False).head(20)
station_sat.to_csv(os.path.join(OUTPUT_DIR, "kpi_top_stations_vides.csv"))
print("✅ Top 20 stations vides → kpi_top_stations_vides.csv")

print("🎉 Tous les KPIs prêts dans outputs/")