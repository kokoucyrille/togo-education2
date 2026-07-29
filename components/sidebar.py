"""
components/sidebar.py
======================
Rendu de la barre laterale : bandeau de logos centre, nom du projet, puis un
menu de navigation unique et cliquable (st.page_link), et enfin les filtres
globaux (delegues a components.filters). Le menu natif Streamlit (liste brute
des fichiers de pages/) est masque via CSS pour n'avoir qu'un seul menu,
propre, dans la sidebar. Les filtres ne sont affiches que sur les pages qui en
tirent une reelle valeur (show_filters=True) ; les autres pages (Accueil,
A propos) appellent render_sidebar(show_filters=False) pour une interface
plus sobre.
"""
import base64

import streamlit as st

from config import APP_ICON, ASSETS_DIR, LOGO_FILES, NAV_SECTIONS
from components.filters import render_page_filters, apply_filters
from utils.preprocessing import clean_etablissements


def _b64(path) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def render_sidebar_brand():
    """Logo du Ministère de l'Éducation Nationale, seul, en grand format, bien
    rond et centre, + nom court du projet."""
    logo_path = ASSETS_DIR / LOGO_FILES[0]
    if logo_path.exists():
        st.markdown(
            f'<div class="sidebar-logos"><img src="data:image/jpeg;base64,{_b64(logo_path)}"></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f'<div class="sidebar-logos-fallback">{APP_ICON}</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-brand">Adéquation<br>Formation-Emploi</div>'
        '<div class="sidebar-brand-sub">Togo · Défi 2 — 2026</div>',
        unsafe_allow_html=True,
    )


def render_page_nav(current: str):
    """Menu de navigation unique, cliquable (st.page_link), en remplacement du
    menu natif Streamlit (masque via CSS pour eviter tout doublon)."""
    for slug, icon, label in NAV_SECTIONS:
        st.page_link(
            f"pages/{slug}.py",
            label=label,
            icon=icon,
            disabled=(slug == current),
        )
    st.markdown("<hr>", unsafe_allow_html=True)


def render_sidebar(show_filters: bool = True, current: str = ""):
    """Affiche la sidebar complete et retourne (df_etab_filtre_ou_complet, filters_dict)."""
    with st.sidebar:
        render_sidebar_brand()
        st.markdown("<hr>", unsafe_allow_html=True)

        if current:
            render_page_nav(current)

        df_etab = clean_etablissements()
        if show_filters:
            filters = render_page_filters(df_etab)
            df_filtered = apply_filters(df_etab, filters)
            st.caption(f"{len(df_filtered)} / {len(df_etab)} établissements")
        else:
            filters = {"regions": [], "annee_range": None}
            df_filtered = df_etab

    return df_filtered, filters
