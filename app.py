"""
app.py
======
Point d'entrée de l'application. Redirige immédiatement vers la page d'accueil
du tableau de bord (pages/1_Accueil.py), qui porte tout le contenu de la page
de garde et configure elle-même la page via setup_page().
"""
import streamlit as st

st.switch_page("pages/1_Accueil.py")
