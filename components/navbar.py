"""
components/navbar.py
=====================
En-tete de page moderne (style Power BI / Looker Studio) : logos institutionnels
circulaires, titre de la section et badge de repere. Affiche en haut de chacune
des 5 pages du tableau de bord.
"""
import base64

import streamlit as st

from config import ASSETS_DIR, LOGO_FILES


def _b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def render_logo_strip():
    """Affiche les logos officiels (Ministere, partenaire) sous forme circulaire,
    bien alignes, en haut de chaque page."""
    logos = [ASSETS_DIR / filename for filename in LOGO_FILES]
    available = [str(logo) for logo in logos if logo.exists()]
    if not available:
        return
    html_imgs = "".join(f'<img src="data:image/jpeg;base64,{_b64(p)}">' for p in available)
    st.markdown(f'<div class="logo-strip">{html_imgs}</div>', unsafe_allow_html=True)


def render_navbar(title: str, badge: str = "", icon: str = "📄", show_logos: bool = False):
    """En-tete de page coherent : icone + titre + badge de repere (theme traite)."""
    if show_logos:
        render_logo_strip()
    badge_html = f'<div class="badge">{badge}</div>' if badge else ""
    st.markdown(
        f"""
        <div class="page-header">
            <div>
                <div class="title">{icon} {title}</div>
            </div>
            {badge_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
