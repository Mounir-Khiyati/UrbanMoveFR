import pandas as pd
import folium
from folium import FeatureGroup, Element, IFrame
from folium.plugins import (
    MarkerCluster, HeatMap, MiniMap, Fullscreen,
    MeasureControl, LocateControl, Search
)
import webbrowser

# ---------- 1) Charger les anomalies ----------
df = pd.read_csv("anomalies_velib.csv", parse_dates=["ts_hour"])
last_ts = df["ts_hour"].max()
df_last = df[df["ts_hour"] == last_ts].copy()
if df_last.empty:
    raise ValueError("Aucune donnée pour la dernière heure. Lance la collecte/agrégation/détection avant.")

# Petites stats pour la sidebar
n_total = len(df_last)
n_anom = int(df_last["is_anomaly"].sum())
pct_anom = 0 if n_total == 0 else round(100 * n_anom / n_total, 1)
top = (df_last[df_last["is_anomaly"]]
       .sort_values("anomaly_score", ascending=False)
       .head(10)[["stationcode","name","arrdt","lat","lon","anomaly_score"]])

# ---------- 2) Carte + fonds ----------
m = folium.Map(location=[48.8566, 2.3522], zoom_start=12, control_scale=True, tiles=None)
folium.TileLayer("CartoDB positron", name="Clair", control=True).add_to(m)
folium.TileLayer("CartoDB dark_matter", name="Sombre", control=True).add_to(m)
folium.TileLayer("OpenStreetMap", name="OSM", control=True).add_to(m)

# Plugins confort
Fullscreen().add_to(m)
MiniMap(toggle_display=True).add_to(m)
MeasureControl(primary_length_unit="meters").add_to(m)
LocateControl().add_to(m)

# ---------- 3) Calques ----------
fg_all  = FeatureGroup(name="Toutes les stations", show=True)
fg_anom = FeatureGroup(name="Anomalies (rouge)", show=True)
fg_norm = FeatureGroup(name="Normales (vert)", show=False)
fg_heat = FeatureGroup(name="Heatmap anomalies", show=False)

cluster_all  = MarkerCluster(name="Cluster (toutes)").add_to(fg_all)
cluster_anom = MarkerCluster(name="Cluster (anomalies)").add_to(fg_anom)
cluster_norm = MarkerCluster(name="Cluster (normales)").add_to(fg_norm)

def icon_html(color, emoji):
    return f"""
    <div style="
      background:{color}; color:white; border-radius:14px; text-align:center;
      width:28px; height:28px; line-height:28px; font-size:16px;
      box-shadow:0 0 6px rgba(0,0,0,.25);">{emoji}</div>"""

def popup_for(row):
    html = f"""
    <div style="font-size:14px;line-height:1.4;">
      <b>{row['name']}</b><br/>
      Arrdt : {row['arrdt']}<br/>
      Médiane vélos : <b>{row['bikes_median']}</b><br/>
      Moyenne docks : <b>{row['docks_mean']}</b><br/>
      Score anomalie : {round(float(row.get('anomaly_score', 0) or 0), 2)}<br/>
      Anomalie : <b>{bool(row['is_anomaly'])}</b>
    </div>
    """
    return folium.Popup(IFrame(html=html, width=260, height=140), max_width=280)

# ---------- 4) Marqueurs + Heatmap ----------
heat_points = []
# On mémorise aussi des "anchors" pour la sidebar (pan/zoom)
anchors_js = []  # [{name, arrdt, lat, lon, score}]

for _, r in df_last.iterrows():
    lat, lon = float(r["lat"]), float(r["lon"])
    is_anom = bool(r["is_anomaly"])
    score = float(r.get("anomaly_score", 0) or 0)

    # Marqueurs spécifiques
    if is_anom:
        folium.Marker(
            [lat, lon],
            icon=folium.DivIcon(html=icon_html("#dc3545", "⚠")),
            popup=popup_for(r),
        ).add_to(cluster_anom)
        heat_points.append([lat, lon, max(score, 1.0)])
    else:
        folium.Marker(
            [lat, lon],
            icon=folium.DivIcon(html=icon_html("#28a745", "✓")),
            popup=popup_for(r),
        ).add_to(cluster_norm)

    # Calque "toutes"
    folium.CircleMarker(
        [lat, lon],
        radius=6,
        color="#dc3545" if is_anom else "#28a745",
        fill=True, fill_color="#dc3545" if is_anom else "#28a745",
        fill_opacity=0.9, popup=popup_for(r),
    ).add_to(cluster_all)

# Heatmap des anomalies
if heat_points:
    HeatMap(heat_points, radius=14, blur=20, max_zoom=15).add_to(fg_heat)

# Calques → carte
fg_all.add_to(m); fg_anom.add_to(m); fg_norm.add_to(m); fg_heat.add_to(m)

# ---------- 5) Recherche par nom (sur toutes) ----------
# Construire un GeoJson minimal pour activer Search
features = [{
    "type": "Feature",
    "properties": {"name": row["name"]},
    "geometry": {"type": "Point", "coordinates": [float(row["lon"]), float(row["lat"])]}
} for _, row in df_last.iterrows()]

geojson = folium.GeoJson(
    {"type":"FeatureCollection","features":features},
    name="Recherche",
    show=False
).add_to(m)

Search(layer=geojson, search_label="name", placeholder="🔎 Rechercher une station…", collapsed=False).add_to(m)

# ---------- 6) Sidebar (KPIs + Top anomalies cliquables) ----------
# Préparer anchors pour JS
for _, r in top.iterrows():
    anchors_js.append({
        "name": str(r["name"]),
        "arrdt": str(r["arrdt"]),
        "lat": float(r["lat"]),
        "lon": float(r["lon"]),
        "score": round(float(r["anomaly_score"]), 2),
    })

sidebar_html = f"""
<style>
#sidebar {{
  position: fixed; top: 12px; right: 12px; z-index: 9999;
  width: 320px; max-height: 80vh; overflow:auto;
  background: #ffffff; border: 1px solid #bbb; border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0,0,0,.15);
  font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial; 
}}
#sidebar .hdr {{
  padding: 10px 12px; border-bottom: 1px solid #eee; display:flex; align-items:center; justify-content:space-between;
}}
#sidebar .title {{ font-weight: 700; }}
#sidebar .body {{ padding: 10px 12px; }}
.kpi {{ display:flex; gap:10px; margin-bottom:8px; }}
.kpi .card {{
  background:#f8f9fa; border:1px solid #eee; border-radius:8px; padding:8px 10px; flex:1; text-align:center;
}}
.kpi .card .big {{ font-size:18px; font-weight:700; }}
.list li {{ margin:6px 0; }}
.list a {{ cursor:pointer; color:#0d6efd; text-decoration:none; }}
.list a:hover {{ text-decoration:underline; }}
.badge-red {{
  display:inline-block; background:#dc3545; color:#fff; border-radius:8px; padding:2px 6px; font-size:12px; margin-left:6px;
}}
</style>

<div id="sidebar">
  <div class="hdr">
    <div class="title">Anomalies Vélib — {last_ts}</div>
    <div><small>Paris</small></div>
  </div>
  <div class="body">
    <div class="kpi">
      <div class="card"><div>Total</div><div class="big">{n_total}</div></div>
      <div class="card"><div>Anomalies</div><div class="big">{n_anom}</div></div>
      <div class="card"><div>%</div><div class="big">{pct_anom}%</div></div>
    </div>

    <div style="margin:10px 0 6px 0; font-weight:700;">Top anomalies</div>
    <ol class="list">
      {"".join([f'<li><a onclick="panTo({row.lat},{row.lon})">{row.name}</a>'
                f'<span class="badge-red">{round(row.anomaly_score,2)}</span><br>'
                f'<small>{row.arrdt}</small></li>' for _, row in top.iterrows()]) or "<li><small>Aucune anomalie détectée.</small></li>"}
    </ol>
    <div style="margin-top:10px; font-size:12px; color:#555;">
      Astuce : utilisez le contrôle des calques (coin haut‑droit) pour afficher
      seulement les anomalies, les normales, ou la heatmap.
    </div>
  </div>
</div>

<script>
function panTo(lat, lon){{
  var mapObj = {m.get_name()};
  mapObj.setView([lat, lon], 16);
}}
</script>
"""
m.get_root().html.add_child(Element(sidebar_html))

# ---------- 7) Légende compacte ----------
legend_html = """
<div style="
position: fixed; bottom: 18px; left: 18px; z-index: 9999;
background: #fff; padding: 10px 12px; border: 1px solid #bbb; border-radius: 8px;
box-shadow: 0 1px 4px rgba(0,0,0,.2); font-size: 14px;">
<b>Légende</b><br>
<span style="display:inline-block;width:10px;height:10px;background:#dc3545;border-radius:50%;margin-right:6px;"></span> Anomalie<br>
<span style="display:inline-block;width:10px;height:10px;background:#28a745;border-radius:50%;margin-right:6px;"></span> Normal
</div>
"""
m.get_root().html.add_child(Element(legend_html))

# ---------- 8) Contrôles ----------
folium.LayerControl(collapsed=False).add_to(m)

# ---------- 9) Export + ouverture ----------
out = "map_anomalies_ultra.html"
m.save(out)
webbrowser.open(out)
print(f"✅ Carte avancée écrite : {out}")
