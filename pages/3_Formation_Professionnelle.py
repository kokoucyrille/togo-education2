"""
pages/3_Formation_Professionnelle.py
======================================
Formation professionnelle : cartographie territoriale de l'offre technique,
catégories et saturation, effectifs et féminisation de l'enseignement
supérieur, public vs privé. Fusionne les anciennes pages Analyse Territoriale,
Formations et une partie d'Enseignement Supérieur.
"""
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_folium import st_folium

from utils.helpers import setup_page, story_box, download_buttons
from components.sidebar import render_sidebar
from components.navbar import render_navbar
from components.metrics import kpi_row
from components.footer import render_footer
from config import REGION_COLORS, PALETTE
from utils.preprocessing import clean_etablissements, clean_repartition_sup
from utils.indicators import compute_cover_df, compute_kpi, compute_saturation_risk
from utils.map_utils import build_map_etablissements

setup_page("Formation professionnelle", "🏫")
df_filtered, filters = render_sidebar(show_filters=True, current="3_Formation_Professionnelle")
render_navbar("Formation professionnelle", "Cartographie · Offre technique · Enseignement supérieur", "🏫")

df_etab = clean_etablissements()
df_repart = clean_repartition_sup()
cover_df = compute_cover_df()
kpi = compute_kpi()

tab1, tab2, tab3 = st.tabs(["Cartographie territoriale", "Offre de formation technique", "Enseignement supérieur"])

# ------------------------------------------------------------------
# Cartographie territoriale
# ------------------------------------------------------------------
with tab1:
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(cover_df.sort_values("nb_etablissements", ascending=False), x="region", y="nb_etablissements",
                     color="region", color_discrete_map=REGION_COLORS, text="nb_etablissements",
                     title="Nombre absolu de formations techniques par région")
        fig.update_layout(showlegend=False, height=380, margin=dict(t=60, b=10))
        st.plotly_chart(fig, width='stretch')
    with c2:
        fig = px.bar(cover_df, x="region", y="etab_pour_100k_hab", color="region", color_discrete_map=REGION_COLORS,
                     text="etab_pour_100k_hab", title="⚠️ Établissements pour 100 000 habitants (RGPH-5, 2022)")
        fig.update_layout(showlegend=False, height=380, margin=dict(t=60, b=10))
        st.plotly_chart(fig, width='stretch')

    best_abs = cover_df.sort_values("nb_etablissements", ascending=False).iloc[0]
    best_rel, worst_rel = cover_df.iloc[0], cover_df.iloc[-1]
    story_box(
        f"Région la mieux dotée en absolu : <b>{best_abs['region']}</b> ({int(best_abs['nb_etablissements'])} "
        f"établissements). Rapportée à la population, la région la mieux dotée est <b>{best_rel['region']}</b> "
        f"et la plus sous-dotée est <b>{worst_rel['region']}</b>.", "info"
    )

    st.markdown("#### Carte interactive des établissements de formation technique")
    m = build_map_etablissements(df_filtered)
    st_folium(m, width='stretch', height=520, key="map_etab")
    st.caption(f"{len(df_filtered)} établissements affichés selon les filtres actifs (sur {len(df_etab)} au total).")

    st.markdown("#### Dynamique de création des établissements")
    creation = df_etab.dropna(subset=["annee_creation"]).copy()
    creation["decennie"] = (creation["annee_creation"] // 10 * 10).astype(int)
    decade_counts = creation.groupby(["decennie", "region_nom_bdd"]).size().reset_index(name="nb")
    fig = px.area(decade_counts, x="decennie", y="nb", color="region_nom_bdd", color_discrete_map=REGION_COLORS,
                  title="Créations d'établissements par décennie et par région")
    fig.update_layout(height=400, margin=dict(t=60, b=10))
    st.plotly_chart(fig, width='stretch')
    pct_recent = (creation["annee_creation"] >= 2010).mean() * 100
    story_box(f"{(creation['annee_creation'] >= 2010).sum()} établissements sur {len(creation)} ont été créés "
              f"depuis 2010 ({pct_recent:.0f}% du parc daté) — signe d'une expansion récente de l'offre.", "success")

# ------------------------------------------------------------------
# Offre de formation technique
# ------------------------------------------------------------------
with tab2:
    kpi_row([
        ("Formations techniques", str(kpi["Nombre de formations techniques recensées"]), "🏫", "#0B3D66"),
        ("Régions couvertes", f"{kpi['Nombre de régions couvertes (formation technique)']}/5", "🗺️", "#17A2B8"),
        ("Préfectures couvertes", str(kpi["Nombre de préfectures couvertes"]), "📍", "#F2994A"),
    ])

    st.markdown("#### Répartition hiérarchique — Togo → Région → Préfecture → Catégorie")
    tm = df_etab.dropna(subset=["etablissement_categorie"]).copy()
    fig = px.treemap(tm, path=[px.Constant("Togo"), "region_nom_bdd", "prefecture_nom_bdd", "etablissement_categorie"],
                      color="region_nom_bdd", color_discrete_map={**REGION_COLORS, "(?)": "#ccc"},
                      title="Répartition hiérarchique de l'offre de formation technique")
    fig.update_layout(height=500, margin=dict(t=60, b=10))
    st.plotly_chart(fig, width='stretch')

    st.markdown("#### ⚠️ Secteurs estimés par région (heuristique par mots-clés)")
    st.caption("⚠️ Le champ *spécialité* n'existe pas dans l'extraction fournie — le secteur est déduit du "
               "nom de l'établissement par détection de mots-clés ; une large part reste « non identifiée ».")
    sector_region = pd.crosstab(df_etab["region_nom_bdd"], df_etab["secteur_estime"])
    fig = px.imshow(sector_region.T, text_auto=True, aspect="auto", color_continuous_scale="YlGnBu",
                     labels=dict(x="Région", y="Secteur estimé ⚠️", color="Nb établissements"),
                     title="⚠️ Secteurs estimés des formations techniques par région")
    fig.update_layout(height=460, margin=dict(t=60, b=10))
    st.plotly_chart(fig, width='stretch')

    st.markdown("#### Formations « saturées » vs « porteuses » ⚠️ (indice de risque proxy)")
    st.warning(
        "⚠️ Aucune donnée ne relie le chômage à une filière, un diplôme ou une région précise. L'indice est un "
        "**proxy structurel** : `poids relatif de la catégorie` × `part des créations récentes depuis 2010`."
    )
    risk = compute_saturation_risk()
    fig = px.bar(risk.reset_index(), x="etablissement_categorie", y="indice_saturation_proxy",
                 color="indice_saturation_proxy", color_continuous_scale="RdYlGn_r",
                 title="⚠️ Indice de saturation proxy par catégorie de formation",
                 labels={"etablissement_categorie": "Catégorie", "indice_saturation_proxy": "Indice (0-100)"})
    fig.update_layout(height=420, margin=dict(t=60, b=10), coloraxis_showscale=False)
    st.plotly_chart(fig, width='stretch')
    download_buttons(risk, "indice_saturation_formations", "risk")
    story_box(
        f"Catégorie la plus exposée au risque de saturation (proxy) : <b>{risk.index[0]}</b>. Catégorie jugée la "
        f"plus porteuse (proxy) : <b>{risk.index[-1]}</b>. À confronter à une véritable enquête d'insertion "
        "professionnelle avant toute décision d'ouverture ou de fermeture de filière.", "warning"
    )

# ------------------------------------------------------------------
# Enseignement supérieur
# ------------------------------------------------------------------
with tab3:
    from utils.preprocessing import build_indicateurs_sup
    ind_wide = build_indicateurs_sup()

    fig = make_subplots(rows=2, cols=2, subplot_titles=(
        "Évolution des effectifs d'étudiants inscrits", "Taux de féminisation des étudiants (%)",
        "Ratio étudiants / enseignants (universités publiques)", "Filières scientifiques et technologiques"))
    s = ind_wide["effectifs_etudiants"].dropna()
    fig.add_trace(go.Scatter(x=s.index, y=s.values, mode="lines+markers", line=dict(color=PALETTE[0], width=3), fill="tozeroy"), row=1, col=1)
    s = ind_wide["taux_feminisation"].dropna()
    fig.add_trace(go.Scatter(x=s.index, y=s.values, mode="lines+markers", line=dict(color=PALETTE[2], width=3)), row=1, col=2)
    fig.add_hline(y=50, line_dash="dash", line_color="gray", row=1, col=2)
    s = ind_wide["ratio_etud_enseignant"].dropna()
    fig.add_trace(go.Bar(x=s.index.astype(str), y=s.values, marker_color=PALETTE[3]), row=2, col=1)
    s1 = ind_wide["pct_filieres_scientifiques"].dropna()
    s2 = ind_wide["pct_filles_filieres_sci"].dropna()
    fig.add_trace(go.Scatter(x=s1.index, y=s1.values, mode="lines+markers", name="% étudiants en filières sci.", line=dict(color=PALETTE[1], width=3)), row=2, col=2)
    fig.add_trace(go.Scatter(x=s2.index, y=s2.values, mode="lines+markers", name="% filles en filières sci.", line=dict(color=PALETTE[4], width=3)), row=2, col=2)
    fig.update_layout(height=700, margin=dict(t=60, b=10), showlegend=True)
    st.plotly_chart(fig, width='stretch')
    story_box(
        "Les effectifs et la féminisation progressent de façon continue, tandis que le ratio étudiants/enseignants "
        "se détend, signe d'un effort d'encadrement. La part des filières scientifiques progresse mais reste "
        "minoritaire, et leur féminisation demeure très inférieure à la féminisation globale.", "info"
    )

    st.markdown("#### Public vs privé (2018)")
    pub_priv = df_repart.groupby(["type", "statut"])["Value"].sum().unstack(fill_value=0)
    st.dataframe(pub_priv, width='stretch')
    fig = make_subplots(rows=1, cols=2, specs=[[{"type": "domain"}, {"type": "xy"}]],
                         subplot_titles=("Répartition Public / Privé", "Établissements par ville, statut et type"))
    totals_statut = df_repart.groupby("statut")["Value"].sum()
    fig.add_trace(go.Pie(labels=totals_statut.index, values=totals_statut.values,
                         marker_colors=[PALETTE[0], PALETTE[2]], hole=0.45, textinfo="label+percent"), row=1, col=1)
    city_type_statut = df_repart.groupby(["villes", "type", "statut"])["Value"].sum().reset_index()
    city_type_statut["label"] = city_type_statut["type"] + " " + city_type_statut["statut"]
    for i, lab in enumerate(city_type_statut["label"].unique()):
        d = city_type_statut[city_type_statut["label"] == lab]
        fig.add_trace(go.Bar(x=d["villes"], y=d["Value"], name=lab, marker_color=px.colors.qualitative.Set2[i % 8]), row=1, col=2)
    fig.update_layout(barmode="stack", height=440, margin=dict(t=60, b=10), title_text="Établissements d'enseignement supérieur ayant fonctionné (2018)")
    st.plotly_chart(fig, width='stretch')
    pct_prive = totals_statut.get("Prive", 0) / totals_statut.sum() * 100
    lome_count = int(city_type_statut[city_type_statut["villes"] == "LOMÉ"]["Value"].sum())
    story_box(f"Sur {int(df_repart['Value'].sum())} structures recensées en 2018, {pct_prive:.0f}% relèvent du "
              f"secteur privé — Lomé concentre à elle seule {lome_count} structures.", "info")

render_footer()
