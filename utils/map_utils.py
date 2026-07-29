"""
utils/map_utils.py
===================
Cartes Folium du tableau de bord : localisation des établissements de formation
technique (§4.2) et carte nationale des priorités d'investissement (§21).
"""
import folium
from folium.plugins import MarkerCluster
import pandas as pd

from config import REGION_COLORS


def build_map_etablissements(df_etab: pd.DataFrame) -> folium.Map:
    """Carte des établissements de formation technique, colorés par région,
    avec regroupement par préfecture pour la lisibilité."""
    geo = df_etab.dropna(subset=["lat", "lon"]).copy()
    m = folium.Map(location=[8.6, 1.0], zoom_start=7, tiles="cartodbpositron")
    clusters = {r: MarkerCluster(name=r).add_to(m) for r in geo["region_nom_bdd"].unique()}

    for _, row in geo.iterrows():
        color = REGION_COLORS.get(row["region_nom_bdd"], "#495057")
        popup_html = (
            f"<b>{row['etab_nom']}</b><br>"
            f"Région : {row['region_nom_bdd']}<br>"
            f"Préfecture : {row['prefecture_nom_bdd']}<br>"
            f"Catégorie : {row.get('etablissement_categorie', 'n/d')}<br>"
            f"Secteur estimé ⚠️ : {row.get('secteur_estime', 'n/d')}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]], radius=5, color=color, weight=1,
            fill=True, fill_color=color, fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=280),
        ).add_to(clusters[row["region_nom_bdd"]])

    folium.LayerControl(collapsed=False).add_to(m)
    return m


def build_map_priorities(df_etab: pd.DataFrame, impact_urgence: pd.DataFrame) -> folium.Map:
    """Carte nationale des priorités d'investissement (§21) : chaque établissement est
    colorié selon le niveau de priorité de sa région (Priorité 1/2/3, cf. §20)."""
    geo_p = df_etab.dropna(subset=["lat", "lon"]).copy()
    geo_p["Priorité"] = geo_p["region_nom_bdd"].map(impact_urgence["Priorité"])
    geo_p["Couleur"] = geo_p["region_nom_bdd"].map(impact_urgence["Couleur"])

    m = folium.Map(location=[8.6, 1.0], zoom_start=7, tiles="cartodbpositron")
    priority_layers = {
        p: MarkerCluster(name=f"{p} ({(geo_p['Priorité'] == p).sum()} étab.)").add_to(m)
        for p in ["Priorité 1", "Priorité 2", "Priorité 3"]
    }

    for _, row in geo_p.iterrows():
        popup_html = (
            f"<b>{row['etab_nom']}</b><br>"
            f"Région : {row['region_nom_bdd']}<br>"
            f"Préfecture : {row['prefecture_nom_bdd']}<br>"
            f"Catégorie : {row.get('etablissement_categorie', 'n/d')}<br>"
            f"<b>Priorité régionale : {row['Priorité']}</b>"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]], radius=5, color=row["Couleur"], weight=1,
            fill=True, fill_color=row["Couleur"], fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=280),
        ).add_to(priority_layers[row["Priorité"]])

    legend_html = """
    <div style="position: fixed; bottom: 30px; left: 30px; z-index: 9999; background: white;
         padding: 10px 14px; border-radius: 6px; box-shadow: 0 1px 6px rgba(0,0,0,0.3); font-size: 13px;">
    <b>Priorité d'investissement (§20)</b><br>
    <span style="color:#D62839">●</span> Priorité 1 — agir en premier<br>
    <span style="color:#F2C744">●</span> Priorité 2 — à surveiller<br>
    <span style="color:#1B6B45">●</span> Priorité 3 — situation plus favorable
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    folium.LayerControl(collapsed=False).add_to(m)
    return m
