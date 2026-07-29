"""
components/footer.py
=====================
Pied de page commun, affiche en fin de chaque page.
"""
import base64

import streamlit as st

from config import ASSETS_DIR, AUTHOR, INSTITUTION, LOGO_FILES, MINISTERE


def _b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def render_footer():
    st.divider()
    logos = [ASSETS_DIR / filename for filename in LOGO_FILES]
    available_logos = [str(logo) for logo in logos if logo.exists()]
    if available_logos:
        html_imgs = "".join(f'<img src="data:image/jpeg;base64,{_b64(p)}">' for p in available_logos)
        st.markdown(f'<div class="logo-strip">{html_imgs}</div>', unsafe_allow_html=True)
    st.markdown(
        f"""<div class="app-footer">
        🇹🇬 Tableau de bord — Adéquation Formation-Emploi au Togo · Data Challenge Éducation, Défi 2 — 2026<br>
        Auteur : {AUTHOR} · {INSTITUTION} · à destination du {MINISTERE}
        </div>""",
        unsafe_allow_html=True,
    )
