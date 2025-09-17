import pandas as pd
import folium
import webbrowser
# 1) Charger le CSV filtré
df = pd.read_csv("velib_filtre.csv")

# 2) Créer une carte centrée sur Paris
carte = folium.Map(location=[48.8566, 2.3522], zoom_start=12)

# 3) Ajouter les stations une par une
for _, row in df.iterrows():
    lat, lon = row["coordonnees_geo"].strip("[]").split(",")  # extraire latitude/longitude
    lat, lon = float(lat), float(lon)

    # Couleur en fonction du nombre de vélos dispo
    if row["numbikesavailable"] == 0:
        couleur = "red"
    elif row["numbikesavailable"] < 5:
        couleur = "orange"
    else:
        couleur = "green"

    # Popup avec détails
    popup = f"""
    <b>{row['name']}</b><br>
    Arrondissement: {row['nom_arrondissement_communes']}<br>
    🚲 Vélos dispo: {row['numbikesavailable']}<br>
    🅿️ Places libres: {row['numdocksavailable']}
    """

    # Ajouter un marqueur
    folium.CircleMarker(
        location=[lat, lon],
        radius=6,
        color=couleur,
        fill=True,
        fill_color=couleur,
        popup=popup
    ).add_to(carte)

# 4) Sauvegarder la carte
carte.save("velib_map.html")
print("✅ Carte enregistrée : velib_map.html (ouvre dans ton navigateur)")
webbrowser.open("velib_map.html")
