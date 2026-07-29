"""
pages/5_A_Propos.py
=====================
Page « À propos » : présentation de l'auteur, méthodologie, sources de
données et limites. Aucun filtre — page purement informative.
"""
import streamlit as st

from utils.helpers import setup_page
from components.sidebar import render_sidebar
from components.navbar import render_navbar
from components.footer import render_footer
from config import AUTHOR, INSTITUTION, MINISTERE

setup_page("À propos", "ℹ️")
_, filters = render_sidebar(show_filters=False, current="5_A_Propos")
render_navbar("À propos", "Auteur · Méthodologie · Sources · Conclusion", "ℹ️")

# ------------------------------------------------------------------
# Carte auteur
# ------------------------------------------------------------------
st.markdown(
    f"""
    <div class="author-card">
        <div style="font-size:20px;font-weight:750;color:#0B3D66;">{AUTHOR}</div>
        <div style="color:#64748B;font-size:14.5px;margin:4px 0 14px 0;">
            Ingénieur de Travaux Informatiques — {INSTITUTION}
        </div>
        <p style="font-size:14.5px;line-height:1.6;">
            Passionné par la Data Science, le développement d'applications décisionnelles, l'intelligence
            artificielle et la transformation numérique. Ce projet a été conçu afin d'aider les décideurs du
            Ministère à analyser efficacement les données relatives à la formation professionnelle et à
            l'emploi pour faciliter la prise de décision basée sur les données.
        </p>
        <div style="margin-top:14px;line-height:1.9;font-size:14.5px;">
            📞 <b>Téléphone</b> : +228 90 51 59 28<br>
            💬 <b>WhatsApp</b> : +228 90 51 59 28<br>
            📧 <b>Email</b> : <a href="mailto:cyridayo@gmail.com">cyridayo@gmail.com</a><br>
            💼 <b>LinkedIn</b> : <a href="https://www.linkedin.com/in/dkc023/" target="_blank">linkedin.com/in/dkc023</a><br>
            💻 <b>GitHub</b> : <a href="https://github.com/kokoucyrille/" target="_blank">github.com/kokoucyrille</a>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")
c1, c2, c3 = st.columns(3)
c1.metric("Auteur", AUTHOR)
c2.metric("Institution", INSTITUTION)
c3.metric("Concours", "Data Challenge Éducation — Défi 2 — 2026")
st.caption(f"Tableau de bord produit à destination du {MINISTERE}.")

st.divider()

# ------------------------------------------------------------------
# Méthodologie
# ------------------------------------------------------------------
st.markdown("### Ce que cette analyse établit (sur données réelles)")
st.markdown(
    """
- Une **cartographie fine et géolocalisée** de 256 établissements de formation technique, avec une forte
  concentration régionale et des disparités marquées de couverture par habitant.
- Une **lecture structurelle par la théorie des graphes** (centralités, PageRank, communautés de Louvain).
- Un **suivi complet des indicateurs nationaux** (effectifs, féminisation, encadrement, budgets, chômage).
- Une **démarche Machine Learning et clustering reproductible**, honnêtement bornée par la taille des
  échantillons disponibles.
- Des **scores composites originaux** (FEAS, IAFE, Opportunity Index, Territorial Equity Score) combinant
  systématiquement le réel et l'estimé, chaque composante étant traçable à sa source.
"""
)

st.markdown("### Ce qu'il manque pour aller plus loin (priorités de collecte pour le Ministère)")
st.markdown(
    """
1. **Une nomenclature de filières/spécialités** systématiquement renseignée dans le recensement des
   établissements techniques.
2. **Une exécution budgétaire régionalisée**, pour remplacer une composante nationale uniforme de l'IAFE par
   une vraie composante régionale.
3. **Une enquête de traçabilité des diplômés (tracer study)** par filière, diplôme et région — condition
   *sine qua non* d'un véritable indicateur d'insertion.
4. **Une mise à jour régulière** des séries nationales (plusieurs indicateurs s'arrêtent en 2018-2019).
"""
)

st.divider()
st.markdown("### Sources de données")
st.markdown(
    """
- Fichiers du Data Challenge Éducation (Défi 2, 2026) : établissements de formation technique géolocalisés,
  répartition des établissements d'enseignement supérieur (2018), indicateurs socio-éducatifs nationaux,
  budgets, indicateurs Banque mondiale (chômage des diplômés, dépense/étudiant, taux d'inscription tertiaire).
- Population régionale : **RGPH-5** (INSEED Togo, résultats définitifs, novembre 2022), reprise par l'Agence
  Togolaise de Presse (ATOP), avril 2023 — seule donnée externe injectée dans ce projet.
"""
)

st.info(
    "🧭 Toutes les sources de données et hypothèses méthodologiques sont rappelées par le symbole ⚠️ à chaque "
    "usage d'une estimation ou d'un proxy, sur l'ensemble des pages du tableau de bord."
)

render_footer()
