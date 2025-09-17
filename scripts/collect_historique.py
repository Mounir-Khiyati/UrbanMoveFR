import os
import requests
import pandas as pd
from datetime import datetime, timezone

API_URL = "https://opendata.paris.fr/api/records/1.0/search/"
DATASET = "velib-disponibilite-en-temps-reel"
OUT_CSV = "historique_velib.csv"   # fichier d’historique

def utc_iso():
    """Horodatage UTC ISO (sans microsecondes)."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def fetch_all(rows=1000):
    """Paginer l'API pour récupérer toutes les stations Vélib."""
    start, out = 0, []
    while True:
        params = {"dataset": DATASET, "rows": rows, "start": start}
        r = requests.get(API_URL, params=params, timeout=20)
        r.raise_for_status()
        batch = [rec["fields"] for rec in r.json().get("records", []) if "fields" in rec]
        if not batch:  # plus de résultats → on arrête
            break
        out.extend(batch)
        start += rows
    return out

def to_rows(fields_list, ts):
    """Transformer les enregistrements bruts en lignes prêtes pour CSV."""
    rows = []
    for f in fields_list:
        lat, lon = (f.get("coordonnees_geo") or [None, None])
        rows.append({
            "ts": ts,  # horodatage du snapshot
            "stationcode": f.get("stationcode"),
            "name": f.get("name"),
            "arrdt": f.get("nom_arrondissement_communes", "Inconnu"),
            "lat": lat,
            "lon": lon,
            "bikes": f.get("numbikesavailable", 0),
            "docks": f.get("numdocksavailable", 0),
            # champs optionnels
            "mechanical": f.get("mechanical"),
            "ebikes": f.get("ebike"),
        })
    return rows

def main():
    ts = utc_iso()
    fields = fetch_all(rows=1000)  # récupère toutes les stations (≈1400)
    rows = to_rows(fields, ts)
    df = pd.DataFrame(rows).dropna(subset=["lat", "lon"])

    # Append dans le CSV (écrit l’en-tête seulement si le fichier n’existe pas)
    header = not os.path.exists(OUT_CSV)
    df.to_csv(OUT_CSV, mode="a", index=False, encoding="utf-8-sig", header=header)

    print(f"✅ Snapshot ajouté : {len(df)} stations @ {ts} → {OUT_CSV}")

if __name__ == "__main__":
    main()
