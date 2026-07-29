"""
pages/2_Marche_Emploi.py
=========================
Marché de l'emploi : chômage des diplômés, budgets de l'enseignement supérieur,
matrice Offre vs Demande potentielle par région, et actions prioritaires
(matrice Impact × Urgence). Fusionne les anciennes pages Chômage, Budgets et
une partie d'Actions prioritaires — aucun filtre régional n'est appliqué ici
car le chômage et les budgets ne sont connus qu'à l'échelle nationale.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.helpers import chart_insights, download_buttons, png_download_button, setup_page, story_box
from components.sidebar import render_sidebar
from components.navbar import render_navbar
from components.cards import decision_card
from components.footer import render_footer
from config import PALETTE
from utils.preprocessing import build_wb_indicators, build_budget_wide, build_indicateurs_sup, build_national_table
from utils.indicators import (
    compute_correlation_analysis, compute_offre_demande_insertion, compute_impact_urgence, compute_saturation_risk,
)
from utils.charts import correlation_heatmap

setup_page("Marché de l'emploi", "📉")
df_filtered, filters = render_sidebar(show_filters=True, current="2_Marche_Emploi")
render_navbar("Marché de l'emploi", "Chômage · Budgets · Offre / Demande · Priorisation", "📉")
st.caption("⚠️ Le chômage et les budgets sont des indicateurs nationaux (non régionalisés). Les filtres "
           "s'appliquent uniquement à la matrice Offre/Demande et aux actions prioritaires, qui s'appuient "
           "sur les établissements de formation technique.")

wb = build_wb_indicators()
budget_wide = build_budget_wide()
ind_wide = build_indicateurs_sup()
national = build_national_table()

tab1, tab2, tab3, tab4 = st.tabs(["Chômage des diplômés", "Budgets", "Offre vs Demande", "Actions prioritaires"])

# ------------------------------------------------------------------
# Chômage des diplômés
# ------------------------------------------------------------------
with tab1:
    s = wb["chomage"]["chomage_diplomes_pct"].dropna().sort_index()
    fig = go.Figure(go.Scatter(x=s.index, y=s.values, mode="lines+markers",
                                line=dict(color=PALETTE[2], width=3), marker=dict(size=10)))
    fig.update_layout(title="Taux de chômage des diplômés de l'enseignement supérieur — Togo (Banque mondiale)",
                       xaxis_title="Année", yaxis_title="% de la population active diplômée", height=400, margin=dict(t=60, b=10))
    st.plotly_chart(fig, width='stretch')
    png_download_button(fig, "evolution_chomage_diplomes", "chomage_evolution")
    story_box(f"Le taux oscille entre {s.min():.1f}% ({s.idxmin()}) et {s.max():.1f}% ({s.idxmax()}), sans "
              "tendance linéaire nette — la série est trop courte et trop irrégulière pour conclure à une "
              "amélioration ou une dégradation structurelle.", "warning")
    chart_insights(
        f"La série observée s'étend de {s.index.min()} à {s.index.max()}.",
        "Les variations annuelles doivent être lues avec prudence vu le faible nombre d'observations.",
        "Le chômage des diplômés est un indicateur national, non attribuable à une région ou une filière.",
        "Mettre en place un suivi annuel de l'insertion par établissement et par filière.",
        "Institutionnaliser une enquête de traçabilité des diplômés.",
    )

    st.markdown("#### Corrélations entre déterminants")
    st.warning("⚠️ Les séries nationales annuelles mobilisées ici ne se recoupent que sur un nombre d'années "
               "très limité. Une corrélation calculée sur un si petit échantillon doit être lue comme un "
               "**indice qualitatif de co-mouvement**, jamais comme une preuve de causalité (N systématiquement affiché).")
    corr = compute_correlation_analysis()
    st.plotly_chart(correlation_heatmap(corr["corr_mat"], corr["n_common"],
                     "Corrélation entre déterminants (r puis N années communes)"), width='stretch')
    if not corr["pairs_df"].empty:
        top_pos, top_neg = corr["pairs_df"].iloc[0], corr["pairs_df"].iloc[-1]
        story_box(
            f"Corrélation la plus forte (positive) : <b>{top_pos['Variable 1']} ↔ {top_pos['Variable 2']}</b> "
            f"(r={top_pos['r']:.2f}, n={top_pos['n']:.0f}). Corrélation la plus forte (négative, hors paire "
            f"circulaire) : <b>{top_neg['Variable 1']} ↔ {top_neg['Variable 2']}</b> (r={top_neg['r']:.2f}, n={top_neg['n']:.0f}).",
            "info",
        )
    else:
        st.info("Aucune paire de séries ne possède trois années communes : aucun coefficient n'est interprété.")

# ------------------------------------------------------------------
# Budgets
# ------------------------------------------------------------------
with tab2:
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Budget voté vs exécuté (millions FCFA)", "Taux d'exécution budgétaire (%)"))
    fig.add_trace(go.Bar(x=budget_wide.index.astype(str), y=budget_wide["budget_sup_vote"], name="Voté", marker_color=PALETTE[3]), row=1, col=1)
    fig.add_trace(go.Bar(x=budget_wide.index.astype(str), y=budget_wide["budget_sup_execute"], name="Exécuté", marker_color=PALETTE[0]), row=1, col=1)
    fig.add_trace(go.Scatter(x=budget_wide.index.astype(str), y=budget_wide["taux_execution_sup"], mode="lines+markers",
                              name="Taux d'exécution", line=dict(color=PALETTE[2], width=3)), row=1, col=2)
    fig.add_hline(y=100, line_dash="dash", line_color="gray", row=1, col=2)
    fig.update_layout(barmode="group", height=400, margin=dict(t=60, b=10), title_text="Exécution budgétaire de l'enseignement supérieur")
    st.plotly_chart(fig, width='stretch')
    taux_moy = budget_wide["taux_execution_sup"].mean()
    story_box(f"Taux d'exécution moyen : {taux_moy:.1f}% — "
              + ("l'exécution est globalement proche ou supérieure au budget voté." if taux_moy > 95
                 else "une part du budget voté n'est pas consommée."), "info")

    c1, c2 = st.columns(2)
    with c1:
        s = ind_wide["depense_annuelle_par_etudiant_fcfa"].dropna()
        fig = px.line(x=s.index, y=s.values, markers=True, title="Dépense annuelle par étudiant (FCFA)",
                      labels={"x": "Année", "y": "FCFA"})
        fig.update_traces(line_color=PALETTE[0])
        st.plotly_chart(fig, width='stretch')
    with c2:
        s2 = wb["depense"]["depense_etud_pct_pib_hab"].dropna().sort_index()
        fig = px.line(x=s2.index, y=s2.values, markers=True, title="Dépense/étudiant (% PIB/hab.) — Banque mondiale",
                      labels={"x": "Année", "y": "%"})
        fig.update_traces(line_color=PALETTE[3])
        st.plotly_chart(fig, width='stretch')
    story_box("La dépense par étudiant en % du PIB/habitant a fortement décru, ce qui traduit une croissance "
              "des effectifs plus rapide que celle du financement par tête.", "info")

    st.markdown("#### Chaîne Budget → Encadrement → Insertion / Chômage")
    st.warning("⚠️ Lecture qualitative uniquement : les années disponibles pour budget, encadrement et chômage "
               "se recoupent sur très peu de points communs.")
    chain = national[["depense_annuelle_par_etudiant_fcfa", "ratio_etud_enseignant",
                       "taux_inscription_immediat_bac", "chomage_diplomes_pct"]].dropna(how="all")
    fig = go.Figure()
    for i, col in enumerate(chain.columns):
        s = chain[col].dropna()
        fig.add_trace(go.Scatter(x=s.index, y=(s - s.min()) / (s.max() - s.min()) * 100, mode="lines+markers",
                                  name=col, line=dict(color=PALETTE[i % len(PALETTE)])))
    fig.update_layout(title="⚠️ Chaîne conceptuelle (indices normalisés 0-100)", xaxis_title="Année",
                       yaxis_title="Indice normalisé", height=420, margin=dict(t=60, b=10))
    st.plotly_chart(fig, width='stretch')

# ------------------------------------------------------------------
# Offre vs Demande
# ------------------------------------------------------------------
with tab3:
    st.caption("Existe-t-il un déséquilibre entre l'offre de formation et la demande potentielle, région par région ?")
    od = compute_offre_demande_insertion(df_filtered)
    offre_demande = od["offre_demande"]
    fig = px.imshow(offre_demande[["Offre de formation", "Demande potentielle", "Insertion (proxy)"]].T,
                     text_auto=True, aspect="auto", color_continuous_scale="RdYlGn", range_color=[0, 100],
                     labels=dict(x="Région", y="", color="Score /100"),
                     title="Offre / Demande potentielle / Insertion (proxy) par région")
    fig.update_layout(height=380, margin=dict(t=60, b=10))
    st.plotly_chart(fig, width='stretch')
    png_download_button(fig, "matrice_offre_demande", "offre_demande_heatmap")
    chart_insights(
        "Les scores d'offre et d'insertion reflètent le périmètre sélectionné.",
        "La demande potentielle est estimée à partir de la population régionale.",
        "Le chômage présenté reste une référence nationale, faute de mesure régionale.",
        "Cibler l'extension de l'offre dans les régions sous-dotées et à forte demande.",
        "Valider les priorités avec les collectivités et les employeurs locaux.",
    )
    st.markdown("#### Diagnostic automatique, région par région")
    for r in offre_demande.index:
        row = offre_demande.loc[r]
        signe_o = "≥" if row["Offre de formation"] >= od["med_offre"] else "<"
        signe_d = "≥" if row["Demande potentielle"] >= od["med_demande"] else "<"
        st.markdown(
            f"**{r}** : offre {row['Offre de formation']:.1f}/100 ({signe_o} médiane {od['med_offre']:.0f}), "
            f"demande {row['Demande potentielle']:.1f}/100 ({signe_d} médiane {od['med_demande']:.0f}) → **{row['Diagnostic']}**"
        )
    download_buttons(offre_demande, "matrice_offre_demande", "od")

# ------------------------------------------------------------------
# Actions prioritaires
# ------------------------------------------------------------------
with tab4:
    priorites = compute_impact_urgence(df_filtered)
    risque = compute_saturation_risk(df_filtered)
    prioritaires = priorites.sort_values(["Impact", "Urgence"], ascending=False)
    regions_p1 = ", ".join(prioritaires[prioritaires["Priorité"] == "Priorité 1"].index) or prioritaires.index[0]
    vulnerables = prioritaires.head(2).index.tolist()
    secteurs = df_filtered["secteur_estime"].value_counts().drop(labels="Non identifié", errors="ignore").head(3).index.tolist()

    c1, c2 = st.columns(2)
    with c1:
        decision_card("Régions prioritaires", regions_p1,
                       "Croisement du déficit structurel et de l'urgence démographique.", "#D64545")
        decision_card("Formations à développer", risque.index[-1],
                       "Catégorie présentant le risque structurel proxy le plus faible.", "#0B3D66")
        decision_card("Secteurs porteurs", ", ".join(secteurs) if secteurs else "À documenter",
                       "Secteurs les plus représentés dans l'offre filtrée.", "#17A2B8")
    with c2:
        decision_card("Populations vulnérables", ", ".join(vulnerables),
                       "Territoires cumulant couverture relative faible et pression de demande élevée.", "#F2994A")
        decision_card("Formation à surveiller", risque.index[0],
                       "Risque de saturation structurel le plus élevé : enquête d'insertion recommandée.", "#D64545")
        decision_card("Impact attendu", "Accès, équité et employabilité",
                       "Une meilleure allocation territoriale doit augmenter la couverture et réduire les déséquilibres.", "#0B6E4F")

    st.markdown("### Recommandations stratégiques")
    st.markdown(
        "1. Programmer l'extension des centres dans les régions Priorité 1.\n"
        "2. Co-construire les nouveaux curricula avec les entreprises et collectivités.\n"
        "3. Lancer une enquête annuelle d'insertion par filière, sexe et région.\n"
        "4. Publier un suivi trimestriel des actions et des indicateurs d'impact."
    )
    export_df = prioritaires.join(compute_offre_demande_insertion(df_filtered)["offre_demande"], how="left")
    download_buttons(export_df, "actions_prioritaires", "actions_prioritaires")

render_footer()
