import pandas as pd

# 1) Charger le fichier d’historique brut
df = pd.read_csv("historique_velib.csv", parse_dates=["ts"])

# 2) Arrondir l’horodatage à l’heure
df["ts_hour"] = df["ts"].dt.floor("H")

# 3) Agréger par station + heure
agg = (
    df.groupby(["stationcode", "name", "arrdt", "lat", "lon", "ts_hour"])
      .agg(
          bikes_mean=("bikes", "mean"),
          bikes_median=("bikes", "median"),
          docks_mean=("docks", "mean"),
      )
      .reset_index()
)

# 4) Sauvegarder dans un nouveau CSV
agg.to_csv("historique_hourly.csv", index=False, encoding="utf-8-sig")

print(f"✅ Fichier écrit : historique_hourly.csv ({len(agg)} lignes)")
