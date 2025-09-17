import os
import pandas as pd

# 🔧 Chemins absolus automatiques
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

IN_CSV      = os.path.join(DATA_DIR, "historique_hourly.csv")
OUT_PARQUET = os.path.join(DATA_DIR, "historique_hourly.parquet")

print("📍 Dossier base :", BASE_DIR)
print("📍 Recherche CSV ici :", IN_CSV)

if not os.path.exists(IN_CSV):
    raise FileNotFoundError(f"❌ Introuvable : {IN_CSV}. Lance l’agrégation d’abord.")

# 1) Charger CSV
df = pd.read_csv(IN_CSV, parse_dates=["ts_hour"])
print(f"📥 Chargé : {IN_CSV} | {len(df):,} lignes")

# 2) Quality checks
print("\n🔎 Vérifications qualité :")

# nombre de stations uniques
n_stations = df["stationcode"].nunique()
print(f"  • Stations uniques : {n_stations}")

# coordonnées valides
invalid_coords = df[(df["lat"].isna()) | (df["lon"].isna())]
print(f"  • Coordonnées invalides : {len(invalid_coords)}")

# doublons
dup = df.duplicated(subset=["stationcode", "ts_hour"])
print(f"  • Doublons trouvés : {dup.sum()}")

# Si doublons → suppression
if dup.any():
    df = df[~dup]
    print(f"    ✅ Doublons supprimés → {len(df):,} lignes restantes")

# 3) Sauvegarde en Parquet
os.makedirs(DATA_DIR, exist_ok=True)  # crée le dossier data s’il manque
df.to_parquet(OUT_PARQUET, index=False)
print(f"\n✅ Fichier Parquet écrit : {OUT_PARQUET}")