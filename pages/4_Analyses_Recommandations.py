"""
pages/4_Analyses_Recommandations.py
=====================================
Cœur analytique du tableau de bord : théorie des graphes, Indice d'Adéquation
Formation-Emploi (IAFE — FEAS, CRITIC, classement, priorisation, scénarios),
Machine Learning exploratoire & clustering régional, puis recommandations
stratégiques et Policy Dashboard. Fusionne les anciennes pages Analyse
Territoriale (théorie des graphes), Enseignement Supérieur (ML/clustering),
Indice Formation-Emploi et Recommandations.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import spearmanr

from utils.helpers import chart_insights, download_buttons, fmt_fr, png_download_button, setup_page, story_box
from components.sidebar import render_sidebar
from components.navbar import render_navbar
from components.cards import recommendation_card, decision_card
from components.metrics import kpi_row
from components.footer import render_footer
from config import REGIONS, REGION_COLORS, PALETTE, IAFE_WEIGHTS
from utils.preprocessing import build_indicateurs_sup, build_budget_wide, clean_etablissements
from utils.indicators import (
    compute_feas, compute_complementary_scores, compute_iafe, compute_iafe_etablissement,
    critic_weights, compute_impact_urgence, compute_scenarios, compute_region_features,
    compute_ml_comparison, compute_clustering, compute_cover_df, compute_saturation_risk,
)
from utils.charts import radar_chart, gauge_chart
from utils.graph_utils import build_global_pyvis_html
from utils.map_utils import build_map_priorities
from streamlit_folium import st_folium

setup_page("Analyses & Recommandations", "🧮")
df_filtered, filters = render_sidebar(show_filters=True, current="4_Analyses_Recommandations")
render_navbar("Analyses & Recommandations", "Graphes · Indice IAFE · Machine Learning · Policy Dashboard", "🧮")

tabs = st.tabs(["Théorie des graphes", "Indice IAFE", "Machine Learning & Clustering", "Recommandations", "Policy Dashboard"])

# ------------------------------------------------------------------
# Théorie des graphes
# ------------------------------------------------------------------
with tabs[0]:
    st.info("Valeur ajoutée distinctive de ce tableau de bord : au-delà des statistiques descriptives, la "
            "théorie des graphes révèle la structure relationnelle du système éducatif togolais.")
    with st.expander("🌐 Graphe global multi-niveaux interactif (Région → Préfecture → Établissement → Catégorie → Secteur)"):
        st.caption("Zoomez, faites glisser les nœuds, survolez un point jaune pour voir le nom de l'établissement.")
        with st.spinner("Construction du graphe global (256 établissements)..."):
            html = build_global_pyvis_html()
        st.iframe(html, height=650)

    st.markdown("#### Carte nationale des priorités d'investissement")
    impact_urgence = compute_impact_urgence()
    m2 = build_map_priorities(df_filtered, impact_urgence)
    st_folium(m2, width='stretch', height=480, key="map_priorities")

# ------------------------------------------------------------------
# Indice IAFE
# ------------------------------------------------------------------
with tabs[1]:
    feas = compute_feas(df_filtered)
    feas_sorted = feas.sort_values("FEAS", ascending=False)
    st.markdown("#### Formation-Employment Alignment Score (FEAS) — 0 à 100")
    fig = px.bar(feas_sorted.reset_index(), x="region", y="FEAS", color="FEAS", color_continuous_scale="RdYlGn",
                 range_color=[0, 100], text=feas_sorted["FEAS"].round(1), title="FEAS par région — 0 à 100")
    fig.update_traces(textposition="outside")
    fig.update_layout(height=380, margin=dict(t=60, b=10), coloraxis_showscale=False)
    st.plotly_chart(fig, width='stretch')

    st.markdown("#### Formule de l'IAFE, indice de référence")
    st.latex(r"""\text{IAFE} = 40\%\times\text{Offre} + 25\%\times\text{Budget/étudiant} + 20\%\times\text{Insertion} + 15\%\times\text{Chômage (inversé)}""")
    iafe_data = compute_iafe(df_filtered)
    iafe = iafe_data["iafe"]
    iafe_sorted = iafe.sort_values("IAFE", ascending=False)
    st.dataframe(iafe_sorted.style.background_gradient(subset=["IAFE"], cmap="RdYlGn").format(precision=1), width='stretch')
    st.caption(f"Budget/étudiant {iafe_data['budget_year']} = {fmt_fr(iafe_data['budget_val'])} FCFA → score "
               f"{iafe_data['budget_score']:.1f}/100. Chômage {iafe_data['chomage_year']} = {iafe_data['chomage_val']:.1f}% "
               f"→ score {iafe_data['chomage_score']:.1f}/100.")

    fig = go.Figure()
    for col in IAFE_WEIGHTS:
        fig.add_trace(go.Bar(x=iafe_sorted.index, y=iafe_sorted[col] * IAFE_WEIGHTS[col], name=col))
    fig.update_layout(barmode="stack", title="IAFE par région — décomposition par pilier", yaxis_title="Score IAFE (0-100)",
                       height=440, margin=dict(t=60, b=10), legend=dict(orientation="h", y=-0.15))
    st.plotly_chart(fig, width='stretch')
    png_download_button(fig, "iafe_piliers", "iafe_piliers")
    story_box("La Maritime concentre l'essentiel de l'offre nationale et obtient le meilleur score d'Offre — "
              "mais affiche le score d'Insertion (proxy) le plus faible du pays. Le Togo n'a donc pas seulement "
              "un problème de <b>volume</b> d'offre, mais aussi de <b>composition</b> de cette offre.", "warning")

    st.plotly_chart(gauge_chart(iafe_data["iafe_national"], "IAFE national (pondéré par la population régionale)"), width='stretch')

    with st.expander("📐 Justification statistique des poids (méthode CRITIC) et test de robustesse"):
        st.caption("CRITIC (Diakoulaki, Mavrotas & Papayannakis, 1995) pondère chaque critère selon sa "
                   "variabilité et son originalité par rapport aux autres critères.")
        w_critic = critic_weights(iafe[list(IAFE_WEIGHTS)])
        w_expert = pd.Series(IAFE_WEIGHTS)
        w_equal = pd.Series(0.25, index=list(IAFE_WEIGHTS))
        comparaison_poids = pd.DataFrame({"Experts (cahier des charges)": w_expert, "CRITIC (statistique)": w_critic, "Égalitaire (référence)": w_equal})
        st.dataframe(comparaison_poids.style.format("{:.1%}").background_gradient(cmap="Blues", axis=1), width='stretch')
        iafe_critic = (iafe[list(IAFE_WEIGHTS)] * w_critic).sum(axis=1).round(1)
        rho, _ = spearmanr(iafe["IAFE"].rank(ascending=False), iafe_critic.rank(ascending=False))
        st.caption(f"Corrélation de rang (Spearman) experts vs CRITIC : {rho:.2f} — accord {'fort' if rho > 0.7 else 'faible à modéré'}.")
        st.info(">>> Décision retenue : les poids du cahier des charges (40/25/20/15) sont conservés comme IAFE "
                "officiel — la tension avec CRITIC est un résultat à porter à la connaissance des décideurs, pas un bug.")

    st.markdown("#### Classement national — régions et établissements")
    classement_regions = iafe[["IAFE"]].copy()
    classement_regions["Rang IAFE"] = classement_regions["IAFE"].rank(ascending=False).astype(int)
    classement_regions["FEAS"] = feas["FEAS"]
    classement_regions = classement_regions.sort_values("IAFE", ascending=False)
    fig = go.Figure(go.Bar(y=classement_regions.index, x=classement_regions["IAFE"], orientation="h",
                            marker=dict(color=classement_regions["IAFE"], colorscale="RdYlGn", cmin=0, cmax=100),
                            text=[f"#{r}  {v:.1f}" for r, v in zip(classement_regions["Rang IAFE"], classement_regions["IAFE"])],
                            textposition="outside"))
    fig.update_layout(title="Classement national des régions — IAFE", xaxis_title="Score IAFE (0-100)",
                       xaxis_range=[0, 115], height=380, margin=dict(t=60, b=10), yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, width='stretch')

    etab_iafe = compute_iafe_etablissement(df_filtered)
    cols_show = ["etab_nom", "region_nom_bdd", "etablissement_categorie", "IAFE_etablissement"]
    rename_show = {"etab_nom": "Établissement", "region_nom_bdd": "Région", "etablissement_categorie": "Catégorie", "IAFE_etablissement": "IAFE"}
    top10 = etab_iafe.dropna(subset=["IAFE_etablissement"]).sort_values("IAFE_etablissement", ascending=False).head(10)[cols_show].rename(columns=rename_show)
    bottom10 = etab_iafe.dropna(subset=["IAFE_etablissement"]).sort_values("IAFE_etablissement", ascending=True).head(10)[cols_show].rename(columns=rename_show)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**TOP 10 établissements**")
        st.dataframe(top10.style.background_gradient(subset=["IAFE"], cmap="RdYlGn"), width='stretch', hide_index=True)
    with c2:
        st.markdown("**BOTTOM 10 établissements**")
        st.dataframe(bottom10.style.background_gradient(subset=["IAFE"], cmap="RdYlGn"), width='stretch', hide_index=True)

    with st.expander("🎯 Matrice de priorisation Impact × Urgence"):
        impact_urgence = compute_impact_urgence(df_filtered)
        med_impact, med_urgence = impact_urgence.attrs["med_impact"], impact_urgence.attrs["med_urgence"]
        fig = go.Figure()
        fig.add_shape(type="rect", x0=med_impact, x1=105, y0=med_urgence, y1=105, fillcolor="#D64545", opacity=0.07, line_width=0)
        fig.add_shape(type="rect", x0=-5, x1=med_impact, y0=-5, y1=med_urgence, fillcolor="#0B6E4F", opacity=0.07, line_width=0)
        fig.add_vline(x=med_impact, line_dash="dot", line_color="gray")
        fig.add_hline(y=med_urgence, line_dash="dot", line_color="gray")
        fig.add_trace(go.Scatter(x=impact_urgence["Impact"], y=impact_urgence["Urgence"], mode="markers+text",
                                  text=impact_urgence.index, textposition="top center",
                                  marker=dict(size=impact_urgence["Population_2022"] / 25000, color=impact_urgence["Couleur"],
                                              line=dict(width=1.5, color="white"), sizemin=18)))
        fig.update_layout(title="Matrice Impact × Urgence (taille = population 2022)", xaxis_title="Impact",
                           yaxis_title="Urgence", xaxis_range=[-5, 105], yaxis_range=[-5, 105], height=500, margin=dict(t=60, b=10))
        st.plotly_chart(fig, width='stretch')
        download_buttons(impact_urgence.drop(columns="Couleur"), "matrice_impact_urgence", "iu")

    with st.expander("🔮 Scénarios prospectifs (simulation transparente de la formule IAFE)"):
        sc = compute_scenarios()
        st.dataframe(
            sc["scenarios_df"].style.background_gradient(subset=["Δ IAFE national"], cmap="RdYlGn", vmin=-10, vmax=10)
            .format({"IAFE national": "{:.1f}", "Δ IAFE national": "{:+.1f}"}, na_rep="n/a"),
            width='stretch', hide_index=True,
        )
        st.caption(f"Référence : IAFE national de base = {sc['iafe_base_nat']:.1f}/100. Il faudrait +{sc['nb_centres_necessaires']} "
                   f"centres pour que {sc['region_cible']} quitte la dernière place en couverture/habitant.")

# ------------------------------------------------------------------
# Machine Learning & Clustering
# ------------------------------------------------------------------
with tabs[2]:
    st.warning(
        "⚠️ Le chômage des diplômés n'est connu qu'à l'échelle **nationale** et sur **6 années seulement**. "
        "Ce qui suit est un **exercice pédagogique de bout en bout** ; les performances n'ont **aucune valeur "
        "prédictive opérationnelle**."
    )
    ml = compute_ml_comparison()
    st.markdown("#### Comparaison de modèles (validation croisée Leave-One-Out)")
    st.dataframe(ml["results_df"], width='stretch', hide_index=True)
    story_box("⚠️ Avec n=6, le R² peut être négatif ou instable : ce n'est PAS un signe d'échec, mais la "
              "conséquence arithmétique attendue d'un échantillon aussi réduit.", "warning")

    fig = px.bar(ml["importance"].reset_index(), x="index", y=0, color=0, color_continuous_scale="Teal",
                 labels={"index": "Variable", "0": "Importance"}, title="Importance des variables — Random Forest (n=6, indicatif ⚠️)")
    fig.update_layout(height=360, margin=dict(t=60, b=10), showlegend=False, coloraxis_showscale=False)
    st.plotly_chart(fig, width='stretch')

    st.markdown("#### Clustering régional")
    st.warning("⚠️ Le Togo compte **5 régions** : ce n'est pas un échantillon statistique mais la population "
               "complète. Le clustering est un outil de regroupement visuel, pas une découverte généralisable.")
    cl = compute_clustering()
    fig = make_subplots(rows=1, cols=3, subplot_titles=("KMeans", "DBSCAN", "Agglomerative"))
    coords = cl["coords_pca"]
    for i, method in enumerate(["KMeans", "DBSCAN", "Agglomerative"]):
        labels = cl["clusters"][method].values
        for lbl in sorted(set(labels)):
            mask = labels == lbl
            fig.add_trace(go.Scatter(x=coords[mask, 0], y=coords[mask, 1], mode="markers+text",
                                      text=[r for r, m in zip(cl["clusters"].index, mask) if m],
                                      textposition="top center", marker=dict(size=14),
                                      name=f"{method}: Cluster {lbl}" if lbl != -1 else f"{method}: Bruit",
                                      showlegend=False), row=1, col=i + 1)
    fig.update_layout(height=400, margin=dict(t=60, b=10), title_text="Segmentation des 5 régions (projection PCA)")
    st.plotly_chart(fig, width='stretch')
    story_box("La Maritime se distingue nettement (volume et diversité les plus élevés, portés par Lomé), "
              "tandis que les autres régions se regroupent selon leur couverture relative et la fraîcheur de leur offre.", "info")

# ------------------------------------------------------------------
# Recommandations stratégiques
# ------------------------------------------------------------------
with tabs[3]:
    st.caption("Recommandations produites par une fonction de règles appliquée aux résultats calculés : si les "
               "données changent, les recommandations changent avec elles.")
    ind_wide = build_indicateurs_sup()
    cover_df = compute_cover_df()
    risk = compute_saturation_risk()
    scores_df, equity = compute_complementary_scores()

    region_faible = cover_df.sort_values("etab_pour_100k_hab").iloc[0]
    region_forte = cover_df.sort_values("etab_pour_100k_hab", ascending=False).iloc[0]
    opportunity_index = scores_df["Opportunity Index"]

    recommendations = [
        f"🗺️ **Rééquilibrer l'offre territoriale** : la région **{region_faible['region']}** affiche la "
        f"couverture la plus faible ({region_faible['etab_pour_100k_hab']:.1f} établissements/100k hab. contre "
        f"{region_forte['etab_pour_100k_hab']:.1f} pour {region_forte['region']}). Prioriser l'ouverture de "
        f"nouveaux centres, en cohérence avec son Opportunity Index ({opportunity_index[region_faible['region']]:.0f}/100).",

        f"⚠️ **Vérifier le risque de saturation** de la catégorie **{risk.index[0]}** (indice proxy le plus "
        f"élevé, {risk.iloc[0]['indice_saturation_proxy']:.0f}/100). La catégorie **{risk.index[-1]}** apparaît "
        "sous-représentée et pourrait justifier un soutien ciblé.",

        f"🔬 **Renforcer les filières scientifiques et technologiques**, qui ne représentent que "
        f"{ind_wide['pct_filieres_scientifiques'].dropna().iloc[-1]:.1f}% des effectifs du supérieur, avec un "
        f"accent sur la féminisation ({ind_wide['pct_filles_filieres_sci'].dropna().iloc[-1]:.1f}% des inscrits).",

        f"💰 **Cibler l'investissement** sur la région **{feas_sorted.index[-1]}**, qui affiche le FEAS le "
        f"plus bas ({feas_sorted.iloc[-1]['FEAS']:.0f}/100).",

        "📋 **Combler le déficit de données** : une nomenclature de filières/spécialités systématiquement "
        "renseignée, une exécution budgétaire régionalisée et une enquête de traçabilité des diplômés sont "
        "nécessaires pour dépasser le stade de l'estimation indicative.",
    ]
    for i, r in enumerate(recommendations, 1):
        recommendation_card(i, r)

# ------------------------------------------------------------------
# Policy Dashboard
# ------------------------------------------------------------------
with tabs[4]:
    df_etab = clean_etablissements()
    impact_urgence = compute_impact_urgence()
    iafe_data = compute_iafe()
    risk = compute_saturation_risk()
    scores_df, equity = compute_complementary_scores()

    region_p1_top = (impact_urgence[impact_urgence["Priorité"] == "Priorité 1"]["Impact"].idxmax()
                      if (impact_urgence["Priorité"] == "Priorité 1").any() else impact_urgence["Impact"].idxmax())
    nb_p1 = int((impact_urgence["Priorité"] == "Priorité 1").sum())

    kpi_row([
        ("IAFE national", f"{iafe_data['iafe_national']:.1f}/100", "🧮", "#0B6E4F"),
        ("Région n°1 en priorité", region_p1_top, "📍", "#D64545"),
        ("Régions en Priorité 1", f"{nb_p1} / 5", "🚨", "#D64545" if nb_p1 else "#0B6E4F"),
        ("Chômage diplômés (dernier)", f"{iafe_data['chomage_val']:.1f}%", "📉", "#17A2B8"),
        ("Budget / étudiant (dernier)", f"{fmt_fr(iafe_data['budget_val'])} FCFA", "💰", "#F2994A"),
    ])
    st.write("")

    st.markdown("#### Décisions prioritaires — calculées automatiquement à partir des données")
    infra_gap_sport = df_etab["terrain_sport"].isna().mean() * 100
    infra_gap_toilette = df_etab["toilette_type"].isna().mean() * 100
    regions_p1 = impact_urgence[impact_urgence["Priorité"] == "Priorité 1"].sort_values("Impact", ascending=False)
    from utils.indicators import compute_offre_demande_insertion
    insertion_score = compute_offre_demande_insertion()["insertion_score"]
    regions_insertion_faible = insertion_score[insertion_score < insertion_score.median()].sort_values()
    categorie_risque, categorie_porteuse = risk.index[0], risk.index[-1]
    sc = compute_scenarios()

    if len(regions_p1):
        decision_card("🏗️ Construire de nouveaux centres techniques", f"Régions Priorité 1 : {', '.join(regions_p1.index)}",
                      f"Déficit d'offre moyen de {regions_p1['deficit_offre'].mean():.0f}/100 ; seuil de rattrapage "
                      f"estimé à +{sc['nb_centres_necessaires']} centres pour {sc['region_cible']} seule.", "#D64545")
    if iafe_data["budget_score"] < 50:
        decision_card("💰 Augmenter le budget par étudiant", "Niveau national",
                      f"Dépense/étudiant {iafe_data['budget_year']} = {fmt_fr(iafe_data['budget_val'])} FCFA, "
                      f"positionnée à {iafe_data['budget_score']:.0f}/100 de sa propre plage historique observée.", "#F2994A")
    decision_card("🎓 Développer certaines filières", f"Renforcer « {categorie_porteuse} » ; encadrer « {categorie_risque} »",
                  f"Indice de saturation proxy : {risk.loc[categorie_porteuse, 'indice_saturation_proxy']:.1f}/100 vs "
                  f"{risk.loc[categorie_risque, 'indice_saturation_proxy']:.1f}/100.", "#17A2B8")
    if len(regions_insertion_faible):
        decision_card("🤝 Renforcer les partenariats entreprises-universités", ", ".join(regions_insertion_faible.index),
                      f"Score d'insertion (proxy) le plus faible pour {regions_insertion_faible.index[0]} "
                      f"({regions_insertion_faible.iloc[0]:.0f}/100).", "#0B6E4F")
    decision_card("🏫 Améliorer les infrastructures", "Ensemble du parc de formation technique",
                  f"{infra_gap_sport:.0f}% des établissements sans terrain de sport recensé, {infra_gap_toilette:.0f}% "
                  "sans type de sanitaire renseigné.", "#8C5E58")
    decision_card("🎯 Créer des bourses ciblées", f"{scores_df['Opportunity Index'].idxmax()}",
                  f"Opportunity Index le plus élevé du pays ({scores_df['Opportunity Index'].max():.0f}/100).", "#F2994A")

    st.markdown("#### En une phrase")
    synthese = (
        f"Le Togo affiche un IAFE national de **{iafe_data['iafe_national']:.1f}/100** : **{region_p1_top}** "
        f"concentre le déficit le plus critique (Priorité 1, {nb_p1} région(s) sur 5), la Maritime illustre un "
        "problème de **composition** de l'offre plutôt que de volume, et le chômage des diplômés "
        f"({iafe_data['chomage_val']:.1f}% en {iafe_data['chomage_year']}) reste proche de son meilleur niveau "
        "observé — une fenêtre favorable pour agir."
    )
    st.markdown(
        f'<div style="padding:18px 22px;background:linear-gradient(135deg,#0B6E4F,#17A2B8);color:white;'
        f'border-radius:10px;font-size:15.5px;line-height:1.6;">{synthese}</div>',
        unsafe_allow_html=True,
    )

render_footer()
