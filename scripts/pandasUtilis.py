import json, glob, os
import pandas as pd

# Prendre le dernier fichier data_velib_*.json trouvé
files = glob.glob("data_velib_*.json")
if not files:
    raise FileNotFoundError("Aucun JSON trouvé. Lance d’abord le script de récupération.")
latest = max(files, key=os.path.getmtime)
print("Lecture :", latest)

with open(latest, "r", encoding="utf-8") as f:
    data = json.load(f)

records = data.get("records", [])
rows = []
for s in records:
    fields = s.get("fields", {
        "name": "Inconnu",
        "nom_arrondissement_communes": "Inconnu",
        "numbikesavailable": 0,
        "numdocksavailable": 0,
        "duedate": "Problème technique"
    })
    rows.append(fields)

df = pd.DataFrame(rows)
df.to_csv("velib_propre.csv", index=False, encoding="utf-8-sig")
print("✅ Écrit : velib_propre.csv | lignes :", len(df))

