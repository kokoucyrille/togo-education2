"""
config.py
=========
Configuration centrale de l'application "Adéquation Formation-Emploi au Togo".
Toutes les constantes partagées (chemins, palette, poids des indices, sources de
données) sont centralisées ici pour éviter toute duplication entre pages et utils.
"""
from pathlib import Path

# ------------------------------------------------------------------
# Chemins
# ------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
CSS_PATH = ASSETS_DIR / "style.css"

DATA_FILES = {
    "etablissements": DATA_DIR / "file-formations-techniques-etablissements-06-01-2025-17-53-15.csv",
    "dict_champs": DATA_DIR / "formations-techniques-etablissements.csv",
    "repartition_sup": DATA_DIR / "repartition-des-etablissements-denseignement-superieur-ayant-fonctionne-par-type-statut-et-localisation-geographique.csv",
    "indicateurs_sup": DATA_DIR / "observationdata-fspjmfg.csv",
    "budgets": DATA_DIR / "observationdata-acikief.csv",
    "chomage_bm": DATA_DIR / "chomage-des-diplomes-de-lenseignement-superieur-de-la-population-active-totale-diplomee-de-lenseignement-superieur-.csv",
    "depense_bm": DATA_DIR / "depenses-publiques-par-etudiant-enseignement-superieur-du-pib-par-habitant-.csv",
    "inscription_bm": DATA_DIR / "inscriptions-scolaires-enseignement-superieur-brut-.csv",
}

# ------------------------------------------------------------------
# Identité visuelle
# ------------------------------------------------------------------
APP_TITLE = "Adéquation Formation-Emploi — Togo"
APP_ICON = "🎓"
AUTHOR = "DAYO Kokou Cyrille"
INSTITUTION = "TOGO AI LAB"
MINISTERE = "Ministère de l'Éducation Nationale et Ministère de l'Enseignement Supérieur"

PALETTE = ["#005BAC", "#2C7BE5", "#0B6E4F", "#F4B942", "#D64545", "#6C757D"]
REGIONS = ["Maritime", "Plateaux", "Centrale", "Kara", "Savanes"]
REGION_COLORS = dict(zip(REGIONS, PALETTE))

COLOR_PRIMARY = "#0B3D66"
COLOR_ACCENT = "#17A2B8"
COLOR_ORANGE = "#F2994A"
COLOR_DANGER = "#D64545"
COLOR_INFO = "#2C7BE5"
COLOR_SUCCESS = "#0B6E4F"

# 5 sections maximum au menu (voir pages/) — libellés utilisés par la navbar
NAV_SECTIONS = [
    ("1_Accueil", "🏠", "Accueil"),
    ("2_Marche_Emploi", "📉", "Marché de l'emploi"),
    ("3_Formation_Professionnelle", "🏫", "Formation professionnelle"),
    ("4_Analyses_Recommandations", "🧮", "Analyses & Recommandations"),
    ("5_A_Propos", "ℹ️", "À propos"),
]

PRIORITY_COLOR = {"Priorité 1": "#D64545", "Priorité 2": "#F4B942", "Priorité 3": "#005BAC"}

LOGO_FILES = (
    "ministere_education_nationale.jpg",
    "ministere_enseignement_superieur.jpg",
    "togo_ai_lab.jpg",
)

# ------------------------------------------------------------------
# Données externes injectées (RGPH-5, INSEED Togo, nov. 2022)
# ------------------------------------------------------------------
POPULATION_REGION_2022 = {
    "Maritime": 3_534_991,
    "Plateaux": 1_635_946,
    "Savanes": 1_143_520,
    "Kara": 985_512,
    "Centrale": 795_529,
}

# ------------------------------------------------------------------
# Correspondance ville -> région (répartition établissements sup. 2018)
# ------------------------------------------------------------------
VILLE_TO_REGION = {
    "LOMÉ": "Maritime", "TSÉVIÉ": "Maritime",
    "ATAKPAMÉ": "Plateaux", "KPALIMÉ": "Plateaux",
    "SOKODÉ": "Centrale",
    "KARA": "Kara",
    "DAPAONG": "Savanes", "AFANGNAN": "Savanes",
}

# ------------------------------------------------------------------
# Estimation heuristique du secteur (text-mining léger sur le nom de l'établissement)
# ------------------------------------------------------------------
SECTOR_KEYWORDS = {
    "Informatique / Numérique": ["informatique", "numerique", "numérique", "électronique", "electronique",
                                  "réseau inform", "digital", "tic "],
    "Couture / Textile / Mode": ["couture", "coupe", "stylisme", "textile", "mode"],
    "Bâtiment / BTP": ["bâtiment", "batiment", "btp", "construction", "génie civil", "genie civil",
                        "maçonnerie", "maconnerie", "plomberie"],
    "Mécanique / Électricité / Auto": ["mécanique", "mecanique", "automobile", "moteur", "électricité",
                                        "electricite", "froid et climat", "electrotechnique", "électrotechnique"],
    "Hôtellerie / Restauration / Tourisme": ["hôtel", "hotel", "restauration", "cuisine", "tourisme"],
    "Commerce / Gestion / Banque": ["commerce", "gestion", "comptab", "bancaire", "banque", "secrétariat",
                                    "secretariat", "entrepreneur"],
    "Agriculture / Agro-industrie": ["agri", "agro", "élevage", "elevage", "rural"],
    "Santé / Social": ["santé", "sante", "social", "infirm", "sage-femme"],
    "Polytechnique / Multi-filières": ["polytechnique", "industrie"],
}

# ------------------------------------------------------------------
# Renommage des indicateurs longs -> libellés courts
# ------------------------------------------------------------------
IND_RENAME = {
    "Evolution des effectifs des étudiants inscrits": "effectifs_etudiants",
    "Proportion de femmes": "prop_femmes",
    "Rapport de féminité des étudiants": "taux_feminisation",
    "ratio étudiant/ enseignants dans les universités publiques": "ratio_etud_enseignant",
    "%d’étudiants dans les filières scientifiques et technologiques": "pct_filieres_scientifiques",
    "%de filles dans les filières scientifiques et technologiques": "pct_filles_filieres_sci",
    "Nombre d'étudiant  pour 100000 hbts": "etudiants_pour_100k_hab",
    "Nombre d'étudiant des universités publiques pour 100000 hbts": "etudiants_public_pour_100k_hab",
    "Taux d’inscription immédiat des nouveaux bacheliers dans les UPT": "taux_inscription_immediat_bac",
    "Part du Budget alloué à l'enseignement (%)": "part_budget_enseignement",
    "Proportion du Budget de l’enseignement supérieur dans le Budget National et par rapport au PIB": "part_budget_sup_national",
    "Dépenses annuelles par étudiants": "depense_annuelle_par_etudiant_fcfa",
}

BUDGET_RENAME = {
    "BUDGET DE L'ENSEIGNEMENT SUPÉRIEUR VOTÉ": "budget_sup_vote",
    "BUDGET DE L'ENSEIGNEMENT SUPÉRIEUR EXÉCUTÉ": "budget_sup_execute",
    "BUDGET NATIONAL VOTÉ": "budget_national_vote",
    "BUDGET NATIONAL EXÉCUTÉ": "budget_national_execute",
    "BUDGET DU SECTEUR DE L'ÉDUCATION VOTÉ": "budget_education_vote",
    "BUDGET DU SECTEUR DE L'ÉDUCATION EXÉCUTÉ": "budget_education_execute",
    "PRODUIT INTÉRIEUR BRUT (PIB)": "pib",
    "SUBVENTION DE L'ETAT ALLOUÉE AUX ÉTABLISSEMENTS PRIVÉS D'ENSEIGNEMENT SUPÉRIEUR": "subvention_prive",
}

# ------------------------------------------------------------------
# Pondérations des indices composites
# ------------------------------------------------------------------
FEAS_WEIGHTS = {
    "couverture_territoriale": 0.25,
    "diversite_offre": 0.20,
    "dynamisme_creations": 0.15,
    "volume_enseignement_sup": 0.15,
    "encadrement_national": 0.10,
    "orientation_scientifique_national": 0.10,
    "execution_budgetaire_national": 0.05,
}

IAFE_WEIGHTS = {
    "Offre de formation": 0.40,
    "Budget par étudiant": 0.25,
    "Insertion professionnelle": 0.20,
    "Chômage des diplômés": 0.15,
}

NA_TOKENS = {"", "nsp", "n/a", "na", "ne sait pas"}
