import pandas as pd
import folium
import webbrowser

# 1) Charger les anomalies
df = pd.read_csv("anomalies_velib.csv", parse_dates=["ts_hour"])

# 2) Récupérer la dernière heure
last_ts = df["ts_hour"].max()
df_last = df[df["ts_hour"] == last_ts]

print(f"Affichage des anomalies pour {last_ts}")

# 3) Sélectionner un arrondissement (à changer selon ce que tu veux analyser)
arrondissement_cible = "Paris 15e Arrondissement"

df_filtre = df_last[df_last["arrdt"] == arrondissement_cible]

# 4) Créer la carte centrée sur Paris
m = folium.Map(location=[48.8566, 2.3522], zoom_start=13)

# 5) Ajouter les stations filtrées
for _, row in df_filtre.iterrows():
    color = "red" if row["is_anomaly"] else "green"

    popup = f"""
    <b>{row['name']}</b><br>
    Arrdt: {row['arrdt']}<br>
    Vélos (médiane): {row['bikes_median']}<br>
    Docks (moyenne): {row['docks_mean']}<br>
    Anomalie: {row['is_anomaly']}
    """

    folium.CircleMarker(
        location=[row["lat"], row["lon"]],
        radius=6,
        color=color,
        fill=True,
        fill_color=color,
        popup=popup
    ).add_to(m)

# 6) Légende
legend_html = """
<div style="
    position: fixed;
    bottom: 30px; left: 30px; width: 160px; height: 70px;
    border:2px solid grey; z-index:9999; font-size:14px;
    background-color:white; padding: 10px;">
<b>Légende</b><br>
<span style="color:green;">●</span> Station normale<br>
<span style="color:red;">●</span> Station anomalie
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# 7) Sauvegarder et ouvrir
m.save("map_anomalies_arrdt.html")
webbrowser.open("map_anomalies_arrdt.html")
print(f"✅ Carte filtrée sur {arrondissement_cible} enregistrée dans map_anomalies_arrdt.html")
