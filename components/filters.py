"""
components/filters.py
======================
Filtres globaux simplifies, appliques au jeu de donnees des etablissements de
formation technique (seul jeu a la granularite individuelle). Conformement a la
demande de simplification de l'interface, seuls les DEUX filtres reellement
exploitables dans les donnees fournies sont conserves : Region et Annee de
creation (aucun champ Sexe ni Niveau d'etude n'existe au niveau etablissement
dans l'extraction fournie par le Ministere, cf. page A propos). Les filtres ne
s'affichent que sur les pages ou ils apportent une reelle valeur d'analyse.
"""
from typing import Dict

import pandas as pd
import streamlit as st

from config import REGIONS


def render_page_filters(df_etab: pd.DataFrame) -> Dict:
    """Affiche les 2 filtres essentiels (Region, Annee de creation) dans la barre laterale."""
    st.markdown("**Filtres**")
    regions_sel = st.multiselect(
        "Région", options=REGIONS, default=REGIONS, key="filt_region",
    )

    annees_valides = df_etab["annee_creation"].dropna()
    if len(annees_valides):
        y_min, y_max = int(annees_valides.min()), int(annees_valides.max())
        annee_range = st.slider(
            "Année de création", min_value=y_min, max_value=y_max,
            value=(y_min, y_max), key="filt_annee",
        )
    else:
        annee_range = None

    return {"regions": regions_sel, "annee_range": annee_range}


def apply_filters(df_etab: pd.DataFrame, filters: Dict) -> pd.DataFrame:
    """Applique le dictionnaire de selections a une copie du DataFrame etablissements."""
    d = df_etab.copy()
    if filters.get("regions"):
        d = d[d["region_nom_bdd"].isin(filters["regions"])]
    if filters.get("annee_range"):
        lo, hi = filters["annee_range"]
        d = d[d["annee_creation"].isna() | d["annee_creation"].between(lo, hi)]
    return d
