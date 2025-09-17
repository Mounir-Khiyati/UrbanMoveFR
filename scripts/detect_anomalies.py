import os
import pandas as pd
import os
import pandas as pd

IN_CSV  = "historique_hourly.csv"
OUT_CSV = "anomalies_velib.csv"

# 🕵️ Diagnostic
print("📂 Dossier courant :", os.getcwd())
print("📄 Fichiers dans ce dossier :", os.listdir("."))
print("📂 Contenu du dossier data :", os.listdir("data") if os.path.exists("data") else "⚠️ Pas de dossier data")

if not os.path.exists(IN_CSV):
    raise FileNotFoundError("❌ 'historique_hourly.csv' introuvable. Lance d'abord l'agrégation horaire.")
    
IN_CSV  = "historique_hourly.csv"
OUT_CSV = "anomalies_velib.csv"

if not os.path.exists(IN_CSV):
    raise FileNotFoundError("❌ 'historique_hourly.csv' introuvable. Lance d'abord l'agrégation horaire.")

# 1) Charger + trier
df = pd.read_csv(IN_CSV, parse_dates=["ts_hour"]).sort_values(["stationcode", "ts_hour"])

# 2) Fonction par station : médiane/IQR glissants (fenêtre ~24h)
def compute_anomaly(g: pd.DataFrame, win: int = 24, thr: float = 3.0) -> pd.DataFrame:
    g = g.copy()
    minp = max(8, win // 3)

    # médiane glissante
    g["roll_med"] = g["bikes_median"].rolling(win, min_periods=minp).median()

    # IQR glissant
    def iqr(x):
        x = pd.Series(x).dropna()
        return (x.quantile(0.75) - x.quantile(0.25)) if len(x) else 0.0

    g["roll_iqr"] = g["bikes_median"].rolling(win, min_periods=minp).apply(iqr, raw=False)
    g["norm_iqr"] = g["roll_iqr"].replace(0, 1e-9)

    # score d'anomalie (écart normalisé)
    g["anomaly_score"] = (g["bikes_median"] - g["roll_med"]).abs() / g["norm_iqr"]
    g["is_anomaly"] = g["anomaly_score"] > thr

    # règle simple: station bloquée (0 vélos ET 0 bornes)
    g["is_blocked_now"] = (g["bikes_median"] == 0) & (g["docks_mean"] == 0)

    # bloquée ≥ 3h d'affilée (compte de runs)
    run_id = (~g["is_blocked_now"]).cumsum()
    g["blocked_run_len"] = g.groupby(run_id)["is_blocked_now"].cumsum().where(g["is_blocked_now"], 0)
    g["is_blocked_3h"] = g["blocked_run_len"] >= 3
    return g

# 3) Appliquer par station
out = df.groupby("stationcode", group_keys=False).apply(compute_anomaly)

# 4) Sauvegarder
cols = [
    "ts_hour","stationcode","name","arrdt","lat","lon",
    "bikes_mean","bikes_median","docks_mean",
    "roll_med","roll_iqr","anomaly_score","is_anomaly",
    "is_blocked_now","blocked_run_len","is_blocked_3h"
]
out[cols].to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

# 5) Résumé
n_rows = len(out)
n_anom = int(out["is_anomaly"].sum())
n_block = int(out["is_blocked_3h"].sum())
last_ts = out["ts_hour"].max()
print(f"✅ Écrit : {OUT_CSV} | lignes: {n_rows} | anomalies: {n_anom} | blocages≥3h: {n_block} | dernière heure: {last_ts}")
