"""
utils/preprocessing.py
=======================
Nettoyage, structuration et mise en forme long -> large des données brutes.
Reproduit fidèlement les sections 1.3 à 1.5 (nettoyage), 2.3 (population RGPH-5)
et les jointures nationales du notebook source. Toute estimation ou donnée
appliquée uniformément est documentée dans les docstrings (cf. note
méthodologique §2 du notebook).
"""
import re
from typing import Dict

import numpy as np
import pandas as pd
import streamlit as st

from config import NA_TOKENS, VILLE_TO_REGION, SECTOR_KEYWORDS, IND_RENAME, BUDGET_RENAME, POPULATION_REGION_2022
from utils.loader import load_raw_data


def _clean_na(series: pd.Series) -> pd.Series:
    """Convertit les codes de non-réponse d'enquête ('Nsp', 'N/a', '', ...) en NaN natif."""
    return series.apply(lambda x: np.nan if (pd.isna(x) or str(x).strip().lower() in NA_TOKENS) else x)


def _parse_point(g):
    """Parse une géométrie WKT 'POINT (lon lat)' en tuple (lon, lat)."""
    if pd.isna(g):
        return (np.nan, np.nan)
    m = re.match(r"POINT\s*\(\s*([\-0-9.]+)\s+([\-0-9.]+)\s*\)", str(g))
    return (float(m.group(1)), float(m.group(2))) if m else (np.nan, np.nan)


def _parse_year(y):
    """Filtre les codes 'Nsp' et les valeurs aberrantes de date de création."""
    s = str(y).strip()
    return int(s) if (s.isdigit() and 1900 < int(s) < 2027) else np.nan


def detect_sector(nom: str) -> str:
    """Estimation heuristique du secteur/spécialité par détection de mots-clés dans le
    nom de l'établissement. ⚠️ Le champ 'spécialité' n'existe pas dans l'extraction
    fournie (cf. note méthodologique §2.2) : ce champ est une estimation, pas une donnée
    observée, et une large part des établissements reste "Non identifié"."""
    if pd.isna(nom):
        return "Non identifié"
    nom_l = nom.lower()
    for sector, kws in SECTOR_KEYWORDS.items():
        if any(kw in nom_l for kw in kws):
            return sector
    return "Non identifié"


@st.cache_data(show_spinner=False)
def clean_etablissements() -> pd.DataFrame:
    """Nettoie le fichier des établissements de formation technique : codes de
    non-réponse -> NaN, harmonisation orthographique des catégories, parsing GPS,
    année de création, secteur estimé (text-mining léger)."""
    raw = load_raw_data()
    df = raw["etab_raw"].copy()

    for col in ["activite_statut", "etablissement_categorie", "terrain", "toilette_type", "terrain_sport"]:
        df[col] = _clean_na(df[col])

    df["etablissement_categorie"] = df["etablissement_categorie"].replace({
        "Formation profesionnelle autre": "Formation Professionnelle autre",
    })

    coords = df["geometry"].apply(_parse_point)
    df["lon"] = coords.apply(lambda t: t[0])
    df["lat"] = coords.apply(lambda t: t[1])

    df["annee_creation"] = df["etab_creation_date"].apply(_parse_year)
    df["secteur_estime"] = df["etab_nom"].apply(detect_sector)
    return df


@st.cache_data(show_spinner=False)
def clean_repartition_sup() -> pd.DataFrame:
    """Nettoie la répartition des établissements d'enseignement supérieur (2018) et
    ajoute la région (mapping ville -> région, cf. config.VILLE_TO_REGION)."""
    raw = load_raw_data()
    df = raw["repart_raw"].copy()
    df.columns = [c.strip() for c in df.columns]
    df = df[(df["villes"] != "TOTAL") & (df["type"] != "Total")].copy()
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce").fillna(0)
    df["Date"] = pd.to_numeric(df["Date"], errors="coerce").astype(int)
    df["region"] = df["villes"].map(VILLE_TO_REGION)
    return df


@st.cache_data(show_spinner=False)
def build_indicateurs_sup() -> pd.DataFrame:
    """Pivote les indicateurs de l'enseignement supérieur (format long -> large) et
    renomme les libellés en identifiants courts (cf. config.IND_RENAME)."""
    raw = load_raw_data()
    df = raw["ind_raw"].copy()
    df.columns = [c.strip() for c in df.columns]
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    df["Date"] = pd.to_numeric(df["Date"], errors="coerce").astype("Int64")
    wide = df.pivot_table(index="Date", columns="indicateur", values="Value", aggfunc="mean").sort_index()
    return wide.rename(columns=IND_RENAME)


@st.cache_data(show_spinner=False)
def build_budget_wide() -> pd.DataFrame:
    """Pivote les budgets (format long -> large, unité = millions FCFA) et calcule le
    taux d'exécution budgétaire de l'enseignement supérieur."""
    raw = load_raw_data()
    df = raw["budget_raw"].copy()
    df.columns = [c.strip() for c in df.columns]
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    df["Date"] = pd.to_numeric(df["Date"], errors="coerce").astype("Int64")
    wide = df.pivot_table(index="Date", columns="libellés", values="Value", aggfunc="mean").sort_index()
    wide = wide.rename(columns=BUDGET_RENAME)
    wide["taux_execution_sup"] = wide["budget_sup_execute"] / wide["budget_sup_vote"] * 100
    return wide


def _load_wb(df_raw: pd.DataFrame, colname: str) -> pd.DataFrame:
    d = df_raw.copy()
    d.columns = [c.strip() for c in d.columns]
    d = d[["date", "value"]].rename(columns={"value": colname})
    d["date"] = pd.to_numeric(d["date"], errors="coerce").astype("Int64")
    d[colname] = pd.to_numeric(d[colname], errors="coerce")
    return d.dropna(subset=[colname]).set_index("date").sort_index()


@st.cache_data(show_spinner=False)
def build_wb_indicators() -> Dict[str, pd.DataFrame]:
    """Charge et structure les 3 indicateurs Banque mondiale (chômage des diplômés,
    dépense par étudiant en % du PIB/habitant, taux brut d'inscription tertiaire)."""
    raw = load_raw_data()
    return {
        "chomage": _load_wb(raw["chomage_raw"], "chomage_diplomes_pct"),
        "depense": _load_wb(raw["depense_raw"], "depense_etud_pct_pib_hab"),
        "inscription": _load_wb(raw["inscription_raw"], "taux_brut_inscription_tertiaire"),
    }


@st.cache_data(show_spinner=False)
def build_national_table() -> pd.DataFrame:
    """Jointure externe sur l'année de tous les indicateurs nationaux disponibles
    (Banque mondiale + indicateurs sup. + budgets)."""
    wb = build_wb_indicators()
    ind_wide = build_indicateurs_sup()
    budget_wide = build_budget_wide()
    national = wb["inscription"].join([wb["chomage"], wb["depense"]], how="outer") \
        .join(ind_wide, how="outer").join(budget_wide, how="outer")
    national = national.sort_index()
    national.index.name = "annee"
    return national


@st.cache_data(show_spinner=False)
def get_population_df() -> pd.DataFrame:
    """Population régionale RGPH-5 (INSEED Togo, résultats définitifs, nov. 2022),
    seule donnée externe injectée dans ce projet (source : INSEED / ATOP, avril 2023)."""
    pop_df = pd.Series(POPULATION_REGION_2022, name="population_2022").rename_axis("region").reset_index()
    pop_df["population_2022_M"] = (pop_df["population_2022"] / 1_000_000).round(2)
    return pop_df


@st.cache_data(show_spinner=False)
def audit_missing_values() -> pd.DataFrame:
    """Audit quantitatif des valeurs manquantes (NaN natif + codes de non-réponse)
    sur les fichiers d'enquête bruts (établissements + répartition sup.)."""
    raw = load_raw_data()

    def audit(df, label):
        rows = []
        for col in df.columns:
            s = df[col]
            n_native = int(s.isna().sum())
            n_coded = int(s.apply(lambda x: isinstance(x, str) and x.strip().lower() in NA_TOKENS).sum())
            total = n_native + n_coded
            if total > 0:
                rows.append({
                    "jeu_de_données": label, "colonne": col,
                    "NaN_natif": n_native, "codes_non_réponse_(Nsp/N-a)": n_coded,
                    "total_manquant": total, "% manquant": round(total / len(df) * 100, 1),
                })
        return pd.DataFrame(rows)

    return pd.concat([
        audit(raw["etab_raw"], "Établissements form. technique"),
        audit(raw["repart_raw"], "Répartition établ. sup. 2018"),
    ], ignore_index=True).sort_values("% manquant", ascending=False)


@st.cache_data(show_spinner=False)
def completeness_table() -> pd.DataFrame:
    """Complétude (% de couverture de la période) des principales séries temporelles
    nationales mobilisées dans le tableau de bord."""
    ind_wide = build_indicateurs_sup()
    budget_wide = build_budget_wide()
    wb = build_wb_indicators()

    def completeness(series, label, period_start=None, period_end=None):
        s = series.dropna()
        start = period_start if period_start is not None else int(s.index.min())
        end = period_end if period_end is not None else int(s.index.max())
        n_years_span = end - start + 1
        return {
            "indicateur": label,
            "1ère année observée": int(s.index.min()),
            "dernière année observée": int(s.index.max()),
            "nb années observées": int(len(s)),
            "années de la période": n_years_span,
            "% couverture de la période": round(len(s) / n_years_span * 100, 1),
        }

    return pd.DataFrame([
        completeness(ind_wide["effectifs_etudiants"], "Effectifs étudiants (national)"),
        completeness(ind_wide["ratio_etud_enseignant"], "Ratio étudiant/enseignant (national)"),
        completeness(ind_wide["depense_annuelle_par_etudiant_fcfa"], "Dépense annuelle/étudiant FCFA (national)"),
        completeness(budget_wide["budget_sup_execute"], "Budget enseign. sup. exécuté (national)"),
        completeness(wb["chomage"]["chomage_diplomes_pct"], "Chômage diplômés (Banque mondiale)", period_start=2006, period_end=2022),
        completeness(wb["depense"]["depense_etud_pct_pib_hab"], "Dépense/étudiant % PIB/hab (Banque mondiale)"),
        completeness(wb["inscription"]["taux_brut_inscription_tertiaire"], "Taux brut inscription tertiaire (Banque mondiale)"),
    ]).sort_values("% couverture de la période")
