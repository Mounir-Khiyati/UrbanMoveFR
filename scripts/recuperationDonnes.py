import requests
import json
from datetime import datetime

BASE_URL = "https://opendata.paris.fr/api/records/1.0/search/"
params = {
    "dataset": "velib-disponibilite-en-temps-reel",
    "rows": 2000  # assez grand pour couvrir toutes les stations
}

resp = requests.get(BASE_URL, params=params, timeout=20)
resp.raise_for_status()  # lève une erreur si l’API répond 4xx/5xx
data = resp.json()

filename = f"data_velib_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(filename, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ Données Vélib sauvegardées dans {filename}")
print("📊 Nb d'enregistrements reçus :", len(data.get("records", [])))
