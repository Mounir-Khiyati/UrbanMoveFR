import os
import pandas as pd

IN_CSV  = "historique_velib.csv"
OUT_CSV = "historique_hourly.csv"

if not os.path.exists(IN_CSV):
    raise FileNotFoundError(f"❌ Introuvable : {IN_CSV}. Lance d'abord la collecte.")

# 1) Charger l’historique
df = pd.read_csv(IN_CSV, parse_dates=["ts"])

# (option) retirer lignes sans coordonnées
df = df.dropna(subset=["lat", "lon"])

# 2) Arrondir l’horodatage à l’heure
df["ts_hour"] = df["ts"].dt.floor("h")

# 3) Agréger par station + heure
agg = (
    df.groupby(["stationcode", "name", "arrdt", "lat", "lon", "ts_hour"], as_index=False)
      .agg(
          bikes_mean=("bikes", "mean"),
          bikes_median=("bikes", "median"),
          docks_mean=("docks", "mean"),
      )
)

# 4) Sauvegarder
agg.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
print(f"✅ Fichier écrit : {OUT_CSV} | lignes: {len(agg)} | heures uniques: {agg['ts_hour'].nunique()}")
