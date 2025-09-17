import requests
import pandas as pd
import folium
from folium import FeatureGroup, Element
from folium.plugins import (
    MarkerCluster, HeatMap, MiniMap, Fullscreen,
    MeasureControl, LocateControl, Search
)
import webbrowser

# ========= 1) Récupération en temps réel =========
url = "https://opendata.paris.fr/api/records/1.0/search/"
params = {
    "dataset": "velib-disponibilite-en-temps-reel",
    "rows": 170  # assez pour tout Paris
}
response = requests.get(url, params=params)
data = response.json()

# Extraire les champs utiles
records = [r["fields"] for r in data.get("records", []) if "fields" in r]
df = pd.DataFrame(records)

# Nettoyer les coordonnées
def parse_coords(coords):
    if isinstance(coords, list) and len(coords) == 2:
        return coords[0], coords[1]  # lat, lon
    return None, None

df["lat"], df["lon"] = zip(*df["coordonnees_geo"].apply(parse_coords))
df = df.dropna(subset=["lat", "lon"])  # supprimer stations sans coord

# ========= 2) Créer la carte =========
m = folium.Map(location=[48.8566, 2.3522], zoom_start=12,
               tiles="cartodbpositron", control_scale=True)

# Plugins pratiques
Fullscreen().add_to(m)
MiniMap(toggle_display=True).add_to(m)
MeasureControl(primary_length_unit="meters").add_to(m)
LocateControl().add_to(m)

# ========= 3) Fonctions utiles =========
def color_for(bikes: int) -> str:
    if bikes == 0:
        return "red"
    elif bikes < 5:
        return "orange"
    return "green"

# ========= 4) Calque Stations (clusters) =========
fg_stations = FeatureGroup(name="Stations Vélib", show=True)
cluster = MarkerCluster().add_to(fg_stations)

for _, r in df.iterrows():
    bikes = int(r.get("numbikesavailable", 0))
    docks = int(r.get("numdocksavailable", 0))
    name  = r.get("name", "Inconnu")
    arrdt = r.get("nom_arrondissement_communes", "Inconnu")

    popup_html = f"""
    <div style="font-size:14px;line-height:1.4">
      <b>{name}</b><br/>
      Arrondissement: {arrdt}<br/>
      🚲 Vélos dispo: <b>{bikes}</b><br/>
      🅿️ Places libres: <b>{docks}</b>
    </div>
    """
    folium.CircleMarker(
        location=[r["lat"], r["lon"]],
        radius=6,
        color=color_for(bikes),
        fill=True,
        fill_color=color_for(bikes),
        fill_opacity=0.95,
        popup=folium.Popup(popup_html, max_width=260),
    ).add_to(cluster)

fg_stations.add_to(m)

# ========= 5) Calque Heatmap =========
fg_heat = FeatureGroup(name="Heatmap vélos", show=False)
heat_pts = df[["lat", "lon", "numbikesavailable"]].dropna().values.tolist()
HeatMap(heat_pts, radius=12, blur=18, max_zoom=15).add_to(fg_heat)
fg_heat.add_to(m)

# ========= 6) Recherche (GeoJson) =========
features = []
for _, r in df.iterrows():
    features.append({
        "type": "Feature",
        "properties": {
            "name": r.get("name", "Inconnu"),
            "arrdt": r.get("nom_arrondissement_communes", "Inconnu"),
            "bikes": int(r.get("numbikesavailable", 0)),
            "docks": int(r.get("numdocksavailable", 0)),
        },
        "geometry": {"type": "Point", "coordinates": [float(r["lon"]), float(r["lat"])]}
    })

geojson = folium.GeoJson(
    {"type": "FeatureCollection", "features": features},
    name="Recherche (GeoJson)",
    show=False,
    tooltip=folium.GeoJsonTooltip(
        fields=["name", "arrdt", "bikes", "docks"],
        aliases=["Station", "Arrdt", "Vélos", "Places"]
    )
).add_to(m)

Search(
    layer=geojson,
    search_label="name",
    placeholder="🔎 Rechercher une station…",
    collapsed=False,
).add_to(m)

# ========= 7) Légende + Aide =========
legend_html = """
<style>
#legend-box {
  position: fixed; bottom: 18px; left: 18px; z-index: 9999;
  background: #fff; padding: 10px 12px; border: 1px solid #bbb; border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,.2); font-size: 14px; max-width: 240px;
}
.legend-dot {display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;}
.legend-green  {background:#28a745;}
.legend-orange {background:#fd7e14;}
.legend-red    {background:#dc3545;}
#help-box {
  position: fixed; top: 12px; right: 12px; z-index: 9999;
  background: #fff; padding: 10px 12px; border: 1px solid #bbb; border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,.2); font-size: 14px; max-width: 320px;
}
#help-title {font-weight:600; margin:0 0 6px 0; display:flex; align-items:center; gap:8px;}
#help-content {display:none; margin-top:6px; color:#333;}
.help-btn {cursor:pointer; text-decoration:underline; color:#007bff;}
</style>
<div id="help-box">
  <div id="help-title">
    <span>ℹ️ Aide</span>
    <span class="help-btn" onclick="toggleHelp()">afficher / masquer</span>
  </div>
  <div id="help-content">
    <div>• <b>Recherche</b> : saisissez le nom d’une station.</div>
    <div>• <b>Calques</b> : cochez <i>Stations</i> ou <i>Heatmap</i>.</div>
    <div>• <b>Plein écran</b> : bouton en haut à gauche.</div>
    <div>• <b>Mesure</b> : règle pour mesurer des distances.</div>
    <div>• <b>Localiser</b> : recentre sur votre position.</div>
  </div>
</div>
<div id="legend-box">
  <div style="font-weight:600;margin-bottom:6px;">Légende</div>
  <div><span class="legend-dot legend-green"></span>≥ 5 vélos</div>
  <div><span class="legend-dot legend-orange"></span>1–4 vélos</div>
  <div><span class="legend-dot legend-red"></span>0 vélo</div>
</div>
<script>
function toggleHelp(){
  var c = document.getElementById('help-content');
  c.style.display = (c.style.display === 'none' || c.style.display === '') ? 'block' : 'none';
}
</script>
"""
m.get_root().html.add_child(Element(legend_html))

# ========= 8) Export + ouverture =========
out_file = "velib_live.html"
m.save(out_file)
print(f"✅ Carte live enregistrée : {out_file}")
webbrowser.open(out_file)
