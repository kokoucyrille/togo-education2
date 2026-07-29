"""
utils/indicators.py
====================
Tous les indicateurs calculés du tableau de bord : KPI de cadrage, variables
régionales, indice de saturation (§9.2), FEAS (§13), IAFE (§18), méthode CRITIC
(§18.2), matrice Offre/Demande (§17), matrice Impact x Urgence (§20) et scénarios
prospectifs (§22). Chaque fonction est un équivalent direct d'une section du
notebook source ; les commentaires ⚠️ signalent les estimations et proxys.
"""
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
import streamlit as st

from config import REGIONS, FEAS_WEIGHTS, IAFE_WEIGHTS
from utils.preprocessing import (
    clean_etablissements, clean_repartition_sup, build_indicateurs_sup,
    build_budget_wide, build_wb_indicators, get_population_df,
)


def minmax_100(s: pd.Series) -> pd.Series:
    """Normalisation min-max sur 0-100. Retourne 50 partout si la série est constante."""
    if s.max() == s.min():
        return pd.Series(50.0, index=s.index)
    return (s - s.min()) / (s.max() - s.min()) * 100


def fmt_fr(x, decimals=0) -> str:
    """Formate un nombre avec des espaces comme séparateurs de milliers (convention française)."""
    if pd.isna(x):
        return "n/d"
    return f"{x:,.{decimals}f}".replace(",", " ")


def score_national_in_history(series: pd.Series, invert: bool = False, override_last=None) -> Tuple[float, float, int]:
    """Positionne une valeur annuelle nationale dans la plage historique OBSERVÉE de sa
    propre série (0=minimum historique, 100=maximum historique). `override_last` permet
    de tester une valeur hypothétique (scénarios prospectifs, §22). invert=True pour les
    indicateurs où une valeur plus faible est préférable (ex. chômage)."""
    s = series.dropna().sort_index()
    lo, hi = s.min(), s.max()
    val = override_last if override_last is not None else s.iloc[-1]
    pos = 50.0 if hi == lo else (val - lo) / (hi - lo) * 100
    pos = max(0.0, min(100.0, pos))
    score = (100 - pos) if invert else pos
    return round(score, 1), val, s.index[-1]


# ------------------------------------------------------------------
# §3 — KPI globaux
# ------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def compute_kpi() -> Dict:
    df_etab = clean_etablissements()
    df_repart = clean_repartition_sup()
    ind_wide = build_indicateurs_sup()
    budget_wide = build_budget_wide()
    wb = build_wb_indicators()

    kpi = {}
    kpi["Nombre de formations techniques recensées"] = len(df_etab)
    kpi["Nombre de régions couvertes (formation technique)"] = df_etab["region_nom_bdd"].nunique()
    kpi["Nombre de préfectures couvertes"] = df_etab["prefecture_nom_bdd"].nunique()
    kpi["Nombre d'établissements sup. recensés (2018)"] = int(df_repart[df_repart["type"] == "Etablissement"]["Value"].sum())
    kpi["Nombre d'universités recensées (2018)"] = int(df_repart[df_repart["type"] == "Université"]["Value"].sum())
    kpi["Taux de féminisation le plus récent (%)"] = round(ind_wide["taux_feminisation"].dropna().iloc[-1], 1)
    kpi["Ratio étudiants/enseignants le plus récent"] = round(ind_wide["ratio_etud_enseignant"].dropna().iloc[-1], 1)
    kpi["Dépense annuelle/étudiant la plus récente (FCFA)"] = fmt_fr(ind_wide["depense_annuelle_par_etudiant_fcfa"].dropna().iloc[-1])
    kpi["Part des filières scientifiques la plus récente (%)"] = round(ind_wide["pct_filieres_scientifiques"].dropna().iloc[-1], 1)
    kpi["Taux d'exécution budgétaire sup. moyen (%)"] = round(budget_wide["taux_execution_sup"].mean(), 1)
    kpi["Chômage diplômés le plus récent connu (%, année)"] = f"{wb['chomage']['chomage_diplomes_pct'].iloc[-1]:.1f}% ({wb['chomage'].index[-1]})"
    return kpi


# ------------------------------------------------------------------
# §4.1 — Couverture territoriale
# ------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def compute_cover_df() -> pd.DataFrame:
    df_etab = clean_etablissements()
    pop_df = get_population_df()
    region_counts = df_etab["region_nom_bdd"].value_counts().reindex(REGIONS).fillna(0).astype(int)
    cover_df = region_counts.rename("nb_etablissements").reset_index().rename(columns={"region_nom_bdd": "region"})
    cover_df = cover_df.merge(pop_df, on="region")
    cover_df["etab_pour_100k_hab"] = (cover_df["nb_etablissements"] / cover_df["population_2022"] * 100_000).round(2)
    return cover_df.sort_values("etab_pour_100k_hab", ascending=False)


# ------------------------------------------------------------------
# §9.2 — Indice de saturation proxy par catégorie de formation
# ------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def compute_saturation_risk(df_etab: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """⚠️ Indice de risque structurel (proxy), non basé sur une mesure réelle du
    chômage par filière : poids relatif de la catégorie x part des créations
    récentes (depuis 2010) dans cette catégorie."""
    if df_etab is None:
        df_etab = clean_etablissements()
    cat_data = df_etab.dropna(subset=["etablissement_categorie"]).copy()
    poids = cat_data["etablissement_categorie"].value_counts(normalize=True)
    recent_share = cat_data.assign(recent=cat_data["annee_creation"] >= 2010).groupby("etablissement_categorie")["recent"].mean()
    risk = pd.DataFrame({"poids_dans_offre": poids, "part_creations_recentes": recent_share}).dropna()
    risk["indice_saturation_proxy"] = (risk["poids_dans_offre"] * risk["part_creations_recentes"] * 100).round(1)
    return risk.sort_values("indice_saturation_proxy", ascending=False)


# ------------------------------------------------------------------
# §12.1 — Variables régionales (base des clusterings et scores composites)
# ------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def compute_region_features(
    df_etab: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Construit les variables régionales, éventuellement sur le périmètre filtré."""
    if df_etab is None:
        df_etab = clean_etablissements()
    df_repart = clean_repartition_sup()
    pop_df = get_population_df()
    counts = df_etab["region_nom_bdd"].value_counts().reindex(REGIONS).fillna(0)
    cover_df = counts.rename("nb_etablissements").rename_axis("region").reset_index()
    cover_df = cover_df.merge(pop_df, on="region", how="left")
    cover_df["etab_pour_100k_hab"] = (
        cover_df["nb_etablissements"] / cover_df["population_2022"] * 100_000
    ).fillna(0)

    region_features = cover_df.set_index("region")[["nb_etablissements", "population_2022", "etab_pour_100k_hab"]].copy()
    diversite_categorie = df_etab.groupby("region_nom_bdd")["etablissement_categorie"].nunique()
    diversite_secteur = df_etab.groupby("region_nom_bdd")["secteur_estime"].nunique()
    part_recentes = df_etab.dropna(subset=["annee_creation"]).assign(
        recent=lambda d: d["annee_creation"] >= 2010).groupby("region_nom_bdd")["recent"].mean() * 100
    sup_2018_region = df_repart.groupby("region")["Value"].sum()

    region_features["diversite_categories"] = diversite_categorie.reindex(
        region_features.index
    ).fillna(0)
    region_features["diversite_secteurs_estimes"] = diversite_secteur.reindex(
        region_features.index
    ).fillna(0)
    region_features["part_creations_recentes_pct"] = part_recentes.reindex(
        region_features.index
    ).fillna(0)
    region_features["nb_etab_sup_2018"] = sup_2018_region.reindex(region_features.index).fillna(0)
    return region_features.reindex(REGIONS)


# ------------------------------------------------------------------
# §13.1 — Formation-Employment Alignment Score (FEAS)
# ------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def compute_feas(df_etab: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    rf = compute_region_features(df_etab)
    ind_wide = build_indicateurs_sup()
    budget_wide = build_budget_wide()

    c_couverture = minmax_100(rf["etab_pour_100k_hab"])
    c_diversite = minmax_100(rf["diversite_categories"] + rf["diversite_secteurs_estimes"])
    c_dynamisme = minmax_100(rf["part_creations_recentes_pct"])
    c_volume_sup = minmax_100(rf["nb_etab_sup_2018"])

    ratio_national = ind_wide["ratio_etud_enseignant"].dropna().iloc[-1]
    c_encadrement_national = max(0, 100 - (ratio_national / 2))
    part_sci_national = ind_wide["pct_filieres_scientifiques"].dropna().iloc[-1]
    c_orientation_sci_national = min(100, part_sci_national / 40 * 100)
    exec_budget_national = budget_wide["taux_execution_sup"].mean()
    c_execution_budget_national = min(100, exec_budget_national)

    feas = pd.DataFrame({
        "couverture_territoriale": c_couverture,
        "diversite_offre": c_diversite,
        "dynamisme_creations": c_dynamisme,
        "volume_enseignement_sup": c_volume_sup,
        "encadrement_national": c_encadrement_national,
        "orientation_scientifique_national": c_orientation_sci_national,
        "execution_budgetaire_national": c_execution_budget_national,
    }, index=rf.index)
    feas["FEAS"] = sum(feas[c] * w for c, w in FEAS_WEIGHTS.items()).round(1)
    return feas


@st.cache_data(show_spinner=False)
def compute_complementary_scores(
    df_etab: Optional[pd.DataFrame] = None,
) -> Tuple[pd.DataFrame, float]:
    """Opportunity Index, Territorial Equity Score et Employment Potential Score (§13.2)."""
    rf = compute_region_features(df_etab)
    feas = compute_feas(df_etab)

    pop_share = rf["population_2022"] / rf["population_2022"].sum() * 100
    coverage_share = minmax_100(rf["etab_pour_100k_hab"])
    opportunity_index = minmax_100(pop_share * (100 - coverage_share)).round(1)

    values = rf["etab_pour_100k_hab"].values
    mad = np.mean([abs(vi - vj) for vi in values for vj in values]) / 2
    gini_like = mad / np.mean(values)
    equity_score_system = round(max(0, 100 - gini_like * 100), 1)

    employment_potential = minmax_100(
        0.6 * (rf["diversite_categories"] + rf["diversite_secteurs_estimes"]) + 0.4 * rf["part_creations_recentes_pct"]
    ).round(1)

    scores_df = pd.DataFrame({
        "FEAS": feas["FEAS"],
        "Opportunity Index": opportunity_index,
        "Employment Potential Score ⚠️": employment_potential,
    })
    scores_df["Territorial Equity Score (système, ⚠️ valeur unique)"] = equity_score_system
    return scores_df, equity_score_system


# ------------------------------------------------------------------
# §17 — Matrice Offre vs Demande
# ------------------------------------------------------------------
def offre_pillar(rf_: pd.DataFrame) -> pd.Series:
    """Pilier 'Offre de formation' : mêmes 4 composantes régionales réelles que FEAS,
    poids renormalisés à somme 1 (25/20/15/15 -> /0.75) pour assurer la continuité
    méthodologique entre FEAS (§13) et l'IAFE (§18)."""
    w_couv, w_div, w_dyn, w_vol = 0.25 / 0.75, 0.20 / 0.75, 0.15 / 0.75, 0.15 / 0.75
    c1 = minmax_100(rf_["etab_pour_100k_hab"])
    c2 = minmax_100(rf_["diversite_categories"] + rf_["diversite_secteurs_estimes"])
    c3 = minmax_100(rf_["part_creations_recentes_pct"])
    c4 = minmax_100(rf_["nb_etab_sup_2018"])
    return (w_couv * c1 + w_div * c2 + w_dyn * c3 + w_vol * c4).round(1)


@st.cache_data(show_spinner=False)
def compute_offre_demande_insertion(
    df_etab: Optional[pd.DataFrame] = None,
) -> Dict:
    """Retourne les piliers Offre / Demande / Insertion (§17.1) + diagnostic (§17.2)."""
    if df_etab is None:
        df_etab = clean_etablissements()
    rf = compute_region_features(df_etab)
    risk = compute_saturation_risk(df_etab)
    wb = build_wb_indicators()

    offre_score = offre_pillar(rf)

    employabilite_categorie = (100 - risk["indice_saturation_proxy"]).rename("employabilite_proxy")
    etab_emp = df_etab.dropna(subset=["etablissement_categorie"]).copy()
    etab_emp["employabilite_proxy"] = etab_emp["etablissement_categorie"].map(employabilite_categorie)
    insertion_region_brut = etab_emp.groupby("region_nom_bdd")["employabilite_proxy"].mean().reindex(REGIONS)
    insertion_score = minmax_100(insertion_region_brut).round(1)

    demande_score = minmax_100(rf["population_2022"]).round(1)

    offre_demande = pd.DataFrame({
        "Offre de formation": offre_score,
        "Demande potentielle": demande_score,
        "Insertion (proxy)": insertion_score,
    }).reindex(REGIONS)
    _, chom_val, chom_year = score_national_in_history(wb["chomage"]["chomage_diplomes_pct"])
    offre_demande[f"Chômage national {chom_year} (réf.) ⚠️ %"] = round(chom_val, 1)

    med_offre, med_demande = offre_demande["Offre de formation"].median(), offre_demande["Demande potentielle"].median()

    def diagnostic(offre, demande, insertion):
        offre_forte, demande_forte = offre >= med_offre, demande >= med_demande
        if offre_forte and not demande_forte:
            return "Offre confortable"
        if offre_forte and demande_forte:
            return "Dynamique équilibrée" if insertion >= 50 else "Dynamique, employabilité à surveiller"
        if not offre_forte and demande_forte:
            return "Sous-dotée — priorité d'investissement"
        return "En retrait — vigilance"

    offre_demande["Diagnostic"] = [
        diagnostic(offre_demande.loc[r, "Offre de formation"], offre_demande.loc[r, "Demande potentielle"], offre_demande.loc[r, "Insertion (proxy)"])
        for r in offre_demande.index
    ]
    return {
        "offre_demande": offre_demande, "offre_score": offre_score, "insertion_score": insertion_score,
        "demande_score": demande_score, "med_offre": med_offre, "med_demande": med_demande,
        "employabilite_categorie": employabilite_categorie, "insertion_region_brut": insertion_region_brut,
    }


# ------------------------------------------------------------------
# §18 — Indice d'Adéquation Formation-Emploi (IAFE)
# ------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def compute_iafe(df_etab: Optional[pd.DataFrame] = None) -> Dict:
    od = compute_offre_demande_insertion(df_etab)
    ind_wide = build_indicateurs_sup()
    wb = build_wb_indicators()
    pop_df = get_population_df()

    budget_score, budget_val, budget_year = score_national_in_history(ind_wide["depense_annuelle_par_etudiant_fcfa"])
    chomage_score, chomage_val, chomage_year = score_national_in_history(wb["chomage"]["chomage_diplomes_pct"], invert=True)

    iafe = pd.DataFrame({
        "Offre de formation": od["offre_score"],
        "Budget par étudiant": budget_score,
        "Insertion professionnelle": od["insertion_score"],
        "Chômage des diplômés": chomage_score,
    }, index=REGIONS)
    iafe["IAFE"] = sum(iafe[c] * w for c, w in IAFE_WEIGHTS.items()).round(1)

    pop_share = (pop_df.set_index("region")["population_2022"] / pop_df["population_2022"].sum()).reindex(REGIONS)
    iafe_national = (iafe["IAFE"] * pop_share).sum()
    iafe_national_simple = iafe["IAFE"].mean()

    return {
        "iafe": iafe, "budget_score": budget_score, "budget_val": budget_val, "budget_year": budget_year,
        "chomage_score": chomage_score, "chomage_val": chomage_val, "chomage_year": chomage_year,
        "iafe_national": iafe_national, "iafe_national_simple": iafe_national_simple, "pop_share": pop_share,
    }


def critic_weights(df: pd.DataFrame) -> pd.Series:
    """Pondération CRITIC (Diakoulaki, Mavrotas & Papayannakis, 1995) : std x (1 -
    corrélation moyenne avec les autres critères), renormalisée à somme 1. Un critère
    constant reçoit un poids nul (aucune information discriminante)."""
    std = df.std(ddof=0)
    corr = df.corr().fillna(0)
    redundancy = (1 - corr).sum(axis=1)
    information = std * redundancy
    if information.sum() == 0:
        return pd.Series(1 / len(df.columns), index=df.columns)
    return (information / information.sum()).round(4)


@st.cache_data(show_spinner=False)
def compute_iafe_etablissement(
    df_etab: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """IAFE au niveau établissement (§18.3) : hérite des piliers régionaux
    Offre/Budget/Chômage, se différencie par la catégorie de formation (pilier Insertion)."""
    if df_etab is None:
        df_etab = clean_etablissements()
    od = compute_offre_demande_insertion(df_etab)
    iafe_data = compute_iafe(df_etab)

    etab_iafe = df_etab.copy()
    etab_iafe["offre_formation"] = etab_iafe["region_nom_bdd"].map(od["offre_score"])
    etab_iafe["budget_par_etudiant"] = iafe_data["budget_score"]
    etab_iafe["chomage_diplomes"] = iafe_data["chomage_score"]
    etab_iafe["insertion_brut"] = etab_iafe["etablissement_categorie"].map(od["employabilite_categorie"])
    etab_iafe["insertion_brut"] = etab_iafe["insertion_brut"].fillna(etab_iafe["region_nom_bdd"].map(od["insertion_region_brut"]))
    etab_iafe["insertion_professionnelle"] = minmax_100(etab_iafe["insertion_brut"])
    etab_iafe["IAFE_etablissement"] = sum(
        etab_iafe[col] * w for col, w in zip(
            ["offre_formation", "budget_par_etudiant", "insertion_professionnelle", "chomage_diplomes"],
            IAFE_WEIGHTS.values())
    ).round(1)
    moyenne_nationale = etab_iafe["IAFE_etablissement"].mean()
    etab_iafe["ecart_moyenne_nationale"] = (etab_iafe["IAFE_etablissement"] - moyenne_nationale).round(1)
    return etab_iafe


# ------------------------------------------------------------------
# §20 — Matrice de priorisation Impact x Urgence
# ------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def compute_impact_urgence(df_etab: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    rf = compute_region_features(df_etab)
    od = compute_offre_demande_insertion(df_etab)

    deficit_offre = (100 - od["offre_score"]).round(1)
    deficit_insertion = (100 - od["insertion_score"]).round(1)
    deficit_infra_sup = (100 - minmax_100(rf["nb_etab_sup_2018"])).round(1)
    impact_score = (deficit_offre * 0.45 + deficit_insertion * 0.30 + deficit_infra_sup * 0.25).round(1)

    dynamisme_inv = (100 - minmax_100(rf["part_creations_recentes_pct"])).round(1)
    urgence_score = (od["demande_score"] * 0.65 + dynamisme_inv * 0.35).round(1)

    impact_urgence = pd.DataFrame({
        "Impact": impact_score, "Urgence": urgence_score, "Population_2022": rf["population_2022"],
        "deficit_offre": deficit_offre, "deficit_insertion": deficit_insertion, "deficit_infra_sup": deficit_infra_sup,
        "dynamisme_inv": dynamisme_inv,
    }).reindex(REGIONS)
    med_impact, med_urgence = impact_urgence["Impact"].median(), impact_urgence["Urgence"].median()

    def priority_bucket(impact, urgence):
        hi_i, hi_u = impact >= med_impact, urgence >= med_urgence
        if hi_i and hi_u:
            return "Priorité 1"
        if hi_i != hi_u:
            return "Priorité 2"
        return "Priorité 3"

    from config import PRIORITY_COLOR
    impact_urgence["Priorité"] = [priority_bucket(impact_urgence.loc[r, "Impact"], impact_urgence.loc[r, "Urgence"]) for r in impact_urgence.index]
    impact_urgence["Couleur"] = impact_urgence["Priorité"].map(PRIORITY_COLOR)
    impact_urgence.attrs["med_impact"] = med_impact
    impact_urgence.attrs["med_urgence"] = med_urgence
    return impact_urgence


# ------------------------------------------------------------------
# §22 — Scénarios prospectifs
# ------------------------------------------------------------------
def iafe_from_pillars(offre, budget, insertion, chomage) -> pd.Series:
    return (IAFE_WEIGHTS["Offre de formation"] * offre + IAFE_WEIGHTS["Budget par étudiant"] * budget +
            IAFE_WEIGHTS["Insertion professionnelle"] * insertion + IAFE_WEIGHTS["Chômage des diplômés"] * chomage).round(1)


@st.cache_data(show_spinner=False)
def compute_scenarios() -> Dict:
    od = compute_offre_demande_insertion()
    iafe_data = compute_iafe()
    rf = compute_region_features()
    ind_wide = build_indicateurs_sup()
    wb = build_wb_indicators()

    offre_score, insertion_score = od["offre_score"], od["insertion_score"]
    budget_score, budget_val = iafe_data["budget_score"], iafe_data["budget_val"]
    chomage_score, chomage_val = iafe_data["chomage_score"], iafe_data["chomage_val"]
    pop_share = iafe_data["pop_share"]

    iafe_base_reg = iafe_from_pillars(offre_score, budget_score, insertion_score, chomage_score)
    iafe_base_nat = (iafe_base_reg * pop_share).sum()
    rows = []

    for pct, label in [(0.20, "Budget enseignement sup. +20%"), (-0.10, "Budget enseignement sup. -10%")]:
        new_val = budget_val * (1 + pct)
        s, _, _ = score_national_in_history(ind_wide["depense_annuelle_par_etudiant_fcfa"], override_last=new_val)
        reg = iafe_from_pillars(offre_score, s, insertion_score, chomage_score)
        nat = (reg * pop_share).sum()
        changed = reg.rank(ascending=False) != iafe_base_reg.rank(ascending=False)
        rows.append({"Scénario": label, "IAFE national": round(nat, 1), "Δ IAFE national": round(nat - iafe_base_nat, 1),
                      "Classement régional": ", ".join(changed[changed].index) or "inchangé",
                      "Détail": f"Score Budget : {budget_score:.1f} → {s:.1f}/100"})

    new_chom = max(0, chomage_val - 5)
    s, _, _ = score_national_in_history(wb["chomage"]["chomage_diplomes_pct"], invert=True, override_last=new_chom)
    reg = iafe_from_pillars(offre_score, budget_score, insertion_score, s)
    nat = (reg * pop_share).sum()
    changed = reg.rank(ascending=False) != iafe_base_reg.rank(ascending=False)
    rows.append({"Scénario": "Chômage des diplômés -5 points", "IAFE national": round(nat, 1),
                  "Δ IAFE national": round(nat - iafe_base_nat, 1),
                  "Classement régional": ", ".join(changed[changed].index) or "inchangé",
                  "Détail": f"Chômage : {chomage_val:.1f}% → {new_chom:.1f}% (score {chomage_score:.1f} → {s:.1f}/100)"})

    region_cible = offre_score.idxmin()
    rf_sim = rf.copy()
    rf_sim.loc[region_cible, "nb_etablissements"] += 5
    rf_sim["etab_pour_100k_hab"] = (rf_sim["nb_etablissements"] / rf_sim["population_2022"] * 100_000).round(2)
    offre_sim = offre_pillar(rf_sim)
    reg = iafe_from_pillars(offre_sim, budget_score, insertion_score, chomage_score)
    nat = (reg * pop_share).sum()
    changed_expansion = reg.rank(ascending=False) != iafe_base_reg.rank(ascending=False)
    croissance_pct = 5 / rf.loc[region_cible, "nb_etablissements"] * 100
    second_plus_bas = rf.drop(index=region_cible)["etab_pour_100k_hab"].min()
    pop_cible = rf.loc[region_cible, "population_2022"]
    nb_centres_necessaires = int(np.ceil(second_plus_bas * pop_cible / 100_000)) - rf.loc[region_cible, "nb_etablissements"]
    rows.append({"Scénario": f"+5 centres techniques ({region_cible})", "IAFE national": round(nat, 1),
                  "Δ IAFE national": round(nat - iafe_base_nat, 1),
                  "Classement régional": ", ".join(changed_expansion[changed_expansion].index) or "inchangé",
                  "Détail": f"Offre {region_cible} : {offre_score[region_cible]:.1f} → {offre_sim[region_cible]:.1f}/100 (+{croissance_pct:.0f}% du parc)"})

    eff = ind_wide["effectifs_etudiants"].dropna()
    last_eff_year = eff.index[-1]
    last_ratio = ind_wide["ratio_etud_enseignant"].dropna().iloc[-1]
    new_ratio = last_ratio * 1.15
    rows.append({"Scénario": "Effectifs étudiants +15%", "IAFE national": np.nan, "Δ IAFE national": np.nan,
                  "Classement régional": "n/a — hors piliers IAFE",
                  "Détail": f"Ratio étud./enseignant : {last_ratio:.0f}:1 → {new_ratio:.0f}:1 si encadrement inchangé ({last_eff_year})"})

    return {
        "scenarios_df": pd.DataFrame(rows), "iafe_base_nat": iafe_base_nat, "region_cible": region_cible,
        "nb_centres_necessaires": nb_centres_necessaires, "croissance_pct": croissance_pct,
        "changed_expansion": changed_expansion, "rf": rf,
    }


# ------------------------------------------------------------------
# §11 — Machine Learning exploratoire (chômage des diplômés, n=6 ⚠️)
# ------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def build_ml_dataset() -> pd.DataFrame:
    """Constitue le jeu de données ML (§11.1) : interpolation transparente des
    prédicteurs, cible (chômage) JAMAIS interpolée. Les colonnes '__observe'
    indiquent si la valeur était réellement mesurée cette année (True) ou
    interpolée/extrapolée (False)."""
    wb = build_wb_indicators()
    years_range = range(1995, 2024)
    ml_base = pd.DataFrame(index=years_range)
    ml_base = ml_base.join(wb["inscription"]).join(wb["depense"])
    ml_base.index.name = "annee"
    observed_mask = ml_base.notna()
    ml_interp = ml_base.interpolate(method="linear", limit_direction="both")
    ml_interp["annee"] = ml_interp.index

    target_years = wb["chomage"].index.tolist()
    dataset = ml_interp.loc[target_years].copy()
    dataset["chomage_diplomes_pct"] = wb["chomage"].loc[target_years, "chomage_diplomes_pct"]
    for col in ["taux_brut_inscription_tertiaire", "depense_etud_pct_pib_hab"]:
        dataset[f"{col}__observe"] = observed_mask.reindex(target_years)[col].values
    return dataset


@st.cache_data(show_spinner=False)
def compute_ml_comparison() -> Dict:
    """Compare 5 modèles par validation croisée Leave-One-Out (§11.2) et calcule
    l'importance des variables d'un Random Forest final (§11.3). ⚠️ n=6 : résultats
    strictement indicatifs, cf. avertissement méthodologique du notebook source."""
    from sklearn.linear_model import LinearRegression
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.tree import DecisionTreeRegressor
    from sklearn.model_selection import LeaveOneOut, cross_val_predict
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    try:
        import xgboost as xgb
        has_xgb = True
    except ImportError:
        has_xgb = False

    dataset = build_ml_dataset()
    feature_cols = ["annee", "taux_brut_inscription_tertiaire", "depense_etud_pct_pib_hab"]
    X = dataset[feature_cols].values
    y = dataset["chomage_diplomes_pct"].values
    loo = LeaveOneOut()

    models = {
        "Régression linéaire": LinearRegression(),
        "Arbre de décision": DecisionTreeRegressor(max_depth=2, random_state=42),
        "Random Forest": RandomForestRegressor(n_estimators=200, max_depth=3, random_state=42),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=100, max_depth=2, learning_rate=0.1, random_state=42),
    }
    if has_xgb:
        models["XGBoost"] = xgb.XGBRegressor(n_estimators=100, max_depth=2, learning_rate=0.1, random_state=42, verbosity=0)

    results = []
    for name, model in models.items():
        preds = cross_val_predict(model, X, y, cv=loo)
        mae = mean_absolute_error(y, preds)
        rmse = mean_squared_error(y, preds) ** 0.5
        r2 = r2_score(y, preds)
        results.append({"Modèle": name, "MAE": round(mae, 2), "RMSE": round(rmse, 2), "R²": round(r2, 2)})
    results_df = pd.DataFrame(results).sort_values("MAE")

    rf_final = RandomForestRegressor(n_estimators=300, max_depth=3, random_state=42).fit(X, y)
    importance = pd.Series(rf_final.feature_importances_, index=feature_cols).sort_values(ascending=False)

    return {"results_df": results_df, "importance": importance, "dataset": dataset, "feature_cols": feature_cols}


# ------------------------------------------------------------------
# §12.2 — Segmentation des régions (clustering)
# ------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def compute_clustering() -> Dict:
    """⚠️ Le Togo compte 5 régions : population complète, pas un échantillon. Le
    clustering est un outil de regroupement visuel, pas une découverte généralisable."""
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
    from sklearn.decomposition import PCA

    region_features = compute_region_features()
    feat_cols = ["nb_etablissements", "etab_pour_100k_hab", "diversite_categories",
                 "diversite_secteurs_estimes", "part_creations_recentes_pct", "nb_etab_sup_2018"]
    Xr = StandardScaler().fit_transform(region_features[feat_cols].fillna(0))

    kmeans = KMeans(n_clusters=3, n_init=10, random_state=42).fit(Xr)
    dbscan = DBSCAN(eps=1.6, min_samples=2).fit(Xr)
    agglo = AgglomerativeClustering(n_clusters=3).fit(Xr)

    clusters = region_features.copy()
    clusters["KMeans"] = kmeans.labels_
    clusters["DBSCAN"] = dbscan.labels_
    clusters["Agglomerative"] = agglo.labels_

    coords_pca = PCA(n_components=2, random_state=42).fit_transform(Xr)
    return {"clusters": clusters, "coords_pca": coords_pca, "region_features": region_features}


# ------------------------------------------------------------------
# §16 — Analyse de corrélation entre déterminants
# ------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def compute_correlation_analysis() -> Dict:
    df_etab = clean_etablissements()
    ind_wide = build_indicateurs_sup()
    budget_wide = build_budget_wide()
    wb = build_wb_indicators()

    years_idx = pd.RangeIndex(1995, 2023, name="annee")
    creation_counts = df_etab.dropna(subset=["annee_creation"]).groupby("annee_creation").size()
    offre_cumulee_ts = creation_counts.reindex(
        range(int(df_etab["annee_creation"].min()), 2023), fill_value=0
    ).cumsum().reindex(years_idx)

    corr_df = pd.DataFrame(index=years_idx)
    corr_df["Offre (étab. techniques, cumul)"] = offre_cumulee_ts
    corr_df["Étudiants inscrits"] = ind_wide["effectifs_etudiants"].reindex(years_idx)
    corr_df["Budget / étudiant (FCFA)"] = ind_wide["depense_annuelle_par_etudiant_fcfa"].reindex(years_idx)
    corr_df["Investissement sup. exécuté"] = budget_wide["budget_sup_execute"].reindex(years_idx)
    corr_df["Chômage diplômés (%)"] = wb["chomage"]["chomage_diplomes_pct"].reindex(years_idx)
    corr_df["Insertion estimée (%) ⚠️"] = 100 - wb["chomage"]["chomage_diplomes_pct"].reindex(years_idx)

    circular_pair = {"Chômage diplômés (%)", "Insertion estimée (%) ⚠️"}
    corr_mat = corr_df.corr(min_periods=3)
    n_common = corr_df.notna().astype(int).T.dot(corr_df.notna().astype(int))

    cols = corr_mat.columns.tolist()
    pairs = []
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            r, n = corr_mat.iloc[i, j], n_common.iloc[i, j]
            if pd.notna(r) and {cols[i], cols[j]} != circular_pair:
                pairs.append((cols[i], cols[j], r, int(n)))
    pairs_df = pd.DataFrame(pairs, columns=["Variable 1", "Variable 2", "r", "n"]).sort_values("r", ascending=False)

    influence = {}
    for c in cols:
        vals = [r for (a, b, r, n) in pairs if c in (a, b)]
        if vals:
            influence[c] = np.mean([abs(v) for v in vals])
    influence = pd.Series(influence).sort_values(ascending=False).rename("Influence (|r| moyen)")

    return {"corr_df": corr_df, "corr_mat": corr_mat, "n_common": n_common, "pairs_df": pairs_df, "influence": influence}
