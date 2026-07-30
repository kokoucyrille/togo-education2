"""
pages/1_Accueil.py
===================
Page de pilotage (executive dashboard) : bandeau, objectifs, KPI principaux,
graphiques clés, resume executif, tendances principales et recommandations
automatiques. Point d'entree unique du tableau de bord (5 sections max).
"""
import streamlit as st
import plotly.express as px

from utils.helpers import setup_page
from components.sidebar import render_sidebar
from components.navbar import render_navbar
from components.cards import objective_grid, recommendation_card
from components.metrics import kpi_row
from components.footer import render_footer
from config import AUTHOR, INSTITUTION, MINISTERE, REGION_COLORS
from utils.preprocessing import build_indicateurs_sup
from utils.indicators import (
    compute_kpi, compute_cover_df, compute_feas, compute_iafe, compute_impact_urgence,
)

setup_page("Accueil", "🏠")
_, filters = render_sidebar(show_filters=False, current="1_Accueil")
render_navbar("Adéquation Formation-Emploi au Togo", "Tableau de bord de pilotage", "🏠", show_logos=True)

# ------------------------------------------------------------------
# Bandeau principal
# ------------------------------------------------------------------
st.markdown(
    """
    <div class="hero-banner">
        <div style="font-size:34px;font-weight:800;">🇹🇬 Adéquation Formation-Emploi au Togo</div>
        <div style="font-size:16px;margin-top:6px;opacity:0.95;">
            Tableau de bord stratégique — Data Challenge Éducation, Défi 2 — 2026
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("")

col_a, col_b = st.columns([2, 1])
with col_a:
    st.markdown("### 🎯 Objectif")
    st.markdown(
        "Évaluer l'**adéquation entre l'offre de formation** et les **besoins du marché de l'emploi** "
        "au Togo, et en tirer des **recommandations stratégiques** pour le Ministère."
    )
with col_b:
    st.markdown("### 📍 Portée : 5 régions")
    st.info("Maritime · Plateaux · Centrale · Kara · Savanes")

# ------------------------------------------------------------------
# KPI principaux
# ------------------------------------------------------------------
st.markdown("### 📈 Indicateurs clés")
kpi = compute_kpi()
ind_wide = build_indicateurs_sup()
femin = ind_wide["taux_feminisation"].dropna()
delta_femin = f"{'▲' if femin.iloc[-1] >= femin.iloc[0] else '▼'} depuis {femin.index[0]}"

kpi_row([
    ("Formations techniques", str(kpi["Nombre de formations techniques recensées"]), "🏫", "#0B3D66"),
    ("Régions couvertes", f"{kpi['Nombre de régions couvertes (formation technique)']}/5", "🗺️", "#17A2B8"),
    ("Préfectures couvertes", str(kpi["Nombre de préfectures couvertes"]), "📍", "#F2994A"),
    ("Universités (2018)", str(kpi["Nombre d'universités recensées (2018)"]), "🎓", "#D64545"),
])
st.write("")
kpi_row([
    ("Féminisation étudiants", f"{kpi['Taux de féminisation le plus récent (%)']}%", "👩‍🎓", "#0B3D66", delta_femin),
    ("Ratio étud./enseignant", f"{kpi['Ratio étudiants/enseignants le plus récent']}:1", "👩‍🏫", "#17A2B8"),
    ("Filières scientifiques", f"{kpi['Part des filières scientifiques la plus récente (%)']}%", "🔬", "#F2994A"),
    ("Chômage diplômés", kpi["Chômage diplômés le plus récent connu (%, année)"], "📉", "#D64545"),
])

# ------------------------------------------------------------------
# Graphiques clés
# ------------------------------------------------------------------
st.markdown("### 📊 Tendances principales")
c1, c2 = st.columns(2)
cover_df = compute_cover_df()
with c1:
    fig = px.bar(cover_df.sort_values("nb_etablissements", ascending=False), x="region", y="nb_etablissements",
                 color="region", color_discrete_map=REGION_COLORS, text="nb_etablissements",
                 title="Formations techniques par région")
    fig.update_layout(showlegend=False, height=340, margin=dict(t=50, b=10))
    st.plotly_chart(fig, width='stretch')
with c2:
    feas = compute_feas().sort_values("FEAS", ascending=False)
    fig = px.bar(feas.reset_index(), x="region", y="FEAS", color="FEAS", color_continuous_scale="RdYlGn",
                 range_color=[0, 100], text=feas["FEAS"].round(1), title="Score FEAS par région (0-100)")
    fig.update_layout(showlegend=False, height=340, margin=dict(t=50, b=10), coloraxis_showscale=False)
    st.plotly_chart(fig, width='stretch')

# ------------------------------------------------------------------
# Résumé exécutif
# ------------------------------------------------------------------
st.markdown("### 🧭 Résumé exécutif")
iafe_data = compute_iafe()
impact_urgence = compute_impact_urgence()
nb_p1 = int((impact_urgence["Priorité"] == "Priorité 1").sum())
region_p1 = (impact_urgence[impact_urgence["Priorité"] == "Priorité 1"]["Impact"].idxmax()
             if nb_p1 else impact_urgence["Impact"].idxmax())
synthese = (
    f"**IAFE national : {iafe_data['iafe_national']:.1f}/100.** La région **{region_p1}** concentre le déficit "
    f"le plus critique ({nb_p1} région(s) en Priorité 1 sur 5) ; chômage des diplômés du supérieur : "
    f"{iafe_data['chomage_val']:.1f}% ({iafe_data['chomage_year']}). Le problème est moins un manque de "
    "**volume** qu'un déséquilibre de **composition** de l'offre de formation."
)
st.markdown(
    f'<div style="padding:18px 22px;background:linear-gradient(135deg,#0B3D66,#17A2B8);color:white;'
    f'border-radius:12px;font-size:15px;line-height:1.6;">{synthese}</div>',
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# Recommandations automatiques (aperçu)
# ------------------------------------------------------------------
st.markdown("### 💡 Recommandations prioritaires")
st.caption("Détail complet dans **Analyses & Recommandations**.")
region_faible = cover_df.sort_values("etab_pour_100k_hab").iloc[0]
recommendation_card(1, f"Rééquilibrer l'offre territoriale : **{region_faible['region']}** est la région la moins "
                       f"couverte ({region_faible['etab_pour_100k_hab']:.1f} établ./100k hab.).")
recommendation_card(2, f"Prioriser les régions classées **Priorité 1** ({nb_p1}/5), selon la matrice Impact × Urgence.")
recommendation_card(3, "Renforcer les filières scientifiques et technologiques, et leur féminisation.")

st.markdown("### 🧩 Explorer le tableau de bord")
objective_grid([
    ("📉", "Marché de l'emploi", "Chômage des diplômés, budgets de l'enseignement supérieur et matrice Offre/Demande par région."),
    ("🏫", "Formation professionnelle", "Cartographie, offre de formation technique, enseignement supérieur et théorie des graphes."),
    ("🧮", "Analyses & Recommandations", "Indice IAFE, Machine Learning, clustering régional, priorisation et Policy Dashboard."),
])

render_footer()
