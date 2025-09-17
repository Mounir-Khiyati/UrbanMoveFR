import pandas as pd
import folium
from folium import FeatureGroup, Element
from folium.plugins import MarkerCluster, HeatMap, MiniMap, Fullscreen, MeasureControl, LocateControl, Search
import webbrowser

# ========= 1) Charger les données (CSV filtré) =========
df = pd.read_csv("velib_filtre.csv")

# Parse coordonnées "[lat, lon]" -> (lat, lon)
def parse_coords(s):
    s = str(s).strip().replace("[", "").replace("]", "")
    lat_str, lon_str = [x.strip() for x in s.split(",")]
    return float(lat_str), float(lon_str)

df = df.dropna(subset=["coordonnees_geo"]).copy()
df[["lat", "lon"]] = df["coordonnees_geo"].apply(lambda x: pd.Series(parse_coords(x)))

# ========= 2) Carte de base + plugins =========
m = folium.Map(location=[48.8566, 2.3522], zoom_start=12, tiles="cartodbpositron", control_scale=True)
Fullscreen().add_to(m)
MiniMap(toggle_display=True).add_to(m)
MeasureControl(primary_length_unit="meters").add_to(m)
LocateControl().add_to(m)

# ========= 3) Couleur selon nb vélos =========
def color_for(bikes: int) -> str:
    if bikes == 0:
        return "red"
    elif bikes < 5:
        return "orange"
    return "green"

# ========= 4) CLUSTERS de stations =========
fg_stations = FeatureGroup(name="Stations (clusters)", show=True)
cluster = MarkerCluster().add_to(fg_stations)

for _, r in df.iterrows():
    bikes = int(r.get("numbikesavailable", 0))
    docks = int(r.get("numdocksavailable", 0))
    name  = r.get("name", "Inconnu")
    arrdt = r.get("nom_arrondissement_communes", "Inconnu")
    lat, lon = r["lat"], r["lon"]

    popup_html = f"""
    <div style="font-size:14px;line-height:1.4">
      <b>{name}</b><br/>
      Arrondissement: {arrdt}<br/>
      🚲 Vélos dispo: <b>{bikes}</b><br/>
      🅿️ Places libres: <b>{docks}</b>
    </div>
    """
    folium.CircleMarker(
        location=[lat, lon],
        radius=6,
        color=color_for(bikes),
        fill=True,
        fill_color=color_for(bikes),
        fill_opacity=0.95,
        popup=folium.Popup(popup_html, max_width=260),
        # 👉 astuce: on stocke le nom pour la recherche (via GeoJson plus bas)
    ).add_to(cluster)

fg_stations.add_to(m)

# ========= 5) HEATMAP (intensité vélos) =========
fg_heat = FeatureGroup(name="Heatmap vélos", show=False)
heat_pts = df[["lat", "lon", "numbikesavailable"]].dropna().values.tolist()
HeatMap(heat_pts, radius=12, blur=18, max_zoom=15).add_to(fg_heat)
fg_heat.add_to(m)

# ========= 6) LAYER contrôle =========
folium.LayerControl(collapsed=False).add_to(m)

# ========= 7) RECHERCHE (par nom de station) =========
# Pour la recherche, on crée une couche GeoJson avec une propriété "name".
import json
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
        "geometry": {
            "type": "Point",
            "coordinates": [float(r["lon"]), float(r["lat"])]
        }
    })

geojson = folium.GeoJson(
    {"type": "FeatureCollection", "features": features},
    name="Recherche (GeoJson caché)",
    show=False,  # on n'affiche pas cette couche, on l'utilise pour Search
    tooltip=folium.GeoJsonTooltip(fields=["name", "arrdt", "bikes", "docks"],
                                  aliases=["Station", "Arrdt", "Vélos", "Places"])
).add_to(m)

Search(
    layer=geojson,
    search_label="name",
    placeholder="🔎 Rechercher une station…",
    collapsed=False,
).add_to(m)

# ========= 8) LÉGENDE + PANNEAU D’AIDE (CSS/HTML) =========
custom_css_html = """
<style>
/* Panneau flottant en bas à gauche (légende) */
#legend-box {
  position: fixed; bottom: 18px; left: 18px; z-index: 9999;
  background: #fff; padding: 10px 12px; border: 1px solid #bbb; border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,.2); font-size: 14px; max-width: 240px;
}
.legend-dot {display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;}
.legend-green  {background:#28a745;}
.legend-orange {background:#fd7e14;}
.legend-red    {background:#dc3545;}

/* Panneau d'aide (toggle) en haut à droite */
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
    <div>• <b>Localiser</b> : recentre sur votre position (si autorisé).</div>
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
m.get_root().html.add_child(Element(custom_css_html))

# ========= 9) Sauvegarde + ouverture =========
out_file = "velib_map.html"  # garde le même nom si tu veux remplacer l’ancienne
m.save(out_file)
print(f"✅ Carte enregistrée : {out_file}")
webbrowser.open(out_file)
