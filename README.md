# UrbanMoveFR – Dashboard Vélib
Smart dashboard d’analyse et de visualisation des données Vélib (Paris & banlieue).

##  Objectifs
- Détecter les heures de pointe
- Identifier les stations les plus saturées
- Visualiser l’état des stations en temps réel via carte interactive

##  Dataset
- Source : Open Data Paris – API « velib-disponibilite-en-temps-reel »
- Période : historique agrégé horaire (1 467 stations)
- Fichiers générés : `historique_hourly.parquet`, `anomalies_velib.csv`, KPIs CSV

##  Pipeline
1. **collect_historique.py** – télécharge l’historique brut
2. **aggregate_hourly.py** – agrège par heure
3. **detect_anomalies.py** – flag stations vides / bloquées
4. **compute_kpis.py** – calcule heures de pointe & saturation
5. **app_final.py** – dashboard Streamlit (carte + graphiques)

##  Lancement rapide
```bash
pip install -r requirements.txt
streamlit run app_final.py
