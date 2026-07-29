# 🇹🇬 Adéquation Formation-Emploi au Togo

Tableau de bord Streamlit — Data Challenge Éducation, Défi 2 (2026).
Analyse des formations techniques, de l'enseignement supérieur, des budgets et
du chômage des diplômés au Togo, à destination du Ministère de l'Éducation
Nationale et du Ministère de l'Enseignement Supérieur.

Application dérivée du notebook `notebooks/Analyse_Adequation_Formation_Emploi_Togo_presentation_v2.ipynb`,
restructurée en plateforme décisionnelle professionnelle — refonte complète
(design, navigation, filtres, performance) réalisée en juillet 2026.

## Installation

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Architecture (5 sections)

```
Formation_Emploi_Togo/
├── app.py                     # Point d'entrée (redirige vers Accueil)
├── config.py                  # Constantes centrales (chemins, palette, poids)
├── requirements.txt
├── .streamlit/config.toml     # Thème Streamlit (bleu marine + turquoise)
├── assets/
│   ├── style.css                                # Design system Power BI / Looker
│   ├── ministere_education_nationale.jpg        # République / MEN
│   ├── ministere_enseignement_superieur.jpg     # République / MESR
│   └── togo_ai_lab.jpg                          # Partenaire Togo AI Lab
├── data/                      # 8 CSV du Data Challenge
├── utils/
│   ├── loader.py              # Chargement brut (cache)
│   ├── preprocessing.py       # Nettoyage, structuration, jointures
│   ├── indicators.py          # KPI, FEAS, IAFE, CRITIC, ML, clustering, scénarios
│   ├── graph_utils.py         # Théorie des graphes (NetworkX + pyvis)
│   ├── map_utils.py           # Cartes Folium
│   ├── charts.py              # Constructeurs de graphiques Plotly génériques
│   └── helpers.py             # Storytelling, exports, setup de page
├── components/
│   ├── sidebar.py, navbar.py, metrics.py, filters.py, cards.py, footer.py
├── pages/
│   ├── 1_Accueil.py                       # Pilotage : KPI, tendances, résumé exécutif
│   ├── 2_Marche_Emploi.py                 # Chômage, budgets, offre/demande, priorisation
│   ├── 3_Formation_Professionnelle.py     # Cartographie, offre technique, enseignement sup.
│   ├── 4_Analyses_Recommandations.py      # Graphes, IAFE, ML/clustering, Policy Dashboard
│   └── 5_A_Propos.py                      # Auteur, méthodologie, sources
├── notebooks/                 # Notebook source (traçabilité)
└── Rapport_Formation_Emploi_Togo.pptx     # Synthèse PowerPoint (10 diapositives)
```

## Filtres

Seuls **2 filtres réellement exploitables** dans les données fournies sont
conservés : **Région** et **Année de création**. Ils n'apparaissent que sur les
pages où ils apportent une valeur d'analyse (Marché de l'emploi — onglets
Offre/Demande et Actions prioritaires ; Formation professionnelle ; Analyses).
Aucun champ « Sexe » ni « Niveau d'étude » n'existe au niveau établissement
dans l'extraction fournie par le Ministère (cf. page **À propos**).

## Note méthodologique

Chaque estimation, proxy ou valeur nationale appliquée uniformément aux régions
est signalée par le symbole **⚠️** dans l'application.

## Corrections apportées (juillet 2026)

- **Bug KPI chômage** : la série Banque mondiale du chômage des diplômés n'était
  pas triée chronologiquement ; le KPI « le plus récent » affichait en réalité
  l'année 2006 (11,7 %) au lieu de 2022 (7,1 %). Corrigé à la source
  (`utils/preprocessing.py::_load_wb`).
- **Bug page Actions prioritaires** : `prioritaires.join(offre_demande, ...)`
  tentait de joindre un `dict` Python à un DataFrame (`TypeError` certain).
  Corrigé en extrayant la clé `"offre_demande"`.
- **Performance** : le graphe global (256 établissements, rendu pyvis) n'était
  pas mis en cache et se reconstruisait à chaque interaction ; ajout de
  `@st.cache_resource`.
- **Configuration serveur** : `enableCORS=false` entrait en conflit avec
  `enableXsrfProtection=true` (Streamlit l'ignorait silencieusement).
- **API dépréciées** : remplacement de `use_container_width=True` par
  `width='stretch'` et de `st.components.v1.html` par `st.iframe` (retraits
  programmés par Streamlit).
- **Noms de fichiers** : les anciens fichiers de pages contenaient des noms
  corrompus à l'export (`2_Donn#U00e9es.py`) ; reconstruits avec des noms ASCII.
- Nettoyage : suppression de tous les `__pycache__`, code mort et imports dupliqués.

## Refonte UX/UI

- Passage de **11 pages / filtres multiples** à **5 sections** (Accueil,
  Marché de l'emploi, Formation professionnelle, Analyses & Recommandations,
  À propos), chacune organisée en onglets thématiques.
- Nouveau design system inspiré de Power BI / Looker Studio / Microsoft Fabric :
  fond blanc/gris clair, cartes arrondies à ombres légères, palette bleu marine
  (`#0B3D66`) + turquoise (`#17A2B8`) + orange (`#F2994A`), animations discrètes.
- Cartes KPI enrichies (icône, titre, valeur, évolution, couleur).
- Logos institutionnels affichés en cercles, alignés en haut de chaque page et
  en pied de page.
- Interprétation automatique sous chaque graphique clé et section
  « Recommandations stratégiques » à la fin des grandes sections.

### Logos institutionnels

Les logos institutionnels fournis sont déjà intégrés à `assets/`. Ils sont
affichés automatiquement dans la barre latérale, l'en-tête de page et le pied
de page.
