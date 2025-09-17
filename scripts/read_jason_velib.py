import json, glob, os

# 1. Trouver le dernier fichier JSON généré
files = glob.glob("data_velib_*.json")
if not files:
    raise FileNotFoundError("❌ Aucun fichier data_velib_*.json trouvé. Lance d’abord recuperationDonnes.py")
latest = max(files, key=os.path.getmtime)
print("📂 Lecture du fichier :", latest)

# 2. Charger le fichier JSON
with open(latest, "r", encoding="utf-8") as f:
    data = json.load(f)

# 3. Récupérer la liste des enregistrements (stations)
records = data.get("records", [])
records_propres = [station["fields"] for station in records if "fields" in station]

# 4. Afficher quelques stations pour vérifier
for station in records_propres[:10]:
    print(station)
