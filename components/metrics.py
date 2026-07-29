"""
components/metrics.py
======================
Rendu de cartes de metriques (KPI) en grille, style Power BI : icone, titre,
valeur et evolution optionnelle, couleur d'accent. Utilise sur toutes les pages
pour un rendu homogene.
"""
from typing import List, Tuple, Optional

import streamlit as st


def metric_row(metrics: List[Tuple[str, str, str]]):
    """Affiche une rangee de st.metric. `metrics` = liste de tuples
    (label, valeur, delta_ou_aide)."""
    cols = st.columns(len(metrics))
    for col, (label, value, helptext) in zip(cols, metrics):
        with col:
            st.metric(label, value, help=helptext or None)


def kpi_card(label: str, value: str, icon: str = "📌", color: str = "#0B3D66", delta: Optional[str] = None):
    """Carte KPI stylee (icone + titre + valeur + evolution + couleur)."""
    delta_html = ""
    if delta:
        cls = "up" if delta.strip().startswith(("+", "▲")) else ("down" if delta.strip().startswith(("-", "▼")) else "flat")
        delta_html = f'<div class="kpi-delta {cls}">{delta}</div>'
    st.markdown(
        f"""
        <div class="kpi-card" style="border-top-color:{color};">
            <div class="kpi-icon">{icon}</div>
            <div class="kpi-value" style="color:{color};">{value}</div>
            <div class="kpi-label">{label}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_row(items: List[Tuple[str, str, str, str]]):
    """Rangee de kpi_card. `items` = liste de tuples (label, value, icon, color)
    ou (label, value, icon, color, delta)."""
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        label, value, icon, color = item[0], item[1], item[2], item[3]
        delta = item[4] if len(item) > 4 else None
        with col:
            kpi_card(label, value, icon, color, delta)
