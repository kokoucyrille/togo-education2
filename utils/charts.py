"""
utils/charts.py
================
Fonctions génériques de construction de graphiques Plotly, réutilisées par
plusieurs pages pour éviter toute duplication de code (KPI, jauges, classements,
heatmaps de corrélation...).
"""
from typing import List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import PALETTE


def kpi_indicator_grid(indicators: List[tuple], n_cols: int = 4, title: str = "") -> go.Figure:
    """Grille de cartes KPI façon tableau de bord. `indicators` = liste de tuples
    (label, valeur, suffixe)."""
    n_rows = -(-len(indicators) // n_cols)
    fig = make_subplots(
        rows=n_rows, cols=n_cols,
        specs=[[{"type": "indicator"}] * n_cols for _ in range(n_rows)],
        horizontal_spacing=0.05, vertical_spacing=0.35,
    )
    for i, (label, value, suffix) in enumerate(indicators):
        r, c = divmod(i, n_cols)
        fig.add_trace(go.Indicator(
            mode="number",
            value=value if isinstance(value, (int, float)) else 0,
            number={"suffix": suffix, "font": {"size": 32, "color": PALETTE[i % len(PALETTE)]}},
            title={"text": label, "font": {"size": 13}},
        ), row=r + 1, col=c + 1)
    fig.update_layout(height=190 * n_rows, margin=dict(t=50, b=10, l=10, r=10), title=title, title_x=0.5)
    return fig


def gauge_chart(value: float, title: str, color: str = PALETTE[0], suffix: str = "/100") -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value, title={"text": title},
        number={"suffix": suffix, "font": {"size": 38}},
        gauge={"axis": {"range": [0, 100]}, "bar": {"color": color},
               "steps": [{"range": [0, 40], "color": "#f8d7da"}, {"range": [40, 65], "color": "#fff3cd"},
                         {"range": [65, 100], "color": "#d4edda"}]},
    ))
    fig.update_layout(height=300, margin=dict(t=60, b=10))
    return fig


def ranking_bar(df: pd.DataFrame, score_col: str, label_col: Optional[str] = None,
                 title: str = "", color_scale: str = "RdYlGn", orientation: str = "h") -> go.Figure:
    """Barres horizontales classées, dégradé de couleur sur le score."""
    d = df.sort_values(score_col, ascending=True)
    y = d[label_col] if label_col else d.index
    fig = go.Figure(go.Bar(
        x=d[score_col], y=y, orientation=orientation,
        marker=dict(color=d[score_col], colorscale=color_scale, cmin=0, cmax=100),
        text=d[score_col].round(1), textposition="outside",
    ))
    fig.update_layout(title=title, height=max(320, 40 * len(d)), margin=dict(t=60, b=10))
    return fig


def correlation_heatmap(corr_mat: pd.DataFrame, n_common: pd.DataFrame, title: str = "") -> go.Figure:
    cols = corr_mat.columns.tolist()
    text_matrix = [[(f"{corr_mat.iloc[i, j]:.2f}<br>(n={int(n_common.iloc[i, j])})" if pd.notna(corr_mat.iloc[i, j]) else "n<3")
                    for j in range(len(cols))] for i in range(len(cols))]
    fig = go.Figure(go.Heatmap(
        z=corr_mat.values, x=cols, y=cols, text=text_matrix, texttemplate="%{text}",
        colorscale="RdBu", zmid=0, zmin=-1, zmax=1, textfont=dict(size=10), colorbar=dict(title="r"),
    ))
    fig.update_layout(title=title, height=560, margin=dict(t=60, b=10), xaxis=dict(tickangle=-25))
    return fig


def radar_chart(scores_df: pd.DataFrame, categories: List[str], color_map: dict, title: str = "") -> go.Figure:
    fig = go.Figure()
    for r in scores_df.index:
        vals = scores_df.loc[r, categories].tolist()
        fig.add_trace(go.Scatterpolar(r=vals + [vals[0]], theta=categories + [categories[0]],
                                       fill="toself", name=r, line=dict(color=color_map.get(r))))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), title=title,
                       height=520, margin=dict(t=60, b=10))
    return fig
