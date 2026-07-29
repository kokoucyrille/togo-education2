"""
components/cards.py
====================
Cartes de contenu reutilisables (recommandations strategiques, decisions
priorisees, objectifs du projet) — rendu HTML/CSS coherent avec assets/style.css.
"""
from typing import List

import streamlit as st

from config import PALETTE


def recommendation_card(index: int, text: str):
    color = PALETTE[index % len(PALETTE)]
    st.markdown(
        f"""<div class="reco-card" style="border-left-color:{color};">
        <b>{index}.</b> {text}</div>""",
        unsafe_allow_html=True,
    )


def decision_card(titre: str, ou: str, justification: str, color: str = PALETTE[0]):
    st.markdown(
        f"""<div class="decision-card" style="border-left-color:{color};">
        <div class="titre">{titre}</div>
        <div class="ou">📍 {ou}</div>
        <div class="justif">📈 {justification}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def objective_card(icon: str, title: str, description: str):
    st.markdown(
        f"""<div class="objective-card">
        <div class="icon">{icon}</div>
        <div class="title">{title}</div>
        <div class="desc">{description}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def objective_grid(items: List[tuple]):
    cols = st.columns(len(items))
    for col, (icon, title, desc) in zip(cols, items):
        with col:
            objective_card(icon, title, desc)
