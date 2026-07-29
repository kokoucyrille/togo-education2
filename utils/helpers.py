"""
utils/helpers.py
=================
Fonctions transverses : boîtes de storytelling (interprétation/conclusion),
boutons de téléchargement (CSV/Excel/PNG), formatage de nombres.
"""
import io

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import APP_TITLE, CSS_PATH


def setup_page(page_title: str, page_icon: str = "📄"):
    """Configuration standard de page (doit être le tout premier appel Streamlit
    du script) + injection du CSS personnalisé. Appelée en tête de chaque page."""
    st.set_page_config(page_title=f"{page_title} · {APP_TITLE}", page_icon=page_icon,
                        layout="wide", initial_sidebar_state="expanded")
    if CSS_PATH.exists():
        st.markdown(f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def story_box(text: str, kind: str = "info") -> None:
    """Encadré d'interprétation affiché systématiquement sous un graphique
    (constat, analyse, implication). `kind` ∈ {info, warning, success, danger}."""
    icons = {"info": "💡", "warning": "⚠️", "success": "✅", "danger": "🚨"}
    css_class = kind if kind in ("warning", "success", "danger") else ""
    st.markdown(
        f"""<div class="story-box {css_class}">
        {icons.get(kind, 'ℹ️')} {text}</div>""",
        unsafe_allow_html=True,
    )


def chart_insights(constats: str, analyse: str, interpretation: str,
                   recommandations: str, actions: str) -> None:
    """Ajoute un bloc décisionnel standard après un graphique."""
    st.markdown(
        "#### Lecture décisionnelle\n"
        f"- **Principaux constats :** {constats}\n"
        f"- **Analyse :** {analyse}\n"
        f"- **Interprétation :** {interpretation}\n"
        f"- **Recommandations :** {recommandations}\n"
        f"- **Actions prioritaires :** {actions}"
    )


def download_buttons(df: pd.DataFrame, base_name: str, key_prefix: str = "") -> None:
    """Ajoute deux boutons de téléchargement (CSV, Excel) pour un DataFrame donné."""
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "⬇️ Télécharger en CSV", data=df.to_csv(index=True).encode("utf-8"),
            file_name=f"{base_name}.csv", mime="text/csv", key=f"{key_prefix}_csv",
            width='stretch',
        )
    with c2:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Données")
        st.download_button(
            "⬇️ Télécharger en Excel", data=buffer.getvalue(),
            file_name=f"{base_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"{key_prefix}_xlsx", width='stretch',
        )


def png_download_button(fig: go.Figure, base_name: str, key: str) -> None:
    """Bouton de téléchargement PNG d'une figure Plotly (nécessite kaleido)."""
    try:
        png_bytes = fig.to_image(format="png", scale=2)
        st.download_button("🖼️ Télécharger le graphique (PNG)", data=png_bytes,
                            file_name=f"{base_name}.png", mime="image/png", key=key)
        pdf_bytes = fig.to_image(format="pdf")
        st.download_button("📄 Télécharger le graphique (PDF)", data=pdf_bytes,
                           file_name=f"{base_name}.pdf", mime="application/pdf",
                           key=f"{key}_pdf")
    except Exception:
        st.caption("Export PNG indisponible dans cet environnement (moteur kaleido manquant).")


def fmt_fr(x, decimals: int = 0) -> str:
    """Formate un nombre avec des espaces comme séparateurs de milliers (convention française)."""
    if pd.isna(x):
        return "n/d"
    return f"{x:,.{decimals}f}".replace(",", " ")


def section_header(icon: str, title: str, subtitle: str = "") -> None:
    """En-tête de section standardisé (icône + titre + sous-titre optionnel)."""
    st.markdown(f"## {icon} {title}")
    if subtitle:
        st.caption(subtitle)
