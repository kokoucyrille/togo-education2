"""
utils/loader.py
================
Chargement des jeux de données bruts. Reproduit fidèlement la section 1.2 du
notebook source : 8 fichiers CSV répartis en 3 familles (établissements de
formation technique géolocalisés, répartition des établissements sup. 2018,
indicateurs socio-éducatifs nationaux, budgets, indicateurs Banque mondiale).
"""
from typing import Dict

import pandas as pd
import streamlit as st

from config import DATA_FILES


def _read_csv_utf8(path) -> pd.DataFrame:
    """Lit un CSV en privilégiant UTF-8 et gère les anciens exports Windows.

    Les fichiers sources ne sont pas modifiés : seul leur décodage à la lecture
    est sécurisé afin de préserver les accents dans toute l'application.
    """
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("utf-8", b"", 0, 1, f"Encodage illisible : {path}")


@st.cache_data(show_spinner=False)
def load_raw_data() -> Dict[str, pd.DataFrame]:
    """Charge les 8 fichiers CSV bruts du Data Challenge et retourne un
    dictionnaire {nom_logique: DataFrame}. Mis en cache pour la durée de la
    session (les fichiers ne changent pas en cours d'exécution)."""
    return {
        "etab_raw": _read_csv_utf8(DATA_FILES["etablissements"]),
        "dict_champs": _read_csv_utf8(DATA_FILES["dict_champs"]),
        "repart_raw": _read_csv_utf8(DATA_FILES["repartition_sup"]),
        "ind_raw": _read_csv_utf8(DATA_FILES["indicateurs_sup"]),
        "budget_raw": _read_csv_utf8(DATA_FILES["budgets"]),
        "chomage_raw": _read_csv_utf8(DATA_FILES["chomage_bm"]),
        "depense_raw": _read_csv_utf8(DATA_FILES["depense_bm"]),
        "inscription_raw": _read_csv_utf8(DATA_FILES["inscription_bm"]),
    }
